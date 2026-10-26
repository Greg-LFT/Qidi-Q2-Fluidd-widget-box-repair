#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fluidd Material Box Patch for Qidi Q2 - V2
Repository: https://github.com/Greg-LFT/Qidi-Q2-Fluidd-widget-box-repair
License: GPL-3.0 (same as Fluidd, which this patches)

Developed with AI assistance and validated on Qidi Q2 hardware.

V2 approach credit: reading box_extras.filament_info, writing with
UPDATE_FILAMENT_INFORMATION, merging multi_color_controller updates and bumping
the sw.js revision come from Assur92's qidi-max4-fluidd-box-fix (GPL-3.0):
https://github.com/Assur92/qidi-max4-fluidd-box-fix

Copyright (C) 2026 Greg-LFT
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version. It is distributed WITHOUT ANY WARRANTY. See the LICENSE file.

Usage:
  python3 patch_fluidd_box.py             apply the patch (asks for sudo when needed)
  python3 patch_fluidd_box.py --restore   restore the factory files from the .bak copies
  python3 patch_fluidd_box.py --dry-run   check that the patch fits, change nothing
  python3 patch_fluidd_box.py --check     read-only compatibility report
Also works piped: curl -sSL <raw url> | python3 - [--restore]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

VERSION = "qdv2-1"
# Markers used to recognise a file that is not the factory original:
# V2 (this script), V1 of this repository, Assur92's patch.
MARKERS = ("qdv2-", "_qFilaCat", "qd-box-fix-")

FLUIDD_DIRS = ["/home/qidi/fluidd", "/home/mks/fluidd", "/usr/share/fluidd"]
CONFIG_DIRS = ["/home/qidi/printer_data/config", "/home/mks/printer_data/config"]
FILAMENT_DB_DIR = "/home/qidi/QIDI_Client/resource/filament_config"
DB_LINK_NAME = ".qidi_filaments"
MOONRAKER = "http://127.0.0.1:7125"

# Fallback catalogue, used by Fluidd only when the firmware database cannot be read.
# Source: filament-0.4.json shipped with the Qidi firmware (vendor -> materials).
FALLBACK_DB = {
    "QIDI": ["PLA Basic", "PLA Matte Basic", "PLA Rapido", "PLA Rapido Matte", "PLA Rapido Metal",
             "PLA Silk", "WOOD Rapido", "PLA-CF", "ASA", "ASA-Aero", "ABS-GF", "ASA-CF20 Core",
             "ABS Odorless", "ABS Rapido", "ABS Rapido Metal", "PC/ABS-FR", "PETG Basic",
             "PETG Rapido", "PETG Tough", "PETG Translucent", "PETG-CF", "PETG-GF", "PAHT-CF",
             "PA6-CF", "PA12-CF", "PAHT-GF", "UltraPA", "UltraPA-CF25", "PPS-CF", "PPS-GF",
             "Support For PET/PA", "Support For PAHT", "PET-CF", "PET-GF", "TPU-Aero",
             "TPU 95A-HF", "TPU-GF", "PEBA 95A"],
    "Generic": ["ABS", "PC", "PETG", "PLA", "PLA Silk", "PLA+", "TPU 95A"],
    "Bambu": ["ABS", "PETG", "PLA"],
    "HATCHBOX": ["ABS", "PETG", "PLA"],
    "Overture": ["ABS", "PLA"],
    "Polymaker": ["ABS", "PLA", "PLA-HT"],
}

