# backend/main.py

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from celery.result import AsyncResult

from celery_app import celery
from video_service import task_video_analysis
from audio_service import task_audio_analysis
from metadata_service import task_metadata_analysis
from scoring import compute_final_score

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/analyze")
async def analyze(video_path: str):

    analysis_id = str(uuid4())

    video_task = task_video_analysis.delay(video_path)
    audio_task = task_audio_analysis.delay(video_path)
    metadata_task = task_metadata_analysis.delay(video_path)

    return {
        "analysis_id": analysis_id,
        "video_task_id": video_task.id,
        "audio_task_id": audio_task.id,
        "metadata_task_id": metadata_task.id
    }
@app.websocket("/ws/{analysis_id}")
async def websocket_endpoint(websocket: WebSocket, analysis_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            video_id = data["video_task_id"]
            audio_id = data["audio_task_id"]
            metadata_id = data["metadata_task_id"]

            video_result = AsyncResult(video_id)
            audio_result = AsyncResult(audio_id)
            metadata_result = AsyncResult(metadata_id)

            if video_result.ready():
                await websocket.send_json({
                    "stage": "video_complete",
                    "result": video_result.result
                })

            if audio_result.ready():
                await websocket.send_json({
                    "stage": "audio_complete",
                    "result": audio_result.result
                })

            if metadata_result.ready():
                await websocket.send_json({
                    "stage": "metadata_complete",
                    "result": metadata_result.result
                })

            if (
                video_result.ready() and
                audio_result.ready() and
                metadata_result.ready()
            ):
                final = compute_final_score(
                    video_result.result,
                    audio_result.result,
                    metadata_result.result
                )

                await websocket.send_json({
                    "stage": "final",
                    "result": final
                })

                break

    except Exception:
        await websocket.close()

