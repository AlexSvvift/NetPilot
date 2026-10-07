const state = { targets: [], refreshInProgress: false };
const DASHBOARD_REFRESH_MS = 5000;

const $ = (selector) => document.querySelector(selector);

function showNotice(message, isError = false) {
  const notice = $("#notice");
  notice.hidden = false;
  notice.textContent = message;
  notice.classList.toggle("error", isError);
  window.clearTimeout(showNotice.timer);
  showNotice.timer = window.setTimeout(() => { notice.hidden = true; }, 4500);
}

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(formatApiError(body, response.status));
  }
  return response.status === 204 ? null : response.json();
}

function formatApiError(body, statusCode) {
  const detail = body?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      if (typeof item !== "object" || item === null) return String(item);
      const location = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : "";
      return location ? `${location}: ${item.msg || "Некорректное значение"}` : (item.msg || JSON.stringify(item));
    }).join("; ");
  }
  if (typeof detail === "object" && detail !== null) {
    return detail.msg || JSON.stringify(detail);
  }
  return detail || `Ошибка HTTP ${statusCode}`;
}

function addressFor(target) {
  if (target.kind === "http") return target.url;
  return `${target.host}:${target.port}`;
}

function statusFor(target) {
  if (!target.last_check) return { text: "Ожидает", className: "waiting" };
  return target.last_check.status ? { text: "Доступна", className: "up" } : { text: "Недоступна", className: "down" };
}

function renderTargets() {
  const body = $("#targets-body");
  body.replaceChildren();
  if (!state.targets.length) {
    body.innerHTML = '<tr><td colspan="6" class="empty">Добавь первую цель для мониторинга.</td></tr>';
    return;
  }
  const template = $("#target-row-template");
  state.targets.forEach((target) => {
    const row = template.content.cloneNode(true);
    row.querySelector(".target-name").textContent = target.name;
    row.querySelector(".target-id").textContent = `ID ${target.id} · каждые ${target.interval_seconds} сек.`;
    row.querySelector(".kind-pill").textContent = target.kind.toUpperCase();
    row.querySelector(".target-address").textContent = addressFor(target);
    const status = statusFor(target);
    const statusElement = row.querySelector(".status-pill");
    statusElement.textContent = status.text;
    statusElement.classList.add(status.className);
    row.querySelector(".latency").textContent = target.last_check?.latency_ms ? `${target.last_check.latency_ms} мс` : "—";
    row.querySelector(".check-button").addEventListener("click", () => runCheck(target.id));
    row.querySelector(".delete-button").addEventListener("click", () => deleteTarget(target.id, target.name));
    body.appendChild(row);
  });
}

function renderDashboard(dashboard) {
  $("#total-count").textContent = dashboard.total;
  $("#up-count").textContent = dashboard.up;
  $("#down-count").textContent = dashboard.down;
  $("#never-count").textContent = dashboard.never_checked;
}

async function refresh() {
  if (state.refreshInProgress) return;
  state.refreshInProgress = true;
  try {
    const [targets, dashboard, health] = await Promise.all([
      request("/api/targets"), request("/api/dashboard"), request("/api/health"),
    ]);
    state.targets = targets;
    renderTargets();
    renderDashboard(dashboard);
    $("#service-status").textContent = health.status === "ok" ? "Сервис работает" : "Сервис недоступен";
  } catch (error) {
    showNotice(error.message, true);
    $("#service-status").textContent = "Ошибка соединения";
  } finally {
    state.refreshInProgress = false;
  }
}

async function runCheck(id) {
  try { await request(`/api/targets/${id}/check`, { method: "POST", body: "{}" }); await refresh(); showNotice("Проверка завершена"); }
  catch (error) { showNotice(error.message, true); }
}

async function deleteTarget(id, name) {
  if (!window.confirm(`Удалить цель «${name}»?`)) return;
  try { await request(`/api/targets/${id}`, { method: "DELETE" }); await refresh(); showNotice("Цель удалена"); }
  catch (error) { showNotice(error.message, true); }
}

function updateKindFields() {
  const kind = $("#kind-field").value;
  const http = kind === "http";
  $("#url-field").hidden = !http;
  $("#host-field").hidden = http;
  $("#port-field").hidden = http;
}

$("#kind-field").addEventListener("change", updateKindFields);
$("#refresh-button").addEventListener("click", refresh);
$("#target-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  const kind = form.get("kind");
  const payload = { name: form.get("name"), kind, interval_seconds: Number(form.get("interval_seconds")), timeout_seconds: 5, enabled: true };
  if (kind === "http") payload.url = form.get("url");
  else { payload.host = form.get("host"); payload.port = Number(form.get("port")); }
  try { await request("/api/targets", { method: "POST", body: JSON.stringify(payload) }); formElement.reset(); updateKindFields(); await refresh(); showNotice("Цель добавлена"); }
  catch (error) { showNotice(error.message, true); }
});

updateKindFields();
refresh();
window.setInterval(refresh, DASHBOARD_REFRESH_MS);
