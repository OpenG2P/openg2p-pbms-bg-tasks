from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


def init_cache():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


# Custom key builder function
def beneficiary_count_key_builder(func, namespace: str, *args, **kwargs):
    """
    Build a custom cache key with `pbms_request_id` and `search_query`.
    """
    pbms_request_id = kwargs.get("pbms_request_id", "none")
    search_query = kwargs.get("search_query", "")

    return f"{namespace}:{pbms_request_id}:{search_query}"
