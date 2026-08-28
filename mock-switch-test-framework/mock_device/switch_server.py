"""
Mock Network Switch Server

Simulates a Layer 2 network switch exposed over a TCP socket with a
simple text-based command protocol (loosely SCPI-inspired: command,
optional args, newline-terminated). This stands in for a real device
(e.g. what IXIA / a physical switch would expose) so the test
framework can be developed and CI'd without real hardware.

Supported commands:
    PING                          -> PONG
    IDN?                          -> device identity string
    PORT.STATUS? <port_id>        -> UP | DOWN | ERROR
    PORT.ENABLE <port_id>         -> OK
    PORT.DISABLE <port_id>        -> OK
    PORT.COUNTERS? <port_id>      -> tx=<n>,rx=<n>,errors=<n>
    VLAN.SET <port_id> <vlan_id>  -> OK
    VLAN.GET? <port_id>           -> <vlan_id>
    TRAFFIC.SEND <port_id> <n>    -> sent=<n>   (simulates sending n frames)
    RESET                         -> OK  (resets all state)
    QUIT                          -> closes connection
"""

import socketserver
import threading
import random
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mock-switch")

NUM_PORTS = 8


class SwitchState:
    """Holds the simulated device state. Thread-safe via a lock since
    the socketserver may (in theory) handle concurrent connections."""

    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        with self.lock:
            self.ports = {
                i: {
                    "status": "UP" if i % 4 != 0 else "DOWN",  # a couple down by default
                    "vlan": 1,
                    "tx": 0,
                    "rx": 0,
                    "errors": 0,
                    "enabled": True,
                }
                for i in range(1, NUM_PORTS + 1)
            }


STATE = SwitchState()


class SwitchRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        client = self.client_address
        log.info(f"Client connected: {client}")
        while True:
            raw = self.rfile.readline()
            if not raw:
                break
            line = raw.decode("utf-8").strip()
            if not line:
                continue
            log.info(f"RX from {client}: {line}")
            response = self.dispatch(line)
            log.info(f"TX to {client}: {response}")
            self.wfile.write((response + "\n").encode("utf-8"))
            if line.upper() == "QUIT":
                break
        log.info(f"Client disconnected: {client}")

    def dispatch(self, line: str) -> str:
        parts = line.split()
        cmd = parts[0].upper()
        args = parts[1:]

        try:
            if cmd == "PING":
                return "PONG"

            if cmd == "IDN?":
                return "MockSwitch,Model-8P,FW1.0.0"

            if cmd == "RESET":
                STATE.reset()
                return "OK"

            if cmd == "QUIT":
                return "BYE"

            if cmd == "PORT.STATUS?":
                port = self._require_port(args)
                with STATE.lock:
                    return STATE.ports[port]["status"]

            if cmd == "PORT.ENABLE":
                port = self._require_port(args)
                with STATE.lock:
                    STATE.ports[port]["enabled"] = True
                    STATE.ports[port]["status"] = "UP"
                return "OK"

            if cmd == "PORT.DISABLE":
                port = self._require_port(args)
                with STATE.lock:
                    STATE.ports[port]["enabled"] = False
                    STATE.ports[port]["status"] = "DOWN"
                return "OK"

            if cmd == "PORT.COUNTERS?":
                port = self._require_port(args)
                with STATE.lock:
                    p = STATE.ports[port]
                    return f"tx={p['tx']},rx={p['rx']},errors={p['errors']}"

            if cmd == "VLAN.SET":
                port = self._require_port(args)
                if len(args) < 2:
                    return "ERROR missing vlan_id"
                vlan_id = int(args[1])
                with STATE.lock:
                    STATE.ports[port]["vlan"] = vlan_id
                return "OK"

            if cmd == "VLAN.GET?":
                port = self._require_port(args)
                with STATE.lock:
                    return str(STATE.ports[port]["vlan"])

            if cmd == "TRAFFIC.SEND":
                port = self._require_port(args)
                if len(args) < 2:
                    return "ERROR missing frame_count"
                n = int(args[1])
                with STATE.lock:
                    p = STATE.ports[port]
                    if not p["enabled"]:
                        return "ERROR port disabled"
                    # simulate a small, realistic error rate
                    dropped = sum(1 for _ in range(n) if random.random() < 0.01)
                    p["tx"] += n
                    p["rx"] += n - dropped
                    p["errors"] += dropped
                return f"sent={n}"

            return f"ERROR unknown command '{cmd}'"

        except (KeyError, ValueError) as e:
            return f"ERROR {e}"

    @staticmethod
    def _require_port(args):
        if not args:
            raise ValueError("missing port_id")
        port = int(args[0])
        if port not in STATE.ports:
            raise KeyError(f"invalid port_id {port}")
        return port


class SwitchServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_server(host="127.0.0.1", port=9090):
    server = SwitchServer((host, port), SwitchRequestHandler)
    log.info(f"Mock switch listening on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
