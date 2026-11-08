# One Dockerfile, three images: `--target api`, `--target ui`, `--target worker` (Flower runs on the
# worker image). Build from the repository root, plain `docker build` (no BuildKit features needed):
#   docker build --target api -f infra/docker/Dockerfile .
FROM python:3.13-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-default-groups --no-install-project

# Shared by the three images. The code is owned by root; only db/ and reports/ are writable by `app`.
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH
RUN useradd --system --uid 10001 --create-home app
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY fingerprinter ./fingerprinter
RUN mkdir db reports && chown app:app db reports
USER app

# The API: Connexion on gunicorn with the uvicorn worker.
FROM base AS api
CMD ["sh", "-c", "exec gunicorn --worker-class uvicorn_worker.UvicornWorker --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT:-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_API_WORKERS:-2} --bind 0.0.0.0:${RDF_FINGERPRINTER_API_PORT:-4020} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL:-info} 'fingerprinter.bootstrap:api_app()'"]

# The UI: Flask on gunicorn, a client of the API.
FROM base AS ui
CMD ["sh", "-c", "exec gunicorn --worker-class gthread --threads ${RDF_FINGERPRINTER_GUNICORN_UI_THREADS:-8} --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT:-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_UI_WORKERS:-1} --bind 0.0.0.0:${RDF_FINGERPRINTER_UI_PORT:-8020} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL:-info} 'fingerprinter.bootstrap:ui_app()'"]

# The Celery worker (also runs Flower).
FROM base AS worker
CMD ["sh", "-c", "exec celery -A fingerprinter.bootstrap:celery_app worker --loglevel ${RDF_FINGERPRINTER_LOG_LEVEL:-info}"]
