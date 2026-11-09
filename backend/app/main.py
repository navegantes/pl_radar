import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api.routes import router
from .infrastructure.config import settings
from .infrastructure.database import create_schema, SessionLocal
from .infrastructure.dependencies import get_repository, get_gateway
from .application.services import SyncProposals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pl-radar")
ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"

async def sync_loop():
    while True:
        await asyncio.sleep(settings.sync_interval_seconds)
        session = SessionLocal()
        try:
            result = await SyncProposals(get_gateway(), get_repository(session)).execute()
            logger.info("Sincronização automática concluída: %s", result)
        except Exception:
            logger.exception("Falha na sincronização automática")
        finally: session.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_schema:
        create_schema()
    if settings.sync_on_startup:
        session = SessionLocal()
        try:
            repo = get_repository(session)
            if repo.count() == 0:
                try: await SyncProposals(get_gateway(), repo).execute()
                except Exception: logger.exception("Sincronização inicial falhou; API permanece disponível")
        finally: session.close()
    task = asyncio.create_task(sync_loop()) if settings.sync_interval_seconds > 0 else None
    yield
    if task:
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass

app = FastAPI(title="PL Radar API", version="1.0.0", description="Backend e camada de persistência do PL Radar", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])
app.include_router(router)
if FRONTEND.exists(): app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
