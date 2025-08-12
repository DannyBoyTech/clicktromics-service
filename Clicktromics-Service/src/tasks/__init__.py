from src.mongo_client import Mongo
from src.utils import system_resources_ok
from src.logger import Logger 
from src.repo.jobs import JobRepo
from src.docker_client import managed_long_container
from datetime import datetime, timezone
from src.tasks.signal import SignalHandler
import os
import shutil
import time

log = Logger.get_logger()

def initialize_job(job_id):
    log.info(f"Starting {job_id} .")
    log.info(f"Starting {job_id} ..")
    log.info(f"Starting {job_id} ...")

    # Ensure MongoDB client is initialized
    if not Mongo.is_initialized():
        log.warning("⚠️ MongoDB client not initialized. Initializing now.")
        Mongo._initialize_sync_client()
        log.info("✅ MongoDB client initialized.")

    job_repo = JobRepo()
    
    job = job_repo.find_by_job_id_sync(job_id=job_id)
    if not job:
        log.error(f"Job with id {job_id} not found in database.")
        raise Exception("Job not found")

    log.debug("Checking system resources before proceeding.")
    if not system_resources_ok():
        log.warning("System resources not OK, lowering priority and retrying.")
        return {
            "retry": True,
            "job": job,
            "job_repo": job_repo
        }
    
    return {
        "retry": False,
        "job_repo": job_repo,
        "job": job
    }

def cleanup_temp_files(output_dir, files: list):
    if output_dir and os.path.exists(output_dir):
        log.info(f"Temporary dir {output_dir} removed.")
        shutil.rmtree(output_dir)
    for file in files:
        if file and os.path.exists(file):
            log.info(f"Temporary {file} removed.")
            os.remove(file)

def execute_docker_job(job_spec, job_id, max_runtime):
    """
    Runs a docker job using managed_long_container, handles timeout and exit code.
    Returns when the job completes successfully.
    Raises TimeoutError or RuntimeError on failure.
    """
    start_time = datetime.now(timezone.utc)
    signal_handler = SignalHandler()
    with managed_long_container(
            image=job_spec["image"],
            command=job_spec["command"],
            volumes=job_spec["volumes"],
            memory=job_spec["memory"],
            environment=job_spec["environment"],
            entrypoint=job_spec["entrypoint"],
            job_id=job_id,
            gpu_enabled=job_spec.get("gpu", False),
            privileged=job_spec.get("privileged", False)
        ) as proc:
            try:
                signal_handler.add_job(job_id, proc)
                while proc.poll() is None:
                    time.sleep(60)

                    if datetime.now(timezone.utc) - start_time > max_runtime:
                        log.critical(f"Job {job_id} exceeded max runtime")
                        raise TimeoutError("Maximum runtime exceeded")
                
                exit_code = proc.wait()
                if exit_code != 0:
                    raise RuntimeError(f"Job failed with exit code {exit_code}")
            except Exception as e:
                raise Exception(f"Error running container {job_id}: {str(e)}")
            finally:
                signal_handler.remove_job(job_id)