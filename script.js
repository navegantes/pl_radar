const API_URL = "https://legis.senado.leg.br/dadosabertos/processo?v=1";
const CONSULTA_PUBLICA_URL = "https://www12.senado.leg.br/ecidadania/visualizacaomateria?id=";
const DETAIL_API_URL = "https://legis.senado.leg.br/dadosabertos/processo/";
const PAGE_SIZE = 20;
const REFRESH_INTERVAL = 5 * 60 * 1000;

const state = {
  all: [],
  filtered: [],
  visibleCount: PAGE_SIZE,
  loading: false,
  lastUpdated: null,
  detailLoading: false,
  currentDetailId: null,
  senatorCache: new Map()
};

const els = {
  list: document.querySelector("#proposal-list"),
  search: document.querySelector("#search-input"),
  status: document.querySelector("#status-filter"),
  type: document.querySelector("#type-filter"),
  total: document.querySelector("#stat-total"),
  active: document.querySelector("#stat-active"),
  latest: document.querySelector("#stat-latest"),
  latestLabel: document.querySelector("#stat-latest-label"),
  resultsCount: document.querySelector("#results-count"),
  refresh: document.querySelector("#refresh-button"),
  loadMore: document.querySelector("#load-more"),
  themeToggle: document.querySelector("#theme-toggle"),
  themeIcon: document.querySelector("#theme-icon"),
  toast: document.querySelector("#toast"),
  detailView: document.querySelector("#detail-view"),
  dashboardSections: [...document.querySelectorAll("main > .hero, main > .stats-grid, main > .toolbar-section, main > #proposal-list, main > .pagination-row, main > .source-note")]
};

