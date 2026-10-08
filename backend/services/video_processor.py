import os
import subprocess
from utils.file_utils import get_frames_dir

FRAMES_PER_SECOND = int(os.getenv("FRAMES_PER_SECOND", "1"))


def extract_frames(video_path: str, session_id: str) -> tuple[list[str], int]:
    """
    Extract frames from a video file using ffmpeg.
    Returns (list_of_frame_paths, duration_seconds).
    """
    frames_dir = get_frames_dir(session_id)

    # Get video duration first
    probe_cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", video_path,
    ]
    try:
        import json
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(result.stdout)
        duration = int(float(info["format"].get("duration", 0)))
    except Exception:
        duration = 0

    # Extract frames
    pattern = os.path.join(frames_dir, "frame_%06d.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps={FRAMES_PER_SECOND}",
        "-q:v", "2",
        pattern,
    ]
    subprocess.run(cmd, capture_output=True, timeout=600)

    # Collect frame paths in order
    frame_files = sorted(
        [
            os.path.join(frames_dir, f)
            for f in os.listdir(frames_dir)
            if f.endswith(".jpg")
        ]
    )
    return frame_files, duration
