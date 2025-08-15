from fastapi import APIRouter, Depends, HTTPException, Form
from src.logger import Logger

log = Logger.get_logger()

from fastapi.responses import JSONResponse
from src.tasks import cleanup_temp_files
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.documents.profile import AuthProfile
from src.helper.aws.batch import submit_job
from src.helper.aws.s3 import get_s3_service, S3Service
from src.config import DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_GAN, JOB_QUEUE_ARN_GPU, USE_AWS
from src.tasks.batch.update import update_job_status
from src.request_model import PeptideJobRequest, JobSuccessResponse, JobErrorResponse, JobData
from src.tasks.gan import run_gan_job
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.auth.dependencies import require_user_context
import tempfile
import os
import json

router = APIRouter(prefix="/gan", tags=["Peptide generating job"])

@router.post("", 
    response_model=JobSuccessResponse,
    responses={
        200: {"description": "Job submitted successfully", "model": JobSuccessResponse},
        400: {"description": "Bad request", "model": JobErrorResponse},
        500: {"description": "Internal server error", "model": JobErrorResponse}
    },
    summary="Submit a GAN/Peptide Generation job",
    description="""
Submit a long-running background job for GAN-based peptide generation.

### Input Parameters:
- **peptide_protein_sequence** (`str`): Gene protein sequence with the desired peptide length
- **peptide_length** (`int`): Length of the peptide to generate (default: 15)

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
async def submitgan_job(
    request: PeptideJobRequest,
    repo: JobRepo = Depends(lambda: JobRepo()),
    s3: S3Service = Depends(get_s3_service),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    current_user: AuthProfile = require_user_context()
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - peptide: Can be used directly with the correct provided data.
            input: Gene protein sequence with the desired peptide length.
            output: Peptide sequence.
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.PEPTIDE), user_email=current_user.email)
        log.info(f"Creating Job: {job}")

        peptide_length = min(request.peptide_length, 50)
        num_binders = 1
        if 15 == peptide_length:
            num_binders = 5
        elif 15 < peptide_length < 20:
            num_binders = 4
        elif 20 == peptide_length:
            num_binders = 3
        elif 20 < peptide_length < 25:
            num_binders = 2
        elif 25 <= peptide_length:
            num_binders = 1

        job.inputs = {
            "peptide_length": peptide_length,
            "num_binders": num_binders,
            "protein_seq": request.peptide_protein_sequence,
            "top_k": 3
        }

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            tf.write(json.dumps(job.inputs).encode('utf-8'))
            tmp_path = tf.name

        objectname = "peptide_generation/" + job.job_id + "/" + s3.generate_valid_object_name("peptide_generation_input.json")
        adapter.upload(tmp_path, objectname)


        if USE_AWS:
            job.outputs = {
                "files": ["peptide_generation/" + job.job_id + "/" + s3.generate_valid_object_name("peptide_generation_output.json")],
            }

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_GAN,
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
            task = run_gan_job.delay(job.job_id, objectname)

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
        log.error(f"Error in submit_job: {error_message}")
        raise HTTPException(
            status_code=500,
            detail=f"Error encountered during processing: {error_message}"
        )
    finally:
        cleanup_temp_files(
                output_dir="",
                files=[tmp_path]
            )