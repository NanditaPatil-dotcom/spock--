(() => {
  const API_BASE = "http://localhost:8000";
  const ANALYZE_URL = `${API_BASE}/analyze`;
  const WS_BASE = "ws://localhost:8000/ws";

  const el = {
    urlInput: document.getElementById("videoUrl"),
    fileInput: document.getElementById("videoFile"),
    analyzeBtn: document.getElementById("analyzeBtn"),
    errorText: document.getElementById("errorText"),
    progressText: document.getElementById("progressText"),
    progressBar: document.getElementById("progressBar"),
    socketState: document.getElementById("socketState"),
    videoScore: document.getElementById("videoScore"),
    videoStatus: document.getElementById("videoStatus"),
    audioScore: document.getElementById("audioScore"),
    audioStatus: document.getElementById("audioStatus"),
    metadataScore: document.getElementById("metadataScore"),
    metadataStatus: document.getElementById("metadataStatus"),
    finalScore: document.getElementById("finalScore"),
    verdict: document.getElementById("verdict"),
    heatmapImage: document.getElementById("heatmapImage"),
    heatmapPlaceholder: document.getElementById("heatmapPlaceholder")
  };

  let ws = null;
  let reconnectTimer = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 3;
  let analysisComplete = false;

  function createUUID() {
    return crypto.randomUUID();
  }

  function showError(message) {
    el.errorText.textContent = message;
    el.errorText.classList.remove("hidden");
  }

  function clearError() {
    el.errorText.textContent = "";
    el.errorText.classList.add("hidden");
  }

  function setLoading(isLoading) {
    el.analyzeBtn.disabled = isLoading;
    el.analyzeBtn.textContent = isLoading ? "Analyzing..." : "Analyze";
  }

  function setSocketState(label, className) {
    el.socketState.textContent = label;
    el.socketState.className = `pill ${className}`;
  }

  function setProgress(text, percent) {
    el.progressText.textContent = text;
    const safePercent = Math.max(0, Math.min(100, percent));
    el.progressBar.style.width = `${safePercent}%`;
  }

  function formatScore(value) {
    if (typeof value !== "number" || Number.isNaN(value)) return "-";
    return value.toFixed(2);
  }

  function verdictTone(verdict) {
    const v = (verdict || "").toLowerCase();
    if (v.includes("real")) {
      return "pill-good";
    }
    if (v.includes("fake")) {
      return "pill-bad";
    }
    return "pill-warn";
  }

  function statusTone(status) {
    const s = (status || "").toLowerCase();
    if (s.includes("real")) {
      return "status-good";
    }
    if (s.includes("fake")) {
      return "status-bad";
    }
    return "status-warn";
  }

  function setTextWithTone(element, text, toneClass) {
    element.textContent = text || "-";
    element.className = toneClass || "status";
  }

  function normalizeHeatmapPath(path) {
    if (!path) return "";
    if (/^https?:\/\//i.test(path)) return path;
    if (path.startsWith("/")) return `${API_BASE}${path}`;

    const cleaned = path.replace(/^\.\//, "").replace(/^temp\//, "");
    return `${API_BASE}/temp/${cleaned}`;
  }

  function showHeatmap(path) {
    const src = normalizeHeatmapPath(path);
    if (!src) return;

    el.heatmapImage.src = src;
    el.heatmapImage.classList.remove("hidden");
    el.heatmapPlaceholder.classList.add("hidden");
  }

  function resetUI() {
    analysisComplete = false;
    clearError();
    setProgress("Waiting for analysis...", 0);
    setSocketState("Idle", "pill-neutral");

    el.videoScore.textContent = "-";
    setTextWithTone(el.videoStatus, "-", "status");
    el.audioScore.textContent = "-";
    setTextWithTone(el.audioStatus, "-", "status");
    el.metadataScore.textContent = "-";
    setTextWithTone(el.metadataStatus, "-", "status");
    el.finalScore.textContent = "-";
    el.verdict.textContent = "-";
    el.verdict.className = "pill pill-neutral";

    el.heatmapImage.removeAttribute("src");
    el.heatmapImage.classList.add("hidden");
    el.heatmapPlaceholder.classList.remove("hidden");
  }

  function applyVideoPayload(msg) {
    const score = msg.video_score;
    const status = msg.status || "-";
    el.videoScore.textContent = formatScore(score);
    setTextWithTone(el.videoStatus, status, statusTone(status));
    if (msg.heatmap) {
      showHeatmap(msg.heatmap);
    }
    setProgress("Video analysis complete.", 35);
  }

  function applyAudioPayload(msg) {
    const score = typeof msg.audio_probability === "number" ? msg.audio_probability : msg.audio_score;
    const status = msg.status || "-";
    el.audioScore.textContent = formatScore(score);
    setTextWithTone(el.audioStatus, status, statusTone(status));
    setProgress("Audio analysis complete.", 65);
  }

  function applyMetadataPayload(msg) {
    const score = msg.metadata_score;
    const recycled = typeof msg.recycled === "boolean" ? (msg.recycled ? "Recycled" : "Original") : "-";
    el.metadataScore.textContent = formatScore(score);
    setTextWithTone(el.metadataStatus, recycled, "status");
    setProgress("Metadata analysis complete.", 85);
  }

  function applyFinalPayload(msg) {
    const score = msg.final_score;
    const verdict = msg.verdict || "Suspicious";
    el.finalScore.textContent = formatScore(score);
    el.verdict.textContent = verdict;
    el.verdict.className = `pill ${verdictTone(verdict)}`;
    setProgress("Analysis finished.", 100);
    analysisComplete = true;
    setLoading(false);
  }

  // Supports both the requested message schema and common wrapped responses.
  function handleBackendMessage(raw) {
    const msg = raw && typeof raw === "object" ? raw : {};

    if (msg.type === "video") {
      applyVideoPayload(msg);
      return;
    }
    if (msg.type === "audio") {
      applyAudioPayload(msg);
      return;
    }
    if (msg.type === "metadata") {
      applyMetadataPayload(msg);
      return;
    }
    if (msg.type === "final") {
      applyFinalPayload(msg);
      return;
    }

    if (msg.stage && msg.result) {
      if (msg.stage === "video_complete") {
        applyVideoPayload(msg.result);
      } else if (msg.stage === "audio_complete") {
        applyAudioPayload(msg.result);
      } else if (msg.stage === "metadata_complete") {
        applyMetadataPayload(msg.result);
      } else if (msg.stage === "final") {
        applyFinalPayload(msg.result);
      } else if (msg.stage === "task_state") {
        const states = msg.result || {};
        const details = `video=${states.video || "?"}, audio=${states.audio || "?"}, metadata=${states.metadata || "?"}`;
        setProgress(`Task states: ${details}`, 20);
      } else if (msg.stage === "error") {
        const errorMessage = msg.result && msg.result.message
          ? msg.result.message
          : "Analysis failed.";
        showError(errorMessage);
        setSocketState("Error", "pill-bad");
        setLoading(false);
      }
    }
  }

  function cleanupWebSocket() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
    if (ws) {
      ws.onopen = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.onmessage = null;
      ws.close();
      ws = null;
    }
  }

  function connectWebSocket(analysisId, initialPayload) {
    cleanupWebSocket();

    const wsUrl = `${WS_BASE}/${analysisId}`;
    ws = new WebSocket(wsUrl);
    setSocketState("Connecting", "pill-warn");

    ws.onopen = () => {
      reconnectAttempts = 0;
      setSocketState("Connected", "pill-good");
      setProgress("WebSocket connected. Waiting for updates...", 10);

      if (initialPayload) {
        ws.send(JSON.stringify(initialPayload));
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleBackendMessage(data);
      } catch (_err) {
        showError("Received invalid WebSocket message.");
      }
    };

    ws.onerror = () => {
      setSocketState("Error", "pill-bad");
    };

    ws.onclose = () => {
      if (analysisComplete) {
        setSocketState("Completed", "pill-neutral");
        return;
      }

      if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts += 1;
        setSocketState("Reconnecting", "pill-warn");
        setProgress(`WebSocket disconnected. Reconnecting (${reconnectAttempts}/${maxReconnectAttempts})...`, 12);
        reconnectTimer = setTimeout(() => connectWebSocket(analysisId, initialPayload), 1200 * reconnectAttempts);
      } else {
        setSocketState("Disconnected", "pill-bad");
        showError("WebSocket connection failed after multiple attempts.");
        setLoading(false);
      }
    };
  }

  async function submitAnalyzeRequest(analysisId, urlValue, file) {
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("analysis_id", analysisId);

      const response = await fetch(ANALYZE_URL, {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Analyze failed (${response.status}): ${text}`);
      }

      return response.json();
    }

    const response = await fetch(ANALYZE_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        video_url: urlValue,
        analysis_id: analysisId
      })
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Analyze failed (${response.status}): ${text}`);
    }

    return response.json();
  }

  async function runAnalysis() {
    clearError();

    const urlValue = el.urlInput.value.trim();
    const file = el.fileInput.files && el.fileInput.files[0] ? el.fileInput.files[0] : null;

    if (!urlValue && !file) {
      showError("Provide a video URL or select a video file.");
      return;
    }

    setLoading(true);
    resetUI();

    const analysisId = createUUID();
    setProgress(`Created analysis: ${analysisId.slice(0, 8)}...`, 5);

    try {
      const analysisResponse = await submitAnalyzeRequest(analysisId, urlValue, file);
      const resolvedAnalysisId = analysisResponse?.analysis_id || analysisId;
      const hasTaskIds = analysisResponse
        && analysisResponse.video_task_id
        && analysisResponse.audio_task_id
        && analysisResponse.metadata_task_id;

      if (!hasTaskIds) {
        throw new Error("Backend did not return task IDs. Check /analyze response.");
      }

      setProgress("Analysis queued. Connecting to live updates...", 8);
      connectWebSocket(resolvedAnalysisId, {
        video_task_id: analysisResponse.video_task_id,
        audio_task_id: analysisResponse.audio_task_id,
        metadata_task_id: analysisResponse.metadata_task_id
      });

      // If REST returns immediate results, render them too.
      if (analysisResponse.video_result) {
        handleBackendMessage({ type: "video", ...analysisResponse.video_result });
      }
      if (analysisResponse.audio_result) {
        handleBackendMessage({ type: "audio", ...analysisResponse.audio_result });
      }
      if (analysisResponse.metadata_result) {
        handleBackendMessage({ type: "metadata", ...analysisResponse.metadata_result });
      }
      if (analysisResponse.final) {
        const verdict = analysisResponse.final.verdict || analysisResponse.final.status || "Suspicious";
        const finalScore = typeof analysisResponse.final.final_score === "number"
          ? analysisResponse.final.final_score
          : analysisResponse.final.score;
        handleBackendMessage({
          type: "final",
          final_score: finalScore,
          verdict
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      showError(message);
      setSocketState("Error", "pill-bad");
      setLoading(false);
    }
  }

  el.analyzeBtn.addEventListener("click", runAnalysis);

  window.addEventListener("beforeunload", () => {
    cleanupWebSocket();
  });

  resetUI();
})();