# ---------------------------------------------------------------------------
# JavaScript members added to the Material Control component.
# ---------------------------------------------------------------------------
JS_MEMBERS = (
    # Displayed slots: Fluidd's own computation, then each slot is overwritten
    # with the live data published by the firmware.
    "get items(){const t=this.qdRawItems.slice(),p=this.$store.state.printer.printer,"
    "bx=(p.box_extras||{}).boxes||[];"
    "for(let m=0;m<16&&m<this.boxCount*4;m++){"
    "const fi=((bx[Math.floor(m/4)]||{}).filament_info||[])[m%4];"
    "if(fi&&t[m]&&this.variables.slot[m]!==0)t[m]=Object.assign({},t[m],this.qdFmt(fi))}"
    "const ex=((p.multi_color_controller||{}).extra||{}).filament_info;"
    "if(ex&&t[16])t[16]=Object.assign({},t[16],this.qdFmt(ex));return t}"

    "qdFmt(fi){const c=String((fi.color_rgb_str||[])[0]||\"\").replace(\"#\",\"\");"
    "return{color:c?\"#\"+c:\"#00000000\",filament:fi.filament_str||\"\",vendor:fi.vendor_str||\"\"}}"

    "qdNewFw(){const b=(this.$store.state.printer.printer.box_extras||{}).boxes;"
    "return!!(b&&b[0]&&b[0].filament_info)}"

    "qdDbNow(){return this.qdNewFw()?(this.$store.state.printer.qdFilaDB||__QD_FALLBACK__):null}"

    # Firmware filament database, read live through Moonraker for the configured nozzle.
    "qdLoadDb(){const st=this.$store.state,pr=st.printer;"
    "if(pr.qdFilaDB||window.__qdDbLoading)return;window.__qdDbLoading=1;let nz=\"0.4\";"
    "try{const d=parseFloat(pr.printer.configfile.settings.extruder.nozzle_diameter);"
    "[0.2,0.4,0.6,0.8].forEach(x=>{Math.abs(d-x)<.01&&(nz=x.toFixed(1))})}catch(e){}"
    "const base=(st.config&&st.config.apiUrl)||\"\";"
    "fetch(base+\"/server/files/config/__QD_LINK__/filament-\"+nz+\".json\",{cache:\"no-store\"})"
    ".then(r=>r.ok?r.json():Promise.reject(\"HTTP \"+r.status)).then(j=>{const db={};"
    "for(const k in j){const e=j[k]||{},v=e.filament_vendor||k.split(\" \")[0],"
    "n=k.indexOf(v+\" \")===0?k.slice(v.length+1):k;(db[v]=db[v]||[]).push(n)}"
    "Object.keys(db).length&&this.$set(pr,\"qdFilaDB\",db)})"
    ".catch(e=>console.warn(\"[qdv2] firmware filament database unavailable, using fallback:\",e))"
    ".finally(()=>{window.__qdDbLoading=0})}"

    # Vendor / material / colour edits, sent the way Qidi Studio does.
    "qdEdit(o){const i=this.selectIndex,p=this.$store.state.printer.printer;"
    "if(!this.qdNewFw())return!1;if(i>16)return!0;"
    "if(i===16&&!((p.multi_color_controller||{}).extra||{}).filament_info)return!1;"
    "const db=this.qdDbNow(),it=this.items[i]||{};"
    "let v=o.vendor!=null?o.vendor:it.vendor,f=o.filament!=null?o.filament:it.filament;"
    "db[v]||(v=Object.keys(db).find(k=>db[k].indexOf(f)>=0)||\"QIDI\");"
    "if(db[v].indexOf(f)<0){const b=String(f||\"\").split(/[ -]/)[0];f=db[v].indexOf(b)>=0?b:"
    "db[v].find(n=>n.split(/[ -]/)[0]===b)||db[v][0]}"
    "let c=String(o.color!=null?o.color:it.color||\"\").replace(\"#\",\"\").toUpperCase().slice(0,6);"
    "/^[0-9A-F]{6}$/.test(c)||(c=\"FAFAFA\");"
    "I.printerGcodeScript(`UPDATE_FILAMENT_INFORMATION SLOT=${i} COLOR='${c}' VENDOR='${v}' FILAMENT='${f}'`);"
    "return!0}"
)

# Live b_endstop_state: box_extras on old firmware, multi_color_controller.box on V2.
B_ENDSTOP = (
    "(this.$store.state.printer.printer.box_extras.b_endstop_state!==void 0"
    "?this.$store.state.printer.printer.box_extras.b_endstop_state"
    ":((this.$store.state.printer.printer.multi_color_controller||{}).box||{}).b_endstop_state)"
)

