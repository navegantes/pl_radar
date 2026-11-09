import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./data/pl_radar.db")
    senado_base_url: str = os.getenv("SENADO_BASE_URL", "https://legis.senado.leg.br/dadosabertos")
    sync_interval_seconds: int = int(os.getenv("SYNC_INTERVAL_SECONDS", "21600"))
    sync_on_startup: bool = os.getenv("SYNC_ON_STARTUP", "true").lower() == "true"
    auto_create_schema: bool = os.getenv("AUTO_CREATE_SCHEMA", "true").lower() == "true"
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
    cors_origins: tuple[str, ...] = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip())

settings = Settings()
Path("data").mkdir(exist_ok=True)
