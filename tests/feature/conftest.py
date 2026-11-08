import pytest
from pytest_bdd import parsers, then

from tests.feature.world import World


@pytest.fixture
def world() -> World:
    return World()


@then(parsers.parse("the service answers {status:d} with a problem response"))
def answers_with_a_problem(world, status):
    assert world.status == status
    assert world.problem is not None
