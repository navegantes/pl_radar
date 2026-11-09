from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..application.services import SyncProposals, GetStatistics
from ..domain.ports import SenadoGateway
from ..infrastructure.dependencies import get_session, get_repository, get_gateway, get_sync_service, get_statistics_service

router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health(): return {"status": "ok", "service": "pl-radar-api"}

@router.get("/proposals")
def proposals(q: str | None = None, status: str = "all", kind: str = "all",
              start_date: str | None = None, end_date: str | None = None,
              limit: int = Query(10000, ge=1, le=100000), session: Session = Depends(get_session)):
    repository = get_repository(session)
    items = repository.list_all(limit=limit)
    def parse_date(value):
        try: return datetime.fromisoformat(str(value)[:10]).date() if value else None
        except ValueError: return None
    start, end = parse_date(start_date), parse_date(end_date)
    filtered = []
    for item in items:
        active = str(item.get("tramitando", "")).lower() == "sim"
        if status == "active" and not active: continue
        if status == "inactive" and active: continue
        ident = str(item.get("identificacao") or "").lower()
        doc_type = str(item.get("tipoDocumento") or item.get("tipoConteudo") or "").lower()
        if kind == "pl" and not (ident.startswith(("pl ", "pls ", "plc ", "plp ", "plv ")) or "projeto de lei" in doc_type): continue
        if kind == "pl-only" and not ident.startswith("pl "): continue
        presented = parse_date(item.get("dataApresentacao"))
        if start and (not presented or presented < start): continue
        if end and (not presented or presented > end): continue
        if q and q.casefold() not in " ".join(str(item.get(k) or "") for k in ("identificacao", "ementa", "autoria", "tipoDocumento", "situacaoAtual")).casefold(): continue
        filtered.append(item)
    return {"items": filtered, "total": len(filtered), "source": "local-database"}

@router.get("/statistics")
def statistics(service: GetStatistics = Depends(get_statistics_service)):
    return service.execute()

@router.post("/sync")
async def sync(service: SyncProposals = Depends(get_sync_service)):
    try: return await service.execute()
    except Exception as exc: raise HTTPException(status_code=502, detail=f"Falha ao sincronizar com o Senado: {exc}") from exc

@router.get("/processes/{process_id}")
async def process_detail(process_id: str, gateway: SenadoGateway = Depends(get_gateway)):
    try: return await gateway.fetch_process(process_id)
    except Exception as exc: raise HTTPException(status_code=502, detail=f"Falha ao consultar processo no Senado: {exc}") from exc

@router.get("/senators/{code}/profile")
async def senator_profile(code: str, gateway: SenadoGateway = Depends(get_gateway)):
    if not code.isdigit(): raise HTTPException(status_code=422, detail="Código parlamentar inválido.")
    try: return {"xml": await gateway.fetch_senator_xml(code)}
    except Exception as exc: raise HTTPException(status_code=502, detail=f"Falha ao consultar perfil parlamentar: {exc}") from exc
