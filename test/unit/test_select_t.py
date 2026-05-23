# Unit tests for the select_t helper class from e3v3se_display
#
# Tests menu selection state tracking used by the display module.
#
# Note: e3v3se_display.py uses relative imports that require the full
# klippy package context. To test select_t in isolation, we extract it
# by importing the source directly.

import sys
import os
import unittest
import importlib.util

# Load e3v3se_display module source without executing relative imports
# by extracting just the select_t class definition.
_extras_dir = os.path.join(
    os.path.dirname(__file__), '..', '..', 'klippy', 'extras')
_source_path = os.path.join(_extras_dir, 'e3v3se_display.py')

# Read select_t class from source to avoid relative import issues
import re as _re

with open(_source_path) as _f:
    _source = _f.read()

# Extract the select_t class from source to avoid relative import issues.
# This is necessary because e3v3se_display.py uses relative imports that
# require the full klippy package context. select_t is a simple standalone
# class with no external dependencies.
_class_match = _re.search(
    r'^class select_t:.*?(?=\nclass |\Z)', _source, _re.MULTILINE | _re.DOTALL
)
if _class_match:
    # Safe: we are executing a known class definition from our own codebase
    exec(compile(_class_match.group(0), _source_path, 'exec'))  # noqa: S102
else:
    raise ImportError("Could not find select_t class in e3v3se_display.py")


class TestSelectT(unittest.TestCase):
    """Test the select_t menu selection tracker."""

    def test_initial_state(self):
        """Initial values should be 0."""
        s = select_t()
        self.assertEqual(s.now, 0)
        self.assertEqual(s.last, 0)

    def test_set(self):
        """set() should update both now and last."""
        s = select_t()
        s.set(5)
        self.assertEqual(s.now, 5)
        self.assertEqual(s.last, 5)

    def test_reset(self):
        """reset() should set both to 0."""
        s = select_t()
        s.set(3)
        s.reset()
        self.assertEqual(s.now, 0)
        self.assertEqual(s.last, 0)

    def test_changed_when_different(self):
        """changed() should return True when now != last."""
        s = select_t()
        s.now = 3
        s.last = 2
        self.assertTrue(s.changed())

    def test_changed_updates_last(self):
        """changed() should update last to match now."""
        s = select_t()
        s.now = 3
        s.last = 2
        s.changed()
        self.assertEqual(s.last, 3)

    def test_changed_when_same(self):
        """changed() should return None (falsy) when now == last."""
        s = select_t()
        s.set(3)
        result = s.changed()
        self.assertIsNone(result)

    def test_inc_increments(self):
        """inc() should increment now by 1."""
        s = select_t()
        s.set(0)
        # Force last != now so changed() detects it
        s.inc(5)  # max value is 5, so now can go up to 4
        self.assertEqual(s.now, 1)

    def test_inc_clamps_at_max(self):
        """inc() should not exceed max - 1."""
        s = select_t()
        s.set(4)
        s.inc(5)  # max is 5, so max now = 4
        self.assertEqual(s.now, 4)

    def test_dec_decrements(self):
        """dec() should decrement now by 1."""
        s = select_t()
        s.set(3)
        s.dec()
        self.assertEqual(s.now, 2)

    def test_dec_clamps_at_zero(self):
        """dec() should not go below 0."""
        s = select_t()
        s.set(0)
        s.dec()
        self.assertEqual(s.now, 0)

    def test_inc_returns_changed_status(self):
        """inc() should return the result of changed()."""
        s = select_t()
        s.set(0)
        result = s.inc(5)
        # now changed from 0 to 1, so should be truthy
        self.assertTrue(result)

    def test_dec_returns_changed_status(self):
        """dec() should return the result of changed()."""
        s = select_t()
        s.set(3)
        result = s.dec()
        # now changed from 3 to 2, so should be truthy
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
