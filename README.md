# Qidi Q2 Fluidd Material Box Patch

Client-side patch for the Material Control (Qidi Box) widget in Fluidd, designed for Qidi Q2 and compatible printers following recent firmware updates.

## AI Disclosure

This project was developed with the assistance of AI for reverse-engineering the minified Fluidd bundle and drafting the patch, and was tested and verified on physical hardware (Qidi Q2).

## Credits

Version 2 builds on the approach of [Assur92/qidi-max4-fluidd-box-fix](https://github.com/Assur92/qidi-max4-fluidd-box-fix) (GPL-3.0): reading the live `box_extras.filament_info` data, writing with `UPDATE_FILAMENT_INFORMATION`, merging `multi_color_controller` updates and bumping the `sw.js` revision. Thanks!

---

## Overview

Since 01.01.03.01 firmware update, Qidi updated the internal multi-color subsystem (`multi_color_controller.so`) to a new V2 data structure:
- Filament types are stored as profile identifier strings (e.g., `'QFA00'`, `'QFL30'`) instead of legacy integer indices.
- Colors are stored as hexadecimal arrays (e.g., `['060606']`) instead of palette index integers.
- G-code action macros were renamed (`LOAD_FILAMENT_CONTROL`, `UNLOAD_FILAMENT_CONTROL`, `EJECT_FILAMENT_CONTROL`, `READ_RFID`).
- Slot edits go through a new command, `UPDATE_FILAMENT_INFORMATION` (the one Qidi Studio sends).
- Sensor reporting fields (`b_endstop_state`) were relocated to `multi_color_controller.box`, which only reports changed fields.

Because Fluidd's bundled frontend expected the legacy schema, the integrated Material Control widget exhibited several issues:
- Empty or missing filament color and type indicators.
- Missing third-party filament vendors available on the touchscreen (Bambu, Polymaker, HATCHBOX, Overture).
- Inability to persist slot configuration changes without breaking synchronization with Qidi Studio and the touchscreen.
- Non-functional control actions (Load, Unload, Eject, Read RFID), Unload staying greyed out.

---

## Technical Details

This patch modifies the client-side JavaScript bundle (`/home/qidi/fluidd/assets/index-*.js`) and `sw.js` directly:
1. **Live slot data**: Slots and the external spool (Rack) display what the firmware publishes (`box_extras.boxes[].filament_info`, `multi_color_controller.extra.filament_info`) — the same data as the touchscreen and Qidi Studio.
2. **Firmware filament database**: Vendor and filament lists are read live from Qidi's own database (`/home/qidi/QIDI_Client/resource/filament_config/filament-<nozzle>.json`) for the configured nozzle. When Qidi adds or renames filaments or vendors, Fluidd follows automatically. A built-in catalogue (`QIDI`, `Generic`, `Bambu`, `Polymaker`, `HATCHBOX`, `Overture`) is used as fallback.
3. **Dynamic Filament Filtering**: Selecting a vendor filters the filament dropdown to that brand's catalog, keeping the same material type when available (e.g. QIDI PLA Basic → Bambu PLA).
4. **Native synchronization**: Edits from Fluidd are sent with `UPDATE_FILAMENT_INFORMATION`, so the touchscreen, Qidi Studio and print temperatures stay in sync.
5. **Working controls**: Load / Unload / Eject / Read RFID send the new commands; `multi_color_controller` updates are merged so Unload and the pre-print check work again.
6. **Cache refresh**: `sw.js` gets a new revision so browsers load the patched bundle instead of a cached one.
7. **No backend modifications**: Klipper binaries, Cython shared libraries, and configuration files remain untouched. The patcher only adds one hidden link, `~/printer_data/config/.qidi_filaments`, pointing to Qidi's filament database (read-only use).
8. **Safety and reversibility**: The patcher checks every code block before writing (nothing is changed if one does not match), creates `.bak` factory copies, and is safe to run again. Upgrading from V1 is automatic.

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

Optional, before patching — check without changing anything:
```bash
curl -sSL https://raw.githubusercontent.com/Greg-LFT/Qidi-Q2-Fluidd-widget-box-repair/main/patch_fluidd_box.py | python3 - --dry-run
```

### Step 3: Clear Browser Cache
Close **every** Fluidd tab, reopen Fluidd, then perform a hard refresh:
- **Windows / Linux**: `Ctrl + F5` or `Ctrl + Shift + R`
- **macOS**: `Cmd + Shift + R`

---

## Rollback Procedure

To revert all modifications and restore the factory files:

### Method A: Using the patch script
```bash
curl -sSL https://raw.githubusercontent.com/Greg-LFT/Qidi-Q2-Fluidd-widget-box-repair/main/patch_fluidd_box.py | python3 - --restore
```

### Method B: Manual shell restoration
```bash
for f in /home/qidi/fluidd/assets/index-*.js.bak /home/qidi/fluidd/sw.js.bak; do [ -f "$f" ] && sudo cp -f "$f" "${f%.bak}" && echo "Restored $f"; done
sudo rm -f /home/qidi/printer_data/config/.qidi_filaments
```

After restoring, close every Fluidd tab and hard refresh the browser (`Ctrl + F5`).

---

## Troubleshooting

Read-only compatibility report (paste it into an issue if the patch does not fit your printer):
```bash
curl -sSL https://raw.githubusercontent.com/Greg-LFT/Qidi-Q2-Fluidd-widget-box-repair/main/patch_fluidd_box.py | python3 - --check
```

After a Qidi firmware update, Fluidd is usually replaced and the patch removed: run the patcher again. If Qidi changed Fluidd, the patcher stops without changing anything.

---

## Compatibility

- **Hardware**: Qidi Q2 (and systems using the Qidi Box V2 multi-color module).
- **Target File**: `/home/qidi/fluidd/assets/index-*.js` (Fluidd v1.30.5 shipped by Qidi, `index-DlFvHGAh.js`).

### Known limitations
- Printing from Fluidd's own slot-mapping dialog still uses the legacy data. Start multi-color prints from Qidi Studio.

---

## License

This project is licensed under the GNU General Public License v3.0, the same license as [Fluidd](https://github.com/fluidd-core/fluidd), which it patches. See the LICENSE file for full details.
