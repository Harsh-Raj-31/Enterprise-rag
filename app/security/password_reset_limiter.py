from app.security.rate_limiter import RateLimiter


forgot_password_limiter = RateLimiter(
    max_requests=5,
    window_seconds=15 * 60,
)

reset_password_limiter = RateLimiter(
    max_requests=10,
    window_seconds=15 * 60,
)