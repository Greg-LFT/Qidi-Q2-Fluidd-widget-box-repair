# Qidi Box Fluidd Patch (Qidi Q2 / Plus 4 / Q1 Pro)

A lightweight client-side translator patch for the **Material Control (Qidi Box)** widget in Fluidd after recent Qidi firmware updates.

---

## 🧐 The Problem

Recent Qidi firmware updates upgraded the multicolor engine (`multi_color_controller.so`) to a new V2 format:
* Filament types are stored as profile IDs (e.g., `'QFA00'`, `'QFU01'`) instead of legacy integers (`7`, `15`).
* Colors are stored as hex arrays (e.g., `['060606']`) instead of legacy palette indices (`1..24`).
* Action macros were renamed (`E_LOAD` / `E_UNLOAD` $\rightarrow$ `LOAD_FILAMENT_CONTROL`, `UNLOAD_FILAMENT_CONTROL`, `EJECT_FILAMENT_CONTROL`).
* Endstop status reporting changed.

As a result, the built-in Fluidd **Material Control** widget broke:
- Filament colors and types disappeared or showed default values.
- Changing materials in Fluidd didn't save properly or broke compatibility with Qidi Studio.
- Action buttons (**Load**, **Unload**, **Eject**, **RFID**) stopped responding.

## 💡 The Solution

This patch operates purely inside Fluidd's web interface (`index-*.js`):
1. **Zero changes to Klipper or Qidi backend code**: Klipper remains completely stock and unmodified.
2. **100% compatible with Qidi Studio and touchscreen**: Materials and colors edited via Fluidd are converted to Qidi V2 format seamlessly.
3. **Automatic backup & 1-command rollback**: An `index-*.js.bak` file is created automatically before any change is made.

---

## 🚀 Installation

### 1. Connect to your printer via SSH
```bash
ssh mks@<YOUR_PRINTER_IP>
```
*(Default password: `makerbase`)*

### 2. Run the patcher
```bash
curl -sSL https://raw.githubusercontent.com/<YOUR_USERNAME>/<YOUR_REPO>/main/patch_fluidd_box.py | python3
```
*(Or clone this repo and run `python3 patch_fluidd_box.py`)*

### 3. Hard-refresh your browser
Reload Fluidd with cache bypassed:
* **Windows / Linux**: `Ctrl + F5` or `Ctrl + Shift + R`
* **Mac**: `Cmd + Shift + R`

---

## 🔄 Restoration / Rollback

To uninstall the patch and return to the factory-original Fluidd file at any time:

```bash
python3 patch_fluidd_box.py --restore
```

Or via direct bash command:
```bash
for f in /home/qidi/fluidd/assets/index-*.js.bak; do [ -f "$f" ] && cp -f "$f" "${f%.bak}" && echo "Restored!"; done
```
Then hard-refresh your browser (`Ctrl + F5`).

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
````
