from fastapi import APIRouter, Depends, HTTPException, Form
from src.logger import Logger

log = Logger.get_logger()

from fastapi.responses import JSONResponse
from src.tasks import cleanup_temp_files
from src.documents.jobs import JobType, JobDocument, JobTypeEnum
from src.repo.jobs import JobRepo
from src.documents.profile import AuthProfile, Name
from src.helper.aws.batch import submit_job
from src.helper.aws.s3 import get_s3_service, S3Service
from src.config import DEFAULT_BUCKET_NAME, JOB_DEFINITION_ARN_GAN, JOB_QUEUE_ARN_GPU, USE_AWS
from src.tasks.batch.update import update_job_status
from src.request_model import PeptideJobRequest
from src.tasks.gan import run_gan_job
from src.helper.file_adapter import get_storage_adapter, StorageAdapter
import tempfile
import os
import json

router = APIRouter(prefix="/gan", tags=["Peptide generating job"])

@router.post("")
async def submitgan_job(
    request: PeptideJobRequest,
    repo: JobRepo = Depends(lambda: JobRepo()),
    s3: S3Service = Depends(get_s3_service),
    adapter: StorageAdapter = Depends(get_storage_adapter),
    user : AuthProfile = Depends(lambda: AuthProfile(email="layth@prepaire.com", name=Name(first="Layth", last="")))
):  
    """
       Submit a long-running process and provide a unique job ID to track the status of the process.
        - peptide: Can be used directly with the correct provided data.
            input: Gene protein sequence with the desired peptide length.
            output: Peptide sequence.
    """
        
    try:
        job = JobDocument(type=JobType(name=JobTypeEnum.PEPTIDE), user_email=user.email)
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
                files=[tmp_path]
            )