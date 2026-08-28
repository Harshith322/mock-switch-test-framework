"""Basic connectivity / sanity checks - the kind you'd run first
against any device before functional testing."""

import pytest


@pytest.mark.smoke
def test_ping(switch):
    assert switch.ping() is True


@pytest.mark.smoke
def test_identity_string(switch):
    idn = switch.identity()
    assert "MockSwitch" in idn


@pytest.mark.smoke
def test_reset_returns_ok(switch):
    assert switch.reset() == "OK"
