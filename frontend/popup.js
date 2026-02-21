const API = "http://127.0.0.1:8000";

const statusEl = document.getElementById("status");
const chooseBtn = document.getElementById("chooseBtn");
const analyzeBtn = document.getElementById("analyzeBtn");
const fileInput = document.getElementById("videoInput");
const probabilityEl = document.getElementById("probability");
const arrowEl = document.getElementById("arrow");

function updateGauge(value) {
  if (!probabilityEl || !arrowEl) return;
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  const angle = -90 + (clamped / 100) * 180;
  arrowEl.style.transform = `rotate(${angle}deg)`;
  probabilityEl.innerText = `${Math.round(clamped)}%`;
}

chooseBtn.onclick = () => {
  fileInput.click();
};

fileInput.onchange = () => {
  const file = fileInput.files?.[0];
  statusEl.innerText = file ? "File uploaded" : "No file selected";
};

analyzeBtn.onclick = async () => {
  const file = fileInput.files?.[0];
  if (!file) {
    statusEl.innerText = "Please choose a file first";
    return;
  }

  statusEl.innerText = "Starting analysis...";

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
    const final = data.final;
    if (final && typeof final.final_score !== "undefined") {
      const asPercent = final.final_score <= 1 ? final.final_score * 100 : final.final_score;
      updateGauge(asPercent);
      statusEl.innerText = `Final: ${final.verdict} (${final.final_score})`;
    } else {
      statusEl.innerText = "Analysis completed";
    }
  } catch (err) {
    statusEl.innerText = "Backend not reachable";
    console.error(err);
  }
};
