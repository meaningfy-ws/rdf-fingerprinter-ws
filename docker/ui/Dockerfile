FROM python:3.8.18-bullseye
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

COPY requirements requirements/
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY . .

CMD gunicorn --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_UI_WORKERS-1} --bind 0.0.0.0:${RDF_FINGERPRINTER_UI_PORT} --reload --log-file ${RDF_FINGERPRINTER_UI_LOGS} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL} fingerprinter.entrypoints.ui.run:app