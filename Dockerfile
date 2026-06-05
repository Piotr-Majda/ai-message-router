FROM python:3.14-slim AS base

RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 755 /install.sh && /install.sh && rm /install.sh

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY . .

RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

FROM base AS app

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

FROM base AS test

RUN uv sync --group dev

CMD ["uv", "run", "pytest"]