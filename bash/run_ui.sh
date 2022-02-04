#!/bin/bash
set -o allexport; source bash/.env; set +o allexport

source env/bin/activate

# run ui server
gunicorn --timeout ${RDF_FINGERPRINTER_GUNICORN_TIMEOUT-1200} --workers ${RDF_FINGERPRINTER_GUNICORN_UI_WORKERS-1} --bind 0.0.0.0:${RDF_FINGERPRINTER_UI_PORT} --reload --log-file ${RDF_FINGERPRINTER_UI_LOGS} --log-level ${RDF_FINGERPRINTER_LOG_LEVEL} fingerprinter.entrypoints.ui.run:app --daemon