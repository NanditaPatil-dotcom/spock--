import os
import cv2
import torch
import numpy as np
import subprocess
import time

from retinaface import RetinaFace
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image

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

def detect_face(image):
    faces = RetinaFace.detect_faces(image)

    if not faces:
        return None

    first_face = list(faces.values())[0]
    x1, y1, x2, y2 = first_face["facial_area"]

    face_crop = image[y1:y2, x1:x2]
    return face_crop
