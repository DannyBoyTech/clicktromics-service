import celery
from src.config import REDIS_URL_BROKER, REDIS_URL_BACKEND

class Celery:
    _celery_client = None

    @classmethod
    def get_client(cls) -> celery.Celery:
        if cls._celery_client is None:
            cls._initialize_client()
        return cls._celery_client
    
    @classmethod
    def _initialize_client(cls):
        """Initialize the logger with a standard configuration."""
        cls._celery_client = celery.Celery(
            __name__,
            broker=REDIS_URL_BROKER,
            backend=REDIS_URL_BACKEND
        )

        cls._celery_client.conf.task_routes = {
            'src.tasks.homelette.run_homelette_job': {'queue': 'homelette'},
            'src.tasks.musite.run_musite_job': {'queue': 'musite'},
            'src.tasks.boltz.run_boltz_job': {'queue': 'boltz'},
            'src.tasks.diffab.run_diffab_job': {'queue': 'diffab'},
            'src.tasks.gnina.run_gnina_job': {'queue': 'gnina'},
            'src.tasks.gan.run_gan_job': {'queue': 'gan'},
            'src.tasks.batch.update.update_job_status': {'queue': 'batch_update'},
        }

        cls._celery_client.conf.task_queues = {
            'homelette': {
                'exchange': 'homelette',
                'routing_key': 'homelette_job'
            },
            'musite': {
                'exchange': 'musite',
                'routing_key': 'musite_job'
            },
            'boltz': {
                'exchange': 'boltz',
                'routing_key': 'boltz_job'
            },
            'diffab': {
                'exchange': 'diffab',
                'routing_key': 'diffab_job'
            },
            'gnina': {
                'exchange': 'gnina',
                'routing_key': 'gnina_job'
            },
            'gan': {
                'exchange': 'gan',
                'routing_key': 'gan_job'
            },
            'batch_update': {
                'exchange': 'batch_update',
                'routing_key': 'batch_update_job'
            }
        }

        cls._celery_client.conf.update(
            worker_concurrency=10,  # This ensures only one task is handled at a time per worker
        )