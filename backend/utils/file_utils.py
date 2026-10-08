import os
from dotenv import load_dotenv

load_dotenv()

STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")


def get_video_dir() -> str:
    path = os.path.join(STORAGE_PATH, "videos")
    os.makedirs(path, exist_ok=True)
    return path


def get_frames_dir(session_id: str) -> str:
    path = os.path.join(STORAGE_PATH, "frames", session_id)
    os.makedirs(path, exist_ok=True)
    return path


def get_video_path(session_id: str, filename: str) -> str:
    return os.path.join(get_video_dir(), f"{session_id}_{filename}")


def get_frame_path(session_id: str, frame_number: int) -> str:
    return os.path.join(get_frames_dir(session_id), f"frame_{frame_number:06d}.jpg")


def screenshot_url(screenshot_path: str) -> str:
    if not screenshot_path:
        return None
    relative = screenshot_path.replace("\\", "/")
    return f"/storage/{relative.lstrip('./')}"
