import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


# Centralized settings
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    # Default points to the compose service name "postgres"
    "postgresql://user:password@postgres:5432/dbname",
)
APP_NAME: str = os.getenv("APP_NAME", "FastAPI Docker App")
DEBUG: bool = _get_bool(os.getenv("DEBUG"), default=False)
PLUGINS_ENABLED: list[str] = [
    p.strip() for p in os.getenv("PLUGINS_ENABLED", "hello,analytics").split(",") if p.strip()
]

# Secret used to encrypt GitHub access tokens (hex, openssl rand -hex 32)
COPILOT_METRICS__TOKEN_SECRET: str | None = os.getenv("COPILOT_METRICS__TOKEN_SECRET")