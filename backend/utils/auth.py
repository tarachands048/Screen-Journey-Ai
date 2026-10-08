import os
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

TEAM_TOKEN = os.getenv("TEAM_SECRET_TOKEN")
if not TEAM_TOKEN:
    raise RuntimeError(
        "TEAM_SECRET_TOKEN is not set. Copy backend/.env.example to backend/.env and set a token."
    )


def verify_token(x_team_token: str = Header(...)):
    if x_team_token != TEAM_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid team token",
        )
    return x_team_token
