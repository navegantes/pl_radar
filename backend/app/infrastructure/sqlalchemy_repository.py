from datetime import datetime
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from ..domain.entities import Proposal
from ..domain.ports import ProposalRepository
from .models import ProposalModel, SnapshotModel, SyncLogModel

class SqlAlchemyProposalRepository(ProposalRepository):
    """Implementação de persistência. O restante da aplicação depende da porta, não desta classe."""
    def __init__(self, session: Session): self.session = session

    def upsert_many(self, proposals: list[Proposal]) -> int:
        # Consulta em lotes reduz o padrão N+1 sem ultrapassar limites de parâmetros do SQLite.
        for offset in range(0, len(proposals), 500):
            batch = proposals[offset:offset + 500]
            ids = [item.process_id for item in batch]
            existing = {row.process_id: row for row in self.session.scalars(
                select(ProposalModel).where(ProposalModel.process_id.in_(ids))
            ).all()}
            for item in batch:
                values = dict(identification=item.identification, subject=item.subject, summary=item.summary,
                    author_text=item.author_text, situation=item.situation, is_active=item.is_active,
                    presented_at=item.presented_at, document_type=item.document_type,
                    consultation_id=item.consultation_id, raw_json=item.raw, synced_at=item.synced_at)
                row = existing.get(item.process_id)
                if row is None:
                    self.session.add(ProposalModel(process_id=item.process_id, **values))
                else:
                    for key, value in values.items(): setattr(row, key, value)
        self.session.commit()
        return len(proposals)

    @staticmethod
    def serialize(row: ProposalModel) -> dict:
        return {"id": row.process_id, "identificacao": row.identification, "ementa": row.summary,
            "autoria": row.author_text, "situacaoAtual": row.situation,
            "tramitando": "Sim" if row.is_active is True else ("Não" if row.is_active is False else None),
            "dataApresentacao": row.presented_at.date().isoformat() if row.presented_at else None,
            "tipoDocumento": row.document_type, "codigoMateria": row.consultation_id,
            **row.raw_json}

    def list_all(self, limit: int = 10000) -> list[dict]:
        rows = self.session.scalars(select(ProposalModel).order_by(desc(ProposalModel.presented_at)).limit(limit)).all()
        return [self.serialize(row) for row in rows]

    def get(self, process_id: str) -> dict | None:
        row = self.session.get(ProposalModel, process_id)
        return self.serialize(row) if row else None

    def count(self) -> int: return self.session.scalar(select(func.count()).select_from(ProposalModel)) or 0

    def save_snapshot(self, captured_at: datetime, total: int, active: int) -> None:
        self.session.add(SnapshotModel(captured_at=captured_at, total=total, active=active)); self.session.commit()

    def list_snapshots(self, limit: int = 365) -> list[dict]:
        rows = self.session.scalars(select(SnapshotModel).order_by(desc(SnapshotModel.captured_at)).limit(limit)).all()
        return [{"capturedAt": x.captured_at.isoformat(), "total": x.total, "active": x.active} for x in reversed(rows)]

    def last_sync(self) -> datetime | None:
        row = self.session.scalar(select(SyncLogModel).order_by(desc(SyncLogModel.synced_at)).limit(1))
        return row.synced_at if row else None

    def mark_sync(self, at: datetime, status: str, message: str | None = None) -> None:
        self.session.add(SyncLogModel(synced_at=at, status=status, message=message)); self.session.commit()