function escapeHTML(value = "") {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

function normalizeText(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

function parseDate(value) {
  if (!value) return null;
  const date = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDate(value) {
  const date = parseDate(value);
  return date ? new Intl.DateTimeFormat("pt-BR").format(date) : "Data não informada";
}

function extractRecords(payload) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];
  // Compatibilidade com possíveis envelopes usados pela API.
  for (const key of ["processos", "Processos", "processo", "dados", "resultado", "items"]) {
    if (Array.isArray(payload[key])) return payload[key];
    if (payload[key] && typeof payload[key] === "object") {
      const nested = extractRecords(payload[key]);
      if (nested.length) return nested;
    }
  }
  return [];
}

function isBill(item) {
  const identification = normalizeText(item.identificacao || "");
  const documentType = normalizeText(item.tipoDocumento || "");
  const contentType = normalizeText(item.tipoConteudo || "");
  return /^(pl|pls|plc|plp|plv)\b/.test(identification) ||
    documentType.includes("projeto de lei") ||
    contentType.includes("projeto de lei");
}

function getConsultationId(item) {
  // codigoMateria é o identificador usado pelo e-Cidadania; item.id é o ID interno do processo.
  const id = item.codigoMateria;
  return id !== undefined && id !== null && /^\d+$/.test(String(id)) ? String(id) : null;
}

function sortNewest(items) {
  return [...items].sort((a, b) => {
    const dateA = parseDate(a.dataApresentacao)?.getTime() ?? 0;
    const dateB = parseDate(b.dataApresentacao)?.getTime() ?? 0;
    return dateB - dateA;
  });
}

async function fetchProposals() {
  if (state.loading) return;
  state.loading = true;
  els.refresh.classList.add("is-loading");
  els.refresh.disabled = true;
  els.refresh.querySelector("span").textContent = "BUSCANDO";

  try {
    const response = await fetch(API_URL, {
      headers: { "Accept": "application/json" },
      cache: "no-store"
    });
    if (!response.ok) throw new Error(`A API respondeu com HTTP ${response.status}.`);
    const payload = await response.json();
    const records = extractRecords(payload);

    if (!records.length) {
      throw new Error("A API respondeu, mas não foi possível localizar a lista de processos no JSON.");
    }

    state.all = sortNewest(records);
    state.lastUpdated = new Date();
    applyFilters();
    showToast(`${state.all.length.toLocaleString("pt-BR")} registros recebidos da API.`);
  } catch (error) {
    console.error("Falha ao consultar a API do Senado:", error);
    if (!state.all.length) {
      els.list.innerHTML = `
        <div class="error-state">
          <strong>Não foi possível carregar os dados.</strong>
          <span>${escapeHTML(error.message)}<br>Verifique sua conexão ou tente novamente.</span>
          <span>Se o navegador bloquear a requisição por CORS, execute o painel por um servidor local ou adicione um proxy de backend.</span>
        </div>`;
      els.resultsCount.textContent = "Falha na consulta";
    } else {
      showToast("Não foi possível atualizar. Exibindo os últimos dados carregados.");
    }
  } finally {
    state.loading = false;
    els.refresh.classList.remove("is-loading");
    els.refresh.disabled = false;
    els.refresh.querySelector("span").textContent = "ATUALIZAR";
  }
}

function applyFilters() {
  const query = normalizeText(els.search.value.trim());
  const status = els.status.value;
  const type = els.type.value;

  state.filtered = state.all.filter(item => {
    if (type !== "all" && !isBill(item)) return false;
    if (type === "pl-only" && !/^pl\b/i.test(item.identificacao || "")) return false;

    const isActive = normalizeText(item.tramitando) === "sim";
    if (status === "active" && !isActive) return false;
    if (status === "inactive" && isActive) return false;

    if (query) {
      const searchable = normalizeText([
        item.identificacao, item.ementa, item.autoria, item.tipoDocumento,
        item.situacaoAtual, item.tipoConteudo
      ].join(" "));
      if (!searchable.includes(query)) return false;
    }
    return true;
  });

  state.filtered = sortNewest(state.filtered);
  state.visibleCount = PAGE_SIZE;
  render();
}

function renderStats() {
  els.total.textContent = state.filtered.length.toLocaleString("pt-BR");
  els.active.textContent = state.filtered.filter(item => normalizeText(item.tramitando) === "sim").length.toLocaleString("pt-BR");
  const latest = state.filtered.find(item => parseDate(item.dataApresentacao));
  els.latest.textContent = latest ? formatDate(latest.dataApresentacao) : "—";
  els.latestLabel.textContent = latest?.identificacao ? latest.identificacao : "data de apresentação";
}

function proposalTemplate(item) {
  const identification = item.identificacao || "Proposição sem identificação";
  const isActive = normalizeText(item.tramitando) === "sim";
  const consultationId = getConsultationId(item);
  const link = consultationId
    ? `<a class="proposal-link" href="${CONSULTA_PUBLICA_URL}${encodeURIComponent(consultationId)}" target="_blank" rel="noopener noreferrer">CONSULTA PÚBLICA ↗</a>`
    : `<span class="no-link">CONSULTA NÃO DISPONÍVEL</span>`;
  const detailsButton = item.id !== undefined && item.id !== null
    ? `<button class="proposal-detail-button" type="button" data-detail-id="${escapeHTML(item.id)}">VER DETALHES <span>→</span></button>`
    : `<span class="no-link">DETALHES INDISPONÍVEIS</span>`;
  const summary = (item.ementa || "Ementa não informada.").trim();
  const author = item.autoria || "Autoria não informada";
  const situation = item.situacaoAtual || "Situação não informada";
  const docType = item.tipoDocumento || item.tipoConteudo || "Tipo não informado";

  return `
    <article class="proposal-card">
      <div class="proposal-main">
        <div class="proposal-meta">
          <span class="proposal-number">${escapeHTML(identification)}</span>
          <span class="tag ${isActive ? "tag-active" : "tag-inactive"}">${isActive ? "EM TRAMITAÇÃO" : "FORA DE TRAMITAÇÃO"}</span>
          ${item.casaIdentificadora ? `<span class="tag">${escapeHTML(item.casaIdentificadora)}</span>` : ""}
        </div>
        <h3>${escapeHTML(docType)}</h3>
        <p class="proposal-summary">${escapeHTML(summary)}</p>
        <div class="proposal-details">
          <span><b>Autoria:</b> ${escapeHTML(author)}</span>
          <span><b>Situação:</b> ${escapeHTML(situation)}</span>
        </div>
      </div>
      <aside class="proposal-side">
        <div class="proposal-date">APRESENTAÇÃO<strong>${escapeHTML(formatDate(item.dataApresentacao))}</strong></div>
        <div class="proposal-actions">${detailsButton}${link}</div>
      </aside>
    </article>`;
}

function render() {
  renderStats();
  const visible = state.filtered.slice(0, state.visibleCount);
  els.resultsCount.textContent = `${state.filtered.length.toLocaleString("pt-BR")} proposta(s) encontrada(s)`;
  if (!visible.length) {
    els.list.innerHTML = `<div class="empty-state"><strong>Nenhuma proposta encontrada.</strong><span>Tente mudar os filtros ou usar outro termo de busca.</span></div>`;
  } else {
    els.list.innerHTML = visible.map(proposalTemplate).join("");
  }
  els.loadMore.hidden = state.visibleCount >= state.filtered.length;
  if (state.lastUpdated) {
    els.resultsCount.title = `Última atualização: ${state.lastUpdated.toLocaleString("pt-BR")}`;
  }
}

function unwrapDetail(payload) {
  if (!payload || typeof payload !== "object") return null;
  if (payload.processo && typeof payload.processo === "object") return payload.processo;
  if (payload.Processo && typeof payload.Processo === "object") return payload.Processo;
  if (payload.dados && typeof payload.dados === "object") return payload.dados;
  return payload;
}

function detailSection(title, content) {
  if (!content) return "";
  return `<section class="detail-section"><div class="detail-section-heading"><span class="eyebrow-line"></span><h3>${escapeHTML(title)}</h3></div>${content}</section>`;
}

function detailValue(label, value) {
  if (value === undefined || value === null || String(value).trim() === "") return "";
  return `<div class="detail-field"><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong></div>`;
}

function xmlText(xml, selector) {
  const node = xml.querySelector(selector);
  return node?.textContent?.trim() || "";
}

function senatorField(label, value) {
  return value ? `<div class="author-profile-field"><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong></div>` : "";
}

async function fetchSenatorProfile(code) {
  if (state.senatorCache.has(code)) return state.senatorCache.get(code);
  const request = (async () => {
    const url = `https://legis.senado.leg.br/dadosabertos/senador/${encodeURIComponent(code)}?v=6`;
    const response = await fetch(url, {headers:{Accept:"application/xml, text/xml"}, cache:"no-store"});
    if (!response.ok) throw new Error(`A API respondeu com HTTP ${response.status}.`);
    const xmlTextBody = await response.text();
    const xml = new DOMParser().parseFromString(xmlTextBody, "application/xml");
    if (xml.querySelector("parsererror") || !xml.querySelector("Parlamentar IdentificacaoParlamentar")) {
      throw new Error("A resposta XML do perfil parlamentar é inválida ou não contém os dados esperados.");
    }
    const identification = xml.querySelector("IdentificacaoParlamentar");
    const basics = xml.querySelector("DadosBasicosParlamentar");
    const phone = xml.querySelector("Telefones Telefone NumeroTelefone")?.textContent?.trim() || "";
    return {
      name: xmlText(identification, "NomeParlamentar"),
      fullName: xmlText(identification, "NomeCompletoParlamentar"),
      gender: xmlText(identification, "SexoParlamentar"),
      photo: xmlText(identification, "UrlFotoParlamentar"),
      profile: xmlText(identification, "UrlPaginaParlamentar"),
      email: xmlText(identification, "EmailParlamentar"),
      party: xmlText(identification, "SiglaPartidoParlamentar"),
      state: xmlText(identification, "UfParlamentar"),
      birth: xmlText(basics, "DataNascimento"),
      birthplace: [xmlText(basics, "Naturalidade"), xmlText(basics, "UfNaturalidade")].filter(Boolean).join(" / "),
      address: xmlText(basics, "EnderecoParlamentar"),
      phone
    };
  })();
  state.senatorCache.set(code, request);
  try { return await request; }
  catch (error) { state.senatorCache.delete(code); throw error; }
}

function renderSenatorProfile(profile) {
  const photo = profile.photo && /^https?:\/\//i.test(profile.photo)
    ? `<img class="author-photo" src="${escapeHTML(profile.photo)}" alt="Foto oficial de ${escapeHTML(profile.name || "parlamentar")}" loading="lazy">` : "";
  const profileLink = profile.profile && /^https?:\/\//i.test(profile.profile)
    ? `<a class="author-profile-link" href="${escapeHTML(profile.profile)}" target="_blank" rel="noopener noreferrer">PERFIL NO SENADO ↗</a>` : "";
  const email = profile.email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)
    ? `<a href="mailto:${escapeHTML(profile.email)}">${escapeHTML(profile.email)}</a>` : profile.email;
  return `<div class="author-profile">
    ${photo}<div class="author-profile-grid">
      ${senatorField("Nome parlamentar", profile.name)}${senatorField("Nome completo", profile.fullName)}
      ${senatorField("Partido / UF", [profile.party, profile.state].filter(Boolean).join(" / "))}
      ${senatorField("Sexo", profile.gender)}${senatorField("Nascimento", formatDate(profile.birth))}
      ${senatorField("Naturalidade", profile.birthplace)}${senatorField("Telefone", profile.phone)}
      ${senatorField("E-mail", email)}${senatorField("Endereço parlamentar", profile.address)}
    </div>${profileLink}
  </div>`;
}

