from app.cache.redis_client import redis_client


class CacheService:
    """
    Service responsible for reading and writing
    cached responses in Redis.
    """

    def get(self, key: str) -> str | None:
        """
        Retrieve a cached value.

        Returns:
            Cached value if found, otherwise None.
        """
        return redis_client.get(key)

    def set(
        self,
        key: str,
        value: str,
        ttl: int = 300,
    ) -> bool:
        """
        Store a value in Redis with a TTL.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Expiration time in seconds.
        """
        return bool(
            redis_client.set(
                key,
                value,
                ex=ttl,
            )
        )

    def delete(self, key: str) -> bool:
        """
        Delete a cached value.
        """
        return bool(redis_client.delete(key))

    def clear(self) -> None:
        """
        Clear the current Redis database.

        Use carefully. This is mainly intended for
        development/testing.
        """
        redis_client.flushdb()

    def get_or_none(self, key: str) -> str | None:
        """
        Retrieve a cached value.

        Returns None when the key does not exist,
        which represents a cache miss.
        """
        return self.get(key)        

