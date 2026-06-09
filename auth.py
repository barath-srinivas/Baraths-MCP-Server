"""Google OAuth 2.0 authentication for Docs and Gmail."""

from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.compose",
]

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = Path(os.getenv("CREDENTIALS_FILE", str(BASE_DIR / "credentials.json")))
TOKEN_FILE = Path(os.getenv("TOKEN_FILE", str(BASE_DIR / "token.json")))


def _ensure_files_from_env() -> None:
    """Materialize credentials/token from Railway env vars when files are absent."""
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if credentials_json and not CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CREDENTIALS_FILE.write_text(credentials_json, encoding="utf-8")

    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json and not TOKEN_FILE.exists():
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(token_json, encoding="utf-8")


def _load_token_credentials() -> Credentials | None:
    token_json = os.getenv("GOOGLE_TOKEN_JSON")
    if token_json:
        return Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)

    if TOKEN_FILE.exists():
        return Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    return None


def get_credentials() -> Credentials:
    """Load saved credentials or run the OAuth flow once (local dev only)."""
    _ensure_files_from_env()

    creds = _load_token_credentials()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds)
        return creds

    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("GOOGLE_TOKEN_JSON"):
        raise RuntimeError(
            "Google token is missing or invalid. Update GOOGLE_TOKEN_JSON in Railway "
            "or re-run local OAuth and redeploy the token."
        )

    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Missing {CREDENTIALS_FILE.name}. Download OAuth client credentials "
            "from Google Cloud Console and place them in this directory, or set "
            "GOOGLE_CREDENTIALS_JSON."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds)
    return creds


def _save_token(creds: Credentials) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
