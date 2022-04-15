#!/bin/bash
set -o allexport; source bash/.env; set +o allexport

source env/bin/activate

# run celery
celery -A fingerprinter.adapters.celery.celery_worker worker --loglevel ${RDF_FINGERPRINTER_LOG_LEVEL} --logfile ${RDF_FINGERPRINTER_CELERY_LOGS} --detach

# run api server
gunicorn --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_API_WORKERS-2} --bind 0.0.0.0:${RDF_FINGERPRINTER_API_PORT} --reload --log-file ${RDF_FINGERPRINTER_API_LOGS} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL} fingerprinter.entrypoints.api.run:app --daemon