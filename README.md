# Google MCP Server

A Python FastAPI server that integrates with **Google Docs** (append text) and **Gmail** (create drafts). Each action is printed to the terminal and requires interactive approval before it runs.

## Project structure

```
google-mcp-server/
├── server.py          # FastAPI app with tool endpoints
├── auth.py            # Google OAuth authentication
├── docs_tool.py       # Google Docs tool (append content)
├── gmail_tool.py      # Gmail tool (create draft)
├── requirements.txt   # Dependencies
├── README.md          # This file
├── credentials.json   # OAuth client credentials (not committed)
└── token.json         # Saved OAuth token (not committed)
```

## Prerequisites

1. A [Google Cloud project](https://console.cloud.google.com/)
2. **Google Docs API** and **Gmail API** enabled for that project
3. OAuth 2.0 **Desktop app** credentials downloaded as `credentials.json`

### Google Cloud setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Library**.
2. Enable:
   - Google Docs API
   - Gmail API
3. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**.
4. Choose **Desktop app**, download the JSON, and save it as `credentials.json` in this folder.
5. Under **OAuth consent screen**, add your Google account as a test user (if the app is in testing mode).

## Installation

```bash
cd google-mcp-server
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## First-time authentication

On the first API call (or when you run a quick auth check), a browser window opens for Google sign-in. After you approve, a `token.json` file is created. Later runs reuse that token and refresh it automatically when needed.

To authenticate before starting the server:

```bash
python -c "from auth import get_credentials; get_credentials()"
```

## Run the server

```bash
python server.py
```

Default URL: `http://127.0.0.1:8000`

Optional custom port:

```bash
python server.py 8080
```

Interactive API docs: `http://127.0.0.1:8000/docs`

## Endpoints

### `GET /health`

Health check.

### `POST /append_to_doc`

Append text to a Google Doc.

**Body:**

```json
{
  "doc_id": "YOUR_DOCUMENT_ID",
  "content": "Text to append.\n"
}
```

The document ID is the long string in the Doc URL:

`https://docs.google.com/document/d/DOCUMENT_ID/edit`

**Example (curl):**

```bash
curl -X POST http://127.0.0.1:8000/append_to_doc \
  -H "Content-Type: application/json" \
  -d "{\"doc_id\": \"YOUR_DOCUMENT_ID\", \"content\": \"Hello from the MCP server!\\n\"}"
```

The server prints the action and payload, then prompts:

```
Action: append_to_doc
Payload: {'doc_id': '...', 'content': '...'}
Approve? (y/n):
```

Type `y` to proceed, anything else cancels with HTTP 403.

### `POST /create_email_draft`

Create a Gmail draft (does not send).

**Body:**

```json
{
  "to": "recipient@example.com",
  "subject": "Draft subject",
  "body": "Draft body text."
}
```

**Example (curl):**

```bash
curl -X POST http://127.0.0.1:8000/create_email_draft \
  -H "Content-Type: application/json" \
  -d "{\"to\": \"you@example.com\", \"subject\": \"Test draft\", \"body\": \"Hello!\"}"
```

Same approval prompt appears in the terminal before the draft is created.

## OAuth scopes

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/documents` | Read and edit Google Docs |
| `https://www.googleapis.com/auth/gmail.compose` | Create and manage Gmail drafts |

## Security notes

- Do **not** commit `credentials.json` or `token.json`.
- Run the server locally; the approval prompt assumes a trusted operator at the terminal.
- Revoke access anytime at [Google Account permissions](https://myaccount.google.com/permissions).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Missing credentials.json` | Download OAuth desktop credentials from Google Cloud Console |
| `403 Access Not Configured` | Enable Google Docs API and Gmail API in your project |
| `invalid_grant` on token refresh | Delete `token.json` and authenticate again |
| Approval prompt never appears | Run `python server.py` in a terminal (not detached); stdin must be connected |
| Doc append fails | Confirm the signed-in account can edit the document |
