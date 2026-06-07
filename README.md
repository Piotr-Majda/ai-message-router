# AI Message Router (PoC)

HTTP API that routes employee messages to a department email using a local LLM (Ollama) and sends mail via SMTP. MailHog is used locally to capture messages.

## What it does

- Accept `email` and `message`
- Validate input (including basic prompt-injection checks on `message`)
- Route with an AI agent (Ollama) that calls a tool to send exactly one email
- Set Reply-To to the sender from the request
- Return `status`, `recipient`, `reply_to`

## Department addresses

The agent may route to one of:

- `kadry@example.com`
- `human-resources@example.com`
- `help-desk@example.com`
- `it@example.com`
- `other@example.com` (when the request is unclear or unrecognized)

## Layout

- `app/api/v1` — HTTP routes (`messages.py`) and dependencies
- `app/agent` — `EmailAgent`, tool calling, `EmailAgentProtocol`
- `app/services` — SMTP (`EmailService` / `SMTPEmailService`)
- `app/domain` — `Department` enum and agent prompt (`INSTRUCTIONS`)
- `app/models` — request and email types
- `app/exceptions` — errors with HTTP status codes

Flow: API → agent (tool) → SMTP.

The HTTP handler calls `EmailAgentProtocol.route_and_send()` directly. There is no separate application service layer in this PoC.

## Run with Docker

Needs Docker and Docker Compose.

```bash
docker compose up -d --build
```

First start pulls the Ollama model (`llama3.2:3b` by default). This can take a while on CPU.

Another model:

```bash
MODEL_NAME=llama3.1:8b docker compose up -d --build
```

Or set `MODEL_NAME` in `.env`.

- API: http://localhost:8000
- Docs: http://localhost:8000/api/v1/docs
- MailHog: http://localhost:8025
- Ollama: http://localhost:11434

### Environment

| Variable | Default | Notes |
|----------|---------|--------|
| SMTP_HOST | localhost | `mailhog` inside compose |
| SMTP_PORT | 1025 | |
| SMTP_USERNAME | | optional |
| SMTP_PASSWORD | | optional |
| MODEL_BASE_URL | http://localhost:11434/v1 | `http://ollama:11434/v1` in compose |
| MODEL_NAME | llama3.2:3b | pulled by `ollama-pull` before app starts |
| LOGFIRE_ENABLED | false | |
| LOGFIRE_TOKEN | | required when Logfire is on |
| DEBUG | false | logs response bodies when true |

After editing `.env`:

```bash
docker compose up -d --no-deps --force-recreate app
```

Logfire is optional. Set `LOGFIRE_ENABLED=true` and `LOGFIRE_TOKEN` in `.env` to trace FastAPI, the agent, and httpx calls to Ollama. Off by default so compose works without an account.

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

- **422** — invalid input (bad email, rejected message content)
- **503** — agent failure (`AgentUnavailable`, `AgentFailedRouteMessage` when the send tool was not called)
- **500** — SMTP failure (`EmailDeliveryFailed`) or other server error

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

By default pytest excludes smoke tests (`-m "not smoke"` in `pyproject.toml`).

Smoke (needs running compose + Ollama):

```bash
docker compose up -d --build
uv run pytest -m smoke
```

Smoke routing covers all five department addresses with the real agent. Each test run may take up to ~2 minutes on CPU with larger models.

Optional env for smoke:

- `SMOKE_BASE_URL` (default `http://localhost:8000`)
- `SMOKE_MAILHOG_API` (default `http://localhost:8025`)

## Why it is built this way

**Pydantic AI** — same stack as the API (FastAPI + Pydantic). Request types, tool parameters, and validation share one model style.

**Tool calling** — the agent picks a department and sends mail through `send_user_email_to_department`. The recipient is constrained by a `Department` enum in the tool schema. Body, sender, and Reply-To are taken from the HTTP request in tool code, not from the LLM.

**No silent fallback** — if the agent finishes without calling the send tool, the API returns 503 (`AgentFailedRouteMessage`). Routing to `other@example.com` is an agent decision via the tool, not a hidden server-side fallback.

**Logfire** — optional tracing for FastAPI and the agent. Disabled by default.

**Exceptions with status codes** — e.g. `AgentUnavailable` and `AgentFailedRouteMessage` map to 503; `EmailDeliveryFailed` maps to 500.

**Default model `llama3.2:3b`** — small and fast to pull on CPU. For reliable routing in smoke tests, `llama3.1:8b` was used successfully; smaller models may misroute edge cases. Change `MODEL_NAME` to try others.

**Direct API → agent wiring** — keeps the PoC focused on agent behaviour. Dependencies are injected (`EmailAgentProtocol`, `EmailService`) so tests can use fakes without patching app internals.
