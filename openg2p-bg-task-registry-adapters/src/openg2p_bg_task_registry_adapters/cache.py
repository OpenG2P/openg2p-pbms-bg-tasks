from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


def init_cache():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")


# Custom key builder function
def beneficiary_count_key_builder(func, namespace: str, *args, **kwargs):
    """
    Build a custom cache key with `beneficiary_list_id` and `search_query`.
    """
    args: list = kwargs.get("args")
    beneficiary_list_id: str = args[2]
    search_query: str = args[4]

    return f"{namespace}{beneficiary_list_id}{search_query}"
