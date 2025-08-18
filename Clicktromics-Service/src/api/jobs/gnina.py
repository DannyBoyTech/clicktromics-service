from fastapi import APIRouter, Depends, HTTPException, Form
from src.logger import Logger

log = Logger.get_logger()

from fastapi.responses import JSONResponse
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.auth.dependencies import require_user_context
from src.documents.profile import AuthProfile
from src.helper.aws.batch import submit_job
from src.helper.aws.s3 import get_s3_service, S3Service
from src.config import DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_GNINA, JOB_QUEUE_ARN_GPU, USE_AWS
from src.tasks.batch.update import update_job_status
from src.utils import get_remote_file_content
from src.request_model import DockingJobRequest
from io import BytesIO
from src.tasks.gnina import run_gnina_job
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.tasks import cleanup_temp_files
import tempfile
import os
import json

router = APIRouter(prefix="/gnina", tags=["Gnina job"])

@router.post("/")
async def submit_gnina_job(
    request: DockingJobRequest,
    repo: JobRepo = Depends(lambda: JobRepo()),
    s3: S3Service = Depends(get_s3_service),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    current_user: AuthProfile = require_user_context()
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - gnina: Used for docking payload with antibody, only after a successful click response and successful Homelette job.
            input: Homelette PDB file and Musite JSON file.
            output: Gnina-generated PDB file and JSON file (affinity result).
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.GNINA), user_email=current_user.email)
        log.info(f"Creating Job: {job}")

        resNumber = ""
        if request.musite_file:
            if request.musite_res_number:

                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
                    adapter.download(request.musite_file, tf.name)
                    json_tmp_path = tf.name

                with open(json_tmp_path, "r") as f:
                    file_content = json.loads(f.read())

                if len(file_content["residue"]) >= request.musite_res_number > 0:
                    resNumber = file_content["residue"][request.musite_res_number - 1]["resNumber"]
                else:
                    raise HTTPException(status_code=400, detail=f"musite_res_number is not correct should be bigger than 0 and not more than {len(file_content["residue"])}")
            else:
                raise HTTPException(status_code=400, detail="Could not found musite_res_number, please send musite_res_number when adding musite_file")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            tf.write(json.dumps({"spacc": request.spacc, "resNumber": resNumber}).encode('utf-8'))
            json_input_tmp_path = tf.name

        objectname = "gnina/" + job.job_id + "/" + s3.generate_valid_object_name("gnina_input.json")
        adapter.upload(json_input_tmp_path, objectname)
        
        job.inputs = {
            "payload": {
                "SPACC": request.spacc
            },
            "compound":{
                "pdb_file": request.pdb_file,
                "musite_json_file": request.musite_file or ""
            }
        }


        if USE_AWS:
            job.outputs = {
                "files": [
                    "gnina/" + job.job_id + "/" + s3.generate_valid_object_name("gnina_output.json"),
                    "gnina/" + job.job_id + "/" + s3.generate_valid_object_name("gnina_output.pdb")
                ]
            }

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_GNINA,
                [
                    {"name": "INPUT", "value": request.pdb_file},
                    {"name": "INPUT_JSON", "value": objectname},
                    {"name": "OUTPUT", "value": job.outputs["files"][1]},
                    {"name": "OUTPUT_JSON", "value": job.outputs["files"][0]},
                    {"name": "BUCKET", "value": DEFAULT_BUCKET_NAME}
                ],
                job.type.name.value,
                job.job_id
            )
            if not response:
                raise HTTPException(detail="Error when submitting job to AWS.", status_code=500)
            
            job.batch_id = response['jobId']
            task = update_job_status.delay(job.job_id, job.batch_id)
        else:
            log.warning("AWS is disabled.")
            task = run_gnina_job.delay(job.job_id, request.pdb_file, objectname)

        job.task_id = task.id
        await repo.save(job)

        return JSONResponse(content={"status": "success", "data":{"job_id": job.job_id, "message": "Job submitted successfully"}}, status_code=200)
    except Exception as e:
        error_message = str(e) or "Unknown error occurred"
        log.error(f"Error in submit_job: {error_message}")
        return JSONResponse(
            content={"status": "error", "message": f"Error encountered during processing: {error_message}"},
            status_code=500,
        )
    finally:
        cleanup_temp_files(
                output_dir="",
                files=[json_tmp_path, json_input_tmp_path]
            )