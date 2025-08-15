from fastapi import APIRouter, Depends, Form, HTTPException
from src.logger import Logger

from fastapi.responses import JSONResponse
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.auth.dependencies import require_user_context
from src.documents.profile import AuthProfile
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.helper.aws.s3 import get_s3_service, S3Service
from src.helper.aws.batch import submit_job
from src.config import JOB_QUEUE_ARN_GPU, DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_FASTQ_PROCESSING, USE_AWS
from src.tasks.batch.update import update_job_status
from src.tasks.variant_calling_fastq.tasks import run_variant_calling_fastq_job
from src.request_model import JobSuccessResponse, JobErrorResponse, JobData

log = Logger.get_logger()

router = APIRouter(prefix="/variant/fastq", tags=["Variant matching job"])

@router.post("",
    response_model=JobSuccessResponse,
    responses={
        200: {"description": "Job submitted successfully", "model": JobSuccessResponse},
        400: {"description": "Bad request", "model": JobErrorResponse},
        500: {"description": "Internal server error", "model": JobErrorResponse}
    },
    summary="Submit a FASTQ Variant Calling job",
    description="""
Submit a long-running background job for variant calling from FASTQ files.

### Input Parameters (multipart/form-data):
- **file_r1** (`str`, required): Path or identifier of the first FASTQ file (R1).
- **file_r2** (`str`, required): Path or identifier of the second FASTQ file (R2).

### Behavior:
- A job is created and stored in the system.
- Corresponding Celery tasks are chained and executed
- A unique `job_id` is returned to track the job.

### Responses:
- `200 OK`: Job successfully submitted.
- `400 Bad Request`: Invalid input parameters.
- `500 Internal Server Error`: Server error during processing.
    """
)
async def submit_job(
    file_r1: str = Form(...),
    file_r2: str = Form(...),
    repo: JobRepo = Depends(lambda: JobRepo()),
    current_user: AuthProfile = require_user_context(),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    s3: S3Service = Depends(get_s3_service),
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - variant_calling_matching: Used after uploading a fast file (.fastq) or compressed FASTQ file (.fastq.gz).
            input: fast file (.fastq) or compressed FASTQ file (.fastq.gz).
            output: BAM file (.bam).
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.FASTQ_PROCESSING), user_email=current_user.email)
        log.info(f"Creating Job: {job}")
        job.inputs = {
                "file": [
                    file_r1,
                    file_r2
                ]
        } 

        if USE_AWS:
            job.outputs = {
                "files": ["variant_calling_fastq/" + job.job_id + "/" + s3.generate_valid_object_name("variant_output.bam")]
            }

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_FASTQ_PROCESSING,
                [
                    {"name": "INPUT_R1", "value": file_r1},
                    {"name": "INPUT_R2", "value": file_r2},
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
            task = run_variant_calling_fastq_job.delay(job.job_id, file_r1, file_r2)

        job.task_id = task.id
        await repo.save(job)

        return JobSuccessResponse(
            data=JobData(
                job_id=job.job_id,
                message="Job submitted successfully"
            )
        )
    except Exception as e:
        error_message = str(e) or "Unknown error occurred"
        log.error(f"Error in /variant/fastq: {error_message}")
        raise HTTPException(
            status_code=500,
            detail=f"Error encountered during processing: {error_message}"
        ) 