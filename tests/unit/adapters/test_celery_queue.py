"""The queue adapter turns broker failures, and only those, into ``QueueUnavailable`` (R2-4)."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from kombu.exceptions import OperationalError

from fingerprinter.adapters.celery_queue import CeleryJobQueue
from fingerprinter.domain.exceptions import QueueUnavailable

BROKER_ERRORS = [OperationalError("broker down"), ConnectionRefusedError("refused"), OSError("io")]


def submit(queue: CeleryJobQueue, kind: str) -> None:
    if kind == "endpoint":
        queue.submit_endpoint("j1", "http://e/sparql", ())
    else:
        queue.submit_file("j1", Path("db/j1/a.ttl"))


@pytest.mark.parametrize("kind", ["endpoint", "file"])
@pytest.mark.parametrize("error", BROKER_ERRORS, ids=type)
def test_a_broker_error_is_queue_unavailable(kind, error):
    app = Mock()
    app.send_task.side_effect = error

    with pytest.raises(QueueUnavailable):
        submit(CeleryJobQueue(app), kind)


@pytest.mark.parametrize("kind", ["endpoint", "file"])
def test_any_other_error_propagates_as_the_bug_it_is(kind):
    app = Mock()
    app.send_task.side_effect = TypeError("bad argument")

    with pytest.raises(TypeError):
        submit(CeleryJobQueue(app), kind)
