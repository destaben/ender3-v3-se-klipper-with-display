# Unit tests for TJC3224 LCD display driver
#
# Tests the display protocol byte generation using a mock serial interface.

import sys
import os
import unittest

# Add the klippy extras path so we can import the modules under test
_extras_path = os.path.join(
    os.path.dirname(__file__), '..', '..', 'klippy', 'extras')
sys.path.insert(0, _extras_path)
sys.path.insert(0, os.path.dirname(__file__))

from mock_serial import MockSerial
from TJC3224 import TJC3224_LCD


class TestTJC3224Init(unittest.TestCase):
    """Test TJC3224 LCD initialization."""

    def setUp(self):
        self.serial = MockSerial()
        self.lcd = TJC3224_LCD(self.serial)

    def test_data_frame_head(self):
        """Data frame head should be 0xAA."""
        self.assertEqual(self.lcd.data_frame_head, b"\xAA")

    def test_data_frame_tail(self):
        """Data frame tail should be [0xCC, 0x33, 0xC3, 0x3C]."""
        self.assertEqual(self.lcd.data_frame_tail, [0xCC, 0x33, 0xC3, 0x3C])

    def test_screen_dimensions(self):
        """Screen should be 240x320."""
        self.assertEqual(self.lcd.screen_width, 240)
        self.assertEqual(self.lcd.screen_height, 320)


class TestTJC3224DataFrame(unittest.TestCase):
    """Test data frame byte building methods."""

    def setUp(self):
        self.serial = MockSerial()
        self.lcd = TJC3224_LCD(self.serial)
        # Reset data_frame to head for each test
        self.lcd.data_frame = self.lcd.data_frame_head

    def test_byte_appends_single_byte(self):
        """byte() should append a single byte to the data frame."""
        self.lcd.byte(0x52)
        # data_frame_head (0xAA) + 0x52
        self.assertEqual(self.lcd.data_frame, b"\xAA\x52")

    def test_word_appends_two_bytes_big_endian(self):
        """word() should append a two-byte big-endian value."""
        self.lcd.word(0x1234)
        self.assertEqual(self.lcd.data_frame, b"\xAA\x12\x34")

    def test_long_appends_four_bytes_big_endian(self):
        """long() should append a four-byte big-endian value."""
        self.lcd.long(0x12345678)
        self.assertEqual(self.lcd.data_frame, b"\xAA\x12\x34\x56\x78")

    def test_string_appends_utf8(self):
        """string() should append UTF-8 encoded bytes."""
        self.lcd.string("Hi")
        self.assertEqual(self.lcd.data_frame, b"\xAAHi")


class TestTJC3224Send(unittest.TestCase):
    """Test that send() writes frame + tail to serial."""

    def setUp(self):
        self.serial = MockSerial()
        self.lcd = TJC3224_LCD(self.serial)
        self.lcd.data_frame = self.lcd.data_frame_head

    def test_send_writes_frame_and_tail(self):
        """send() should write the data frame then the tail bytes."""
        self.lcd.byte(0x00)  # handshake command
        self.lcd.send()
        # First write: data_frame (head + 0x00)
        self.assertEqual(self.serial.writes[0], b"\xAA\x00")
        # Second write: tail
        self.assertEqual(
            self.serial.writes[1], bytes([0xCC, 0x33, 0xC3, 0x3C]))

    def test_send_resets_data_frame(self):
        """After send(), data_frame should be reset to head."""
        self.lcd.byte(0x00)
        self.lcd.send()
        self.assertEqual(self.lcd.data_frame, self.lcd.data_frame_head)


class TestTJC3224Commands(unittest.TestCase):
    """Test high-level display commands."""

    def setUp(self):
        self.serial = MockSerial()
        self.lcd = TJC3224_LCD(self.serial)
        self.lcd.data_frame = self.lcd.data_frame_head

    def test_handshake(self):
        """handshake() should send a 0x00 command byte."""
        result = self.lcd.handshake()
        self.assertTrue(result)
        # Should have written at least one frame with 0x00
        self.assertIn(b"\x00", self.serial.all_bytes)

    def test_set_backlight_brightness(self):
        """set_backlight_brightness() should send brightness command."""
        self.lcd.set_backlight_brightness(0x20)
        # Command byte is 0x5F followed by clamped brightness
        self.assertIn(bytes([0x5F, 0x20]), self.serial.all_bytes)

    def test_set_backlight_brightness_clamps_max(self):
        """Brightness should be clamped to 0x40 maximum."""
        self.lcd.set_backlight_brightness(0xFF)
        self.assertIn(bytes([0x5F, 0x40]), self.serial.all_bytes)

    def test_clear_screen(self):
        """clear_screen() should send palette + clear command."""
        self.lcd.clear_screen(0x0000)
        # Should contain the clear screen command byte (0x52)
        self.assertIn(bytes([0x52]), self.serial.all_bytes)

    def test_draw_line(self):
        """draw_line() should send line command with coordinates."""
        self.lcd.draw_line(0xFFFF, 10, 20, 100, 200)
        # Should contain the draw line command (0x51)
        self.assertIn(bytes([0x51]), self.serial.all_bytes)


if __name__ == '__main__':
    unittest.main()
