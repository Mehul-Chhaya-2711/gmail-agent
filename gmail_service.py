"""
Gmail service setup and email fetching utilities.
Handles OAuth authentication and safe read-only inbox scanning.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service():
    """
    Authenticate and return a Gmail API service object.
    Uses token.json if present, otherwise starts OAuth flow.
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    if not creds or not creds.valid:
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "credentials.json not found in project root. "
                "Please upload your Google OAuth desktop app credentials."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES,
        )
        creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def _extract_header(headers: List[Dict[str, str]], name: str) -> str:
    """
    Safely extract a named header from Gmail message headers.
    """
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _decode_base64url(data: str) -> str:
    """
    Decode Gmail base64url encoded content safely.
    """
    if not data:
        return ""

    padding = "=" * (-len(data) % 4)
    try:
        return base64.urlsafe_b64decode(data + padding).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_body_from_payload(payload: Dict[str, Any]) -> str:
    """
    Extract plain text body from Gmail message payload.
    Falls back carefully if multipart sections are present.
    """
    body_data = payload.get("body", {}).get("data")
    if body_data:
        return _decode_base64url(body_data)

    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            return _decode_base64url(data)

    return ""


def fetch_emails(service, max_results: int = 50, query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch a batch of emails from Gmail.

    Args:
        service: Authenticated Gmail API service
        max_results: Number of emails to fetch
        query: Optional Gmail search query

    Returns:
        List of normalized email dictionaries
    """
    response = service.users().messages().list(
        userId="me",
        maxResults=max_results,
        q=query,
    ).execute()

    messages = response.get("messages", [])
    results: List[Dict[str, Any]] = []

    for msg in messages:
        msg_id = msg["id"]
        full_message = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full",
        ).execute()

        payload = full_message.get("payload", {})
        headers = payload.get("headers", [])

        sender = _extract_header(headers, "From")
        subject = _extract_header(headers, "Subject")
        date = _extract_header(headers, "Date")
        snippet = full_message.get("snippet", "")
        body = _extract_body_from_payload(payload)

        results.append(
            {
                "email_id": msg_id,
                "thread_id": full_message.get("threadId", ""),
                "sender": sender,
                "subject": subject,
                "date": date,
                "snippet": snippet,
                "body": body,
            }
        )

    return results