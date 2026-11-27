# Qidi Q2 Fluidd Material Box Patch

Client-side patch for the Material Control (Qidi Box) widget in Fluidd, designed for Qidi Q2 and compatible printers following recent firmware updates.

## AI Disclosure

This project was developed with the assistance of AI for reverse-engineering the minified Fluidd bundle and drafting the patch, and was tested and verified on physical hardware (Qidi Q2).

## Credits

Versions 2 to 4 build on the approach of [Assur92/qidi-max4-fluidd-box-fix](https://github.com/Assur92/qidi-max4-fluidd-box-fix) (GPL-3.0): reading the live `box_extras.filament_info` data, writing with `UPDATE_FILAMENT_INFORMATION`, merging `multi_color_controller` updates recursively, bumping the `sw.js` revision, and matching print-start dialog slots by `filament_type`. Thanks!

---

## Overview

Since 01.01.03.01 firmware update, Qidi updated the internal multi-color subsystem (`multi_color_controller.so`) to a new V2 data structure:
- Filament types are stored as profile identifier strings (e.g., `'QFA00'`, `'QFL30'`) instead of legacy integer indices.
- Colors are stored as hexadecimal arrays (e.g., `['060606']`) instead of palette index integers.
- G-code action macros were renamed (`LOAD_FILAMENT_CONTROL`, `UNLOAD_FILAMENT_CONTROL`, `EJECT_FILAMENT_CONTROL`, `READ_RFID`).
- Slot edits go through a new command, `UPDATE_FILAMENT_INFORMATION` (the one Qidi Studio sends).
- Sensor reporting fields (`b_endstop_state`) were relocated to `multi_color_controller.box`, which only reports changed fields.

With firmware 01.01.03.04, Qidi also ships a new Fluidd build (`index-nyEzQB9T.js`) where the Material Control card was removed from the dashboard, and so was the print-start dialog that lets you check each tool's slot before printing: their code is still in the bundle, but nothing displays them anymore.

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
5. **Working controls**: Load / Unload / Eject / Read RFID send the new commands; `multi_color_controller` partial updates are merged at every nesting level, so Unload, the pre-print check and the Rack material stay correct after a change.
6. **Print-start dialog**: the file's materials are matched to box slots using the live `filament_type`, so slots no longer show `?` and **Print** is no longer blocked. The slot list offered for each tool is filtered by that type.
7. **Cache refresh**: `sw.js` gets a new revision so browsers load the patched bundle instead of a cached one.
8. **No backend modifications**: Klipper binaries, Cython shared libraries, and configuration files remain untouched. The patcher only adds one hidden link, `~/printer_data/config/.qidi_filaments`, pointing to Qidi's filament database (read-only use).
9. **Material Box card restored (firmware 01.01.03.04)**: when the Fluidd build no longer registers the dashboard card, the patcher rebuilds it exactly as in the previous build (same title, icon and layout entry). Minified names that change between builds are detected automatically. Builds that still have the card are left untouched.
10. **Print-start dialog restored (firmware 01.01.03.04)**: when the Fluidd build no longer shows the dialog, the patcher rebuilds it as in the previous build and opens it again from Print, Reprint and Upload & Print, as long as a box is configured. As before, it shows the file's tools with their materials and colours, proposes a matching slot for each, saves the choice (`SAVE_VARIABLE VARIABLE=value_tN`) and starts the print. Qidi's check needs the file's folder loaded in Fluidd, which is not the case when the dashboard has no Jobs card: the patcher loads it when missing, so the dialog also opens from Reprint in that layout. After an upload, it waits for Moonraker to read the file. Without tool information after 10 s, the print starts directly. Builds that still have the dialog are left untouched.
11. **Safety and reversibility**: The patcher checks every code block before writing (nothing is changed if one does not match), creates `.bak` factory copies, and is safe to run again. Upgrading from V1, V2 or V3 is automatic.

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

If the Material Control card does not appear on the dashboard, enable it again from the dashboard layout settings.

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
- **Target File**: `/home/qidi/fluidd/assets/index-*.js` (Fluidd v1.30.5 shipped by Qidi):
  - `index-DlFvHGAh.js` (firmware 01.01.03.01 / 01.01.03.02)
  - `index-nyEzQB9T.js` (firmware 01.01.03.04, Material Control card and print-start dialog rebuilt by the patch)

---

## License

This project is licensed under the GNU General Public License v3.0, the same license as [Fluidd](https://github.com/fluidd-core/fluidd), which it patches. See the LICENSE file for full details.
