import socket
import threading
import time

import pytest

from mock_device.switch_server import SwitchServer, SwitchRequestHandler, STATE
from mock_device.switch_client import SwitchClient

TEST_HOST = "127.0.0.1"
TEST_PORT = 9191


def _free_port_check(host, port, retries=20, delay=0.1):
    """Wait until the server is actually accepting connections."""
    for _ in range(retries):
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(delay)
    return False


@pytest.fixture(scope="session")
def switch_server():
    """Starts one mock switch server for the whole test session in a
    background thread, and tears it down at the end."""
    server = SwitchServer((TEST_HOST, TEST_PORT), SwitchRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    if not _free_port_check(TEST_HOST, TEST_PORT):
        server.shutdown()
        pytest.fail("mock switch server did not start in time")

    yield server

    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def reset_switch_state(switch_server):
    """Ensures every test starts from a clean device state."""
    STATE.reset()
    yield


@pytest.fixture
def switch(switch_server):
    """A connected SwitchClient, ready to use in a test."""
    client = SwitchClient(host=TEST_HOST, port=TEST_PORT)
    client.connect()
    yield client
    client.close()
