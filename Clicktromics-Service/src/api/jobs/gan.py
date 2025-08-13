from fastapi import APIRouter, Depends, Form
from src.logger import Logger

from fastapi.responses import JSONResponse
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.documents.profile import AuthProfile, Name
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.helper.aws.s3 import get_s3_service, S3Service
from src.helper.aws.batch import submit_job
from src.config import JOB_QUEUE_ARN_GPU, DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_GAN, USE_AWS
from src.tasks.batch.update import update_job_status
from src.tasks.gan import run_gan_job

log = Logger.get_logger()

router = APIRouter(prefix="/gan", tags=["GAN job"])

@router.post("")
async def submit_job(
    file: str = Form(...),
    repo: JobRepo = Depends(lambda: JobRepo()),
    user: AuthProfile = Depends(lambda: AuthProfile(email="layth@prepaire.com", name=Name(first="Layth", last=""))),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    s3: S3Service = Depends(get_s3_service),
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - gan: Used for GAN-based peptide generation.
            input: Input file for GAN processing.
            output: GAN-generated output file.
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.GAN), user_email=user.email)
        log.info(f"Creating Job: {job}")
        job.inputs = {
                "file": file
        } 

        if USE_AWS:
            job.outputs = {
                "files": ["gan/" + job.job_id + "/" + s3.generate_valid_object_name("gan_output.json")]
            }

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_GAN,
                [
                    {"name": "INPUT", "value": file},
                    {"name": "OUTPUT", "value": job.outputs["files"][0]},
                    {"name": "BUCKET", "value": DEFAULT_BUCKET_NAME}
                ],
                job.type.name.value,
                job.job_id
            )
            if not response:
                raise Exception("Error when submitting job to AWS.")
                            
            job.batch_id = response['jobId']
            task = update_job_status.delay(job.job_id, job.batch_id)
        else:
            log.warning("AWS is disabled.")
            task = run_gan_job.delay(job.job_id, file)

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