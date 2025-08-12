from dotenv import load_dotenv
load_dotenv()

from src.logger import Logger 
from celery import states
from src.redis_client import Redis
from src.repo.jobs import JobRepo, JobDocument
from src.helper.aws.s3 import get_s3_service
from src.celery_client import Celery
from src.config import LOCAL_STORAGE_PATH, DEFAULT_VOLUME_NAME, DEFAULT_BUCKET_NAME
from src.documents.jobs import JobStatusEnum
from src.docker_client import get_docker_client
from datetime import timedelta
from src.helper.file_adapter import get_storage_adapter
from docker.errors import NotFound
from src.tasks import initialize_job, cleanup_temp_files, execute_docker_job
import tempfile
import os
import shutil

redis_client = Redis.get_client()
log = Logger.get_logger()
tasks = Celery.get_client()
docker_client = get_docker_client()
MAX_RUNTIME = timedelta(hours=4)
        

@tasks.task(bind=True, max_retries=30, priority=5)
def run_boltz_job(self, *args):
     # Case 1: Chained call (single tuple)
    if len(args) == 1 and isinstance(args[0], (tuple, list)):
        job_id, json_file = args[0]  # Unpack nested tuple
    # Case 2: Standalone call (two args)
    elif len(args) == 2:
        job_id, json_file = args
    # Case 3: Serialized as a single string (edge case)
    elif len(args) == 1 and isinstance(args[0], str):
        job_id, json_file = eval(args[0])
    else:
        raise ValueError(f"Invalid args: {args}")

    init_result = initialize_job(job_id)
    job_repo: JobRepo = init_result["job_repo"]
    job: JobDocument = init_result["job"]

    if init_result.get("retry"):
        self.request.delivery_info['priority'] = 0
        job.status = JobStatusEnum.RETRY.value
        job_repo.update_sync(job)
        self.update_state(state=states.RETRY)
        log.warning(f"Task with jobID {job_id} delayed due to high resource usage")
        raise self.retry(countdown=60) # retry 30 times each time wait for 60s, which mean it will wait for maximum 30 minutes    

    adapter = get_storage_adapter()
    s3 = get_s3_service()
    # Initialize variables to avoid UnboundLocalError in finally
    output_dir = None
    temp_path = None

    try:
        job.status = JobStatusEnum.STARTING.value
        job_repo.update_sync(job)
        self.update_state(state=states.STARTED)
        log.info(f"Job {job_id} status set to STARTING.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tf:
            temp_path = tf.name

        adapter.download(json_file, temp_path)

        with open(temp_path, "rb") as f:
            content = f.read()
            if not content:
                raise Exception("Downloaded file is empty.")
            
        log.info(f"Temporary JSON file created at {temp_path}")

        output_dir = f"{LOCAL_STORAGE_PATH}/tmp/{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        input_file = f"{output_dir}/input.json"
        shutil.copy(temp_path, input_file)

        output_file = f"{output_dir}/output.pdb"
        job_spec = {
            "image": "loudprepaire/boltz-job:latest",
            "memory": "48g",
            "entrypoint": None,
            "command": [],
            "volumes": {
                f"{DEFAULT_VOLUME_NAME}": f"{LOCAL_STORAGE_PATH}"
            },
            "environment": {
                "INPUT": input_file,
                "OUTPUT": output_file,
                "BUCKET": DEFAULT_BUCKET_NAME
            },
            "gpu": True,
            "privileged": True
        }

        execute_docker_job(job_spec, job_id, MAX_RUNTIME)

        with open(output_file, "rb") as f:
            content = f.read()

        if not content:
            raise Exception("Generated PDB file is empty.")

        pdb_objectname = "boltz/" + job_id + "/" + s3.generate_valid_object_name("boltz_output.pdb")
        adapter.upload(output_file, pdb_objectname)
        
        job.outputs["files"].append(pdb_objectname)
        log.info(f"job {job_id} completed, output saved to: {pdb_objectname}")
        if not self.request.chain:
            job.status = JobStatusEnum.SUCCEEDED.value
        job_repo.update_sync(job)
        self.update_state(state=states.SUCCESS)

        return job_id, pdb_objectname
    except Exception as e:
        log.error(f"job {job_id} failed: {str(e)}")
        self.update_state(state=states.FAILURE, meta=str(e))
        job.status = JobStatusEnum.FAILED.value
        job.error_message = str(e)
        job_repo.update_sync(job)
        
        return job_id, None
    finally:
        try:
            container = docker_client.containers.get(f"job_{job_id}")
            if container.status != "running":
                log.info(f"Container job_{job_id} was stopped externally (e.g., by JobHealthMonitor).")
            else:
                container.kill()
                log.info(f"Container job_{job_id} forcefully terminated.")
        except NotFound:
            log.info(f"Container job_{job_id} no longer exists. Assuming it was stopped.")
        finally:
            cleanup_temp_files(
                output_dir=output_dir,
                files=[temp_path]
            )