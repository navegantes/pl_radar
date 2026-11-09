from collections.abc import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .senado_gateway import SenadoApiClient
from .sqlalchemy_repository import SqlAlchemyProposalRepository
from ..application.services import SyncProposals, GetStatistics

def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try: yield session
    finally: session.close()

def get_repository(session: Session = Depends(get_session)) -> SqlAlchemyProposalRepository:
    return SqlAlchemyProposalRepository(session)

def get_gateway() -> SenadoApiClient:
    return SenadoApiClient()

def get_sync_service(gateway: SenadoApiClient = Depends(get_gateway), repository: SqlAlchemyProposalRepository = Depends(get_repository)) -> SyncProposals:
    return SyncProposals(gateway, repository)

def get_statistics_service(repository: SqlAlchemyProposalRepository = Depends(get_repository)) -> GetStatistics:
    return GetStatistics(repository)
