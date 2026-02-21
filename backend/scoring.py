def compute_final_score(video_result, audio_result, metadata_result):

    video_score = video_result.get("video_score", 0.5)
    audio_score = audio_result.get("audio_probability", 0.5)
    metadata_score = metadata_result.get("metadata_score", 0.5)

    final_score = (
        0.4 * video_score +
        0.3 * audio_score +
        0.3 * metadata_score
    )

    if metadata_result.get("recycled"):
        final_score = max(final_score, 0.8)

    verdict = "Likely Fake" if final_score > 0.6 else "Likely Real"

    return {
        "final_score": round(final_score, 3),
        "verdict": verdict
    }