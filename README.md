***Brownie Point: This project won under Best Women's Team at IEEE Kalpana 6.0 - Hack for Humanity***

# Verifyy

Verifyy is a real-time multimodal deepfake detection system designed to restore trust in digital media. It analyzes video, audio, and metadata to generate a calibrated trust score indicating whether content is likely real or manipulated.

The system is built with a scalable backend architecture and a browser extension interface, making deepfake detection accessible and practical for real-world use.

---
> **Important Note**
> 
> This extension currently detects deepfakes based on patterns learned from the **DFDC (Kaggle) dataset** used during training.
> 
> Detection performance may vary significantly on content outside this dataset due to domain shift. If you have access to a more diverse or representative dataset, you are encouraged to fork the project and retrain the models accordingly.
> 
> Current observed accuracy: **~80–85%** under DFDC-like conditions.
> 
> This project is an evolving research prototype and not a production-grade forensic system.


## Overview

Verifyy performs detection across three independent layers:

* **Video Analysis** – Detects facial manipulation artifacts.
* **Audio Analysis** – Identifies synthetic or cloned voice patterns.
* **Metadata Analysis** – Examines file-level forensic signals.

The outputs from these components are fused into a final trust score that reflects the overall likelihood of manipulation.

---

## Key Features

* Multimodal deepfake detection (video + audio + metadata)
* Real-time inference using asynchronous backend services
* Explainable using Grad-CAM heatmaps
* Browser extension interface
* REST API and WebSocket support for live updates

---

## System Architecture

```
[User Layer]
   ↓
[Browser Extension]
   ↓
[API Gateway]
   ↓
[Processing Engine]
   ↓
[Trust Scoring System]
   ↓
[Database]
```
---

## Technical Stack

### Backend

* Python
* FastAPI
* Celery
* Redis
* PyTorch
* FFmpeg
* Librosa
* ImageHash

### Frontend

* Chrome Extension (Manifest V3)
* HTML, CSS, JavaScript

### Models

* ResNet18 (Video classification)
* CRNN (Audio spoof detection)

---

## How It Works

### 1. Video Analysis

* Extracts key frames using FFmpeg.
* Detects faces using MTCNN.
* Crops and preprocesses facial regions.
* Runs inference using a fine-tuned ResNet18 model.
* Generates probability of facial manipulation.
* Optionally produces Grad-CAM heatmaps for explainability.

### 2. Audio Analysis

* Extracts audio from video at 16 kHz mono.
* Converts waveform to Mel-spectrogram.
* Processes through a CRNN model.
* Outputs probability of voice spoofing.

### 3. Metadata Analysis

* Computes SHA-256 hash for duplicate detection.
* Generates perceptual hash (pHash) for similarity detection.
* Extracts encoding metadata using FFprobe.
* Produces metadata risk score.

### 4. Fusion

Final trust score is computed using weighted fusion:

```
Final Score = 0.6 × Video Score + 0.4 × Audio Score
```

Metadata acts as an override signal in cases of detected recycling or duplication.

The result is categorized as:

* Likely Real
* Likely Fake

---

## Installation

### 1. Clone Repository

```
git clone <repository-url>
cd Verifyy
```

### 2. Create Virtual Environment

#### Linux

```
python3 -m venv venv
source venv/bin/activate
```

#### Windows

```
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 4. Install FFmpeg

Ensure both `ffmpeg` and `ffprobe` are installed and available in PATH.

Verify:

```
ffmpeg -version
ffprobe -version
```
### 5. Train the Model
a)
```
cd backend/audio_service
python train.py
```
b)
```
cd backend/video_service
python train.py
```
### 6. Start Redis

```
redis-server
```

### 7. Start Celery Worker

```
cd backend
celery -A backend.celery_app worker --loglevel=info -P solo
```

### 8. Start FastAPI Server

In a new terminal:

```
cd backend
uvicorn main:app --reload
```

API available at:

```
http://127.0.0.1:8000
```

---

## Testing

To test the full pipeline locally:

```
python test_full_pipeline.py
```
Expected results:

<img width="1920" height="302" alt="image" src="https://github.com/user-attachments/assets/46210026-c45d-42cb-a034-2b1f56b7d6db" />


## Chrome Extension Setup

1. Open Chrome.
2. Go to `chrome://extensions`.
3. Enable Developer Mode.
4. Click “Load Unpacked”.
5. Select the extension folder.

Ensure the backend server is running before testing.

---

## Project Structure

```
spock--/
├── .git/
├── .gitignore
├── README.md
├── requirements.txt
├── mac-requirements.txt
├── fedora-requirements-freeze.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── popup.html
│   ├── popup.js
│   ├── analyzer.html
│   └── analyzer.js
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── celery_app.py
│   ├── metadata_service.py
│   ├── scoring.py
│   ├── utils.py
│   ├── test_full_pipeline.py
│   ├── audio_service/
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── model.py
│   │   ├── service.py
│   │   └── train.py
│   ├── video_service/
│   │   ├── __init__.py
│   │   ├── model.py
│   │   ├── service.py
│   │   └── train.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_audio_module.py
│   │   ├── test_video_module.py
│   │   ├── test_scoring.py
│   │   ├── test_celery.py
│   │   └── test_ws.py
│   ├── weights/               
│   ├── media/                  
│   ├── audio_dataset/          
│   │   ├── fake/
│   │   └── real/
│   └── video_dataset/          
│       ├── fake/
│       └── real/                  

```

---

## Limitations

* Performance may vary across datasets (domain shift).
* Lip-sync consistency is not currently verified.
* Low-resolution faces may reduce detection accuracy.
* Highly advanced generative models may evade detection.

---

## Future Improvements

* Transformer-based multimodal fusion
* Lip-sync detection module
* Larger cross-dataset training
* Cloud deployment with scalable worker pools