# (anchor in the factory Fluidd bundle, replacement, expected occurrences)
BUNDLE_EDITS = [
    # Keep Fluidd's own slot computation under another name; JS_MEMBERS wraps it.
    ("get items(){var i,a,o,l,c,u,d,p,h;const t=[],s=new Array(16).fill(!1);",
     "/*" + VERSION + "*/get qdRawItems(){var i,a,o,l,c,u,d,p,h;const t=[],s=new Array(16).fill(!1);", 1),
    # New members + load of the filament database when the panel is created.
    ("created(){this.$store.state.printer.officiallFilasList?",
     "__QD_MEMBERS__created(){this.qdLoadDb();this.$store.state.printer.officiallFilasList?", 1),
    # Lists offered in the edit dialog.
    ("get vendorItems(){",
     "get vendorItems(){const qd=this.qdDbNow();if(qd)return Object.keys(qd);", 1),
    ("get filamentItems(){",
     "get filamentItems(){const qd=this.qdDbNow();if(qd){const v=(this.items[this.selectIndex]||{}).vendor;"
     "return qd[v]||qd.QIDI||[]}", 1),
    # Edits.
    ("set selectedVendor(t){", "set selectedVendor(t){if(t&&this.qdEdit({vendor:t}))return;", 1),
    ("set selectedFilament(t){", "set selectedFilament(t){if(t&&this.qdEdit({filament:t}))return;", 1),
    ("set selectedColor(t){", "set selectedColor(t){if(t&&this.qdEdit({color:t}))return;", 1),
    # Renamed box commands.
    ('const n=["E_BOX","E_LOAD","E_UNLOAD"];I.printerGcodeScript(`${n[t-1]} slot=${s}`)',
     'const n=["EJECT_FILAMENT_CONTROL","LOAD_FILAMENT_CONTROL","UNLOAD_FILAMENT_CONTROL"];'
     'I.printerGcodeScript(`${n[t-1]} SLOT=${s}`)', 1),
    ("RFID_READ SLOT=slot${t}", "READ_RFID SLOT=${t}", 1),
    # Buttons: b_endstop_state moved to multi_color_controller.box.
    ("this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot",
     B_ENDSTOP + "===0&&this.variables.lastLoadSlot", 2),
    # Pre-print check: e/b endstop states are no longer in box_extras.
    ("get isOkPrinter(){return this.enableBox===!1?this.$store.state.printer.printer.box_extras.e_endstop_state"
     "===1?this.$store.state.printer.printer.box_extras.b_endstop_state===0?",
     "get isOkPrinter(){const qp=this.$store.state.printer.printer,qx=qp.box_extras||{},"
     "qf=qp[\"filament_switch_sensor filament_switch_sensor\"]||{},"
     "qe=qx.e_endstop_state!==void 0?qx.e_endstop_state:qf.filament_detected?1:0,"
     "qb=qx.b_endstop_state!==void 0?qx.b_endstop_state:((qp.multi_color_controller||{}).box||{}).b_endstop_state;"
     "return this.enableBox===!1?qe===1?qb===0?", 1),
    # Store: multi_color_controller only sends changed fields, so merge them.
    ("t[s]!==e.payload[s]&&$.set(r.printer[e.key],s,e.payload[s])",
     "t[s]!==e.payload[s]&&$.set(r.printer[e.key],s,e.key===\"multi_color_controller\"&&t[s]&&e.payload[s]"
     "&&typeof t[s]==\"object\"&&typeof e.payload[s]==\"object\"&&!Array.isArray(e.payload[s])"
     "?Object.assign({},t[s],e.payload[s]):e.payload[s])", 1),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def fail(msg):
    print("[ERROR] " + msg)
    sys.exit(1)


def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def is_original(text):
    return not any(m in text for m in MARKERS)


def sudo(args):
    """Run a command with sudo; reads the password from the terminal, which also
    works when the script itself is piped through `curl ... | python3`."""
    try:
        with open("/dev/tty", "r") as tty_in:
            subprocess.run(["sudo"] + args, stdin=tty_in, check=True)
    except Exception as e:  # noqa: BLE001
        fail("sudo %s failed: %s" % (" ".join(args), e))


def privileged_write(dst, text):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as tmp:
        tmp.write(text)
        tmp_path = tmp.name
    try:
        try:
            with open(dst, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        except PermissionError:
            print("[INFO] Elevating permissions with sudo to write %s..." % dst)
            sudo(["cp", "-f", tmp_path, dst])
    finally:
        os.remove(tmp_path)


def find_fluidd():
    for fdir in FLUIDD_DIRS:
        index_html = os.path.join(fdir, "index.html")
        if os.path.isfile(index_html):
            match = re.search(r'src="(?:\./|/)?(assets/index-[\w-]+\.js)"', read_text(index_html))
            if match and os.path.isfile(os.path.join(fdir, match.group(1))):
                return fdir, match.group(1)
    fail("Could not detect the active Fluidd JavaScript bundle (looked in %s)." % ", ".join(FLUIDD_DIRS))


def factory_text(path):
    """Factory version of a file: the file itself if unpatched, else its .bak copy."""
    text = read_text(path)
    if is_original(text):
        return text
    for bak in (path + ".bak", path + ".qdv2.orig"):  # .qdv2.orig: early V2 builds
        if os.path.isfile(bak) and is_original(read_text(bak)):
            return read_text(bak)
    return None


# ---------------------------------------------------------------------------
# Building the patched files
# ---------------------------------------------------------------------------
def js_members():
    fallback = json.dumps(FALLBACK_DB, separators=(",", ":"), ensure_ascii=False)
    return JS_MEMBERS.replace("__QD_FALLBACK__", fallback).replace("__QD_LINK__", DB_LINK_NAME)


def patch_bundle(js):
    for anchor, repl, expected in BUNDLE_EDITS:
        found = js.count(anchor)
        if found != expected:
            fail("Target code block not found (expected %d, found %d): %s...\n"
                 "        Firmware/Fluidd version may differ. Nothing was changed. "
                 "Run with --check and open an issue." % (expected, found, anchor[:60]))
        js = js.replace(anchor, repl.replace("__QD_MEMBERS__", js_members()))
    return js


def patch_sw(sw, bundle):
    pat = re.compile(r'\{"revision":(?:null|"[^"]*"),"url":"' + re.escape(bundle) + r'"\}')
    if len(pat.findall(sw)) != 1:
        return None
    return pat.sub('{"revision":"%s","url":"%s"}' % (VERSION, bundle), sw)


def build(fdir, bundle):
    """Return [(path, factory_text, patched_text)] without writing anything."""
    bpath = os.path.join(fdir, bundle)
    js = factory_text(bpath)
    if js is None:
        fail("%s is patched and no factory backup (.bak) was found.\n"
             "        Reinstall Fluidd from the Qidi update, then run the patcher again." % bpath)
    files = [(bpath, js, patch_bundle(js))]
    swpath = os.path.join(fdir, "sw.js")
    if os.path.isfile(swpath):
        sw = factory_text(swpath) or read_text(swpath)
        new_sw = patch_sw(sw, bundle)
        if new_sw is not None:
            files.append((swpath, sw, new_sw))
    return files


# ---------------------------------------------------------------------------
# Filament database link
# ---------------------------------------------------------------------------
def config_dir():
    for d in CONFIG_DIRS:
        if os.path.isdir(d):
            return d
    return None


def ensure_db_link():
    cfg = config_dir()
    if not cfg or not os.path.isdir(FILAMENT_DB_DIR):
        print("[WARN] Qidi filament database not found, Fluidd will use the built-in catalogue.")
        return
    link = os.path.join(cfg, DB_LINK_NAME)
    if os.path.islink(link) and os.readlink(link) == FILAMENT_DB_DIR:
        print("[INFO] Filament database link already present: %s" % link)
        return
    if os.path.exists(link) and not os.path.islink(link):
        print("[WARN] %s exists and is not a link, left untouched." % link)
        return
    try:
        if os.path.islink(link):
            os.unlink(link)
        os.symlink(FILAMENT_DB_DIR, link)
    except PermissionError:
        sudo(["ln", "-sfn", FILAMENT_DB_DIR, link])
    print("[OK] Filament database linked: %s -> %s" % (link, FILAMENT_DB_DIR))


def remove_db_link():
    cfg = config_dir()
    link = os.path.join(cfg, DB_LINK_NAME) if cfg else None
    if link and os.path.islink(link):
        try:
            os.unlink(link)
        except PermissionError:
            sudo(["rm", "-f", link])  # removes the link only, never the Qidi files
        print("[OK] Removed filament database link: %s" % link)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def patch(dry_run=False):
    fdir, bundle = find_fluidd()
    print("[INFO] Active target bundle detected: %s" % os.path.join(fdir, bundle))
    files = build(fdir, bundle)

    if all(VERSION in read_text(p) for p, _, _ in files):
        print("[INFO] Patch %s already applied, nothing to do." % VERSION)
        if not dry_run:
            ensure_db_link()
        return
    if dry_run:
        print("[OK] Dry run: the patch fits this Fluidd build. Nothing was changed.")
        return

    for path, factory, patched in files:
        bak = path + ".bak"
        # An unpatched file is the current factory version (maybe from a newer
        # Qidi update), so it always refreshes the backup.
        if is_original(read_text(path)) or not os.path.isfile(bak) or not is_original(read_text(bak)):
            privileged_write(bak, factory)
            print("[OK] Factory backup created: %s" % bak)
        else:
            print("[INFO] Existing backup preserved: %s" % bak)
        privileged_write(path, patched)
        print("[OK] Patched: %s" % path)

    ensure_db_link()
    print("[OK] Material Box patch V2 successfully applied.")
    print("[INFO] Close every Fluidd tab, reopen Fluidd and hard-refresh your browser (Ctrl+F5).")


def restore():
    fdir, bundle = find_fluidd()
    restored = 0
    for path in (os.path.join(fdir, bundle), os.path.join(fdir, "sw.js")):
        if is_original(read_text(path)):
            continue
        text = factory_text(path)
        if text is None:
            print("[WARN] No factory backup for %s, skipped." % path)
            continue
        privileged_write(path, text)
        print("[OK] Successfully restored %s from backup." % path)
        restored += 1
    remove_db_link()
    if not restored:
        fail("No backup file (.bak) found to restore.")
    print("[INFO] Close every Fluidd tab, reopen Fluidd and hard-refresh your browser (Ctrl+F5).")


def moonraker(path):
    with urllib.request.urlopen(MOONRAKER + path, timeout=10) as r:
        return json.load(r)["result"]


def check():
    rows, problems = [("Script", VERSION)], []
    try:
        fdir, bundle = find_fluidd()
        rows.append(("Fluidd bundle", os.path.join(fdir, bundle)))
        bpath = os.path.join(fdir, bundle)
        js = factory_text(bpath)
        if js is None:
            raise ValueError("patched file without factory backup")
        missing = [a[:50] for a, _, n in BUNDLE_EDITS if js.count(a) != n]
        if missing:
            raise ValueError("code blocks not found: " + "; ".join(missing))
        rows.append(("Fluidd patch", "applied (V2)" if VERSION in read_text(bpath) else "fits"))
    except SystemExit:
        rows.append(("Fluidd patch", "Fluidd not found"))
        problems.append("Fluidd bundle not found")
    except ValueError as e:
        rows.append(("Fluidd patch", "does NOT fit"))
        problems.append(str(e))
    rows.append(("Filament database", "found" if os.path.isdir(FILAMENT_DB_DIR) else "missing (built-in catalogue)"))
    try:
        cmds = moonraker("/printer/gcode/help")
        need = ["LOAD_FILAMENT_CONTROL", "UNLOAD_FILAMENT_CONTROL", "EJECT_FILAMENT_CONTROL",
                "READ_RFID", "UPDATE_FILAMENT_INFORMATION"]
        absent = [c for c in need if c not in cmds]
        rows.append(("Box commands", "all present" if not absent else "missing: " + ", ".join(absent)))
        if absent:
            problems.append("Firmware lacks: " + ", ".join(absent))
        st = moonraker("/printer/objects/query?box_extras&multi_color_controller")["status"]
        boxes = (st.get("box_extras") or {}).get("boxes") or []
        infos = [fi for b in boxes if b.get("is_online") for fi in (b.get("filament_info") or [])]
        rows.append(("Slots with filament_info", str(len(infos))))
        if not infos:
            problems.append("box_extras.boxes[].filament_info missing (old firmware?)")
        mcc = st.get("multi_color_controller") or {}
        rows.append(("b_endstop_state", "present" if "b_endstop_state" in (mcc.get("box") or {}) else "missing"))
        rows.append(("External spool info", "present" if (mcc.get("extra") or {}).get("filament_info") else "missing"))
    except Exception as e:  # noqa: BLE001 - report only
        rows.append(("Moonraker", "not reachable (%s)" % e))
        problems.append("Printer side not checked: run --check on the printer while Klipper is running.")
    print("### Qidi Q2 Fluidd Material Box Patch - check report\n")
    print("| Item | Value |\n|---|---|")
    for k, v in rows:
        print("| %s | %s |" % (k, str(v).replace("|", "/")))
    print("\n**Result: %s**" % ("looks compatible" if not problems else "NOT compatible as is"))
    for p in problems:
        print("- " + p)
    print("\nNothing was changed.")


def main():
    ap = argparse.ArgumentParser(description="Fluidd Material Box Patch for Qidi Q2 - V2")
    ap.add_argument("action", nargs="?", choices=["restore"], help="same as --restore")
    ap.add_argument("--restore", "-r", action="store_true", help="restore the factory files from .bak")
    ap.add_argument("--dry-run", action="store_true", help="check that the patch fits, change nothing")
    ap.add_argument("--check", action="store_true", help="read-only compatibility report")
    args = ap.parse_args()
    if args.check:
        check()
    elif args.restore or args.action == "restore":
        restore()
    else:
        patch(args.dry_run)


if __name__ == "__main__":
    main()
