"""
Gmail notification helper for CoralKita.
Sends one separate message per recipient with proper RFC 2822 headers.
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKEN_PATH = "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Reuse one service + sender per process; lock for thread-safe parallel SST workers
_service = None
_sender_email: str | None = None
_service_lock = threading.Lock()


def get_gmail_service():
    """Initialize and return a cached Gmail API service."""
    global _service, _sender_email

    with _service_lock:
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_PATH, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())
            else:
                raise RuntimeError(
                    "Gmail credentials missing or invalid. Re-authorize and update token.json."
                )

        if _service is None:
            _service = build("gmail", "v1", credentials=creds, cache_discovery=False)
            _sender_email = None

        return _service


def get_sender_email() -> str | None:
    """
    Optional From address for logging/display.

    gmail.send does NOT allow users.getProfile — Gmail sets From automatically
    when the header is omitted. Use GMAIL_SENDER_EMAIL env or token.json "account".
    """
    global _sender_email
    if _sender_email:
        return _sender_email

    env_sender = (os.environ.get("GMAIL_SENDER_EMAIL") or "").strip()
    if env_sender:
        _sender_email = env_sender
        return _sender_email

    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, encoding="utf-8") as f:
                data = json.load(f)
            account = (data.get("account") or "").strip()
            if account:
                _sender_email = account
                return _sender_email
        except (OSError, json.JSONDecodeError):
            pass

    return None


def send_email_to_recipients(
    to_emails: list[str],
    subject: str,
    body: str,
    *,
    log_prefix: str = "[Gmail]",
    delay_seconds: float = 0.4,
) -> tuple[int, int]:
    """
    Send the same message to each address in its own Gmail API call.

    Returns:
        (success_count, failure_count)
    """
    emails: list[str] = []
    seen: set[str] = set()
    for raw in to_emails:
        email = (raw or "").strip()
        key = email.lower()
        if email and key not in seen:
            seen.add(key)
            emails.append(email)

    if not emails:
        print(f"{log_prefix} No recipient emails provided")
        return 0, 0

    try:
        service = get_gmail_service()
        sender = get_sender_email()
    except Exception as e:
        print(f"{log_prefix} Gmail setup failed: {e}")
        return 0, len(emails)

    from_line = f"From={sender} " if sender else ""
    print(f"{log_prefix} {from_line}sending to {len(emails)} recipient(s): {', '.join(emails)}")

    ok = 0
    fail = 0
    for i, recipient in enumerate(emails):
        try:
            mime = MIMEText(body, "plain", "utf-8")
            mime["Subject"] = subject
            mime["To"] = recipient
            if sender and os.environ.get("GMAIL_SENDER_EMAIL"):
                mime["From"] = sender

            raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
            with _service_lock:
                result = service.users().messages().send(
                    userId="me",
                    body={"raw": raw},
                ).execute()
            msg_id = result.get("id", "?")
            print(f"{log_prefix} OK id={msg_id} -> {recipient}")
            ok += 1
        except HttpError as e:
            fail += 1
            detail = e.content.decode("utf-8", errors="replace") if e.content else str(e)
            print(f"{log_prefix} HttpError -> {recipient}: {detail}")
        except Exception as e:
            fail += 1
            print(f"{log_prefix} Error -> {recipient}: {e}")

        if i < len(emails) - 1 and delay_seconds > 0:
            time.sleep(delay_seconds)

    print(f"{log_prefix} Done: {ok} sent, {fail} failed")
    return ok, fail
