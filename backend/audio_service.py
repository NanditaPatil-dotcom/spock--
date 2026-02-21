import os
import subprocess
import librosa
import numpy as np
import torch
import time

from audio_model import CRNN
from audio_model import load_audio_model

DEVICE = torch.device("cpu")
torch.set_num_threads(2)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

model, THRESHOLD = load_audio_model()

model.to(DEVICE)
model.eval()

DEVICE = torch.device("cpu")
torch.set_num_threads(2)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

model = CRNN()
model.to(DEVICE)
model.eval()


# --------------------
# Extract audio from video
# --------------------
def extract_audio(video_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-ac", "1",
        "-ar", "16000",
        "-t", "10",
        "-vn",
        output_path,
        "-y"
    ]
    subprocess.run(cmd)
    return output_path


def load_audio(path):
    audio, sr = librosa.load(path, sr=16000)
    return audio, sr


def create_mel(audio, sr):
    mel = librosa.feature.melspectrogram(
        y=audio,
        sr=sr,
        n_mels=128,
        n_fft=1024,
        hop_length=512
    )

    mel_db = librosa.power_to_db(mel, ref=np.max)

    # CRITICAL
    mel_db = np.nan_to_num(mel_db)

    return mel_db

def preprocess(mel_db):
    mel_tensor = torch.tensor(mel_db).float()
    mel_tensor = mel_tensor.unsqueeze(0).unsqueeze(0)  # (1,1,128,T)

    return mel_tensor.to(DEVICE)


def analyze_audio(video_path):

    start = time.time()

    wav_path = os.path.join(TEMP_DIR, "temp.wav")

    extract_audio(video_path, wav_path)

    audio, sr = load_audio(wav_path)

    if sr != 16000:
        return {"error": "Sample rate mismatch"}

    mel = create_mel(audio, sr)
    mel = (mel - mel.mean()) / (mel.std() + 1e-6)

    MAX_LEN = 300

    if mel.shape[1] < MAX_LEN:
      pad_size = MAX_LEN - mel.shape[1]
      mel = np.pad(mel, ((0,0),(0,pad_size)), mode='constant')
    else:
      mel = mel[:, :MAX_LEN]
    
    print("Mel shape:", mel.shape)

    tensor = preprocess(mel)
    print("Tensor shape:", tensor.shape)

    with torch.no_grad():
        prob = model(tensor).item()

    if prob > THRESHOLD + 0.1:
      status = "Likely Fake"
    elif prob < THRESHOLD - 0.1:
      status = "Likely Real"
    else:
      status = "Uncertain"
    
    print(f"[AUDIO] Score: {prob:.3f} | Time: {time.time() - start:.2f}s")

    return {
        "type": "audio",
        "audio_probability": prob,
        "status":status
    }