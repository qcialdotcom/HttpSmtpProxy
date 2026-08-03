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

Auth header expected on requests:
    Authorization: Bearer <api-key>
    Authorization: <token_type> <api-key>   # token_type is ignored, only the key is checked
"""

import os
import smtplib
import ssl
from email.message import EmailMessage as PyEmailMessage
from email.utils import formataddr

from fastapi import FastAPI, Header, HTTPException

from .schema import EmailAddress, EmailMessage, EmailPayload, SMTPConfig

ALLOWED_API_KEYS = {
    key.strip()
    for key in os.environ.get("ALLOWED_API_KEYS", "").split(",")
    if key.strip()
}

ALLOWED_TOKEN = os.environ.get("ALLOWED_TOKEN").strip()

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

