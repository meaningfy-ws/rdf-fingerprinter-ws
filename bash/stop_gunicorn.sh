#!/bin/bash
# stop celery
pkill -9 -f celery
# stop ui and api
pkill -f gunicorn