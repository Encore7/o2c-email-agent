from __future__ import annotations

import base64
import json
from email.message import EmailMessage
from urllib import parse, request
from urllib.error import HTTPError, URLError


class GmailIntegrationError(RuntimeError):
    """Raised when Gmail draft creation fails."""


class GmailClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        user_id: str = "me",
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._user_id = user_id

    def create_draft(self, to_email: str, subject: str, body: str) -> str:
        access_token = self._get_access_token()
        raw_message = self._build_raw_message(to_email=to_email, subject=subject, body=body)
        payload = {"message": {"raw": raw_message}}

        req = request.Request(
            url=f"https://gmail.googleapis.com/gmail/v1/users/{self._user_id}/drafts",
            method="POST",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise GmailIntegrationError(f"Gmail draft API failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise GmailIntegrationError(f"Gmail draft API unreachable: {exc.reason}") from exc

        draft_id = data.get("id")
        if not draft_id:
            raise GmailIntegrationError("Gmail draft API response missing draft id.")
        return str(draft_id)

    def _get_access_token(self) -> str:
        token_req = request.Request(
            url="https://oauth2.googleapis.com/token",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=parse.urlencode(
                {
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": self._refresh_token,
                    "grant_type": "refresh_token",
                }
            ).encode("utf-8"),
        )
        try:
            with request.urlopen(token_req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise GmailIntegrationError(f"OAuth token refresh failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise GmailIntegrationError(f"OAuth token endpoint unreachable: {exc.reason}") from exc

        token = data.get("access_token")
        if not token:
            raise GmailIntegrationError("OAuth token response missing access_token.")
        return str(token)

    @staticmethod
    def _build_raw_message(to_email: str, subject: str, body: str) -> str:
        msg = EmailMessage()
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        raw_bytes = msg.as_bytes()
        return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")
