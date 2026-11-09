/** Adapter HTTP do frontend. A interface visual não conhece URLs nem detalhes do transporte. */
export class ApiClient {
  constructor(baseUrl = "/api/v1") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  async request(path, options = {}) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { Accept: "application/json", ...(options.headers || {}) },
      cache: "no-store",
      ...options
    });
    if (!response.ok) {
      let message = `A API respondeu com HTTP ${response.status}.`;
      try {
        const payload = await response.json();
        message = payload.detail || message;
      } catch { /* Resposta sem JSON: mantém a mensagem HTTP. */ }
      throw new Error(message);
    }
    return response.status === 204 ? null : response.json();
  }

  listProposals() { return this.request("/proposals?limit=100000"); }
  synchronize() { return this.request("/sync", { method: "POST" }); }
  getStatistics() { return this.request("/statistics"); }
  getProcess(processId) { return this.request(`/processes/${encodeURIComponent(processId)}`); }
  getSenatorProfile(code) { return this.request(`/senators/${encodeURIComponent(code)}/profile`); }
}
