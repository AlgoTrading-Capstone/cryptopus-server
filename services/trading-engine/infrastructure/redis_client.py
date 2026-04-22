from shared.redis_client import RedisClient
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

def create_redis_client() -> RedisClient:
    return RedisClient(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
    )