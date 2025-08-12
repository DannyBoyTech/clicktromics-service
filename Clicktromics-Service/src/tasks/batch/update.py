from src.logger import Logger 
import time
from celery import states
from src.redis_client import Redis
from src.celery_client import Celery
from src.mongo_client import Mongo
from src.helper.aws.batch import poll_job
from src.repo.jobs import JobRepo
from src.documents.jobs import JobStatusEnum

redis_client = Redis.get_client()
tasks = Celery.get_client()
log = Logger.get_logger()
timeout=7200

@tasks.task(bind=True)
def update_job_status(self, job_id: str, batch_job_id: str):
    log.info(f"Running job with id {job_id} for batch id {batch_job_id} ...")
    # Ensure MongoDB client is initialized
    if not Mongo.is_initialized():
        log.warning("⚠️ MongoDB client not initialized. Initializing now.")
        Mongo._initialize_sync_client()
        log.info("✅ MongoDB client initialized.")

    try:

        job_repo = JobRepo()
        job = job_repo.find_by_job_id_sync(job_id=job_id)
        log.info(f"Type: {job.type.name}")
        job.status = JobStatusEnum.RUNNABLE.value
        job_repo.update_sync(job)
        self.update_state(state=states.STARTED)

        start = time.time()
        while True:
            if time.time() - start > timeout:
                log.error(f"Polling timed out for {job_id}.")
                raise Exception(f"Polling timed out for {job_id}.")
            
            batch_job = poll_job(batch_job_id)

            container = batch_job.get('container', {})
            exit_code = container.get('exitCode')
            if exit_code is not None:
                log.error(f"Exit code: {exit_code}")

            status = batch_job['status']
            if status in [JobStatusEnum.STARTING.value, JobStatusEnum.RUNNING.value]:
                self.update_state(state=states.STARTED)
                job.status = JobStatusEnum.STARTING.value
                job_repo.update_sync(job)
            elif status in [JobStatusEnum.SUCCEEDED.value]:
                self.update_state(state=states.SUCCESS)
                job.status = JobStatusEnum.SUCCEEDED.value
                job_repo.update_sync(job)
                break
            elif status in [JobStatusEnum.FAILED.value]:
                raise Exception("Status Failed")

    except Exception as e:
        job.status = JobStatusEnum.FAILED.value
        job_repo.update_sync(job)
        log.error(f"boltz request failed: {str(e)}")
        self.update_state(state=states.FAILURE, meta=str(e))