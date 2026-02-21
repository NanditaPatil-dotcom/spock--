const API = "http://127.0.0.1:8000";

const statusEl = document.getElementById("status");
const fileInput = document.getElementById("videoInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const probabilityEl = document.getElementById("probability");
const arrowEl = document.getElementById("arrow");

function updateGauge(value) {
  if (!probabilityEl || !arrowEl) return;
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));
  const angle = -90 + (clamped / 100) * 180;
  arrowEl.style.transform = `rotate(${angle}deg)`;
  probabilityEl.innerText = `${Math.round(clamped)}%`;
}

function connectWs(result) {
  const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${result.analysis_id}`);

  ws.onopen = () => {
    ws.send(JSON.stringify({
      video_task_id: result.video_task_id,
      audio_task_id: result.audio_task_id,
      metadata_task_id: result.metadata_task_id
    }));
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.stage === "final") {
        const finalScore = data.result?.final_score;
        statusEl.innerText = finalScore != null
          ? `Final score: ${finalScore}`
          : "Analysis complete";
        if (finalScore != null) {
          const asPercent = finalScore <= 1 ? finalScore * 100 : finalScore;
          updateGauge(asPercent);
        }
        return;
      }
      statusEl.innerText = `Stage complete: ${data.stage}`;
    } catch (err) {
      console.error("Invalid WS payload", err);
      statusEl.innerText = "Received invalid update from backend";
    }
  };

  ws.onerror = () => {
    statusEl.innerText = "WebSocket connection error";
  };
}

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

    const res = await fetch(API + "/analyze-upload", {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      throw new Error("Request failed with status " + res.status);
    }

    const data = await res.json();
    statusEl.innerText = "Upload accepted. Waiting for results...";
    connectWs(data);
  } catch (err) {
    statusEl.innerText = "Backend not reachable";
    console.error(err);
  }
};

fileInput.addEventListener("change", () => {
  statusEl.innerText = fileInput.files?.[0] ? "File uploaded" : "No file selected";
});
