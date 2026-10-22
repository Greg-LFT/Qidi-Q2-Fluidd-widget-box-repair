# Qidi-Q2-Fluidd-widget-box-repair
Repair Fluidd widget box after 01.01.03.01 update

Voici les réponses à tes questions ainsi qu'un **README.md** complet prêt à être déposé sur GitHub.

---

### 1. Quelle licence choisir pour ton dépôt GitHub ?

Dans l'écosystème Klipper / Fluidd :
* **Recommandation : Licence MIT**
  * C'est la licence la plus simple, libre et populaire pour les scripts utilitaires et les patchs. Elle autorise tout le monde à utiliser, modifier et redistribuer ton script librement tout en te dégageant de toute responsabilité (*as-is, without warranty*).
* **Alternative : GPL-3.0**
  * Fluidd et Klipper sont sous licence GNU GPLv3. Si tu préfères forcer toute personne qui réutiliserait ton code à conserver ce projet obligatoirement open-source, tu peux opter pour la GPL-3.0.

> [!TIP]
> Pour un script de patch comme celui-ci, la **licence MIT** est idéale et la plus adoptée par la communauté.

---

### 2. Le script Python enrichi (avec argument `--restore`)

Pour rendre l'utilisation et la restauration ultra simples, nous pouvons ajouter le support de `--restore` directement au script. Ainsi :
* Pour patcher : `python3 patch_fluidd_box.py`
* Pour restaurer : `python3 patch_fluidd_box.py --restore`

Voici le script `patch_fluidd_box.py` complet :