async function loadAuthorDropdown(detailsElement) {
  const code = detailsElement.dataset.senatorId;
  const content = detailsElement.querySelector("[data-author-content]");
  if (!code || !content || detailsElement.dataset.loaded === "true" || detailsElement.dataset.loading === "true") return;
  detailsElement.dataset.loading = "true";
  try {
    const profile = await fetchSenatorProfile(code);
    if (!detailsElement.isConnected) return;
    content.innerHTML = renderSenatorProfile(profile);
    detailsElement.dataset.loaded = "true";
  } catch (error) {
    console.error(`Falha ao consultar perfil parlamentar ${code}:`, error);
    if (detailsElement.isConnected) content.innerHTML = `<p class="detail-muted">Não foi possível carregar o perfil completo. ${escapeHTML(error.message)} Verifique também se a API permite acesso via CORS.</p><button class="author-retry-button" type="button" data-author-retry> TENTAR NOVAMENTE </button>`;
  } finally {
    detailsElement.dataset.loading = "false";
  }
}

function renderDetail(data) {
  const content = data.conteudo || {};
  const documentData = data.documento || {};
  const authors = documentData.autoria || data.autoriaIniciativa || [];
  const authorMarkup = authors.length
    ? `<div class="detail-authors">${authors.map((author, index) => {
        const code = Number(author.codigoParlamentar);
        const senatorId = Number.isInteger(code) && code > 0 ? String(code) : "";
        const authorName = author.autor || "Autor não informado";
        const role = [author.descricaoTipo, author.siglaPartido, author.uf].filter(Boolean).join(" · ");
        return `<details class="author-dropdown" data-senator-id="${escapeHTML(senatorId)}">
          <summary><span class="author-summary-main"><strong>${escapeHTML(authorName)}</strong><small>${escapeHTML(role || "Informações de autoria")}</small></span><span class="author-chevron" aria-hidden="true">＋</span></summary>
          <div class="author-dropdown-content" data-author-content>${senatorId
            ? `<div class="author-loading"><span class="loader loader-small"></span> Carregando perfil parlamentar...</div>`
            : `<p class="detail-muted">A API não forneceu um código parlamentar para consultar o perfil completo deste autor.</p>`}</div>
        </details>`;
      }).join("")}</div>`
    : `<p class="detail-muted">Autoria não informada pela API.</p>`;
  const classifications = (data.classificacoes || []).map(item => `<span class="detail-chip">${escapeHTML(item.descricaoHierarquia || item.descricao || "Classificação")}</span>`).join("");
  const apensados = (data.processosApensados || []).map(item => `<article class="detail-list-item"><strong>${escapeHTML(item.identificacao || "Processo")}</strong><span>${escapeHTML(item.tipoApensamento || "Apensamento")}${item.dataApensamento ? ` · ${escapeHTML(formatDate(item.dataApensamento))}` : ""}</span></article>`).join("");
  const related = (data.processosRelacionados || []).map(item => `<article class="detail-list-item"><strong>${escapeHTML([item.sigla, item.numero, item.ano].filter(Boolean).join(" "))}</strong><span>${escapeHTML(item.tipoRelacao || "Processo relacionado")}</span></article>`).join("");
  const documents = documentData.url ? `<a class="detail-external-link" href="${escapeHTML(documentData.url)}" target="_blank" rel="noopener noreferrer">ABRIR DOCUMENTO OFICIAL ↗</a>` : "";
  const movements = [];
  (data.autuacoes || []).forEach(autuacao => {
    (autuacao.situacoes || []).forEach(item => movements.push({date:item.inicio, title:item.descricao || "Situação", description:[autuacao.nomeColegiadoControleAtual, item.colegiado?.nome].filter(Boolean).join(" · ")}));
    (autuacao.informesLegislativos || []).forEach(item => movements.push({date:item.data, title:item.descricao || "Informe legislativo", description:item.colegiado?.nome || item.enteAdministrativo?.nome || ""}));
    (autuacao.movimentacoes || []).forEach(item => movements.push({date:item.dataEnvio, title:"Movimentação", description:[item.enteOrigem?.nome, "→", item.enteDestino?.nome, item.colegiadoDestino?.nome].filter(Boolean).join(" ")}));
  });
  (data.despachos || []).forEach(item => movements.push({date:item.data, title:item.tipoMotivacao || item.siglaTipoMotivacao || "Despacho", description:(item.providencias || []).map(p => p.descricao || p.tipo).filter(Boolean).join(" · ")}));
  movements.sort((a,b) => (new Date(b.date || 0)) - (new Date(a.date || 0)));
  const movementMarkup = movements.length ? `<ol class="detail-timeline">${movements.map(item => `<li><time>${escapeHTML(formatDate(item.date))}</time><div><strong>${escapeHTML(item.title)}</strong>${item.description ? `<p>${escapeHTML(item.description)}</p>` : ""}</div></li>`).join("")}</ol>` : `<p class="detail-muted">A API não retornou movimentações detalhadas para este processo.</p>`;

  els.detailView.innerHTML = `
    <button class="detail-back-button" id="detail-back" type="button">← VOLTAR ÀS PROPOSTAS</button>
    <header class="detail-hero"><div><p class="eyebrow"><span class="eyebrow-line"></span> FICHA DA PROPOSIÇÃO</p><h1>${escapeHTML(data.identificacao || "Detalhes da proposta")}</h1><p>${escapeHTML(data.descricaoSigla || data.sigla || content.tipo || "Processo legislativo")}</p></div><div class="detail-id-stamp"><span>ID DO PROCESSO</span><strong>${escapeHTML(data.id ?? "—")}</strong></div></header>
    <div class="detail-status-row"><span class="tag ${normalizeText(data.tramitando)==="sim" ? "tag-active":"tag-inactive"}">${normalizeText(data.tramitando)==="sim" ? "EM TRAMITAÇÃO":"FORA DE TRAMITAÇÃO"}</span><span class="detail-updated">ATUALIZADO EM ${escapeHTML(formatDate(data.dataSituacaoAtual || data.dthUltimaAtualizacao))}</span></div>
    ${detailSection("Resumo", `<div class="detail-grid">${detailValue("Situação atual", data.situacaoAtual)}${detailValue("Objetivo", data.objetivo)}${detailValue("Casa identificadora", data.casaIdentificadora)}${detailValue("Casa iniciadora", data.siglaCasaIniciadora)}${detailValue("Data de apresentação", formatDate(documentData.dataApresentacao || data.dataDocumentoInicial))}${detailValue("Última atualização", data.dthUltimaAtualizacao ? new Date(data.dthUltimaAtualizacao).toLocaleString("pt-BR") : "")}</div><div class="detail-ementa"><span>EMENTA</span><p>${escapeHTML(content.ementa || "Ementa não informada.")}</p>${content.explicacaoEmenta ? `<p>${escapeHTML(content.explicacaoEmenta)}</p>` : ""}</div>`)}
    ${detailSection("Autoria", authorMarkup)}
    ${detailSection("Classificação temática", classifications ? `<div class="detail-chips">${classifications}</div>` : `<p class="detail-muted">Sem classificação informada.</p>`)}
    ${detailSection("Tramitação e movimentações", movementMarkup)}
    ${detailSection("Despachos e providências", (data.despachos || []).length ? `<div class="detail-list">${data.despachos.map(item => `<article class="detail-list-item"><strong>${escapeHTML(item.tipoMotivacao || item.siglaTipoMotivacao || "Despacho")} · ${escapeHTML(formatDate(item.data))}</strong><span>${escapeHTML((item.providencias || []).map(p => p.descricao || p.tipo).filter(Boolean).join("; ") || "Sem providências detalhadas")}</span></article>`).join("")}</div>` : "")}
    ${detailSection("Processos apensados", apensados ? `<div class="detail-list">${apensados}</div>` : "")}
    ${detailSection("Processos relacionados", related ? `<div class="detail-list">${related}</div>` : "")}
    ${detailSection("Documento e observações", `${documents}${data.observacao ? `<p class="detail-observation">${escapeHTML(data.observacao)}</p>` : `<p class="detail-muted">Nenhuma observação adicional.</p>`}`)}
    <div class="detail-footer-actions">${data.codigoMateria ? `<a class="detail-external-link" href="${CONSULTA_PUBLICA_URL}${encodeURIComponent(data.codigoMateria)}" target="_blank" rel="noopener noreferrer">CONSULTAR NO E-CIDADANIA ↗</a>` : ""}<button class="detail-back-button" type="button" id="detail-back-bottom">← VOLTAR À LISTA</button></div>`;
}

