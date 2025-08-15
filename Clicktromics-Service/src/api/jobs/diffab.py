from fastapi import APIRouter, Depends, HTTPException, Form
from src.logger import Logger

log = Logger.get_logger()

from fastapi.responses import JSONResponse
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.auth.dependencies import require_user_context
from src.documents.profile import AuthProfile
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.helper.aws.batch import submit_job
from src.helper.aws.s3 import get_s3_service, S3Service
from src.config import DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_DIFFAB, JOB_QUEUE_ARN_GPU, USE_AWS
from src.tasks.batch.update import update_job_status
from src.tasks.diffab import run_diffab_job
import tempfile
from src.tasks import cleanup_temp_files

router = APIRouter(prefix="/diffab", tags=["Diffab job"])

@router.post("")
async def submit_job(
    file: str = Form(...),
    repo: JobRepo = Depends(lambda: JobRepo()),
    s3: S3Service = Depends(get_s3_service),
    current_user: AuthProfile = require_user_context()
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - diffab: Used after a successful input response or successful Boltz job.
            input: PDB file from input or Boltz.
            output: Diffab-generated PDB file.
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.DIFFAB), user_email=current_user.email)
        log.info(f"Creating Job: {job}")

        job.inputs = {
                "pdb_file": file,
                "n": 1
        }

        if USE_AWS:
            job.outputs = {
                "files":[
                    "diffab/" + job.job_id + "/" + s3.generate_valid_object_name("top1.pdb"),
                    "diffab/" + job.job_id + "/" + s3.generate_valid_object_name("results.json")
                ]
            }

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_DIFFAB,
                [
                    {"name": "INPUT", "value": job.inputs["pdb_file"]},
                    {"name": "OUTPUT", "value": job.outputs["files"][0]},
                    {"name": "JSON_OUTPUT", "value": job.outputs["files"][1]},
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
            task = run_diffab_job.delay(job.job_id, file)

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