const API = "http://127.0.0.1:8000";

const statusEl = document.getElementById("status");
const chooseBtn = document.getElementById("chooseBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const heatmapBtn = document.getElementById("heatmapBtn");
const fileInput = document.getElementById("videoInput");
const probabilityEl = document.getElementById("probability");
const arrowEl = document.getElementById("arrow");
const fakenessEl = document.getElementById("fakenessValue");
const heatmapModal = document.getElementById("heatmapModal");
const heatmapImage = document.getElementById("heatmapImage");
const closeHeatmapBtn = document.getElementById("closeHeatmapBtn");

let latestHeatmapUrl = null;

function updateGauge(value) {
  if (!probabilityEl || !arrowEl) return;
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  const angle = -90 + (clamped / 100) * 180;
  arrowEl.style.transform = `rotate(${angle}deg)`;
  probabilityEl.innerText = `${Math.round(clamped)}%`;
}

function setResultValues(score01) {
  const score = Math.max(0, Math.min(1, Number(score01) || 0));
  const percent = score * 100;
  // Animate from 0 to target for a visible needle movement each run.
  updateGauge(0);
  requestAnimationFrame(() => updateGauge(percent));
  if (fakenessEl) {
    fakenessEl.innerText = `Fakeness: ${percent.toFixed(1)}%`;
  }
}

chooseBtn.onclick = () => {
  fileInput.click();
};

fileInput.onchange = () => {
  const file = fileInput.files?.[0];
  statusEl.innerText = file ? "File uploaded" : "No file selected";
  latestHeatmapUrl = null;
  if (heatmapBtn) heatmapBtn.disabled = true;
};

if (heatmapBtn) {
  heatmapBtn.onclick = () => {
    if (!latestHeatmapUrl || !heatmapModal || !heatmapImage) return;
    heatmapImage.src = latestHeatmapUrl;
    heatmapModal.classList.add("show");
  };
}

if (closeHeatmapBtn && heatmapModal) {
  closeHeatmapBtn.onclick = () => heatmapModal.classList.remove("show");
  heatmapModal.onclick = (event) => {
    if (event.target === heatmapModal) {
      heatmapModal.classList.remove("show");
    }
  };
}

analyzeBtn.onclick = async () => {
  const file = fileInput.files?.[0];
  if (!file) {
    statusEl.innerText = "Please choose a file first";
    return;
  }

  statusEl.innerText = "Starting analysis...";
  setResultValues(0);
  latestHeatmapUrl = null;
  if (heatmapBtn) heatmapBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(API + "/analyse", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      throw new Error(`Upload failed: ${res.status}`);
    }

    const data = await res.json();
    if (typeof data.final_score !== "undefined") {
      statusEl.innerText = `Final: ${data.verdict} (${data.final_score})`;
      setResultValues(data.fakeness_score ?? data.final_score);
      if (data.heatmap_url) {
        latestHeatmapUrl = `${API}${data.heatmap_url}`;
        if (heatmapBtn) heatmapBtn.disabled = false;
      } else {
        latestHeatmapUrl = null;
        if (heatmapBtn) heatmapBtn.disabled = true;
      }
    } else {
      statusEl.innerText = "Analysis completed";
    }
  } catch (err) {
    statusEl.innerText = "Backend not reachable";
    console.error(err);
  }
};
