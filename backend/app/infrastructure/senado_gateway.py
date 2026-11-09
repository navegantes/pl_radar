import httpx
from typing import Any
from ..domain.ports import SenadoGateway
from .config import settings

class SenadoApiClient(SenadoGateway):
    """Adapter HTTP: concentra URLs, timeouts e interpretação das respostas do Senado."""
    def __init__(self) -> None:
        self.base_url = settings.senado_base_url.rstrip("/")
        self.timeout = settings.request_timeout_seconds

    async def _get(self, path: str, *, accept: str = "application/json") -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(f"{self.base_url}/{path.lstrip('/')}", headers={"Accept": accept})
            response.raise_for_status()
            return response

    @staticmethod
    def _records(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list): return [x for x in payload if isinstance(x, dict)]
        if not isinstance(payload, dict): return []
        for key in ("processos", "Processos", "processo", "dados", "resultado", "items"):
            value = payload.get(key)
            if isinstance(value, list): return [x for x in value if isinstance(x, dict)]
            if isinstance(value, dict):
                nested = SenadoApiClient._records(value)
                if nested: return nested
        # Algumas respostas envolvem os dados em uma chave com nome específico.
        for value in payload.values():
            if isinstance(value, dict):
                nested = SenadoApiClient._records(value)
                if nested: return nested
        return []

    async def fetch_proposals(self) -> list[dict[str, Any]]:
        response = await self._get("processo?v=1")
        records = self._records(response.json())
        if not records:
            raise ValueError("A API respondeu sem uma lista reconhecível de processos.")
        return records

    async def fetch_process(self, process_id: str) -> dict[str, Any]:
        response = await self._get(f"processo/{process_id}?v=1")
        payload = response.json()
        for key in ("processo", "Processo", "dados"):
            if isinstance(payload, dict) and isinstance(payload.get(key), dict): return payload[key]
        if not isinstance(payload, dict): raise ValueError("Resposta de processo inválida.")
        return payload

    async def fetch_senator_xml(self, code: str) -> str:
        response = await self._get(f"senador/{code}?v=6", accept="application/xml, text/xml")
        return response.text
