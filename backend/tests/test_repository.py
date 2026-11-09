from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.database import Base
from app.infrastructure.sqlalchemy_repository import SqlAlchemyProposalRepository
from app.domain.entities import Proposal

def test_sqlite_repository_upserts_and_snapshots():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    repository = SqlAlchemyProposalRepository(session)
    now = datetime(2026, 2, 1)
    item = Proposal("10", "PL 10/2026", None, "Ementa", "Autoria", "Em tramitação", True,
                    datetime(2026, 1, 10), "Projeto de Lei", "123", {"id": 10}, now)
    assert repository.upsert_many([item]) == 1
    updated = Proposal("10", "PL 10/2026", None, "Ementa atualizada", "Autoria", "Em tramitação", True,
                       datetime(2026, 1, 10), "Projeto de Lei", "123", {"id": 10}, now)
    assert repository.upsert_many([updated]) == 1
    assert repository.count() == 1
    assert repository.get("10")["ementa"] == "Ementa atualizada"
    repository.save_snapshot(now, 1, 1)
    assert repository.list_snapshots()[0]["total"] == 1
    session.close()
    engine.dispose()
