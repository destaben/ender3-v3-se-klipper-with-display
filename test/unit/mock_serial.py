# Mock serial interface for testing display communication
#
# This module provides a MockSerial class that records all bytes written
# to it, allowing unit tests to verify the exact byte sequences sent by
# the TJC3224 display driver without requiring real hardware.


class MockSerial:
    """A mock serial port that records all written data.

    Usage:
        serial = MockSerial()
        lcd = TJC3224_LCD(serial)
        lcd.clear_screen()
        assert len(serial.writes) > 0
    """

    def __init__(self):
        self.writes = []
        self._buffer = b""

    def write(self, data):
        """Record data written to the serial port."""
        if isinstance(data, (list, tuple)):
            data = bytes(data)
        elif isinstance(data, int):
            data = bytes([data])
        elif isinstance(data, str):
            data = data.encode("utf-8")
        self.writes.append(bytes(data))
        self._buffer += bytes(data)

    def read(self, size=1):
        """Return empty bytes (no display response in mock mode)."""
        return b""

    def reset(self):
        """Clear all recorded writes."""
        self.writes = []
        self._buffer = b""

    @property
    def all_bytes(self):
        """Return all bytes written as a single bytes object."""
        return self._buffer

    @property
    def write_count(self):
        """Return the number of write() calls made."""
        return len(self.writes)
