import time

from app.cache.cache_service import CacheService


def test_cache_expires_after_ttl():
    cache = CacheService()

    key = "test:cache:ttl"

    cache.set(
        key,
        "temporary answer",
        ttl=2,
    )

    assert cache.get(key) == "temporary answer"

    time.sleep(3)

    assert cache.get(key) is None