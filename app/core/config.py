import os

from dotenv import load_dotenv


load_dotenv()


LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL"
)

LLM_BEARER_KEY = os.getenv(
    "LLM_BEARER_KEY"
)

LLM_VERIFY_SSL = (
    os.getenv(
        "LLM_VERIFY_SSL",
        "true"
    ).lower()
    not in {"false", "0", "no"}
)

MODEL = os.getenv(
    "MODEL",
    "gpt-5.4-mini"
)


if not LLM_BASE_URL:
    raise ValueError(
        "LLM_BASE_URL is not configured."
    )


if not LLM_BEARER_KEY:
    raise ValueError(
        "LLM_BEARER_KEY is not configured."
    )