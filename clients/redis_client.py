import redis
import json
from typing import Any, Optional
from logging_config import get_logger
from config import settings

logger = get_logger(__name__)


class RedisClient:
    def __init__(self):
        logger.info(
            "Initializing Redis client host=%s port=%s db=%s",
            settings.REDIS_HOST,
            settings.REDIS_PORT,
            settings.REDIS_DB,
        )
        self._redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

    def get_json(self, key: str) -> Optional[dict]:
        logger.info("Getting JSON value for key=%s", key)
        val = self._redis.get(key)
        if val is None:
            logger.info("Key %s not found", key)
            return None
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            logger.error("Failed to decode JSON for key=%s", key)
            return None

    def set_json(self, key: str, value: dict, ex: Optional[int] = None) -> bool:
        logger.info("Setting JSON value for key=%s", key)
        try:
            return self._redis.set(key, json.dumps(value), ex=ex)
        except (TypeError, ValueError):
            logger.error("Invalid JSON value provided for key=%s", key)
            return False

    def exists(self, key: str) -> bool:
        logger.info("Checking existence for key=%s", key)
        return self._redis.exists(key) > 0

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        logger.info("Setting value for key=%s", key)
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self._redis.set(key, value, ex=ex)

    def get(self, key: str) -> Optional[str]:
        logger.info("Getting value for key=%s", key)
        return self._redis.get(key)

    def xadd(self, stream: str, fields: dict, maxlen: Optional[int] = None) -> str:
        logger.info("Adding entry to stream=%s with fields=%s", stream, list(fields.keys()))
        safe_fields = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in fields.items()
        }
        return self._redis.xadd(name=stream, fields=safe_fields, maxlen=maxlen)

    def flush(self):
        logger.warning("Flushing all Redis keys")
        self._redis.flushall()

    def keys(self, pattern: str = "*") -> list:
        logger.info("Listing keys with pattern=%s", pattern)
        return self._redis.keys(pattern)

    def xreadgroup(
            self,
            groupname: str,
            consumername: str,
            streams: dict,
            count: int = 1,
            block: int = 2000,
            noack: bool = False,
            claim_min_idle_time: Optional[int] = None,
    ):
        logger.info(
            "Reading from stream with group=%s consumer=%s", groupname, consumername
        )
        return self._redis.xreadgroup(
            groupname=groupname,
            consumername=consumername,
            streams=streams,
            count=count,
            block=block,
            noack=noack,
            claim_min_idle_time=claim_min_idle_time
        )

    def xgroup_create(self, stream: str, group: str, id: str = "0", mkstream: bool = True):
        """
        Creates a consumer group for a stream. Does not error if group already exists.
        """
        logger.info(
            "Creating consumer group=%s for stream=%s starting id=%s", group, stream, id
        )
        try:
            self._redis.xgroup_create(name=stream, groupname=group, id=id, mkstream=mkstream)
            print(f"Created consumer group {group} for stream {stream}")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Group already exists — safe to ignore
                print(f"Group {group} for stream {stream} already exists")
            else:
                raise

    def smembers(self, key: str):
        logger.info("Retrieving set members for key=%s", key)
        return self._redis.smembers(key)

    def sadd(self, key: str, value: str):
        logger.info("Adding value to set key=%s", key)
        self._redis.sadd(key, value)

    def srem(self, key: str, value: str):
        logger.info("Removing value from set key=%s", key)
        self._redis.srem(key, value)


redis_client = RedisClient()
