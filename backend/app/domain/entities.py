from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass(frozen=True)
class Proposal:
    process_id: str
    identification: str | None
    subject: str | None
    summary: str | None
    author_text: str | None
    situation: str | None
    is_active: bool | None
    presented_at: datetime | None
    document_type: str | None
    consultation_id: str | None
    raw: dict[str, Any]
    synced_at: datetime

@dataclass(frozen=True)
class Snapshot:
    captured_at: datetime
    total: int
    active: int
