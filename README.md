# AI Message Router (PoC)

Microservice PoC that receives user messages over HTTP, classifies/routes them (agent planned), and sends an email to a target department via SMTP.

This project is designed to be easy to evolve: small modules, dependency injection, and replaceable adapters (SMTP now, AI Agent later).

## What the API is intended to do
- Accept a user request with:
  - `email`: sender email
  - `message`: free-form text
- Validate the input (basic prompt-injection guard)
- Route the message to a target department email (currently a placeholder, agent-based routing planned)
- Send an email through SMTP (captured by MailHog in local env)
- Set `Reply-To` to the original sender address

## Architecture (high-level)
The code is intentionally modular and dependency-injected to keep it SOLID/KISS and testable.

- **API / Router layer** (`app/api/v1/*`)
  - Owns HTTP concerns: request/response, validation errors, mapping to internal models
  - Delegates side effects through injected dependencies
- **Services layer** (`app/services/*`)
  - Owns application/business behavior and external I/O adapters (e.g. SMTP)
  - Small interfaces (e.g. `EmailService`) make implementations swappable (MailHog/SMTP provider)
- **Models** (`app/models/*`)
  - Typed request and message models (Pydantic)

Design goal: changing SMTP implementation or adding an AI agent should require minimal changes at the edges, without rewriting the endpoint tests.

## Current scope
- **API + MailHog**: implemented and wired in `docker-compose.yaml`.
- **Ollama + AI Agent/tool calling**: planned next step (compose + routing implementation).

## Quick start (Docker Compose)
Prerequisites:
- Docker + Docker Compose

Start services:

```bash
docker compose up -d --build
```

Endpoints:
- API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/api/v1/docs`
- MailHog UI: `http://localhost:8025`

### Environment variables
The API reads SMTP settings from environment variables:
- `smtp_host` (in compose this is `mailhog`)
- `smtp_port` (in compose this is `1025`)
- `smtp_username` (optional)
- `smtp_password` (optional)

## API
### POST `/api/v1/messages`
Accepts a message and sends an email via SMTP.

Request body:

```json
{
  "email": "jan.nowak@example.com",
  "message": "Nie działa mi komputer"
}
```

Success response (200):

```json
{
  "status": "sent",
  "recipient": "it@example.com",
  "reply_to": "jan.nowak@example.com"
}
```

Validation error (422):
- Returned by FastAPI/Pydantic when input is invalid or rejected by the message validator.

Server error (500):
- Returned when the SMTP adapter fails (connection/auth/etc).

### cURL example (copy/paste)

```bash
curl -X POST "http://localhost:8000/api/v1/messages" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"jan.nowak@example.com\",\"message\":\"Nie działa mi komputer\"}"
```

## Tests
This repo intentionally has multiple test layers.

### Integration tests (default)
Run the integration suite (fast, no Docker required):

```bash
uv run pytest
```

These tests focus on:
- router behavior (validation + response contract + error mapping)
- SMTP adapter behavior in isolation (fake SMTP transport)

### Smoke / end-to-end tests (explicit)
Smoke tests verify the running stack (API + MailHog) and are **not executed by default**.

1) Start compose:

```bash
docker compose up -d --build
```

2) Run smoke tests:

```bash
uv run pytest -m smoke
```

Optional overrides:
- `SMOKE_BASE_URL` (default `http://localhost:8000`)
- `SMOKE_MAILHOG_API` (default `http://localhost:8025`)

## Architectural decisions (why)
- **Dependency injection everywhere it matters**: makes it easy to swap adapters (SMTP provider, agent/router implementation) and to test behavior without fragile monkeypatching across the app.
- **Thin routers, focused services**: routers handle HTTP boundaries; services handle the work. This keeps responsibilities clear and prevents “god endpoints”.
- **Typed models and explicit error behavior**: predictable request/response contracts and safer refactors.
