from audio_service import analyze_audio
import os
MEDIA_DIR="media"

audio_path = os.path.join(MEDIA_DIR, "real_sample.mp4")
result = analyze_audio(audio_path)
print(result)