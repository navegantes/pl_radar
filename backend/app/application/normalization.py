from datetime import datetime
from typing import Any
from ..domain.entities import Proposal

def _first(data: dict, *keys: str):
    for key in keys:
        value = data.get(key)
        if value not in (None, ""): return value
    return None

def _date(value: Any) -> datetime | None:
    if not value: return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text[:26] if len(text) > 26 and "+" not in text[19:] else text)
        return parsed.replace(tzinfo=None)
    except (ValueError, TypeError):
        try: return datetime.strptime(str(value)[:10], "%Y-%m-%d")
        except ValueError: return None

def _author_text(value: Any) -> str | None:
    if isinstance(value, str): return value
    if isinstance(value, list):
        names = []
        for author in value:
            if isinstance(author, str): names.append(author)
            elif isinstance(author, dict): names.append(str(_first(author, "autor", "nome", "nomeParlamentar") or "").strip())
        return ", ".join(x for x in names if x) or None
    if isinstance(value, dict): return str(_first(value, "autor", "nome") or "") or None
    return None

def to_proposal(raw: dict, synced_at: datetime) -> Proposal | None:
    process_id = _first(raw, "id", "codigoProcesso", "idProcesso")
    if process_id is None: return None
    active_raw = str(_first(raw, "tramitando", "emTramitacao") or "").strip().lower()
    active = True if active_raw in ("sim", "s", "true", "1", "em tramitação") else False if active_raw in ("não", "nao", "n", "false", "0", "fora de tramitação") else None
    return Proposal(
        process_id=str(process_id),
        identification=_first(raw, "identificacao", "siglaNumeroAno"),
        subject=_first(raw, "assunto", "descricaoAssunto"),
        summary=_first(raw, "ementa", "descricao", "resumo"),
        author_text=_author_text(_first(raw, "autoria", "autores", "autor")),
        situation=_first(raw, "situacaoAtual", "descricaoSituacao"),
        is_active=active,
        presented_at=_date(_first(raw, "dataApresentacao", "dataDocumentoInicial")),
        document_type=_first(raw, "tipoDocumento", "tipoConteudo", "sigla"),
        consultation_id=str(_first(raw, "codigoMateria") or "") or None,
        raw=raw,
        synced_at=synced_at,
    )
