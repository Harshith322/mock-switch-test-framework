"""Traffic generation / performance-style tests.
Stands in for what you'd do with an IXIA traffic generator: send N
frames on a port, then validate counters (tx/rx/errors)."""

import pytest


@pytest.mark.performance
def test_send_traffic_updates_tx_counter(switch):
    switch.enable_port(1)
    sent = switch.send_traffic(1, 1000)
    assert sent == 1000

    counters = switch.port_counters(1)
    assert counters["tx"] == 1000


@pytest.mark.performance
def test_rx_plus_errors_equals_tx(switch):
    switch.enable_port(4)
    switch.send_traffic(4, 5000)

    counters = switch.port_counters(4)
    assert counters["rx"] + counters["errors"] == counters["tx"]


@pytest.mark.performance
def test_error_rate_is_within_expected_bound(switch):
    """Regression-style guard: the simulated link shouldn't drop more
    than ~5% of frames under normal conditions."""
    switch.enable_port(6)
    switch.send_traffic(6, 10000)

    counters = switch.port_counters(6)
    error_rate = counters["errors"] / counters["tx"]
    assert error_rate < 0.05, f"error rate too high: {error_rate:.2%}"


@pytest.mark.performance
def test_traffic_on_disabled_port_fails(switch):
    switch.disable_port(7)
    with pytest.raises(RuntimeError, match="port disabled"):
        switch.send_traffic(7, 100)


@pytest.mark.performance
def test_counters_accumulate_across_sends(switch):
    switch.enable_port(8)
    switch.send_traffic(8, 100)
    switch.send_traffic(8, 200)

    counters = switch.port_counters(8)
    assert counters["tx"] == 300
