from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON
from .database import Base

class ProposalModel(Base):
    __tablename__ = "proposals"
    process_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    identification: Mapped[str | None] = mapped_column(String(120), index=True)
    subject: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    author_text: Mapped[str | None] = mapped_column(Text)
    situation: Mapped[str | None] = mapped_column(String(500), index=True)
    is_active: Mapped[bool | None] = mapped_column(Boolean, index=True)
    presented_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    document_type: Mapped[str | None] = mapped_column(String(180), index=True)
    consultation_id: Mapped[str | None] = mapped_column(String(80))
    raw_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

class SnapshotModel(Base):
    __tablename__ = "proposal_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False)

class SyncLogModel(Base):
    __tablename__ = "sync_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    synced_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)

Index("ix_proposals_type_presented", ProposalModel.document_type, ProposalModel.presented_at)

# Tabelas preparadas para ingestões incrementais de outras famílias de endpoints.
# Permanecem vazias até que o respectivo contrato de resposta seja validado.
from sqlalchemy import ForeignKey, UniqueConstraint

class ParliamentarianModel(Base):
    __tablename__ = "parliamentarians"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    parliamentary_name: Mapped[str | None] = mapped_column(String(240))
    full_name: Mapped[str | None] = mapped_column(String(300))
    party: Mapped[str | None] = mapped_column(String(40), index=True)
    state: Mapped[str | None] = mapped_column(String(2), index=True)
    profile_json: Mapped[dict | None] = mapped_column(JSON)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime)

class AuthorshipModel(Base):
    __tablename__ = "authorships"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[str] = mapped_column(ForeignKey("proposals.process_id", ondelete="CASCADE"), index=True)
    parliamentarian_code: Mapped[str | None] = mapped_column(ForeignKey("parliamentarians.code"), index=True)
    author_name: Mapped[str] = mapped_column(String(300), nullable=False)
    author_role: Mapped[str | None] = mapped_column(String(100))
    is_primary: Mapped[bool | None] = mapped_column(Boolean)
    __table_args__ = (UniqueConstraint("process_id", "parliamentarian_code", "author_name", name="uq_authorship_process_parliamentarian"),)

class PartyAffiliationModel(Base):
    __tablename__ = "party_affiliations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parliamentarian_code: Mapped[str] = mapped_column(ForeignKey("parliamentarians.code", ondelete="CASCADE"), index=True)
    party: Mapped[str] = mapped_column(String(40), nullable=False)
    state: Mapped[str | None] = mapped_column(String(2))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)

class VoteEventModel(Base):
    __tablename__ = "vote_events"
    event_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    process_id: Mapped[str | None] = mapped_column(ForeignKey("proposals.process_id"), index=True)
    voted_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    session_code: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    result: Mapped[str | None] = mapped_column(String(200))
    voting_type: Mapped[str | None] = mapped_column(String(60))
    raw_json: Mapped[dict | None] = mapped_column(JSON)

class VoteModel(Base):
    __tablename__ = "votes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_key: Mapped[str] = mapped_column(ForeignKey("vote_events.event_key", ondelete="CASCADE"), index=True)
    parliamentarian_code: Mapped[str | None] = mapped_column(ForeignKey("parliamentarians.code"), index=True)
    vote: Mapped[str] = mapped_column(String(80), nullable=False)
    __table_args__ = (UniqueConstraint("event_key", "parliamentarian_code", name="uq_vote_event_parliamentarian"),)

class ProceedingEventModel(Base):
    __tablename__ = "proceeding_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[str] = mapped_column(ForeignKey("proposals.process_id", ondelete="CASCADE"), index=True)
    event_date: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    event_type: Mapped[str | None] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    raw_json: Mapped[dict | None] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("process_id", "event_date", "event_type", "description", name="uq_proceeding_event"),)

class RapporteurModel(Base):
    __tablename__ = "rapporteurs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    process_id: Mapped[str] = mapped_column(ForeignKey("proposals.process_id", ondelete="CASCADE"), index=True)
    parliamentarian_code: Mapped[str | None] = mapped_column(ForeignKey("parliamentarians.code"), index=True)
    rapporteur_name: Mapped[str] = mapped_column(String(300), nullable=False)
    committee: Mapped[str | None] = mapped_column(String(200))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime)
    __table_args__ = (UniqueConstraint("process_id", "parliamentarian_code", "committee", name="uq_rapporteur_assignment"),)
