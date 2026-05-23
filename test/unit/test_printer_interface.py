# Unit tests for printer interface data structures
#
# Tests the helper classes used by the display module for managing state.

import sys
import os
import unittest

# Add the klippy extras path so we can import the modules under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'klippy', 'extras'))

from printerInterface import (
    xyze_t, AxisEnum, HMI_value_t, HMI_Flag_t, material_preset_t
)


class TestXyzeT(unittest.TestCase):
    """Test the xyze_t position tracking class."""

    def test_initial_values(self):
        """All axes should start at 0."""
        pos = xyze_t()
        self.assertEqual(pos.x, 0.0)
        self.assertEqual(pos.y, 0.0)
        self.assertEqual(pos.z, 0.0)
        self.assertEqual(pos.e, 0.0)

    def test_initial_homing_state(self):
        """All axes should start as not homed."""
        pos = xyze_t()
        self.assertFalse(pos.home_x)
        self.assertFalse(pos.home_y)
        self.assertFalse(pos.home_z)

    def test_homing_resets_home_flags(self):
        """homing() should reset all home flags to False."""
        pos = xyze_t()
        pos.home_x = True
        pos.home_y = True
        pos.home_z = True
        pos.homing()
        self.assertFalse(pos.home_x)
        self.assertFalse(pos.home_y)
        self.assertFalse(pos.home_z)

    def test_position_assignment(self):
        """Should be able to set position values."""
        pos = xyze_t()
        pos.x = 10.5
        pos.y = 20.3
        pos.z = 5.0
        pos.e = 100.0
        self.assertEqual(pos.x, 10.5)
        self.assertEqual(pos.y, 20.3)
        self.assertEqual(pos.z, 5.0)
        self.assertEqual(pos.e, 100.0)


class TestAxisEnum(unittest.TestCase):
    """Test AxisEnum constants."""

    def test_axis_values(self):
        """Axis enum values should match expected constants."""
        self.assertEqual(AxisEnum.X_AXIS, 0)
        self.assertEqual(AxisEnum.Y_AXIS, 1)
        self.assertEqual(AxisEnum.Z_AXIS, 2)
        self.assertEqual(AxisEnum.E_AXIS, 3)

    def test_all_axes(self):
        """ALL_AXES should be 0xFE."""
        self.assertEqual(AxisEnum.ALL_AXES, 0xFE)

    def test_no_axis(self):
        """NO_AXIS should be 0xFF."""
        self.assertEqual(AxisEnum.NO_AXIS, 0xFF)


class TestHMIValueT(unittest.TestCase):
    """Test HMI_value_t defaults."""

    def test_initial_print_speed(self):
        """Default print speed should be 100."""
        hmi = HMI_value_t()
        self.assertEqual(hmi.print_speed, 100)

    def test_initial_temperatures(self):
        """Default temperatures should be 0."""
        hmi = HMI_value_t()
        self.assertEqual(hmi.E_Temp, 0)
        self.assertEqual(hmi.Bed_Temp, 0)


class TestHMIFlagT(unittest.TestCase):
    """Test HMI_Flag_t defaults."""

    def test_initial_flags(self):
        """All flags should start as False."""
        flags = HMI_Flag_t()
        self.assertFalse(flags.pause_flag)
        self.assertFalse(flags.pause_action)
        self.assertFalse(flags.print_finish)
        self.assertFalse(flags.heat_flag)


class TestMaterialPresetT(unittest.TestCase):
    """Test material_preset_t."""

    def test_pla_preset(self):
        """PLA preset should have correct temperatures."""
        preset = material_preset_t("PLA", 200, 60)
        self.assertEqual(preset.name, "PLA")
        self.assertEqual(preset.hotend_temp, 200)
        self.assertEqual(preset.bed_temp, 60)
        self.assertEqual(preset.fan_speed, 100)

    def test_custom_fan_speed(self):
        """Should accept custom fan speed."""
        preset = material_preset_t("PETG", 230, 80, 50)
        self.assertEqual(preset.fan_speed, 50)


if __name__ == '__main__':
    unittest.main()
