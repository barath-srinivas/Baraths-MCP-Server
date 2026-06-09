"""FastAPI server exposing Google Docs and Gmail tools."""

from __future__ import annotations

import os
import sys
from typing import Annotated, Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from docs_tool import append_to_doc
from gmail_tool import create_email_draft

API_KEY = os.getenv("API_KEY")

app = FastAPI(
    title="Google MCP Server",
    description="Append to Google Docs and create Gmail drafts.",
    version="1.0.0",
)


class AppendToDocRequest(BaseModel):
    doc_id: str = Field(..., description="Google Doc ID from the document URL")
    content: str = Field(..., description="Text to append to the document")


class CreateEmailDraftRequest(BaseModel):
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Plain-text email body")


def authorize_action(
    action: str,
    payload: dict[str, Any],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    """Require API key on Railway, or terminal approval for local dev."""
    print(f"\nAction: {action}")
    print(f"Payload: {payload}")

    if API_KEY:
        if x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key.")
        return

    response = input("Approve? (y/n): ").strip().lower()
    if response != "y":
        raise HTTPException(status_code=403, detail="Action rejected by user.")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/append_to_doc")
def append_to_doc_endpoint(
    request: AppendToDocRequest,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, Any]:
    payload = request.model_dump()
    authorize_action("append_to_doc", payload, x_api_key)

    try:
        result = append_to_doc(doc_id=request.doc_id, content=request.content)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google Docs API error: {exc}") from exc

    return {"status": "success", "result": result}


@app.post("/create_email_draft")
def create_email_draft_endpoint(
    request: CreateEmailDraftRequest,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, Any]:
    payload = request.model_dump()
    authorize_action("create_email_draft", payload, x_api_key)

    try:
        result = create_email_draft(to=request.to, subject=request.subject, body=request.body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gmail API error: {exc}") from exc

    return {"status": "success", "result": result}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    uvicorn.run("server:app", host=host, port=port, reload=False)
