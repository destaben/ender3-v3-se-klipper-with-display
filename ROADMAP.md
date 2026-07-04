# Code Review & Improvement Roadmap

This document summarizes the findings from a comprehensive code review of the
Ender 3 V3 SE display support code and proposes a staged improvement plan.

The review focuses on the three main custom files:

- `klippy/extras/e3v3se_display.py` — Main display/menu logic (4533 lines)
- `klippy/extras/printerInterface.py` — Printer data abstraction layer (530 lines)
- `klippy/extras/TJC3224.py` — LCD display driver (663 lines)

---

## 1. Critical Issues (P0)

These issues may cause incorrect behavior or crashes.

### 1.1 Mutable Class-Level Defaults

**Files**: `TJC3224.py`, `printerInterface.py`

Mutable objects (lists, dicts) defined as class variables are shared across all
instances. Mutations on one instance leak to all others.

| File | Variable | Line |
|------|----------|------|
| `TJC3224.py` | `data_frame = []` | 23 |
| `TJC3224.py` | `data_frame_tail = [...]` | 22 |
| `printerInterface.py` | `subdirs = []` | 148 |
| `printerInterface.py` | `fl = []` | 150 |

**Recommended fix**: Move mutable defaults into `__init__()` as instance
variables. Use tuples for truly constant sequences.

### 1.2 Type Mismatch in TJC3224 Data Frame

**File**: `TJC3224.py`

`data_frame` is initialized as a list (`[]`) but all `byte()`/`word()`/`long()`
methods concatenate bytes objects to it. After the first `send()` call,
`data_frame` is reassigned as `bytes`. The initial state should be `b"\xAA"`
(bytes) to match the actual usage.

### 1.3 Unguarded Dictionary Access

**File**: `printerInterface.py`

`printingIsPaused()` (line 351) accesses `self.job_Info["state"]` without
checking whether `job_Info` is `None` or whether the key exists. This can raise
`TypeError` or `KeyError` if called before `update_variable()`.

---

## 2. Important Issues (P1)

### 2.1 Bare `except` Clauses

Bare `except:` catches all exceptions (including `SystemExit`,
`KeyboardInterrupt`) and masks real errors.

| File | Line | Context |
|------|------|---------|
| `e3v3se_display.py` | 76 | `encoder_pins.split(',')` |
| `e3v3se_display.py` | 684 | `is_manual_probe_active()` |
| `printerInterface.py` | 341 | `update_variable()` — 37-line try block |

**Recommended fix**: Catch specific exception types (`ValueError`, `KeyError`,
`AttributeError`) and log unexpected errors.

### 2.2 Busy-Wait Without Timeout

**File**: `TJC3224.py` (line 70)

```python
while not self.handshake():
    pass
```

Currently `handshake()` always returns `True`, so this loop exits immediately.
However, if the display is disconnected or unresponsive the loop will consume
100% CPU with no timeout or sleep.

**Recommended fix**: Add a `time.sleep()` call and a maximum retry count with
logging on failure.

### 2.3 `print()` Statements Instead of Logging

**File**: `TJC3224.py` (lines 69, 72)

Direct `print()` calls bypass Klipper's logging infrastructure and are lost in
production.

**Recommended fix**: Replace with `logging.info()`/`logging.debug()`.

### 2.4 No Error Handling on Serial Writes

**File**: `TJC3224.py` — `send()` method

`self.serial.write()` is called without any error handling. If the serial
connection drops, the error propagates uncontrolled.

---

## 3. Code Quality Issues (P2)

### 3.1 Naming Inconsistencies

The codebase mixes multiple naming conventions:

- **camelCase**: `GetFiles()`, `selectFile()`, `sendGCode()`, `setBedTemp()`
- **snake_case**: `update_variable()`, `handle_ready()`, `key_event()`
- **UPPER_CASE methods**: `MBASE()`, `Clear_Screen()`
- **Mixed**: `HMI_StartFrame()`, `Draw_Print_File_Menu()`

Python convention (PEP 8) calls for `snake_case` for methods and functions.

**Recommendation**: Adopt snake_case for all new methods. Consider gradual
migration of existing methods using deprecation wrappers.

### 3.2 Docstring Mismatch in TJC3224.py

Several docstrings reference incorrect parameter names:

| Method | Docstring param | Actual param |
|--------|----------------|--------------|
| `byte()` | `bval` | `bool_val` |
| `word()` | `wval` | `word_val` |
| `long()` | `lval` | `long_val` |
| `double_64()` | `dval` | `double_val` |

### 3.3 Missing Documentation

