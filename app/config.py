import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]


def _load_local_env() -> None:
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Settings:
    """Configuration loaded from environment variables or a local .env file."""

    database_url: str
    api_url: str
    log_rows: int


@lru_cache
def get_settings() -> Settings:
    _load_local_env()
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://databurguer:databurguer@localhost:5432/databurguer",
        ),
        api_url=os.getenv("API_URL", "http://localhost:8000"),
        log_rows=int(os.getenv("LOG_ROWS", "10000")),
    )
