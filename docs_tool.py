"""Google Docs tool — append text to a document."""

from __future__ import annotations

from googleapiclient.discovery import build

from auth import get_credentials


def append_to_doc(doc_id: str, content: str) -> dict:
    """Append text to the end of a Google Doc."""
    creds = get_credentials()
    service = build("docs", "v1", credentials=creds)

    doc = service.documents().get(documentId=doc_id).execute()
    end_index = doc["body"]["content"][-1]["endIndex"] - 1

    requests = [
        {
            "insertText": {
                "location": {"index": end_index},
                "text": content,
            }
        }
    ]

    result = (
        service.documents()
        .batchUpdate(documentId=doc_id, body={"requests": requests})
        .execute()
    )

    return {
        "document_id": doc_id,
        "appended_chars": len(content),
        "replies": result.get("replies", []),
    }