- `printerInterface.py`: 0 out of 42 methods have docstrings.
- `e3v3se_display.py`: ~2 out of 142 methods have docstrings.
- No module-level docstrings describing the architecture or data flow.

### 3.4 Dead / Placeholder Code

| File | Line | Code |
|------|------|------|
| `printerInterface.py` | 232 | `postREST()` — logs "called" and does nothing |
| `printerInterface.py` | 405 | `zero_fan_speeds()` — empty `pass` |
| `printerInterface.py` | 518 | `add_mm()` — empty `pass` |
| `e3v3se_display.py` | 990 | Commented-out `HMI_ToggleLanguage()` call |
| `e3v3se_display.py` | 4495 | Commented-out `HMI_FanSpeed()` call |

### 3.5 Duplicate Logic

`getPercent()` and `duration()` in `printerInterface.py` both perform identical
lookups of `virtual_sdcard` status. This should be extracted into a helper.

### 3.6 Redundant Helper Functions

`e3v3se_display.py` defines `_MAX()` and `_MIN()` (lines 14–25) that replicate
Python's built-in `max()` and `min()`.

---

## 4. Enhancement Opportunities

### 4.1 Fan Speed Control

Fan speed display and control is partially implemented but disabled
(`TUNE_CASE_FAN`, `TEMP_CASE_FAN` offsets are set to +0, commented-out
`HMI_FanSpeed`). Completing this would provide a commonly requested feature.

### 4.2 Language Selection

Language constants are defined (`languages` dict with 11 entries) but the
language toggle in the prepare menu is commented out. Implementing multi-language
support would benefit non-English users.

### 4.3 Print Metadata Display

The `scanMetadata()` method parses layer height, estimated time, and filament
usage from G-code files. Consider adding thumbnail preview support for slicers
that embed PNG thumbnails.

### 4.4 Screen Dimming / Power Save

The display dim timeout is implemented (`display_dim_timeout = 300`) but could
be made configurable through `printer.cfg`.

### 4.5 Configurable Material Presets

Material presets are currently hardcoded (`PLA: 200/60`, `ABS: 210/100`). Making
these configurable via `printer.cfg` sections would allow users to customize
without code changes.

---

## 5. Proposed Milestones

### Phase 1: Stability & Correctness (Immediate)

- [ ] Fix mutable class-level defaults (move to `__init__()`)
- [ ] Fix `data_frame` type initialization in `TJC3224.py`
- [ ] Add null checks in `printingIsPaused()` and related methods
- [ ] Replace bare `except:` with specific exception types
- [ ] Add timeout to display handshake loop
- [ ] Replace `print()` with `logging` calls

### Phase 2: Robustness (Short-term)

- [ ] Add error handling around serial write operations
- [ ] Add bounds checking in `selectFile()` and `fileListBack()`
- [ ] Add division-by-zero guard in `remain()`
- [ ] Extract duplicate virtual_sdcard lookup into a helper method
- [ ] Remove dead code (`postREST`, empty `pass` methods) or add TODO markers

### Phase 3: Code Quality (Medium-term)

- [ ] Fix docstring parameter name mismatches in `TJC3224.py`
- [ ] Add docstrings to all public methods in `printerInterface.py`
- [ ] Add module-level docstrings explaining architecture
- [ ] Replace `_MAX()`/`_MIN()` with built-in `max()`/`min()`
- [ ] Standardize on snake_case for new code; add aliases for old names

### Phase 4: Features & Enhancements (Long-term)

- [ ] Complete fan speed control implementation
- [ ] Implement language selection UI
- [ ] Make material presets configurable via `printer.cfg`
- [ ] Make display dim timeout configurable via `printer.cfg`
- [ ] Add thumbnail preview support in print preview screen
- [ ] Investigate adding notification sounds/beeps for print events

---

## 6. Contribution Guidelines

When contributing to the display code:

1. **Follow snake_case** for all new method and variable names.
2. **Add a docstring** to every new public method.
3. **Catch specific exceptions** — never use bare `except:`.
4. **Use `logging`** — never use `print()` for runtime output.
5. **Avoid class-level mutables** — use `__init__()` for lists and dicts.
6. **Test with the physical display** — the LCD protocol has no simulator.

---

## References

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [DWIN T5L Instruction Set (LCD protocol)](https://www.dwin-global.com/uploads/T5L_TA-Instruction-Set-Development-Guide.pdf)
- [Original DWIN_T5UIC1_LCD repository](https://github.com/odwdinc/DWIN_T5UIC1_LCD)
- [E3V3SE Display Klipper project](https://github.com/jpcurti/E3V3SE_display_klipper)
