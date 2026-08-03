"""
main.py
=======

FastAPI SMTP proxy server.

This API receives SMTP configuration and email data in a JSON request,
then sends the emails using the provided SMTP server.


API Key Stored in Environment Variable
---------------------------------------

ALLOWED_API_KEYS: Comma-separated list of allowed API keys
                    ex: 1st-key,2nd-key,3rd-key so on
ALLOWED_TOKEN: Optional token type to be used in the Authorization header.
                    ex: Bearer, Token, etc. If not provided, any token type will be accepted.

Auth header expected on requests:
    Authorization: Bearer <api-key>
    Authorization: <token_type> <api-key>   # token_type is ignored, only the key is checked
"""

import base64
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage as PyEmailMessage
from email.utils import formataddr

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException

from .schema import EmailAddress, EmailMessage, EmailPayload, EmailResponse, SMTPConfig

load_dotenv()

logger = logging.getLogger("smtp_proxy")

ALLOWED_API_KEYS = {
    key.strip()
    for key in os.environ.get("ALLOWED_API_KEYS", "").split(",")
    if key.strip()
}

ALLOWED_TOKEN = os.environ.get("ALLOWED_TOKEN", "").strip()

IS_DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

if not ALLOWED_API_KEYS and not ALLOWED_TOKEN:
    raise RuntimeError(
        "No API keys or token provided. Set ALLOWED_API_KEYS or ALLOWED_TOKEN environment variable."
    )


app = FastAPI(
    docs_url="/docs" if IS_DEBUG else None,
    redoc_url="/redoc" if IS_DEBUG else None,
    openapi_url="/openapi.json" if IS_DEBUG else None,
)


def _extract_key_and_token(authorization: str | None) -> tuple[str, str] | None:
    """Extract API key and token type from Authorization header."""

    if not authorization:
        return None
    try:
        token_type, api_key = authorization.split(" ", 1)
        return token_type.strip(), api_key.strip()
    except ValueError:
        return None


def _verify_authorization(authorization: str | None) -> bool:
    """Verify the provided Authorization header against allowed API keys and token."""

    token_and_key = _extract_key_and_token(authorization)

    if not token_and_key:
        return False

    token_type, api_key = token_and_key

    return api_key in ALLOWED_API_KEYS and token_type == ALLOWED_TOKEN


def _format_address(addr: EmailAddress) -> str:
    """
    format an EmailAddress into a string suitable for email headers.

    i.e. "Name <example@example.com>"
    """

    return formataddr((addr.name or "", addr.email))


def _build_email(sender: EmailAddress, message: EmailMessage) -> PyEmailMessage:
    """Build a PyEmailMessage from the provided sender and EmailMessage data."""

    email_msg = PyEmailMessage()

    email_msg["From"] = _format_address(sender)
    email_msg["To"] = ", ".join(_format_address(addr) for addr in message.to)

    if message.cc:
        email_msg["Cc"] = ", ".join(_format_address(addr) for addr in message.cc)

    if message.reply_to:
        email_msg["Reply-To"] = _format_address(message.reply_to)

    email_msg["Subject"] = message.subject or ""

    for key, value in message.headers.items():
        email_msg[key] = value

    if message.text_body:
        email_msg.set_content(message.text_body)

    else:
        email_msg.set_content("")

    if message.html_body:
        email_msg.add_alternative(message.html_body, subtype="html")

    for attachment in message.attachments:
        maintype, _, subtype = attachment.mimetype.partition("/")
        email_msg.add_attachment(
            base64.b64decode(attachment.content),
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=attachment.filename,
        )

    return email_msg


def _send_via_smtp(
    config: SMTPConfig, sender: EmailAddress, message: EmailMessage
) -> None:
    """Blocking SMTP send. Meant to be run in a worker thread."""

    email_msg = _build_email(sender, message)
    all_recipients = [addr.email for addr in message.to + message.cc + message.bcc]

    connection_cls = smtplib.SMTP_SSL if config.use_ssl else smtplib.SMTP
    connection_kwargs = {}

    if config.timeout is not None:
        connection_kwargs["timeout"] = config.timeout

    if config.use_ssl:
        context = ssl.create_default_context()
        connection_kwargs["context"] = context

    with connection_cls(config.host, config.port, **connection_kwargs) as smtp:
        if not config.use_ssl and config.use_tls:
            smtp.starttls(context=ssl.create_default_context())
        if config.username and config.password:
            smtp.login(config.username, config.password)
        smtp.sendmail(sender.email, all_recipients, email_msg.as_bytes())


def _send_all_messages(payload: EmailPayload) -> None:
    """Send all messages in the payload using the provided SMTP configuration and sender."""

    for message in payload.messages:
        if not (message.to or message.cc or message.bcc):
            continue
        try:
            _send_via_smtp(payload.smtp_config, payload.sender, message)
        except Exception:
            logger.exception(
                "Failed to send email with subject=%r to=%r",
                message.subject,
                [addr.email for addr in message.to],
            )


@app.post("/send")
def send_emails(
    payload: EmailPayload,
    authorization: str | None = Header(default=None),
) -> EmailResponse:
    """Send emails using the provided SMTP configuration and email data."""

    if not _verify_authorization(authorization):
        raise HTTPException(status_code=401, detail="Unauthorized request")

    count = sum(
        1 for message in payload.messages if (message.to or message.cc or message.bcc)
    )

    _send_all_messages(payload)

    return EmailResponse(
        message=f"Count {count} email's sent successfully.",
        status="success",
        sent=count,
    )
