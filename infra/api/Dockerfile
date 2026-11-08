# The API: Connexion on gunicorn with the uvicorn worker. Build from the repository root:
#   docker build -f infra/api/Dockerfile .
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
RUN mkdir db reports && chown app:app db reports
USER app
CMD ["sh", "-c", "exec gunicorn --worker-class uvicorn_worker.UvicornWorker --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT:-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_API_WORKERS:-2} --bind 0.0.0.0:${RDF_FINGERPRINTER_API_PORT:-4020} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL:-info} 'fingerprinter.bootstrap:api_app()'"]
