# Mock Switch Test Automation Framework

A Python/pytest test automation framework validating a simulated
network switch (Layer 1/Layer 2 behavior: port status, VLAN config,
traffic counters) over a TCP socket protocol. Built as practice for
test-automation-engineer roles involving Python, networking
protocols, and CI/CD.

## Structure

```
mock_device/
  switch_server.py   - simulated switch device (TCP server)
  switch_client.py    - Python client/driver used by tests
tests/
  conftest.py          - fixtures: starts server, resets state, connects client
  test_smoke.py         - basic connectivity sanity checks
  test_port_status.py   - port enable/disable/status
  test_vlan.py           - VLAN set/get
  test_traffic.py         - traffic gen + counter validation
.github/workflows/ci.yml - GitHub Actions pipeline
pytest.ini               - markers + HTML report config
requirements.txt
```

## Run locally

```bash
pip install -r requirements.txt
pytest                 # full suite, generates report.html
pytest -m smoke        # just smoke tests
pytest -m performance  # just traffic/perf tests
```

## Run the mock device standalone

```bash
python -m mock_device.switch_server
```

Then connect with `nc 127.0.0.1 9090` and try commands like `PING`,
`IDN?`, `PORT.STATUS? 1`, `TRAFFIC.SEND 1 100`.

## What this demonstrates

- Python test automation (pytest, fixtures, parametrization, markers)
- Simulated L1/L2 device validation (port state, VLAN, traffic/error counters)
- A traffic-generator-style test (stands in for IXIA)
- CI/CD: GitHub Actions runs the suite on every push, uploads HTML report
- Clean separation of device driver (client) vs test logic
