from app.security.rate_limiter import RateLimiter


def test_requests_are_allowed_within_limit():
    limiter = RateLimiter(
        max_requests=3,
        window_seconds=60,
    )

    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True


def test_request_is_blocked_after_limit():
    limiter = RateLimiter(
        max_requests=3,
        window_seconds=60,
    )

    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True

    assert limiter.is_allowed("client-1") is False


def test_clients_are_limited_independently():
    limiter = RateLimiter(
        max_requests=2,
        window_seconds=60,
    )

    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is True
    assert limiter.is_allowed("client-1") is False

    assert limiter.is_allowed("client-2") is True
    assert limiter.is_allowed("client-2") is True