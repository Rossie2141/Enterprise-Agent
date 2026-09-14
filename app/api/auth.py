import os

from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()


def verify_api_key(
    x_api_key: str | None = Header(default=None),
):
    expected_api_key = os.getenv("API_KEY")

    if not expected_api_key:
        raise HTTPException(
            status_code=500,
            detail="API authentication is not configured.",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key.",
        )

    if x_api_key != expected_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return True