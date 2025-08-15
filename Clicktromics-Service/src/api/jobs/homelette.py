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
from src.config import DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_HOMELETTE, JOB_QUEUE_ARN_CPU, USE_AWS
from src.tasks.batch.update import update_job_status
from src.helper.pdb_convert import convert
from src.utils import get_remote_file_content
from io import BytesIO
from src.tasks.homelette import run_homelette_job
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.tasks import cleanup_temp_files
import tempfile
import os
import json

router = APIRouter(prefix="/homelette", tags=["Homelette job"])

@router.post("")
async def submit_homelette_job(
    file: str = Form(...),
    repo: JobRepo = Depends(lambda: JobRepo()),
    s3: S3Service = Depends(get_s3_service),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    current_user: AuthProfile = require_user_context()
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - homelette: Used only after a successful Diffab job.
            input:  Diffab-generated PDB file.
            output: Homelette-generated PDB file.
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.HOMELETTE), user_email=current_user.email)
        log.info(f"Creating Job: {job}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdb") as tf:
            adapter.download(file, tf.name)
            pdb_tmp_path = tf.name

        with open(pdb_tmp_path, "rb") as f:
            chain = convert(f, "homelette")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            tf.write(json.dumps({**chain}).encode('utf-8'))
            json_tmp_path = tf.name

        objectname = "homelette_genearted/" + job.job_id + "/" + s3.generate_valid_object_name("homelette_input.json")
        adapter.upload(json_tmp_path, objectname)

        job.inputs = {
            **chain
        }

        if USE_AWS:
            job.outputs = {
                "files":  "homelette_genearted/" + job.job_id + "/" + s3.generate_valid_object_name("homelette_output.pdb"),
            }

            response = submit_job(
                JOB_QUEUE_ARN_CPU,
                JOB_DEFINITION_ARN_HOMELETTE,
                [
                    {"name": "INPUT", "value": objectname},
                    {"name": "OUTPUT", "value": job.outputs["files"][0]},
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
            task = run_homelette_job.delay(job.job_id, objectname)

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
                files=[pdb_tmp_path, json_tmp_path]
            )