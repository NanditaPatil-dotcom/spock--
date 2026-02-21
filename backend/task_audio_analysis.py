import os
import torch
import librosa
import numpy as np
from celery import Celery

# 👉 change this to your broker (Redis recommended)
celery_app = Celery(
    "audio_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

MODEL_PATH = "crnn_audio_fake.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ---- Load model once when worker starts ----
model = None

def load_model():
    global model
    if model is None:
        model = torch.load(MODEL_PATH, map_location=DEVICE)
        model.eval()
    return model


# ---- Audio preprocessing ----
def wav_to_mel(path, sr=22050, n_mels=128, duration=3):
    y, _ = librosa.load(path, sr=sr)

    # pad / trim
    target_len = sr * duration
    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)))
    else:
        y = y[:target_len]

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    mel = librosa.power_to_db(mel, ref=np.max)

    return torch.tensor(mel).unsqueeze(0).unsqueeze(0).float()


# ---- Celery task ----
@celery_app.task(name="audio.analyze")
def analyze_audio(file_path):
    """
    Returns:
        { "prediction": "real" | "fake", "confidence": float }
    """
    if not os.path.exists(file_path):
        return {"error": "file not found"}

    model = load_model()

    mel = wav_to_mel(file_path).to(DEVICE)

    with torch.no_grad():
        output = model(mel)
        prob = torch.sigmoid(output).item()

    label = "fake" if prob > 0.5 else "real"

    return {
        "prediction": label,
        "confidence": round(prob, 4)
    }