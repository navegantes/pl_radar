from datetime import datetime
from app.application.normalization import to_proposal

def test_normalizes_senate_process():
    item = to_proposal({"id": 123, "identificacao": "PL 10/2026", "ementa": "Ementa",
        "tramitando": "Sim", "dataApresentacao": "2026-01-02", "codigoMateria": 456}, datetime(2026, 1, 3))
    assert item is not None
    assert item.process_id == "123"
    assert item.consultation_id == "456"
    assert item.is_active is True
    assert item.presented_at.date().isoformat() == "2026-01-02"

def test_ignores_records_without_process_id():
    assert to_proposal({"identificacao": "PL 1/2026"}, datetime.now()) is None
