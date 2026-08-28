"""Functional tests for port state - enable/disable/status.
Analogous to L1 link-state validation on a real switch."""

import pytest

ALL_PORTS = range(1, 9)


@pytest.mark.functional
@pytest.mark.parametrize("port", ALL_PORTS)
def test_port_status_is_valid_value(switch, port):
    status = switch.port_status(port)
    assert status in ("UP", "DOWN", "ERROR")


@pytest.mark.functional
def test_enable_port_brings_it_up(switch):
    switch.disable_port(3)
    assert switch.port_status(3) == "DOWN"

    switch.enable_port(3)
    assert switch.port_status(3) == "UP"


@pytest.mark.functional
def test_disable_port_takes_it_down(switch):
    switch.enable_port(2)
    assert switch.port_status(2) == "UP"

    switch.disable_port(2)
    assert switch.port_status(2) == "DOWN"


@pytest.mark.functional
def test_invalid_port_returns_error(switch):
    response = switch.send("PORT.STATUS? 999")
    assert response.startswith("ERROR")


@pytest.mark.functional
def test_missing_port_arg_returns_error(switch):
    response = switch.send("PORT.STATUS?")
    assert response.startswith("ERROR")
