from fastapi import APIRouter, Depends, Form, HTTPException
import traceback

from fastapi.responses import JSONResponse
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.documents.profile import AuthProfile, Name
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
from src.helper.aws.s3 import get_s3_service, S3Service
from src.helper.aws.batch import submit_job
from src.config import JOB_QUEUE_ARN_GPU, DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_GENETIC, USE_AWS
from src.tasks.batch.update import update_job_status
from src.tasks.genetic.tasks import run_genetic_job
from src.logger import Logger

log = Logger.get_logger()

from typing import Optional
from enum import Enum

router = APIRouter(prefix="/genetic", tags=["Genetic File Processing job"])

class GeneticAnnotationPipelineType(str, Enum):
    VCF2RESULT = "vcf2result"
    BAM2RESULTS = "bam2results"
    FASTQ2RESULTS = "fastq2results"

@router.post("",
    summary="Submit a Genetic File Processing Job",
    description="""
Submit a long-running background job for processing genetic data from VCF or FASTQ files.  
This endpoint handles three pipeline types:
- `vcf2result`: Processes a single `.vcf` or `.vcf.gz` file (Vep → Annotation).
- `bam2results`: Processes a `.bam` files (Variant Calling BAM → Vep → Annotation).
- `fastq2results`: Processes a pair of `.fastq` or `.fastq.gz` files (Variant Calling FATSQ → Variant Calling BAM  → Vep → Annotation).

### Input Parameters (multipart/form-data):
- **first_file** (`str`, required): Path or identifier of the first uploaded file.
  - For `vcf2result`: a `.vcf` or `.vcf.gz` file.
  - For `bam2results`: a `.bam`.
  - For `fastq2results`: the first `.fastq` or `.fastq.gz` file.
- **second_file** (`str`, optional): Only required for `fastq2results`. Second `.fastq` or `.fastq.gz` file.
- **flag** (`PipelineType`, required): Type of pipeline to execute.
  - `vcf2result` for VCF-based analysis.
  - `bam2results` for BAM-based analysis.
  - `fastq2results` for FASTQ-based analysis.

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
    first_file: str = Form(...),
    second_file: Optional[str] = Form(None),
    flag: GeneticAnnotationPipelineType = Form(...),
    repo: JobRepo = Depends(lambda: JobRepo()),
    user: AuthProfile = Depends(lambda: AuthProfile(email="layth@prepaire.com", name=Name(first="Layth", last=""))),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    s3: S3Service = Depends(get_s3_service),
):  
    try:
        if flag.value == GeneticAnnotationPipelineType.FASTQ2RESULTS.value:
            if not second_file:
                raise HTTPException(status_code=400, detail=f"second_file should not be empty when selecting {GeneticAnnotationPipelineType.FASTQ2RESULTS.value}")
        
        job = JobDocument(type=JobType(name=JobTypeEnum.GENETIC), user_email=user.email)
        log.info(f"Creating Job: {job}")

        job.inputs = {
                "files": [first_file, second_file ] if second_file else [first_file]
        }
        
        if USE_AWS:
            job.outputs = {
                "files": ["genetic/" + job.job_id + "/" + s3.generate_valid_object_name("genetic_output")]
            }

            parameters = [
                {"name": "FIRST_FILE", "value": first_file},
                {"name": "FLAG", "value": flag.value},
                {"name": "OUTPUT", "value": job.outputs["files"][0]},
                {"name": "BUCKET", "value": DEFAULT_BUCKET_NAME}
            ]
            
            if second_file:
                parameters.append({"name": "SECOND_FILE", "value": second_file})

            response = submit_job(
                JOB_QUEUE_ARN_GPU,
                JOB_DEFINITION_ARN_GENETIC,
                parameters,
                job.type.name.value,
                job.job_id
            )
            if not response:
                raise Exception("Error when submitting job to AWS.")
                            
            job.batch_id = response['jobId']
            task = update_job_status.delay(job.job_id, job.batch_id)
        else:
            log.warning("AWS is disabled.")
            if second_file:
                task = run_genetic_job.delay(job.job_id, flag, first_file, second_file)
            else:
                task = run_genetic_job.delay(job.job_id, flag, first_file)

        job.task_id = task.id
        await repo.save(job)

        return JSONResponse(content={"status": "success", "data":{"job_id": job.job_id, "message": "Job submitted successfully"}}, status_code=200)
    except Exception as e:
        error_message = str(e) or "Unknown error occurred"
        tb = traceback.format_exc()
        log.error(f"Error in submit_job: {error_message}\nTraceback:\n{tb}")
        return JSONResponse(
            content={"status": "error", "message": f"Error encountered during processing: {error_message}"},
            status_code=500,
        ) 