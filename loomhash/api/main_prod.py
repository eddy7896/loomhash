import os
import redis
from fastapi import FastAPI

from loomhash.api.app import create_app
from loomhash.storage.combined import PostgresRedisStorageBackend
from loomhash.storage.postgres import PostgresStorageBackend
from loomhash.storage.redis_cache import RedisEnrollmentCache

def get_prod_app() -> FastAPI:
    conninfo = os.environ.get("POSTGRES_CONNINFO")
    if not conninfo:
        raise RuntimeError("POSTGRES_CONNINFO environment variable is required")

    redis_host = os.environ.get("REDIS_HOST", "redis")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    redis_password = os.environ.get("REDIS_PASSWORD")

    postgres = PostgresStorageBackend(conninfo)
    postgres.ensure_schema()

    client = redis.Redis(host=redis_host, port=redis_port, password=redis_password)
    cache = RedisEnrollmentCache(client)
    
    storage = PostgresRedisStorageBackend(postgres, cache)
    
    return create_app(storage=storage, enable_dev_cors=False)

app = get_prod_app()

