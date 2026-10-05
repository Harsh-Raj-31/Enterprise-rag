from app.cache.cache_service import CacheService


def test_cache_miss():
    cache = CacheService()

    cache.delete("test:cache:miss")

    result = cache.get_or_none("test:cache:miss")

    assert result is None


def test_cache_hit():
    cache = CacheService()

    cache.set(
        "test:cache:hit",
        "cached answer",
        ttl=60,
    )

    result = cache.get_or_none("test:cache:hit")

    assert result == "cached answer"

    cache.delete("test:cache:hit")


def test_cache_delete():
    cache = CacheService()

    cache.set(
        "test:cache:delete",
        "temporary answer",
        ttl=60,
    )

    cache.delete("test:cache:delete")

    result = cache.get_or_none(
        "test:cache:delete"
    )

    assert result is None