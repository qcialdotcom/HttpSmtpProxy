"""
schema.py
=========

Email and SMTP configuration schemas for the FastAPI SMTP proxy server.
"""

from typing import Any

from pydantic import BaseModel


class EmailAddress(BaseModel):
    email: str
    name: str | None = None


class SMTPConfig(BaseModel):
    host: str
    port: int
    username: str
    password: str
    sender: EmailAddress
    use_tls: bool = False
    use_ssl: bool = False
    timeout: float | None = None
    ssl_keyfile: str | None = None
    ssl_certfile: str | None = None


class Attachment(BaseModel):
    filename: str
    content: str  # base64-encoded content
    mimetype: str = "application/octet-stream"


class EmailMessage(BaseModel):
    to: list[EmailAddress]
    subject: str | None = None
    text_body: str | None = None
    html_body: str | None = None
    cc: list[EmailAddress] = []
    bcc: list[EmailAddress] = []
    reply_to: EmailAddress | None = None
    headers: dict[str, str] = {}
    params: dict[str, Any] = {}
    attachments: list[Attachment] = []


class EmailPayload(BaseModel):
    smtp_config: SMTPConfig
    sender: EmailAddress
    messages: list[EmailMessage]

class EmailResponse(BaseModel):
    message: str
    status: str
    queued: int