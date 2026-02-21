
import os
import torch
import cv2

from utils import DEVICE
from video_model import load_model
from video_service import analyze_video, detect_face

MEDIA_DIR = "media"

print("\n===== DEVICE TEST =====")
print("Device:", DEVICE)

print("\n===== MODEL TEST =====")
model,threshold = load_model()
model.to(DEVICE)
model.eval()

print(f"Threshold: {threshold}")

dummy = torch.randn(1,3,224,224).to(DEVICE)
output = model(dummy)
print("Model output shape:", output.shape)

print("\n===== MTCNN TEST =====")
img_path = os.path.join(MEDIA_DIR, "test.jpg")
img = cv2.imread(img_path)

if img is None:
    print(f"{img_path} not found.")
else:
    face = detect_face(img)
    print("Face detected:", face is not None)

print("\n===== FULL PIPELINE TEST =====")
video_path = os.path.join(MEDIA_DIR, "real_sample.mp4")
result = analyze_video(video_path)
print("Final Result:", result)
