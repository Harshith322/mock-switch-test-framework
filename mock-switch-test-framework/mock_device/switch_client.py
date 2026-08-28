"""
Thin TCP client for talking to the mock switch server.
Mirrors how a real test framework would wrap an instrument driver
(e.g. an IXIA REST client or a SCPI/VISA instrument) behind a clean
Python API that tests call into.
"""

import socket


class SwitchClient:
    def __init__(self, host="127.0.0.1", port=9090, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock = None
        self._file = None

    def connect(self):
        self._sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self._file = self._sock.makefile("rwb", buffering=0)
        return self

    def close(self):
        try:
            if self._sock:
                self.send("QUIT")
        finally:
            if self._sock:
                self._sock.close()
            self._sock = None
            self._file = None

    def send(self, command: str) -> str:
        if not self._sock:
            raise ConnectionError("not connected - call connect() first")
        self._file.write((command.strip() + "\n").encode("utf-8"))
        line = self._file.readline().decode("utf-8").strip()
        return line

    # --- convenience wrappers over raw protocol commands ---

    def ping(self) -> bool:
        return self.send("PING") == "PONG"

    def identity(self) -> str:
        return self.send("IDN?")

    def reset(self):
        return self.send("RESET")

    def port_status(self, port: int) -> str:
        return self.send(f"PORT.STATUS? {port}")

    def enable_port(self, port: int):
        return self.send(f"PORT.ENABLE {port}")

    def disable_port(self, port: int):
        return self.send(f"PORT.DISABLE {port}")

    def port_counters(self, port: int) -> dict:
        raw = self.send(f"PORT.COUNTERS? {port}")
        if raw.startswith("ERROR"):
            raise RuntimeError(raw)
        result = {}
        for kv in raw.split(","):
            k, v = kv.split("=")
            result[k] = int(v)
        return result

    def set_vlan(self, port: int, vlan_id: int):
        return self.send(f"VLAN.SET {port} {vlan_id}")

    def get_vlan(self, port: int) -> int:
        return int(self.send(f"VLAN.GET? {port}"))

    def send_traffic(self, port: int, frame_count: int) -> int:
        raw = self.send(f"TRAFFIC.SEND {port} {frame_count}")
        if raw.startswith("ERROR"):
            raise RuntimeError(raw)
        return int(raw.split("=")[1])

    # context manager support
    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
