import pytest

from fingerprinter.config import strtobool


@pytest.mark.parametrize("value", ["1", "true", "True", " yes ", "on", "y", "t"])
def test_true_values(value):
    assert strtobool(value) is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", "n", "f"])
def test_false_values(value):
    assert strtobool(value) is False


def test_an_unknown_value_is_an_error():
    with pytest.raises(ValueError, match="ture"):
        strtobool("ture")
