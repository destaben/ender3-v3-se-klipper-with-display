# AI Documentation: Ender 3 V3 SE Klipper with Display Support

> This document provides structured context for AI agents, contributors, and automation tools to quickly understand and work with this repository.

---

## 1. Project Purpose and High-Level Summary

This repository is a **modified fork of [Klipper](https://www.klipper3d.org/)** firmware, specifically tailored for the **Creality Ender 3 V3 SE** 3D printer. Its primary innovation is **native display support** — enabling the stock Creality DWIN display to work with Klipper without any hardware modifications.

**Key innovation:** Combines [E4ST2W3ST's serial bridge](https://github.com/Klipper3d/klipper/commit/6469418d73be6743a7130b50fdb5a57d311435ca) (MCU acts as USB-to-display serial bridge) with [jpcurti's display interface](https://github.com/jpcurti/E3V3SE_display_klipper) to communicate with the stock display over the existing ribbon cable.

**Upstream lineage:** Forked from [0xD34D's Klipper config](https://github.com/0xD34D/klipper_ender3_v3_se), which itself is a Klipper fork.

---

## 2. Key Components

### Hardware

| Component | Details |
|-----------|---------|
| Printer | Creality Ender 3 V3 SE |
| MCU | STM32F103 (28KiB bootloader offset) |
| Display | DWIN TJC3224 (stock Creality display) |
| Communication | USART1 (host serial), USART2 (serial bridge to display) |
| Host | Raspberry Pi 4/5 or comparable Linux device |
| Display firmware | **Must be version 1.0.6** |

### Software / Firmware Stack

| Layer | Technology | Location |
|-------|-----------|----------|
| MCU firmware | C (Klipper MCU code + serial bridge) | `src/` |
| Host-side Klipper | Python (klippy) | `klippy/` |
| Display driver | Python (e3v3se_display extra) | `klippy/extras/e3v3se_display.py` |
| Display protocol | TJC3224 LCD communication | `klippy/extras/TJC3224/` |
| Printer interface | Python abstraction | `klippy/extras/printerInterface.py` |
| Serial bridge (MCU) | C | `src/serial_bridge.c` |
| Serial bridge (host) | Python | `klippy/extras/serial_bridge.py` |
| Build system | Make + Kconfig | `Makefile`, `src/Kconfig` |
| CI/CD | GitHub Actions | `.github/workflows/` |

### Configuration

- **printer.cfg section:** `[e3v3se_display]` enables the display with optional `language` and `logging` parameters.
- **Custom macros:** Defined via `[e3v3se_display MACRO%I]` sections with `gcode`, `label`, and optional `icon` properties.
- **Klipper config files** for the Ender 3 V3 SE are sourced from [0xD34D's config repo](https://github.com/0xD34D/ender3-v3-se-klipper-config).

---

## 3. Repository Structure

```
├── AI_DOC.md                  # This file — AI context documentation
├── README.md                  # Primary project README
├── Makefile                   # Build system entry point
├── COPYING                    # License (GPLv3)
├── config/                    # Klipper printer configuration examples
├── docs/                      # Upstream Klipper documentation
├── e3v3se_docs/               # Ender 3 V3 SE specific documentation (Docsify site)
│   ├── install.md             # Step-by-step installation guide
│   ├── configuration.md       # Configuration guide
│   ├── calibration.md         # Calibration instructions
│   ├── troubleshooting.md     # Common issues and fixes
│   └── images/                # Screenshots and demos
├── klippy/                    # Python host-side Klipper code
│   ├── extras/                # Klipper extras/plugins
│   │   ├── e3v3se_display.py  # Main display driver (the core custom code)
│   │   ├── TJC3224/           # Display communication protocol
│   │   ├── printerInterface.py# Printer data abstraction
│   │   ├── serial_bridge.py   # Host-side serial bridge handling
│   │   └── display/           # Display menu and UI logic
│   └── ...                    # Standard Klipper host modules
├── src/                       # C firmware source code
│   ├── serial_bridge.c        # MCU serial bridge implementation
│   ├── stm32/                 # STM32-specific MCU code
│   └── ...                    # Standard Klipper MCU modules
├── lib/                       # External libraries
├── scripts/                   # Build/utility scripts
├── test/                      # Test suite
└── ci_build/                  # CI build configurations
```

---

## 4. Usage Scenarios and Common Workflows

### End-User Workflows

1. **Flash pre-built firmware:** Download `.bin` from [Releases](https://github.com/jpcurti/ender3-v3-se-klipper-with-display/releases), rename, copy to SD card, power-cycle printer.
2. **Build from source:** `git clone` → `make menuconfig` (enable serial bridge on USART2) → `make` → flash `klipper.bin`.
3. **Configure display:** Add `[e3v3se_display]` to `printer.cfg` with language/logging preferences.
4. **Add custom macros:** Define `[e3v3se_display MACRO1]` sections in `printer.cfg` for screen-accessible macros.
5. **Install via KIAUH:** Add this repo to `klipper_repos.txt`, switch repo in KIAUH settings, install Klipper.

### Developer Workflows

1. **Modify display behavior:** Edit `klippy/extras/e3v3se_display.py` and related display modules.
2. **Change serial bridge:** Edit `src/serial_bridge.c` (MCU side) and `klippy/extras/serial_bridge.py` (host side).
3. **Add display features:** Work with `klippy/extras/TJC3224/` for protocol-level changes.
4. **CI builds:** GitHub Actions automatically builds firmware on push (see `.github/workflows/build-firmware.yaml`).
5. **Testing:** `test/` directory contains Klipper's test infrastructure.

---

## 5. Special Considerations

### Display Firmware Compatibility

- **Critical:** The display firmware **must be version 1.0.6**. Newer Creality display firmware versions will have different asset memory layouts and require re-mapping.
- To verify your display firmware version, check the display's startup screen or the Creality printer info menu before flashing Klipper.
- Display firmware 1.0.6 can be downloaded from the [Creality downloads page](https://www.creality.com/pages/download-ender-3-v3-se). Instructions for updating are available on [YouTube](https://www.youtube.com/watch?v=8oRuCusCyUM&ab_channel=CrealityAfter-sale).
- Display communication uses the TJC3224 protocol (similar to Nextion/DWIN).
- Icons are stored at fixed memory addresses in the display firmware.

### Serial Bridge Architecture

- The STM32 MCU acts as a **serial bridge** between the USB host connection (USART1) and the display (USART2).
- This is a hardware-level feature compiled into the MCU firmware — it cannot be enabled via software config alone.
- The `make menuconfig` step must explicitly enable "serial bridge" on USART2.

### Klipper Integration

- The display module registers as a Klipper "extra" (`klippy/extras/`).
- It interacts with the Klipper printer object model via `PrinterData` abstraction.
- Menu navigation and screen state are managed in Python, not on the display MCU.

### Build Requirements

- Cross-compiler for ARM (arm-none-eabi-gcc) for MCU firmware.
- Python 3 for klippy host code.
- Standard Klipper build dependencies.

---

## 6. Existing Documentation and Gaps

### Available Documentation

| Document | Location | Content |
|----------|----------|---------|
| Main README | `README.md` | Installation, features, macros, FAQ |
| E3V3SE docs (Docsify) | `e3v3se_docs/` | Install guide, configuration, troubleshooting |
| Upstream Klipper docs | `docs/` | Full Klipper documentation |
| This AI doc | `AI_DOC.md` | AI/agent context |

### Identified Gaps

- **No API/code documentation** for the display driver Python modules.
- **No architecture diagram** showing the serial bridge data flow.
- **No contribution guide** specific to this fork (only upstream Klipper's).
- **No changelog** tracking display-specific features per release.
- **Missing instructions** for copying firmware to SD card for Linux beginners (noted as TODO in `e3v3se_docs/install.md`).
- **No automated testing** for the display driver code specifically.

### Recommendations

1. Add docstrings to `e3v3se_display.py` and related modules.
2. Create an architecture diagram showing: Host ↔ USB ↔ MCU (USART1) ↔ Serial Bridge ↔ USART2 ↔ Display.
3. Document the TJC3224 protocol commands used.
4. Add a CONTRIBUTING.md for this fork's specific workflow.

---

## 7. Best Practices for Extending and Automating

### Adding New Display Features

1. Identify the display page/asset addresses using the icon finder macro (`ENDER_SE_DISPLAY_ICON_FINDER` — run via the Klipper console, e.g., in Mainsail/Fluidd, then use the physical display to browse icons).
2. Implement the screen logic in `klippy/extras/e3v3se_display.py`.
3. Use the `TJC3224` class methods for display communication.
4. Register new menu items following the existing `MenuKeys` pattern.

### Adding New Macros

- Follow the `[e3v3se_display MACRO%I]` pattern in `printer.cfg`.
- Each macro needs a unique number, a `gcode` command, and a `label`.
- Optional `icon` integer references the display's built-in icon library.

### CI/CD

- `build-firmware.yaml` — Builds MCU firmware on push.
- `release-firmware.yaml` — Creates releases with pre-built binaries.
- `build-test.yaml` — Runs Klipper test suite.
- Firmware artifacts are `.bin` files for SD card flashing.

### Code Style

- Python code follows Klipper's existing conventions (no strict PEP8 enforcement observed).
- C code follows Klipper's MCU coding style.
- Markdown uses markdownlint with some disabled rules (MD041, MD026, MD001).

---

## 8. FAQs for AI Agents

### Q: What makes this different from standard Klipper?

**A:** Two additions: (1) a serial bridge in the MCU firmware (`src/serial_bridge.c`) that routes display communication through the USB connection, and (2) a Python display driver (`klippy/extras/e3v3se_display.py`) that renders the Klipper UI on the stock Creality display.

### Q: Can I apply these changes to upstream Klipper?

**A:** Yes, the commits are designed to be applied independently. The serial bridge and display extras can theoretically be cherry-picked onto any Klipper fork.

### Q: What language options are available for the display?

**A:** The display supports the following languages (configured via the `language` property in `[e3v3se_display]`): `chinese`, `english` (default), `german`, `russian`, `french`, `turkish`, `spanish`, `italian`, `portuguese`, `japanese`, `korean`. These are defined in `klippy/extras/e3v3se_display.py`.

### Q: Why does the display go crazy after flashing?

**A:** The display firmware version must be exactly **1.0.6**. Other versions have different memory layouts for display assets.

### Q: What is the relationship between this repo and jpcurti/E3V3SE_display_klipper?

**A:** The standalone Python project (`E3V3SE_display_klipper`) was the original display interface that ran as a separate process. This repository integrates that functionality directly into the Klipper firmware as a native extra, eliminating the need for a separate daemon.

### Q: How do I find the build output?

**A:** After running `make`, the firmware binary is at `out/klipper.bin`. For CI builds, check the GitHub Actions artifacts.

---

## 9. Agent Instructions

### Parsing This Repository

1. **Start here** (`AI_DOC.md`) for full project context.
2. **For display logic:** Focus on `klippy/extras/e3v3se_display.py` and `klippy/extras/TJC3224/`.
3. **For firmware/MCU questions:** Look at `src/serial_bridge.c` and `src/stm32/`.
4. **For configuration questions:** Reference `README.md` and `e3v3se_docs/configuration.md`.
5. **For build/install questions:** Reference `e3v3se_docs/install.md` and the Makefile.
6. **For upstream Klipper questions:** The `docs/` directory contains full Klipper documentation.

### Generating Answers

- Always note the **display firmware 1.0.6 requirement** when discussing installation.
- When discussing serial bridge, clarify it's a **compile-time MCU feature**, not a runtime config.
- Distinguish between **MCU firmware** (C, flashed via SD card) and **host software** (Python, runs on Pi).
- The `[e3v3se_display]` config section is the user-facing entry point for all display features.

### Common Tasks for Agents

| Task | Key Files |
|------|-----------|
| Fix display bug | `klippy/extras/e3v3se_display.py`, `klippy/extras/TJC3224/` |
| Add display feature | `klippy/extras/e3v3se_display.py`, `klippy/extras/display/` |
| Fix serial communication | `src/serial_bridge.c`, `klippy/extras/serial_bridge.py` |
| Update build config | `src/Kconfig`, `Makefile` |
| Update documentation | `README.md`, `e3v3se_docs/` |
| Debug CI failures | `.github/workflows/`, `ci_build/` |
| Add printer config | `config/` |

---

## 10. Maintenance Notes

- This document should be updated when:
  - New display features are added
  - The repository structure changes significantly
  - New dependencies or build requirements are introduced
  - Display firmware compatibility changes
- The document is designed to be parseable by both humans and AI systems.
- Keep sections concise and factual — avoid speculation about future features.
