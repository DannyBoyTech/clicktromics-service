from fastapi import APIRouter, Depends, HTTPException
from src.logger import Logger

log = Logger.get_logger()

from fastapi.responses import JSONResponse
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.request_model import BoltzJobRequest
from src.auth.dependencies import require_user_context
from src.documents.profile import AuthProfile
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.helper.aws.s3 import get_s3_service, S3Service
from src.helper.aws.batch import submit_job
from src.config import JOB_QUEUE_ARN_GPU, DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_BOLTZ, USE_AWS
from src.tasks.batch.update import update_job_status
import json
from src.tasks.boltz import run_boltz_job
import tempfile
from src.tasks import cleanup_temp_files
from io import BytesIO

router = APIRouter(prefix="/boltz", tags=["Boltz job"])

@router.post("")
async def submit_boltz_job(
    request: BoltzJobRequest,
    repo: JobRepo = Depends(lambda: JobRepo()),
    current_user: AuthProfile = require_user_context(),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    s3: S3Service = Depends(get_s3_service),
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - boltz: Can be used directly with the correct provided data.
            input: Protein sequence.
            output: Boltz-generated PDB file.
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.BOLTZ), user_email=current_user.email)
        log.info(f"Creating Job: {job}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            tf.write(json.dumps({"sequences": [request.boltz_sequence]}).encode('utf-8'))
            json_tmp_path = tf.name

        objectname = "boltz/" + job.job_id + "/" + s3.generate_valid_object_name("boltz_input.json")
        adapter.upload(json_tmp_path, objectname)

        job.inputs = {
            "sequence": request.boltz_sequence,
            "json_file": objectname
        }

        if USE_AWS:
            job.outputs = {
                "files": ["boltz/" + job.job_id + "/" + s3.generate_valid_object_name("boltz_output.pdb")]
            }

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_BOLTZ,
                [
                    {"name": "INPUT", "value": job.inputs["json_file"]},
                    {"name": "OUTPUT", "value": job.outputs["files"][0]},
                    {"name": "BUCKEt", "value": DEFAULT_BUCKET_NAME}
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
            task = run_boltz_job.delay(job.job_id, objectname)
            

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
            files=[json_tmp_path]
        )