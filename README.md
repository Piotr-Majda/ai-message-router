# AI Message Router (PoC)

HTTP API that routes employee messages to a department email using a local LLM (Ollama) and sends mail via SMTP. MailHog is used locally to capture messages.

## What it does

- Accept `email` and `message`
- Validate input
- Classify with an agent and pick a department address
- Send email (Reply-To = sender)
- Return `status`, `recipient`, `reply_to`

## Layout

- `app/api/v1` — HTTP routes and dependencies
- `app/services` — orchestration (`EmailRouterService`) and SMTP
- `app/agent` — routing agent (Pydantic AI, structured output to `DepartmentEmail`)
- `app/domain` — routing rules and prompts
- `app/models` — request types
- `app/exceptions` — errors with HTTP status codes

Flow: API → `EmailRouterService` → agent + SMTP.

## Run with Docker

Needs Docker and Docker Compose.

```bash
docker compose up -d --build
```

First start pulls the Ollama model (`llama3.2:3b` by default). This can take a while on CPU.

Another model:

```bash
MODEL_NAME=llama3.2:1b docker compose up -d --build
```

Or set `MODEL_NAME` in `.env`.

- API: http://localhost:8000
- Docs: http://localhost:8000/api/v1/docs
- MailHog: http://localhost:8025
- Ollama: http://localhost:11434

### Environment

| Variable | Default | Notes |
|----------|---------|--------|
| SMTP_HOST | localhost | mailhog in compose |
| SMTP_PORT | 1025 | |
| MODEL_BASE_URL | http://localhost:11434/v1 | ollama service in compose |
| MODEL_NAME | llama3.2:3b | pulled before app starts |
| LOGFIRE_ENABLED | false | |
| LOGFIRE_TOKEN | | needed when Logfire is on |

After editing `.env`:

```bash
docker compose up -d --no-deps --force-recreate app
```

Logfire is optional. Set `LOGFIRE_ENABLED=true` and `LOGFIRE_TOKEN` in `.env` to trace FastAPI, the agent, and httpx calls to Ollama. Useful when checking agent input/output during development. Off by default so compose works without an account.

## API

POST `/api/v1/messages`

```json
{
  "email": "jan.nowak@example.com",
  "message": "Nie działa mi komputer"
}
```

200 response:

```json
{
  "status": "sent",
  "recipient": "it@example.com",
  "reply_to": "jan.nowak@example.com"
}
```

422 — invalid input. 503 — agent failure (`AgentUnavailable`). 500 — SMTP or other server error.

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/messages" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"jan.nowak@example.com\",\"message\":\"Nie działa mi komputer\"}"
```

## Tests

Integration (default, no Docker):

```bash
uv run pytest
```

Smoke (needs running compose + Ollama):

```bash
docker compose up -d --build
uv run pytest -m smoke
```

Optional: `SMOKE_BASE_URL`, `SMOKE_MAILHOG_API`.

## Why it is built this way

Pydantic AI — same stack as the API (FastAPI + Pydantic models). One way to define request types, agent output, and validation.

Structured output — the agent returns a `DepartmentEmail` Pydantic model (`output_type=...`), not free-form text. That keeps the recipient on the allowed list and makes routing results consistent. Pydantic AI may use internal mechanisms (including its own “tools”) to validate structured output against the schema; that is framework internals, not a user-facing “send email” tool. Email is sent by `EmailRouterService` via SMTP after classification.

Logfire — optional tracing for FastAPI and the agent while testing routing behaviour. Disabled by default.

Exceptions with status codes — e.g. `AgentUnavailable` maps to 503 so HTTP status is defined on the error type, not scattered in handlers.

Default model `llama3.2:3b` — smaller and faster to pull and run on CPU than larger models. Routing is a short classification task; bigger models are slower with limited gain here. Prompt rules in `app/domain/constants.py` aim to keep routing accurate without a heavy model. Change `MODEL_NAME` to try others.

Service layer — `EmailRouterService` coordinates agent and email. Dependencies are injected so tests can use fakes without patching the app internals.
