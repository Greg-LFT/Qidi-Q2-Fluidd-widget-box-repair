# Qidi Q2 Fluidd Material Box Patch

Client-side patch for the Material Control (Qidi Box) widget in Fluidd, designed for Qidi Q2 and compatible printers following recent firmware updates.

---

## Overview

Recent Qidi firmware releases updated the internal multi-color subsystem (`multi_color_controller.so`) to a new V2 data structure:
- Filament types are stored as profile identifier strings (e.g., `'QFA00'`, `'QFU01'`) instead of legacy integer indices.
- Colors are stored as hexadecimal arrays (e.g., `['060606']`) instead of palette index integers.
- G-code action macros were renamed (`LOAD_FILAMENT_CONTROL`, `UNLOAD_FILAMENT_CONTROL`, `EJECT_FILAMENT_CONTROL`, `READ_RFID`).
- Sensor reporting fields (`b_endstop_state`) were relocated.

Because Fluidd's bundled frontend expected the legacy schema, the integrated Material Control widget exhibited several issues:
- Empty or missing filament color and type indicators.
- Inability to persist slot configuration changes without breaking synchronization with Qidi Studio and the touchscreen.
- Non-functional control actions (Load, Unload, Eject, Read RFID).

---

## Technical Details

This patch modifies the client-side JavaScript bundle (`/home/qidi/fluidd/assets/index-*.js`) directly:
1. **No backend modifications**: Klipper binaries, Cython shared libraries, and configuration files remain completely untouched.
2. **Bidirectional translation**: Incoming V2 parameters are mapped to the UI, and user edits from Fluidd are converted to official V2 identifiers before sending `SAVE_VARIABLE` commands.
3. **Safety and reversibility**: The patcher automatically creates a `.bak` copy prior to writing changes, allowing immediate rollback.

---

## Installation

### Prerequisites
- SSH access to the printer (`mks` user, default password: `makerbase`).

### Step 1: Connect via SSH
```bash
ssh mks@<PRINTER_IP>
```

### Step 2: Execute the Patcher
```bash
curl -sSL https://raw.githubusercontent.com/Greg-LFT/Qidi-Q2-Fluidd-widget-box-repair/main/patch_fluidd_box.py | python3
```

### Step 3: Clear Browser Cache
Perform a hard refresh on the Fluidd web page:
- **Windows / Linux**: `Ctrl + F5` or `Ctrl + Shift + R`
- **macOS**: `Cmd + Shift + R`

---

## Rollback Procedure

To revert all modifications and restore the factory JavaScript bundle:

### Method A: Using the patch script
```bash
curl -sSL https://raw.githubusercontent.com/Greg-LFT/Qidi-Q2-Fluidd-widget-box-repair/main/patch_fluidd_box.py | python3 - --restore
```

### Method B: Manual shell restoration
```bash
for f in /home/qidi/fluidd/assets/index-*.js.bak; do [ -f "$f" ] && cp -f "$f" "${f%.bak}" && echo "Restored $f"; done
```

After restoring, hard refresh the browser (`Ctrl + F5`).

---

## Compatibility

- **Hardware**: Qidi Q2 (and systems using the Qidi Box V2 multi-color module).
- **Target File**: `/home/qidi/fluidd/assets/index-*.js`.

---

## License

This project is licensed under the MIT License. See the LICENSE file for full details.
