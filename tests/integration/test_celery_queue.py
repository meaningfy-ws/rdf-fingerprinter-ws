import base64
import json
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import redis
from celery import Celery
from celery.contrib.testing.worker import start_worker

from fingerprinter.adapters.celery_queue import CeleryJobQueue

WAIT_SECONDS = 30
DEFAULT_QUEUE = "celery"


@pytest.fixture
def broker(redis_url) -> Iterator[redis.Redis]:
    client = redis.Redis.from_url(redis_url)
    client.delete(DEFAULT_QUEUE)
    yield client
    client.delete(DEFAULT_QUEUE)


def sent_message(broker: redis.Redis) -> tuple[str, str, list]:
    """The one task message waiting in the broker: its task name, task id and positional args."""
    (raw,) = broker.lrange(DEFAULT_QUEUE, 0, -1)
    message = json.loads(raw)
    args, _kwargs, _embed = json.loads(base64.b64decode(message["body"]))
    return message["headers"]["task"], message["headers"]["id"], args


def test_submit_endpoint_sends_the_endpoint_task_under_the_job_id(redis_url, broker):
    CeleryJobQueue(Celery(broker=redis_url)).submit_endpoint(
        "job-e", "http://example.org/sparql", ("g1", "g2")
    )

    assert sent_message(broker) == (
        "fingerprint_endpoint",
        "job-e",
        ["job-e", "http://example.org/sparql", ["g1", "g2"]],
    )


def test_submit_file_sends_the_file_task_under_the_job_id(redis_url, broker):
    CeleryJobQueue(Celery(broker=redis_url)).submit_file("job-f", Path("db/job-f/data.ttl"))

    assert sent_message(broker) == ("fingerprint_file", "job-f", ["job-f", "db/job-f/data.ttl"])


def test_cancel_revokes_the_task(redis_url, broker):
    app = Celery(broker=redis_url)
    with start_worker(app, perform_ping_check=False, shutdown_timeout=30):
        CeleryJobQueue(app).cancel("job-c")

        deadline = time.monotonic() + WAIT_SECONDS
        while time.monotonic() < deadline:
            revoked = app.control.inspect().revoked() or {}
            if any("job-c" in ids for ids in revoked.values()):
                return
            time.sleep(0.5)
    pytest.fail("the worker never saw job-c revoked")


def test_submit_with_the_broker_down_raises():
    app = Celery(broker="redis://localhost:1/0")
    app.conf.task_publish_retry_policy = {"max_retries": 1, "interval_start": 0}
    app.conf.broker_connection_timeout = 1

    with pytest.raises(Exception, match="Connection refused|connect"):
        CeleryJobQueue(app).submit_endpoint("job-x", "http://example.org/sparql", ())