function showDashboard() {
  els.dashboardSections.forEach(section => section.hidden = false);
  els.detailView.hidden = true;
  state.currentDetailId = null;
  if (location.hash.startsWith("#detalhes/")) history.replaceState(null, "", location.pathname + location.search);
  window.scrollTo({top:0, behavior:"smooth"});
}

async function openDetails(id, updateHistory = true) {
  if (state.detailLoading) return;
  state.detailLoading = true;
  state.currentDetailId = String(id);
  els.dashboardSections.forEach(section => section.hidden = true);
  els.detailView.hidden = false;
  els.detailView.innerHTML = `<div class="loading-state"><span class="loader"></span><strong>Carregando detalhes da proposição...</strong><span>Consultando o processo ${escapeHTML(id)} na API do Senado.</span></div>`;
  if (updateHistory) history.pushState({detailId:String(id)}, "", `#detalhes/${encodeURIComponent(id)}`);
  window.scrollTo({top:0, behavior:"smooth"});
  try {
    const response = await fetch(`${DETAIL_API_URL}${encodeURIComponent(id)}?v=1`, {headers:{Accept:"application/json"}, cache:"no-store"});
    if (!response.ok) throw new Error(`A API respondeu com HTTP ${response.status}.`);
    const data = unwrapDetail(await response.json());
    if (!data) throw new Error("A API retornou uma resposta vazia ou inválida.");
    renderDetail(data);
  } catch (error) {
    console.error("Falha ao consultar detalhes do processo:", error);
    els.detailView.innerHTML = `<button class="detail-back-button" id="detail-back" type="button">← VOLTAR ÀS PROPOSTAS</button><div class="error-state"><strong>Não foi possível carregar os detalhes.</strong><span>${escapeHTML(error.message)}</span><span>Se houver bloqueio de CORS, será necessário consultar a API por meio de um proxy no backend.</span><button class="detail-back-button" id="detail-retry" type="button">TENTAR NOVAMENTE</button></div>`;
  } finally {
    state.detailLoading = false;
  }
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => els.toast.classList.remove("show"), 3200);
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("pl-radar-theme", theme);
  const dark = theme === "dark";
  els.themeToggle.setAttribute("aria-label", dark ? "Ativar tema claro" : "Ativar tema escuro");
  els.themeToggle.title = dark ? "Ativar tema claro" : "Ativar tema escuro";
  els.themeIcon.innerHTML = dark
    ? '<path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.7 8.7 0 1 0 20.5 14.2Z"/>'
    : '<path d="M12 3v2m0 14v2M3 12h2m14 0h2M5.64 5.64l1.42 1.42m9.88 9.88 1.42 1.42m0-12.72-1.42 1.42m-9.88 9.88-1.42 1.42M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/>';
}

