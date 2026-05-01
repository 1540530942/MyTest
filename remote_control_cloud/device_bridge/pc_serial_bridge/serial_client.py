from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import serial
from serial import SerialException


@dataclass
class ArduinoConfig:
    port: str
    baudrate: int = 115200
    timeout: float = 2.0
    startup_delay: float = 2.0


class ArduinoSerialClient:
    def __init__(self, config: ArduinoConfig):
        self.config = config
        self._lock = threading.Lock()
        self._serial: serial.Serial | None = None

    def connect(self) -> None:
        if self._serial and self._serial.is_open:
            return

        self._serial = serial.Serial(
            port=self.config.port,
            baudrate=self.config.baudrate,
            timeout=self.config.timeout,
        )
        time.sleep(self.config.startup_delay)
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def disconnect(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def ensure_connection(self) -> None:
        if not self._serial or not self._serial.is_open:
            self.connect()

    def send_command(self, command: str) -> str:
        last_error: Exception | None = None

        with self._lock:
            for attempt in range(2):
                try:
                    self.ensure_connection()
                    assert self._serial is not None
                    self._serial.write((command.strip() + "\n").encode("utf-8"))
                    self._serial.flush()
                    response = self._serial.readline().decode("utf-8", errors="replace").strip()
                    if not response:
                        raise TimeoutError(f"No response from Arduino for command: {command}")
                    return response
                except (OSError, SerialException, TimeoutError) as exc:
                    last_error = exc
                    self.disconnect()
                    if attempt == 0:
                        time.sleep(self.config.startup_delay)

            assert last_error is not None
            raise last_error


def create_client(port: str, baudrate: int = 115200) -> ArduinoSerialClient:
    return ArduinoSerialClient(ArduinoConfig(port=port, baudrate=baudrate))
