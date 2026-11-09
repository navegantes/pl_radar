from collections import Counter
from datetime import datetime, timezone
from typing import Any
from ..domain.ports import ProposalRepository, SenadoGateway
from .normalization import to_proposal

class SyncProposals:
    def __init__(self, gateway: SenadoGateway, repository: ProposalRepository):
        self.gateway, self.repository = gateway, repository

    async def execute(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            raw_items = await self.gateway.fetch_proposals()
            items = [p for raw in raw_items if (p := to_proposal(raw, now)) is not None]
            if not items: raise ValueError("Nenhum processo com identificador válido foi recebido.")
            self.repository.upsert_many(items)
            all_items = self.repository.list_all(limit=100000)
            active = sum(1 for item in all_items if str(item.get("tramitando", "")).lower() == "sim")
            self.repository.save_snapshot(now, len(all_items), active)
            self.repository.mark_sync(now, "success", f"{len(items)} processos recebidos")
            return {"received": len(items), "stored": len(all_items), "syncedAt": now.isoformat()}
        except Exception as exc:
            self.repository.mark_sync(now, "error", str(exc)[:1000])
            raise

class GetStatistics:
    def __init__(self, repository: ProposalRepository): self.repository = repository

    def execute(self) -> dict[str, Any]:
        items = self.repository.list_all(limit=100000)
        monthly, situations, types, authors = Counter(), Counter(), Counter(), Counter()
        active = 0
        for item in items:
            date = str(item.get("dataApresentacao") or "")[:7]
            if date: monthly[date] += 1
            situation = item.get("situacaoAtual") or "Não informada"
            situations[str(situation)] += 1
            kind = item.get("tipoDocumento") or item.get("tipoConteudo") or "Não informado"
            types[str(kind)] += 1
            if str(item.get("tramitando", "")).lower() == "sim": active += 1
            # Estatística exploratória: não atribui coautoria a um autor principal.
            raw_authors = item.get("autoria") or item.get("autores") or []
            if isinstance(raw_authors, list):
                for author in raw_authors:
                    if isinstance(author, dict):
                        name = author.get("autor") or author.get("nomeParlamentar") or author.get("nome")
                        if name: authors[str(name)] += 1
                    elif isinstance(author, str) and author.strip(): authors[author.strip()] += 1
            # A API pode fornecer autoria como texto agregado. Não dividimos essa string,
            # pois isso poderia atribuir coautoria indevidamente a cada nome mencionado.
        snapshots = self.repository.list_snapshots(limit=365)
        last_sync = self.repository.last_sync()
        return {
            "overview": {"total": len(items), "active": active, "inactive": len(items)-active,
                "latestPresentation": max((str(x.get("dataApresentacao")) for x in items if x.get("dataApresentacao")), default=None)},
            "monthly": [{"label": k, "value": v} for k, v in sorted(monthly.items())[-24:]],
            "situations": [{"label": k, "value": v} for k, v in situations.most_common(8)],
            "types": [{"label": k, "value": v} for k, v in types.most_common(8)],
            "authors": [{"label": k, "value": v} for k, v in authors.most_common(10)],
            "snapshots": snapshots,
            "voting": {"available": False, "message": "A coleta de votações nominais ainda não foi habilitada. Nenhum ranking de votação é estimado."},
            "lastSyncAt": last_sync.isoformat() if last_sync else None,
            "dataNote": "Os indicadores refletem os registros recebidos e armazenados pelo PL Radar; não representam necessariamente o histórico integral do Senado."
        }
