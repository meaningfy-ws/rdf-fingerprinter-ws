# The UI: Flask on gunicorn, a client of the API. Build from the repository root:
#   docker build -f infra/ui/Dockerfile .
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-default-groups --no-install-project

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH
RUN useradd --system --uid 10001 --create-home app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app fingerprinter ./fingerprinter
USER app
CMD ["sh", "-c", "exec gunicorn --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT:-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_UI_WORKERS:-1} --bind 0.0.0.0:${RDF_FINGERPRINTER_UI_PORT:-8020} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL:-info} 'fingerprinter.bootstrap:ui_app()'"]
