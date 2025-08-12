import redis
import redis.asyncio
from src.config import REDIS_PASSWORD, REDIS_HOST, REDIS_PORT


class Redis:
    _redis_client = None
    _ay_redis_client = None


    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._redis_client is None:
            cls._initialize_client()
        return cls._redis_client
    
    @classmethod
    def get_ay_client(cls) -> redis.asyncio.Redis:
        if cls._ay_redis_client is None:
            cls._initialize_client(True)
        return cls._ay_redis_client
    
    @classmethod
    def _initialize_client(cls, async_client: bool = False):
        """Initialize the logger with a standard configuration."""
        if async_client:
            cls._ay_redis_client = redis.asyncio.Redis(host=REDIS_HOST, password=REDIS_PASSWORD, port=REDIS_PORT, db=2, decode_responses=True)
        else:
            cls._redis_client = redis.Redis(host=REDIS_HOST, password=REDIS_PASSWORD, port=REDIS_PORT, db=2, decode_responses=True)
