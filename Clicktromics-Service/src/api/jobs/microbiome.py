from fastapi import APIRouter, Depends, Form
from src.logger import Logger

from fastapi.responses import JSONResponse
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.documents.profile import AuthProfile, Name
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.helper.aws.s3 import get_s3_service, S3Service
from src.helper.aws.batch import submit_job
from src.config import JOB_QUEUE_ARN_GPU, DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_MICROBIOME, USE_AWS
from src.tasks.batch.update import update_job_status
from src.tasks.microbiome.tasks import run_microbiome_job

log = Logger.get_logger()

from enum import Enum

router = APIRouter(prefix="/microbiome", tags=["Microbiome File Processing job"])

class MethodEnum(str, Enum):
    SHOTGUN = "shotgun"
    _16S = "16s"

@router.post("",
    summary="Submit a Microbiome File Processing job",
    description="""
Submit a long-running background job for processing genetic data from VCF or FASTQ files.  
This endpoint handles two pipeline types:
- `shotgun`: Processes a pair of `.fastq` or `.fastq.gz` files (Microbiome SHOTGUN).
- `16s`: Processes a pair of `.fastq` or `.fastq.gz` files (Microbiome SHOTGUN).

### Input Parameters (multipart/form-data):
- **file_r1** (`str`, required): the first `.fastq` or `.fastq.gz` file.
- **file_r2** (`str`, required): the second `.fastq` or `.fastq.gz` file.
- **method** (`Method`, required): Type of pipeline to execute.
  - `shotgun`
  - `16s`

### Behavior:
- A job is created and stored in the system.
- Corresponding Celery tasks are chained and executed
- A unique `job_id` is returned to track the job.

### Responses:
- `200 OK`: Job successfully submitted.
  ```json
  {
    "status": "success",
    "data": {
      "job_id": "<uuid>",
      "message": "Job submitted successfully"
    }
  }
  """
)
async def submit_job(
    file_r1: str = Form(...),
    file_r2: str = Form(...),
    method: MethodEnum = Form(...),
    repo: JobRepo = Depends(lambda: JobRepo()),
    user: AuthProfile = Depends(lambda: AuthProfile(email="layth@prepaire.com", name=Name(first="Layth", last=""))),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    s3: S3Service = Depends(get_s3_service),
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - microbiome: Used after uploading a fast file (.fastq) or compressed FASTQ file (.fastq.gz).
            input: fast file (.fastq) or compressed FASTQ file (.fastq.gz).
            output: Text file (.txt) in case shotgun or csv and tsv in case 16s .
    """
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.MICROBIOME), user_email=user.email)
        log.info(f"Creating Job: {job}")
        job.inputs = {
                "file": [
                    file_r1,
                    file_r2
                ]
        } 

        if USE_AWS:
            job.outputs = {
                "files": ["microbiome/" + job.job_id + "/" + s3.generate_valid_object_name("microbiome_output")]
            }

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_MICROBIOME,
                [
                    {"name": "INPUT_R1", "value": file_r1},
                    {"name": "INPUT_R2", "value": file_r2},
                    {"name": "METHOD", "value": method.value},
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
            task = run_microbiome_job.delay(job.job_id, file_r1, file_r2, method.value)

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