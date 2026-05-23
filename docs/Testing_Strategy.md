# Test Strategy: Visual and Emulated Printer Testing

This document describes the test strategy for the Ender 3 V3 SE Klipper with
Display project. The goal is to enable contributors to test changes without
requiring physical printer hardware.

## Overview

Testing is organized into three layers:

1. **Unit tests** — validate individual Python modules (display logic,
   printer interface, serial protocol) in isolation using mock objects.
2. **Integration tests** — run Klipper's klippy host software against
   emulated MCU dictionaries (existing `test/klippy/*.test` infrastructure).
3. **Visual/manual tests** — use Klipper's simulavr-based emulation or
   virtual serial ports to observe display behavior.

## 1. Unit Tests (No Hardware Needed)

Unit tests live in `test/unit/` and can be run with Python's built-in
`unittest` module. They exercise:

- **TJC3224 LCD protocol** (`klippy/extras/TJC3224.py`): Verify that
  display commands produce the correct byte sequences using a mock serial
  object.
- **Printer data structures** (`klippy/extras/printerInterface.py`): Test
  helper classes (`select_t`, `xyze_t`, `HMI_value_t`, etc.) for correct
  behavior.
- **Display state machine** (`klippy/extras/e3v3se_display.py`): Test
  menu navigation logic and encoder handling with simulated inputs.

### Running Unit Tests

```bash
# From the repository root:
python -m pytest test/unit/ -v

# Or with unittest directly:
python -m unittest discover -s test/unit -v
```

### Writing New Unit Tests

- Place test files in `test/unit/` with the naming convention
  `test_<module_name>.py`.
- Use `unittest.mock` to create mock objects for hardware-dependent
  interfaces (serial ports, MCU pins, printer objects).
- Each test should be deterministic and run in under 1 second.

## 1b. Visual Tests (Rendered Display Screenshots)

Visual tests use the `Pillow` library to render display screens to PNG
images and animated GIFs. These provide visual verification of the
display layout without requiring physical hardware.

Visual test outputs are:
- Saved to `test/unit/visual_output/` (gitignored)
- Uploaded as CI artifacts on every push/PR
- Include screenshots of main menu, print progress, temperature screens
- Include animated GIFs demonstrating menu navigation
- Include protocol frame diagrams

### Running Visual Tests

```bash
# Install Pillow (required for visual tests)
pip install Pillow

# Run visual tests
python -m unittest test.unit.test_visual_display -v

# Screenshots will be saved to test/unit/visual_output/
```

### CI Integration

The `.github/workflows/unit-tests.yaml` workflow automatically:
1. Runs all unit tests (no dependencies needed)
2. Runs visual tests (installs Pillow)
3. Uploads rendered screenshots and GIFs as downloadable artifacts
4. Provides a summary of generated visual outputs

## 2. Integration Tests (Existing Infrastructure)

The existing Klipper test infrastructure (`scripts/test_klippy.py`) runs
gcode through klippy using pre-compiled MCU dictionaries. These tests
validate that the host software correctly processes commands.

### Running Integration Tests

```bash
# Requires compiled dictionaries in ci_build/dict/
python scripts/test_klippy.py -d ci_build/dict test/klippy/*.test
```

### Adding Display-Related Integration Tests

To test the e3v3se_display module in an integration context:

1. Create a config file referencing the display module with a mock serial
   setup.
2. Create a `.test` file with gcode commands that exercise display state
   transitions.

## 3. Visual Testing with Emulation

### Using simulavr

The `scripts/avrsim.py` tool allows running compiled firmware in an
emulated AVR environment. See `docs/Debugging.md` for full instructions.

```bash
# Build firmware for simulavr
make menuconfig  # Select SIMULAVR software emulation support
make

# Run the simulator
PYTHONPATH=/path/to/simulavr/build/pysimulavr/ ./scripts/avrsim.py out/klipper.elf

# In another terminal, run klippy with test gcode
python klippy/klippy.py config/generic-simulavr.cfg -i test.gcode -v
```

### Using Virtual Serial Ports

For testing display communication without hardware, create a virtual
serial port pair:

```bash
# Create a virtual serial port pair
socat -d -d pty,raw,echo=0 pty,raw,echo=0

# This outputs two PTY devices (e.g., /dev/pts/3 and /dev/pts/4)
# Use one end for klippy and the other for a display emulator script.
```

### Mock Display Emulator

The `test/unit/mock_serial.py` module provides a `MockSerial` class that
records all bytes sent to the display. This can be used to:

- Verify the exact byte sequences sent during a display operation.
- Replay captured display sessions for regression testing.
- Build a visual display emulator that renders commands to an image or
  terminal output.

## 4. Guidelines for Contributors

### Before Submitting a PR

1. Run unit tests: `python -m pytest test/unit/ -v`
2. Run the klippy import test: `python klippy/klippy.py --import-test`
3. If modifying display logic, add or update unit tests covering the change.
4. If modifying gcode handling, add or update integration tests in
   `test/klippy/`.

### Testing Without Hardware — Quick Reference

| What to test              | Method                              | Location              |
| ------------------------- | ----------------------------------- | --------------------- |
| Display byte protocol     | Unit test with MockSerial           | `test/unit/`          |
| Menu navigation logic     | Unit test with mock encoder inputs  | `test/unit/`          |
| Printer data structures   | Unit test                           | `test/unit/`          |
| Gcode command processing  | Integration test via test_klippy.py | `test/klippy/`        |
| Full firmware behavior    | simulavr emulation                  | `scripts/avrsim.py`   |
| Display serial protocol   | Virtual serial port + socat         | Manual                |

### Useful Tools

- **pytest** — test runner for unit tests
- **unittest.mock** — mock hardware interfaces
- **socat** — create virtual serial port pairs
- **simulavr** — AVR microcontroller emulator
- **gtkwave** — view signal traces from simulavr

## 5. Future Improvements

- Add a CI job that runs unit tests on every push/PR.
- Create a display rendering emulator that produces PNG screenshots of
  the display state for visual regression testing.
- Add property-based testing for encoder input sequences.
- Record and replay real display sessions for golden-file testing.
