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
- `app/core` — config and logging
- `app/services` — SMTP (`EmailService` / `SMTPEmailService`)
- `app/domain` — `Department` enum and agent prompt (`INSTRUCTIONS`)
- `app/models` — request and email types
- `app/exceptions` — errors with HTTP status codes
- `tests/routing_cases.py` — shared routing scenarios for smoke and integration tests

Flow: API → agent (tool) → SMTP.

The HTTP handler calls `EmailAgentProtocol.route_and_send()` directly. There is no separate application service layer in this PoC.

## Run with Docker

Needs Docker and Docker Compose.

```bash
docker compose up -d
```

First start builds the app image and pulls the Ollama model (`llama3.1:8b` by default). This can take a while on CPU.

Another model:

```bash
MODEL_NAME=llama3.2:3b docker compose up -d --build
```

Or set `MODEL_NAME` in `.env` (Compose reads `.env` for variable substitution).

- API: http://localhost:8000
- Docs: http://localhost:8000/api/v1/docs
- MailHog: http://localhost:8025
- Ollama: http://localhost:11434

### Environment

| Variable | Default (local `uv run`) | In Docker Compose |
|----------|--------------------------|-------------------|
| SMTP_HOST | localhost | `mailhog` |
| SMTP_PORT | 1025 | 1025 |
| SMTP_USERNAME | (empty) | not set |
| SMTP_PASSWORD | (empty) | not set |
| MODEL_BASE_URL | http://localhost:11434/v1 | http://ollama:11434/v1 |
| MODEL_NAME | llama3.1:8b | llama3.1:8b (override via `.env` or shell) |
| LOGFIRE_ENABLED | false | from `.env` / shell (`${LOGFIRE_ENABLED:-false}`) |
| LOGFIRE_TOKEN | (empty) | from `.env` / shell |
| DEBUG | false | not passed to the app container by default |

After editing `.env`:

- **App-only settings** (e.g. `LOGFIRE_*`): recreate the app service:

  ```bash
  docker compose up -d --no-deps --force-recreate app
  ```

- **`MODEL_NAME` change**: rebuild so `ollama-pull` runs again and the app gets the new value:

  ```bash
  docker compose up -d --build
  ```

Logfire is optional. Set `LOGFIRE_ENABLED=true` and `LOGFIRE_TOKEN` in `.env` to trace FastAPI, Pydantic AI, and httpx calls to Ollama. Disabled by default so compose works without an account.

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
- **500** — SMTP failure (`EmailDeliveryFailed`) or unexpected server error (`Internal server error`)

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/messages" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"jan.nowak@example.com\",\"message\":\"Nie działa mi komputer\"}"
```

## Tests

Shared routing scenarios live in `tests/routing_cases.py` (five cases, one per department). Smoke and integration routing tests import the same data.

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

Smoke runs seven tests: five routing cases (real agent), OpenAPI docs, and MailHog delivery with Reply-To. Routing smoke may take several minutes on CPU with the default model.

Optional env for smoke:

- `SMOKE_BASE_URL` (default `http://localhost:8000`)
- `SMOKE_MAILHOG_API` (default `http://localhost:8025`)

## Why it is built this way

**Pydantic AI** — same stack as the API (FastAPI + Pydantic). Request types, tool parameters, and validation share one model style.

**Tool calling** — the agent picks a department and sends mail through `send_user_email_to_department`. The recipient is constrained by a `Department` enum in the tool schema. Body, sender, and Reply-To are taken from the HTTP request in tool code, not from the LLM.

**No silent fallback** — if the agent finishes without calling the send tool, the API returns 503 (`AgentFailedRouteMessage`). Routing to `other@example.com` is an agent decision via the tool, not a hidden server-side fallback.

**Logfire** — optional tracing for FastAPI, Pydantic AI, and httpx. Disabled by default.

**Exceptions with status codes** — e.g. `AgentUnavailable` and `AgentFailedRouteMessage` map to 503; `EmailDeliveryFailed` maps to 500.

**Direct API → agent wiring** — keeps the PoC focused on agent behaviour. Dependencies are injected (`EmailAgentProtocol`, `EmailService`) so tests can use fakes without patching app internals.

### Default model `llama3.1:8b`

This PoC routes Polish employee messages with **tool calling** (pick department → send email). That requires the model to follow instructions reliably and call the tool with a valid enum value.

During development we compared `llama3.2:3b` and `llama3.1:8b`:

| Model | Observation |
|-------|-------------|
| `llama3.2:3b` | Faster to pull and run, but **unstable** in smoke tests: intermittent 503 (no tool call), wrong department (e.g. IT → `other@`), flaky pass rate on the same cases. |
| `llama3.1:8b` | Slower and heavier on CPU, but **consistent** routing on the five canonical test cases. |

**Decision:** default to **`llama3.1:8b`** for Docker Compose and app config. Reliability matters more than speed for this PoC — a router that sometimes fails or misroutes is worse than one that is slower but predictable.

You can still override with `MODEL_NAME` in `.env` (e.g. `llama3.2:3b` for experiments), but smoke tests assume the 8B default.

**Prompt format:** department inboxes in `INSTRUCTIONS` use enum `.value` (e.g. `kadry@example.com`), not Python enum names, so the model passes valid tool arguments.
