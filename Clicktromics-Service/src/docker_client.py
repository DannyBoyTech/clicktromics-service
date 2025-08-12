import os
import time
import subprocess
import threading
from docker import DockerClient
from datetime import datetime, timedelta, timezone
from src.logger import Logger
from contextlib import contextmanager
from docker.errors import DockerException, NotFound

logger = Logger.get_logger()

_docker_client = None
DEFAULT_USER = "root"
DEFAULT_MEMORY = "2g"
GPU_PAIRS = [(0, 1), (1, 2), (0, 2)]
counter_file = "./gpu_pair_index.txt"

def get_next_gpu_pair():
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("0")

    with open(counter_file, "r+") as f:
        index = int(f.read().strip())
        pair = GPU_PAIRS[index % len(GPU_PAIRS)]

        f.seek(0)
        f.write(str((index + 1) % len(GPU_PAIRS)))
        f.truncate()

    return pair

def get_docker_client():
    global _docker_client
    if _docker_client is None:
        try:
            _docker_client = DockerClient(
                base_url='unix:///var/run/docker.sock',
                timeout=30,
                max_pool_size=20
            )
            _docker_client.ping()
        except DockerException as e:
            raise RuntimeError(f"Failed to connect to Docker daemon: {e}")
    return _docker_client

class JobHealthMonitor:
    def __init__(self, job_id):
        self.job_id = job_id
        self.last_activity = datetime.now(timezone.utc)
        self.active = True
        self.thread = threading.Thread(target=self.monitor, daemon=True)
        self.thread.start()
    
    def update_activity(self):
        self.last_activity = datetime.now(timezone.utc)
    
    def monitor(self):
        while self.active:
            time.sleep(300)  # Check every 5 minutes
            inactivity = datetime.now(timezone.utc) - self.last_activity
            if inactivity > timedelta(hours=1):
                logger.error(f"Job {self.job_id} inactive for {inactivity}.")
            if inactivity > timedelta(days=2):
                logger.critical(f"Job {self.job_id} inactive for {inactivity}. Ensuring container is terminated...")
                try:
                    container = get_docker_client().containers.get(f"job_{self.job_id}")
                    container.kill()  
                    logger.info(f"Container job_{self.job_id} forcefully terminated.")
                    self.active = False
                except NotFound:
                    logger.info(f"Container job_{self.job_id} not found. No further action needed.")
                    self.active = False
                except Exception as e:
                    logger.error(f"Failed to kill container job_{self.job_id}: {str(e)}")

@contextmanager
def managed_long_container(image, command, volumes, environment, memory, entrypoint, job_id, gpu_enabled, privileged):
    """Container manager with health checks and timeout handling"""
    health_monitor = JobHealthMonitor(job_id)
    proc = None
    docker_client = get_docker_client()
    gpu0, gpu1 = get_next_gpu_pair()

    try:
        if not memory:
            memory = DEFAULT_MEMORY

        cmd = [
            "docker", "run",
            "--rm",
            f"--user={DEFAULT_USER}",
            # f"--memory={memory}",
            "--security-opt=no-new-privileges",
            # "--log-driver=json-file",
            # "--log-opt=max-size=100m",
            # "--log-opt=max-file=10",
            f"--name=job_{job_id}"
        ]

        if privileged:
            cmd.append(
                "--privileged"
            )

        if gpu_enabled:
            cmd.append(
                "--runtime=nvidia"
            )
            cmd.extend([
                "--gpus", f'"device={gpu0},{gpu1}"'
            ])

        if entrypoint:
            cmd.append(f"--entrypoint={entrypoint}")
            
        for src, dest in volumes.items():
            cmd.extend(["-v", f"{src}:{dest}"])
        for k, v in environment.items():
            cmd.extend(["-e", f"{k}={v}"])
        
        cmd.append(image)
        cmd.extend(command)
        
        logger.info(f"Starting job {job_id}: {' '.join(cmd)}")
        
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        def stream_logs():
            while proc.poll() is None:
                line = proc.stdout.readline()
                if line:
                    logger.info(f"[JOB-{job_id}] {line.strip()}")
                    health_monitor.update_activity()
        
        log_thread = threading.Thread(target=stream_logs, daemon=True)
        log_thread.start()
        
        yield proc
        
    except Exception as e:
        logger.exception(f"Container manager error: {str(e)}")
        raise
    finally:
        health_monitor.active = False
        if proc and proc.poll() is None:
            logger.warning(f"Terminating job {job_id}")
            try:
                container = docker_client.containers.get(f"job_{job_id}")
                container.stop(timeout=300)
                logger.info(f"Container job_{job_id} stopped gracefully.")
            except NotFound:
                logger.info(f"Container job_{job_id} not found. It may have already stopped.")
            except Exception as e:
                logger.error(f"Graceful stop failed for job_{job_id}: {str(e)}")
                try:
                    container = docker_client.containers.get(f"job_{job_id}")
                    container.kill()
                    logger.info(f"Container job_{job_id} forcefully terminated.")
                except NotFound:
                    logger.info(f"Container job_{job_id} not found during kill attempt.")
                except Exception as e:
                    logger.error(f"Forceful termination failed for job_{job_id}: {str(e)}")
