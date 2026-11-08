# Transitional image (stage 1); stage 4 replaces docker/ with multistage non-root images in infra/.
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /usr/src/app

COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-default-groups --no-install-project

COPY . .

CMD gunicorn --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_API_WORKERS-2} --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${RDF_FINGERPRINTER_API_PORT} --log-file ${RDF_FINGERPRINTER_API_LOGS} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL} fingerprinter.entrypoints.api.run:connexion_app
