const form = document.getElementById("download-form");
const statusEl = document.getElementById("status");
const statusText = document.getElementById("status-text");
const historyList = document.getElementById("history-list");

function setStatus(state, text) {
  statusEl.className = `glass-status-pill status-${state}`;
  statusText.textContent = text;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatBytes(bytes) {
  if (!bytes) return "";
  const units = ["o", "Ko", "Mo", "Go"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(1)} ${units[unit]}`;
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const items = await res.json();
  historyList.innerHTML = "";
  items.slice().reverse().forEach((item) => {
    const li = document.createElement("li");
    li.className = "history-item";
    li.innerHTML = `<span class="history-title">${escapeHtml(item.title)}</span>
                     <span class="history-meta">${escapeHtml(item.platform)} · ${new Date(item.timestamp).toLocaleString()}</span>`;
    historyList.appendChild(li);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    url: document.getElementById("url").value.trim(),
    audio_only: document.getElementById("audio_only").checked,
    video_only: document.getElementById("video_only").checked,
    quality: document.getElementById("quality").value.trim() || null,
    start: document.getElementById("start").value.trim() || null,
    end: document.getElementById("end").value.trim() || null,
  };

  if (!payload.url) return;

  setStatus("analyzing", "Analyse du lien…");

  let jobId;
  try {
    const res = await fetch("/api/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Erreur serveur (${res.status})`);
    ({ job_id: jobId } = await res.json());
  } catch (err) {
    setStatus("error", err.message);
    return;
  }

  const ws = new WebSocket(`ws://${location.host}/ws/progress/${jobId}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case "analyzing":
        setStatus("analyzing", "Analyse du lien…");
        break;
      case "start":
        setStatus("downloading", `Téléchargement — ${data.title}`);
        break;
      case "progress": {
        const pct = data.total ? Math.round((data.downloaded / data.total) * 100) : null;
        setStatus("downloading", pct !== null ? `Téléchargement — ${pct}%` : `Téléchargement — ${formatBytes(data.downloaded)}`);
        break;
      }
      case "processing":
        setStatus("downloading", "Traitement en cours (FFmpeg)…");
        break;
      case "finished":
        setStatus("finished", `Terminé — ${data.title}`);
        loadHistory();
        break;
      case "error":
        setStatus("error", data.message);
        break;
    }
  };

  ws.onerror = () => setStatus("error", "Connexion perdue avec le serveur");
});

loadHistory();
