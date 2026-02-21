import os
import cv2
import torch
import numpy as np
import subprocess
import time

from facenet_pytorch import MTCNN
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image

from video_model import load_model
from utils import DEVICE


model ,THRESHOLD= load_model()
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

    frames= sorted([os.path.join(TEMP_DIR, f)
                     for f in os.listdir(TEMP_DIR)
                     if f.endswith(".jpg")
                     ])
    return frames

mtcnn = MTCNN(keep_all=False, device=DEVICE)

def detect_face(image):
    rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    boxes, _ = mtcnn.detect(rgb_img)
    if boxes is None:
        return None

    x1, y1, x2, y2 = boxes[0]
    face = image[int(y1):int(y2), int(x1):int(x2)]
    return face

def preprocess(face_img):
    face_img = cv2.resize(face_img, (224, 224))
    face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    face_img = face_img.astype(np.float32) / 255.0

    tensor = torch.from_numpy(face_img).permute(2, 0, 1).unsqueeze(0)

    return tensor.to(DEVICE)

def predict(tensor):
    with torch.no_grad():
        output = model(tensor)
        prob = torch.sigmoid(output).item()
    return prob


def aggregate_scores(scores):
    return float(sum(scores) / len(scores))

def generate_gradcam(tensor):
    try:
        original_device = next(model.parameters()).device

        if DEVICE.type == "mps":
           model_cpu = model.cpu()
           target_layers = [model_cpu.target_layer]
           cam = GradCAM(model=model_cpu, target_layers=target_layers)
        else:
          target_layers = [model.target_layer]
          cam = GradCAM(model=model, target_layers=target_layers)
        targets = [ClassifierOutputTarget(0)]

        grayscale_cam = cam(input_tensor=tensor, targets=targets)[0]

        rgb_img = tensor.squeeze().permute(1, 2, 0).cpu().numpy()
        heatmap = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)

        heatmap_path = os.path.join(TEMP_DIR, "heatmap.jpg")
        cv2.imwrite(heatmap_path, heatmap)

        model.to(original_device)
        return heatmap_path

    except Exception as e:
        print("GradCAM failed:", e)
        return None
    

def analyze_video(video_path):
    start_time = time.time()

    frame_paths = extract_frames(video_path)

    scores = []
    last_tensor = None

    for frame_path in frame_paths:
        img = cv2.imread(frame_path)
        if img is None:
            continue

        face = detect_face(img)
        if face is None:
            continue

        tensor = preprocess(face)
        score = predict(tensor)

        scores.append(score)
        last_tensor = tensor

    if len(scores) == 0:
        return {
            "type": "video",
            "video_score": 0.5,
            "status": "No Face Detected"
        }

    final_score = 0.7 * max(scores) + 0.3 * (sum(scores) / len(scores))
    margin=0.02
    result = {
        "type": "video",
        "video_score": final_score,
        "status": "Likely Fake" if final_score > THRESHOLD + margin else ("Likely Real" if final_score < THRESHOLD - margin else "Suspicious")
    }

    if final_score > 0.8 and last_tensor is not None:
        heatmap_path = generate_gradcam(last_tensor)
        if heatmap_path:
            result["heatmap"] = heatmap_path

    print(f"[VIDEO] Score: {final_score:.3f} | Time: {time.time() - start_time:.2f}s")

    return result
