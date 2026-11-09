from datetime import datetime
from app.application.services import GetStatistics

class FakeRepository:
    def list_all(self, limit=10000):
        return [
            {"dataApresentacao":"2026-01-10", "situacaoAtual":"Em tramitação", "tipoDocumento":"Projeto de Lei", "tramitando":"Sim", "autoria":[{"autor":"Senadora A"}]},
            {"dataApresentacao":"2026-01-12", "situacaoAtual":"Aguardando comissão", "tipoDocumento":"Projeto de Lei", "tramitando":"Não", "autoria":"Senador B e Senadora C"},
        ]
    def list_snapshots(self, limit=365): return []
    def last_sync(self): return datetime(2026, 1, 13)

def test_statistics_do_not_split_aggregated_author_text():
    result = GetStatistics(FakeRepository()).execute()
    assert result["overview"]["total"] == 2
    assert result["overview"]["active"] == 1
    assert result["monthly"] == [{"label":"2026-01", "value":2}]
    assert result["authors"] == [{"label":"Senadora A", "value":1}]
    assert result["voting"]["available"] is False
