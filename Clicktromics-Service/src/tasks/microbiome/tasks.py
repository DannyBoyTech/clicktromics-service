from src.logger import Logger
from src.celery_client import Celery
from src.redis_client import Redis
from src.repo.jobs import JobRepo, JobDocument
from src.helper.aws.s3 import get_s3_service
from src.config import LOCAL_STORAGE_PATH, DEFAULT_VOLUME_NAME, DEFAULT_BUCKET_NAME
from src.documents.jobs import JobStatusEnum
from src.docker_client import get_docker_client
from src.helper.file_adapter import get_storage_adapter
from src.tasks import initialize_job, cleanup_temp_files, execute_docker_job

log = Logger.get_logger()
tasks = Celery.get_client()

@tasks.task(bind=True)
def run_microbiome_job(self, job_id: str, file_r1: str, file_r2: str, method: str):
    """
    Run microbiome analysis job
    """
    try:
        # Initialize job
        job = initialize_job(job_id, self.request.id)
        
        # Process microbiome data
        # This is a placeholder - implement actual microbiome analysis logic
        log.info(f"Processing microbiome data: {file_r1}, {file_r2}, method: {method}")
        
        # Update job status to succeeded
        job.status = JobStatusEnum.SUCCEEDED.value
        job.save()
        
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        log.error(f"Error in microbiome job {job_id}: {str(e)}")
        job.status = JobStatusEnum.FAILED.value
        job.error_message = str(e)
        job.save()
        raise 