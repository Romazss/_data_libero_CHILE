// app.js
// /web_app/frontend/app.js
const API = (location.hostname === "localhost" || location.hostname === "127.0.0.1")
  ? "http://localhost:5001"
  : window.location.origin.replace(/:\d+$/, ""); // naive, ajusta si usas proxy

const tbody = document.getElementById("tbody");
const errBox = document.getElementById("error");
const stats = document.getElementById("stats");
const refreshBtn = document.getElementById("refreshBtn");
const autoSel = document.getElementById("autoRefresh");

let timer = null;

async function loadStatus() {
  errBox.textContent = "";
  tbody.innerHTML = `<tr><td colspan="5">Cargando…</td></tr>`;
  try {
    const res = await fetch(`${API}/status`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const items = data.results || [];
    tbody.innerHTML = items.map(row => {
      const badgeCls = row.status === "up" ? "badge up" : "badge down";
      const badgeText = row.status === "up" ? "Disponible" : "Caído";
      const latency = row.latency_ms != null ? `${row.latency_ms} ms` : "—";
      const http = row.http_code != null ? row.http_code : (row.error || "—");
      return `
        <tr>
          <td><a href="${row.url}" target="_blank" rel="noreferrer">${escapeHtml(row.name)}</a></td>
          <td>${escapeHtml(row.category)}</td>
          <td><span class="${badgeCls}">${badgeText}</span></td>
          <td>${latency}</td>
          <td>${http}</td>
        </tr>
      `;
    }).join("");

    const up = items.filter(x => x.status === "up").length;
    const down = items.length - up;
    stats.textContent = `Datasets: ${items.length} · Disponibles: ${up} · Caídos: ${down}`;
  } catch (e) {
    errBox.textContent = `Error al cargar /status: ${e.message}`;
    tbody.innerHTML = "";
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, m => ({
    "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"
  }[m]));
}

refreshBtn.addEventListener("click", loadStatus);

autoSel.addEventListener("change", () => {
  if (timer) { clearInterval(timer); timer = null; }
  const secs = parseInt(autoSel.value, 10);
  if (secs > 0) {
    timer = setInterval(loadStatus, secs * 1000);
  }
});

loadStatus(); // primera carga
if (parseInt(autoSel.value, 10) > 0) {
  timer = setInterval(loadStatus, parseInt(autoSel.value, 10) * 1000);
}