els.search.addEventListener("input", applyFilters);
els.status.addEventListener("change", applyFilters);
els.type.addEventListener("change", applyFilters);
els.refresh.addEventListener("click", fetchProposals);
els.loadMore.addEventListener("click", () => {
  state.visibleCount += PAGE_SIZE;
  render();
});
els.themeToggle.addEventListener("click", () => {
  const current = document.documentElement.dataset.theme || "light";
  setTheme(current === "light" ? "dark" : "light");
});

document.addEventListener("click", event => {
  const detailsButton = event.target.closest("[data-detail-id]");
  if (detailsButton) openDetails(detailsButton.dataset.detailId);
  if (event.target.closest("#detail-back, #detail-back-bottom")) showDashboard();
  if (event.target.closest("#detail-retry") && state.currentDetailId) openDetails(state.currentDetailId);
  const authorRetry = event.target.closest("[data-author-retry]");
  if (authorRetry) loadAuthorDropdown(authorRetry.closest(".author-dropdown"));
});

document.addEventListener("toggle", event => {
  if (event.target.matches(".author-dropdown") && event.target.open) loadAuthorDropdown(event.target);
}, true);
window.addEventListener("popstate", () => {
  if (!location.hash.startsWith("#detalhes/")) showDashboard();
  else {
    const id = decodeURIComponent(location.hash.slice("#detalhes/".length));
    if (id) openDetails(id, false);
  }
});

const savedTheme = localStorage.getItem("pl-radar-theme");
const preferredTheme = savedTheme || (window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light");
setTheme(preferredTheme);
document.querySelector("#current-year").textContent = new Date().getFullYear();

fetchProposals();
window.setInterval(fetchProposals, REFRESH_INTERVAL);
