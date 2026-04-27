import time
from threading import RLock
from typing import Any, Callable


DEFAULT_TTL_SECONDS = 300

_cache: dict[str, tuple[float, Any]] = {}
_lock = RLock()


def make_cache_key(namespace: str, *parts: Any, **params: Any) -> str:
    serialized_parts = [namespace, *[str(part) for part in parts]]
    for key in sorted(params):
        serialized_parts.append(f"{key}={params[key]}")
    return ":".join(serialized_parts)


def get_or_set(key: str, factory: Callable[[], Any], ttl: int = DEFAULT_TTL_SECONDS) -> Any:
    now = time.time()
    with _lock:
        cached = _cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

    value = factory()
    with _lock:
        _cache[key] = (now + ttl, value)
    return value


def invalidate_namespace(namespace: str) -> None:
    prefix = f"{namespace}:"
    with _lock:
        for key in list(_cache):
            if key == namespace or key.startswith(prefix):
                _cache.pop(key, None)


def invalidate_namespaces(*namespaces: str) -> None:
    for namespace in namespaces:
        invalidate_namespace(namespace)
