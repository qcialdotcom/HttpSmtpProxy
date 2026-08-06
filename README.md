# HTTP SMTP Proxy

FastAPI service for sending emails through an SMTP server using a simple HTTP API.

This project receives SMTP settings and email content as JSON, then relays the message through the SMTP server you provide. It is useful when you want to let another service send mail without exposing SMTP credentials directly to that service.

## What It Does

- Accepts requests at `/send` and `/send_async`
- Authenticates requests with an `Authorization` header
- Builds and sends plain text, HTML, and attachment-based emails
- Supports TLS and SSL SMTP connections
- Can run locally, in Docker, or as a Vercel Python function wrapper

## API Overview

### Authentication

Every request must include an `Authorization` header in the form:

```text
Authorization: Bearer your-api-key
```

The token type must match `ALLOWED_TOKEN` and the key must be present in `ALLOWED_API_KEYS`.

### Endpoints

| Method | Path          | Description                                                |
| ------ | ------------- | ---------------------------------------------------------- |
| `POST` | `/send`       | Sends all emails before responding                         |
| `POST` | `/send_async` | Queues the work in the background and responds immediately |

### Request Shape

The request body follows the `EmailPayload` schema:

- `smtp_config`: SMTP host, port, username, password, and connection flags
- `sender`: The sender address used when sending mail
- `messages`: A list of messages to send

Note: the current code uses the top-level `sender` field when sending mail. Keep it populated.

### Example Request

```json
{
  "smtp_config": {
    "host": "smtp.example.com",
    "port": 587,
    "username": "user@example.com",
    "password": "your-password",
    "sender": { "email": "user@example.com", "name": "Example Sender" },
    "use_tls": true,
    "use_ssl": false,
    "timeout": 10
  },
  "sender": { "email": "user@example.com", "name": "Example Sender" },
  "messages": [
    {
      "to": [{ "email": "recipient@example.com", "name": "Recipient" }],
      "subject": "Test message",
      "text_body": "Hello from the SMTP proxy",
      "html_body": "<p>Hello from the SMTP proxy</p>"
    }
  ]
}
```

### Example Response

`/send`

```json
{ "message": "1 email's sent successfully, 0 failed.", "status": "success", "sent": 1 }
```

`/send_async`

```json
{ "message": "Email sending initiated in the background.", "status": "initiated", "queued": 1 }
```

## Environment Variables

Create a `.env` file or set these in your deployment platform:

```env
ALLOWED_API_KEYS=mykey1,mykey2
ALLOWED_TOKEN=Bearer
DEBUG=true
```

- `ALLOWED_API_KEYS`: Comma-separated list of allowed API keys
- `ALLOWED_TOKEN`: The token prefix expected in the `Authorization` header
- `DEBUG`: Set to `true` to enable `/docs`, `/redoc`, and `/openapi.json`

If neither `ALLOWED_API_KEYS` nor `ALLOWED_TOKEN` is set, the app will fail on startup.

## Run Locally

### With `uv`

1. Install dependencies

```bash
uv sync
```

2. Start the API

```bash
DEBUG=true uv run uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

3. Open the docs in your browser

```text
http://127.0.0.1:8000/docs
```

### With Python

If you do not want to use `uv`, install the dependencies from `pyproject.toml` and run:

```bash
DEBUG=true python -m uvicorn app.app:app --reload --host 0.0.0.0 --port 8000
```

## Docker Deployment

### Pull

```bash
docker pull krsahil8825/http-smtp-proxy:latest
```

### Run

Using a `.env` file:

```bash
docker run -d \
  --name http-smtp-proxy \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  krsahil8825/http-smtp-proxy:latest
```

Or pass the environment variables directly:

```bash
docker run -d \
  --name http-smtp-proxy \
  --restart unless-stopped \
  -p 8000:8000 \
  -e ALLOWED_API_KEYS=mykey1,mykey2 \
  -e ALLOWED_TOKEN=Bearer \
  -e DEBUG=false \
  krsahil8825/http-smtp-proxy:latest
```

### Docker Compose

Create a `docker-compose.yml` file:

```yaml
# using .env file
version: "3.9"

services:
  http-smtp-proxy:
    image: krsahil8825/http-smtp-proxy:latest
    container_name: http-smtp-proxy

    restart: unless-stopped

    ports:
      - "8000:8000"

    env_file:
      - .env
```

```yaml
# without .env file
version: "3.9"

services:
  http-smtp-proxy:
    image: krsahil8825/http-smtp-proxy:latest
    container_name: http-smtp-proxy

    restart: unless-stopped

    ports:
      - "8000:8000"

    environment:
      - ALLOWED_API_KEYS=mykey1,mykey2
      - ALLOWED_TOKEN=Bearer
      - DEBUG=false
```

Start the container:

```bash
docker compose up -d
```

Stop the container:

```bash
docker compose down
```

View logs:

```bash
docker compose logs -f
```

## Vercel Direct Code Deployment

Set up a Vercel project and deploy this repository directly.

1. Open the Vercel dashboard and create a new project.

2. Connect your GitHub repository containing this code.

3. Select `FastAPI` as the framework preset.

4. Add build command `pip install uv && uv export --no-hashes > requirements.txt`

5. Dont change the output directory, leave it as `/` or `.`.

6. Install command `pip install -r requirements.txt`

7. Dont change the Deploy command (if available, leave it as default).

8. Add the environment variables `ALLOWED_API_KEYS`, `ALLOWED_TOKEN`, and `DEBUG` in the Vercel project settings.

9. Deploy the project.

## Project Files

- `app/app.py`: FastAPI app and send logic
- `app/schema.py`: Request and response models
- `Dockerfile`: Production container build
- `pyproject.toml`: Python dependencies and project metadata
- `uv.lock`: Locked dependency versions

## Troubleshooting

- If you get `401 Unauthorized`, check the `Authorization` header and the `ALLOWED_API_KEYS` / `ALLOWED_TOKEN` values.
- If the app exits on startup, confirm at least one allowed API key or token setting is present.
- If email sending fails, verify the SMTP host, port, authentication, TLS/SSL mode, and recipient addresses.
- If you want interactive API docs, start the app with `DEBUG=true`. But keep it disabled in production for security reasons.

## License

See [LICENSE](LICENSE) for the full text.
