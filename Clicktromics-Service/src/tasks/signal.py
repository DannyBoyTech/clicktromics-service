from src.logger import Logger 
import signal

logger = Logger.get_logger()

class SignalHandler:
    def __init__(self):
        self.job_processes = {} 
        signal.signal(signal.SIGTERM, self.handle_sigterm)

    def add_job(self, job_id, proc):
        self.job_processes[job_id] = proc

    def remove_job(self, job_id):
        self.job_processes.pop(job_id, None)

    def handle_sigterm(self, signum, frame):
        logger.info("Received SIGTERM, checking for running jobs...")
        if self.job_processes:
            logger.info(f"Waiting for {len(self.job_processes)} job(s) to complete...")
            for job_id, proc in list(self.job_processes.items()):
                if proc.poll() is None:
                    logger.info(f"Waiting for job_{job_id} to finish...")
                    proc.wait()  # Wait for the job to complete
                    logger.info(f"Job {job_id} completed.")
            logger.info("All jobs completed, proceeding with shutdown.")
        else:
            logger.info("No running jobs, shutting down immediately.")