```python
#!/usr/bin/env python3
"""
Fluidd Material Box Patch for Qidi Q2 / Plus4 / Q1 Pro
Fixes the Qidi Box widget in Fluidd after recent Qidi firmware updates.
License: MIT
"""

import os
import glob
import sys
import shutil

ASSETS_DIR = "/home/qidi/fluidd/assets"

def get_target_files():
    files = glob.glob(os.path.join(ASSETS_DIR, "index-*.js"))
    files = [f for f in files if not f.endswith(".bak")]
    return files

def restore():
    bak_files = glob.glob(os.path.join(ASSETS_DIR, "index-*.js.bak"))
    if not bak_files:
        print("[-] No backup file (.bak) found to restore.")
        sys.exit(1)
    for bak in bak_files:
        orig = bak[:-4]
        shutil.copyfile(bak, orig)
        print(f"[✓] Successfully restored {orig} from backup.")
    print("[*] Don't forget to hard-refresh your browser (Ctrl+F5)!")

def patch():
    targets = get_target_files()
    if not targets:
        print(f"[-] No index-*.js found in {ASSETS_DIR}")
        sys.exit(1)

    js_path = targets[0]
    print(f"[*] Target file: {js_path}")

    with open(js_path, "r", encoding="utf-8") as f:
        js = f.read()

    bak_path = js_path + ".bak"
    if not os.path.exists(bak_path):
        with open(bak_path, "w", encoding="utf-8") as f:
            f.write(js)
        print(f"[+] Backup created at {bak_path}")
    else:
        print(f"[*] Existing backup preserved at {bak_path}")

    t1 = 'get isOkPrinter(){return this.enableBox===!1?this.$store.state.printer.printer.box_extras.e_endstop_state===1?this.$store.state.printer.printer.box_extras.b_endstop_state===0?(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.error_msg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t("app.file_system.tooltip.warning_text"),this.usedExtruders.every(t=>this.selectedValueSlot[t]))}'
    r1 = 'get isOkPrinter(){const bx=this.$store.state.printer.printer.box_extras||{},mc=(this.$store.state.printer.printer.multi_color_controller||{}).box||{},fs=this.$store.state.printer.printer["filament_switch_sensor filament_switch_sensor"]||{},eS=bx.e_endstop_state!==void 0?bx.e_endstop_state:fs.filament_detected?1:0,bS=bx.b_endstop_state!==void 0?bx.b_endstop_state:mc.b_endstop_state;return this.enableBox===!1?eS===1?bS===0?(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.error_msg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t("app.file_system.tooltip.warning_text"),this.usedExtruders.every(t=>this.selectedValueSlot[t]))}'

    t2 = 'get isOperating(){const t=this.$store.state.printer.printer.box_extras;return!(!t||!t.box_button_state)}get buttonStatus(){const t=new Array(3).fill(!0);return this.selectIndex>=16||(this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?t[0]=!1:t[0]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0?this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[1]=!0:t[1]=!1:t[1]=!0,this.$store.state.printer.printer["box_stepper slot"+this.selectIndex].runout_button===0&&this.$store.state.printer.printer.box_extras.b_endstop_state===0&&this.variables.lastLoadSlot===this.selectIndex?t[2]=!1:t[2]=!0),t}get autoReloadDetect(){return this.$store.getters["printer/getAutoSwitchState"][2]===1}get selectedVendor(){return this.items[this.selectIndex].vendor}set selectedVendor(t){const s=this.getKeyByValue(this.officialFilasListDictData.vendor_list,t);s&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot16 VALUE="${s}"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE="${s}"`))}get selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){for(const s in this.officialFilasListDictData)s.startsWith("fila")&&this.officialFilasListDictData[s].filament===t&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot16 VALUE="${s.replace("fila","")}"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="${s.replace("fila","")}"`))}get selectedColor(){return this.items[this.selectIndex].color}set selectedColor(t){const s=this.getKeyByValue(this.officialFilasListDictData.colordict,t);s&&(this.selectIndex===16?I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot16 VALUE="${s}"`):I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot${this.selectIndex} VALUE="${s}"`))}created(){this.$store.state.printer.officiallFilasList?console.log("officiallFilasList has been initialized"):this.getOfficiallFilasList().then(t=>{this.$store.commit("printer/setOfficiallFilasList",wn.configToDict(t))}).catch(t=>{console.error("Failed to fetch official filas list dict:",t)})}handleColorClick(t){this.selectedColor=t}handleBoxButtonClick(){this.selectIndex=17}showConfig(){this.isConfig=!0}showAuto(){this.isAuto=!0}showHumidityDisplay(){this.isHumidityDisplay=!0}handleClick(t){this.selectIndex=t}handleButtonClick(t){const s=this.selectIndex;if(s===null){console.error("Invalid slot");return}const n=["E_BOX","E_LOAD","E_UNLOAD"];I.printerGcodeScript(`${n[t-1]} slot=${s}`)}handleRfidClick(t){I.printerGcodeScript(`RFID_READ SLOT=slot${t}`),this.selectIndex=t}'
    r2 = '''get isOperating(){const t=this.$store.state.printer.printer.box_extras,m=this.$store.state.printer.printer.multi_color_controller;return!!(t&&t.box_button_state||m&&m.task&&m.task.flow_id)}get buttonStatus(){const t=new Array(3).fill(!0);if(this.selectIndex<16){const st=this.$store.state.printer.printer["box_stepper slot"+this.selectIndex],hasFila=st&&st.runout_button===0,isLoaded=this.slotSync===this.selectIndex;t[0]=!hasFila,t[1]=!(hasFila&&!isLoaded),t[2]=!(hasFila&&isLoaded)}return t}get autoReloadDetect(){return this.$store.getters["printer/getAutoSwitchState"][2]===1}_toQidiId(fNum,vKey){const gMap={1:"QFA91",4:"QFA92",7:"QFA90",11:"QFB91",23:"QFC90",39:"QFG90",50:"QFU91"},qMap={1:"QFA02",2:"QFA03",3:"QFA04",4:"QFA05",5:"QFA50",6:"QFA16",7:"QFA00",8:"QFA01",10:"QFS01",11:"QFB54",12:"QFB50",13:"QFB55",14:"QFB53",15:"QFU02",18:"QFB01",19:"QFB02",20:"QFB51",23:"QFC90",24:"QFN20",25:"QFN05",26:"QFN21",27:"QFN12",30:"QFN04",31:"QFN14",32:"QFS03",33:"QFS01",34:"QFC02",35:"QFU03",36:"QFU03",37:"QFT01",38:"QFT02",39:"QFG00",40:"QFG03",41:"QFG02",42:"QFG50",43:"QFG51",44:"QFP01",45:"QFG04",46:"QFP02",47:"QFS01",48:"QFU00",49:"QFU00",50:"QFU01"};return String(vKey)==="0"&&gMap[fNum]?gMap[fNum]:qMap[fNum]||"QFA00"}get selectedVendor(){return this.items[this.selectIndex].vendor}set selectedVendor(t){const s=this.getKeyByValue(this.officialFilasListDictData.vendor_list,t);if(s!==void 0){const fNum=this.variables.filamentSlot[this.selectIndex]||7,qid=this._toQidiId(fNum,s);I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=vendor_slot${this.selectIndex} VALUE=${s}\nSAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="'${qid}'"`)}}get selectedFilament(){return this.items[this.selectIndex].filament}set selectedFilament(t){for(const s in this.officialFilasListDictData)if(s.startsWith("fila")&&this.officialFilasListDictData[s].filament===t){const fNum=parseInt(s.replace("fila",""),10),vKey=this.variables.vendorSlot[this.selectIndex]??1,qid=this._toQidiId(fNum,vKey);I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="'${qid}'"`);break}}get selectedColor(){return this.items[this.selectIndex].color}set selectedColor(t){if(t){const hex=String(t).replace(/^#/,"").toUpperCase();I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot${this.selectIndex} VALUE="['${hex}']"`)}}created(){this.$store.state.printer.officiallFilasList?console.log("officiallFilasList has been initialized"):this.getOfficiallFilasList().then(t=>{this.$store.commit("printer/setOfficiallFilasList",wn.configToDict(t))}).catch(t=>{console.error("Failed to fetch official filas list dict:",t)})}handleColorClick(t){this.selectedColor=t}handleBoxButtonClick(){this.selectIndex=17}showConfig(){this.isConfig=!0}showAuto(){this.isAuto=!0}showHumidityDisplay(){this.isHumidityDisplay=!0}handleClick(t){this.selectIndex=t}handleButtonClick(t){const s=this.selectIndex;if(s===null){console.error("Invalid slot");return}const n=["EJECT_FILAMENT_CONTROL","LOAD_FILAMENT_CONTROL","UNLOAD_FILAMENT_CONTROL"];I.printerGcodeScript(`${n[t-1]} SLOT=${s}`)}handleRfidClick(t){I.printerGcodeScript(`READ_RFID SLOT=${t}`),this.selectIndex=t}'''

    t3 = 'getVariables:r=>{var d,p,h,m;const e=((p=(d=r==null?void 0:r.printer)==null?void 0:d.save_variables)==null?void 0:p.variables)??{},t=e.box_count??0,s=[],n=[],i=[],a=new Array(17).fill(0),o=[],l=e.slot_sync??"",c=[e.color_slot16,e.filament_slot16,e.vendor_slot16],u=parseInt(((h=e.last_load_slot)==null?void 0:h.replace("slot",""))??"0",10);for(const g in e)if(Object.prototype.hasOwnProperty.call(e,g)){if(g.startsWith("color_slot")){const v=parseInt(g.replace("color_slot",""),10);s[v]=parseInt(e[g]??"0",10)}else if(g.startsWith("filament_slot")){const v=parseInt(g.replace("filament_slot",""),10);n[v]=parseInt(e[g]??"0",10)}else if(g.startsWith("vendor_slot")){const v=parseInt(g.replace("vendor_slot",""),10);i[v]=parseInt(e[g]??"0",10)}}for(let g=0;g<16;g++){const v=(m=r==null?void 0:r.printer)==null?void 0:m[`box_stepper slot${g}`];(v==null?void 0:v.runout_button)===0?a[g]=1:a[g]=0}return a[16]=1,{boxCount:t,colorSlot:s,filamentSlot:n,vendorSlot:i,slot:a,valueSlot:o,slotSync:l,rackExtra:c,lastLoadSlot:u}}'
    r3 = r'''getVariables:r=>{var d,p,h,m;const e=((p=(d=r==null?void 0:r.printer)==null?void 0:d.save_variables)==null?void 0:p.variables)??{},t=e.box_count??0,s=[],n=[],i=[],a=new Array(17).fill(0),o=[],l=e.slot_sync??"",u=parseInt(((h=e.last_load_slot)==null?void 0:h.replace("slot",""))??"0",10),qIdMap={QFA02:[1,1],QFA03:[2,1],QFA04:[3,1],QFA05:[4,1],QFA50:[5,1],QFA16:[6,1],QFA00:[7,1],QFA01:[8,1],QFB54:[11,1],QFB50:[12,1],QFB55:[13,1],QFB53:[14,1],QFU02:[15,1],QFB01:[18,1],QFB02:[19,1],QFB51:[20,1],QFN20:[24,1],QFN05:[25,1],QFN21:[26,1],QFN12:[27,1],QFN04:[30,1],QFN14:[31,1],QFS03:[32,1],QFS01:[33,1],QFC02:[34,1],QFU03:[36,1],QFT01:[37,1],QFT02:[38,1],QFG00:[39,1],QFG03:[40,1],QFG02:[41,1],QFG50:[42,1],QFG51:[43,1],QFP01:[44,1],QFG04:[45,1],QFP02:[46,1],QFU00:[49,1],QFU01:[50,1],QFA90:[7,0],QFA91:[1,0],QFA92:[4,0],QFB91:[11,0],QFC90:[23,0],QFG90:[39,0],QFU91:[50,0],QFL30:[7,0],QFL31:[39,0],QFL32:[11,0],QFL10:[7,0],QFL11:[39,0],QFL12:[11,0],QFL60:[7,0],QFL62:[11,0],QFL20:[7,0],QFL22:[11,0],QFL24:[1,0]},qCols=["FAFAFA","060606","D9E3ED","5CF30F","63E492","2850FF","FE98FE","DFD628","228332","99DEFF","1714B0","CEC0FE","CADE4B","1353AB","5EA9FD","A878FF","FE717A","FF362D","E2DFCD","898F9B","6E3812","CAC59F","F28636","B87F2B"],parseCol=val=>{if(typeof val=="number"&&val>=1&&val<=24)return val;let hx=(Array.isArray(val)?String(val[0]??""):String(val??"")).replace(/^#/,"").trim().toUpperCase();if(/^\d+$/.test(hx)){const num=parseInt(hx,10);if(num>=1&&num<=24&&hx.length<=2)return num}if(hx.length===6){const ex=qCols.indexOf(hx);if(ex!==-1)return ex+1;const r1=parseInt(hx.slice(0,2),16),g1=parseInt(hx.slice(2,4),16),b1=parseInt(hx.slice(4,6),16);if(!isNaN(r1)){let best=1,minD=1e9;qCols.forEach((cHex,idx)=>{const d=(r1-parseInt(cHex.slice(0,2),16))**2+(g1-parseInt(cHex.slice(2,4),16))**2+(b1-parseInt(cHex.slice(4,6),16))**2;d<minD&&(minD=d,best=idx+1)});return best}}return 1};for(const g in e)if(Object.prototype.hasOwnProperty.call(e,g)){if(g.startsWith("color_slot")){const v=parseInt(g.replace("color_slot",""),10);s[v]=parseCol(e[g])}else if(g.startsWith("filament_slot")){const v=parseInt(g.replace("filament_slot",""),10),raw=e[g];if(typeof raw=="string"&&qIdMap[raw]){n[v]=qIdMap[raw][0],i[v]=qIdMap[raw][1]}else n[v]=parseInt(raw??"1",10)||1}else if(g.startsWith("vendor_slot")){const v=parseInt(g.replace("vendor_slot",""),10),fRaw=e["filament_slot"+v];if(!(typeof fRaw=="string"&&qIdMap[fRaw]))i[v]=parseInt(e[g]??"0",10)}}const c=[s[16],n[16],i[16]];for(let g=0;g<16;g++){const v=(m=r==null?void 0:r.printer)==null?void 0:m[`box_stepper slot${g}`];(v==null?void 0:v.runout_button)===0?a[g]=1:a[g]=0}return a[16]=1,{boxCount:t,colorSlot:s,filamentSlot:n,vendorSlot:i,slot:a,valueSlot:o,slotSync:l,rackExtra:c,lastLoadSlot:u}}'''

    if js.count(t1) != 1 or js.count(t2) != 1 or js.count(t3) != 1:
        print("[-] Target code blocks not found. File may already be patched or firmware version differs.")
        sys.exit(1)

    patched = js.replace(t1, r1).replace(t2, r2).replace(t3, r3)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(patched)

    print("[✓] Patch successfully applied!")
    print("[*] Don't forget to hard-refresh your browser (Ctrl+F5)!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--restore", "-r", "restore"):
        restore()
    else:
        patch()
```

#### Commande shell universelle pour restaurer (même sans le script) :
Si quelqu'un veut restaurer sans rien d'autre :
```bash
for f in /home/qidi/fluidd/assets/index-*.js.bak; do [ -f "$f" ] && cp -f "$f" "${f%.bak}" && echo "Restored $f"; done
```

---

### 3. Fichier `README.md` (prêt pour GitHub)

Voici le markdown que tu peux copier directement dans ton fichier `README.md` :

````markdown
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
