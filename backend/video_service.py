import os
import cv2
import torch
import numpy as np
import subprocess
import time
from model import load_model
from utils import DEVICE


model = load_model()
model.to(DEVICE)
model.eval()

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

#frame extraction
def extract_frames(video_path):

    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", "fps=1",
        "-frames:v", "5",
        f"{TEMP_DIR}/frame_%03d.jpg"
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return sorted([os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR)])

