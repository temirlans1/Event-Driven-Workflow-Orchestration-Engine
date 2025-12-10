import redis
import json
from typing import Any, Optional
from config import settings


class RedisClient:
    def __init__(self):
        self._redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

    def get_json(self, key: str) -> Optional[dict]:
        val = self._redis.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return None

    def set_json(self, key: str, value: dict, ex: Optional[int] = None) -> bool:
        try:
            return self._redis.set(key, json.dumps(value), ex=ex)
        except (TypeError, ValueError):
            return False

    def exists(self, key: str) -> bool:
        return self._redis.exists(key) > 0

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self._redis.set(key, value, ex=ex)

    def get(self, key: str) -> Optional[str]:
        return self._redis.get(key)

    def xadd(self, stream: str, fields: dict, maxlen: Optional[int] = None) -> str:
        safe_fields = {
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in fields.items()
        }
        return self._redis.xadd(name=stream, fields=safe_fields, maxlen=maxlen)

    def flush(self):
        self._redis.flushall()

    def keys(self, pattern: str = "*") -> list:
        return self._redis.keys(pattern)


redis_client = RedisClient()
