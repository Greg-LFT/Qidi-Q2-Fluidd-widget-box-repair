#!/usr/bin/env python3
"""
Fluidd Material Box Patch for Qidi Q2
Repository: https://github.com/Greg-LFT/Qidi-Q2-Fluidd-widget-box-repair
License: MIT

Developed with AI assistance and validated on Qidi Q2 hardware.
"""

import os
import glob
import sys
import shutil
import re
import subprocess
import tempfile

FLUIDD_DIRS = [
    "/home/qidi/fluidd",
    "/home/mks/fluidd",
    "/usr/share/fluidd"
]


def find_active_bundle():
    for fdir in FLUIDD_DIRS:
        index_html = os.path.join(fdir, "index.html")
        assets_dir = os.path.join(fdir, "assets")
        if os.path.isfile(index_html) and os.path.isdir(assets_dir):
            try:
                with open(index_html, "r", encoding="utf-8") as f:
                    content = f.read()
                match = re.search(r'assets/(index-[^"]+\.js)', content)
                if match:
                    active_path = os.path.join(assets_dir, match.group(1))
                    if os.path.isfile(active_path) or os.path.isfile(active_path + ".bak"):
                        return active_path, assets_dir
            except Exception:
                pass

    for fdir in FLUIDD_DIRS:
        assets_dir = os.path.join(fdir, "assets")
        if os.path.isdir(assets_dir):
            files = glob.glob(os.path.join(assets_dir, "index-*.js"))
            files = [f for f in files if not f.endswith(".bak")]
            if files:
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return files[0], assets_dir

    return None, None


def privileged_copy(src, dst):
    try:
        shutil.copyfile(src, dst)
    except PermissionError:
        print(f"[INFO] Elevating permissions with sudo to write {dst}...")
        try:
            with open("/dev/tty", "r") as tty_in:
                subprocess.run(["sudo", "cp", "-f", src, dst], stdin=tty_in, check=True)
        except Exception as e:
            print(f"[ERROR] Failed to write {dst} via sudo: {e}")
            sys.exit(1)


def restore():
    target_file, assets_dir = find_active_bundle()
    if not assets_dir:
        print("[ERROR] Could not find Fluidd installation directory.")
        sys.exit(1)

    bak_files = glob.glob(os.path.join(assets_dir, "index-*.js.bak"))
    if not bak_files:
        print("[ERROR] No backup file (.bak) found to restore.")
        sys.exit(1)

    for bak in bak_files:
        orig = bak[:-4]
        privileged_copy(bak, orig)
        print(f"[OK] Successfully restored {orig} from backup.")
    print("[INFO] Please hard-refresh your browser (Ctrl+F5).")


def patch():
    target_file, assets_dir = find_active_bundle()
    if not target_file:
        print("[ERROR] Could not detect active Fluidd JavaScript bundle.")
        sys.exit(1)

    print(f"[INFO] Active target bundle detected: {target_file}")

    bak_path = target_file + ".bak"
    if not os.path.exists(bak_path):
        privileged_copy(target_file, bak_path)
        print(f"[OK] Factory backup created: {bak_path}")
    else:
        print(f"[INFO] Existing backup preserved: {bak_path}")

    with open(bak_path, "r", encoding="utf-8") as f:
        js = f.read()

    t1 = (
        'get isOkPrinter(){return this.enableBox===!1?this.$store.state.printer.printer.box_ex'
        'tras.e_endstop_state===1?this.$store.state.printer.printer.box_extras.b_endstop_state'
        '===0?(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.er'
        'ror_msg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t('
        '"app.file_system.tooltip.warning_text"),this.usedExtruders.every(t=>this.selectedValu'
        'eSlot[t]))}'
    )

    r1 = (
        'get isOkPrinter(){const bx=this.$store.state.printer.printer.box_extras||{},mc=(this.'
        '$store.state.printer.printer.multi_color_controller||{}).box||{},fs=this.$store.state'
        '.printer.printer["filament_switch_sensor filament_switch_sensor"]||{},eS=bx.e_endstop'
        '_state!==void 0?bx.e_endstop_state:fs.filament_detected?1:0,bS=bx.b_endstop_state!==v'
        'oid 0?bx.b_endstop_state:mc.b_endstop_state;return this.enableBox===!1?eS===1?bS===0?'
        '(this.error_msg=this.$t("app.file_system.tooltip.warning_text1"),!1):!0:(this.error_m'
        'sg=this.$t("app.file_system.tooltip.warning_text2"),!1):(this.error_msg=this.$t("app.'
        'file_system.tooltip.warning_text"),this.usedExtruders.every(t=>this.selectedValueSlot'
        '[t]))}'
    )

    t2_start = (
        'get items(){var i,a,o,l,c,u,d,p,h;const t=[],s=new Array(16).fill(!1);this.itemsCopy='
        '[];for(let m=0;m<this.boxCount*4;m++){const g=this.variables.slot[m],v=Math.floor(m/4'
        '+1)+String.fromCharCode(m%4+65),y=((i=this.$store.state.printer.printer[`box_stepper '
        'slot${m}`])==null?void 0:i.rfid_state)||"";let C="#00000000",w="",S="";if(g!==0){C=(('
        'a=this.officialFilasListDictData)==null?void 0:a.colordict[String(this.variables.colo'
        'rSlot[m])])??"#00000000";const W="fila"+this.variables.filamentSlot[m]||"";w=((l=(o=t'
        'his.officialFilasListDictData)==null?void 0:o[W])==null?void 0:l.filament)??"",S=((c='
        'this.officialFilasListDictData)==null?void 0:c.vendor_list[this.variables.vendorSlot['
        'm]])??"",this.itemsCopy.push({label:v,color:C,filament:w,vendor:S,isRotating:!1})}con'
        'st E=s[m]=y===1;t[m]={label:v,color'
    )

    t2_end = (
        'handleRfidClick(t){I.printerGcodeScript(`RFID_READ SLOT=slot${t}`),this.selectIndex=t'
        '}'
    )

    idx_start = js.find(t2_start)
    idx_end = js.find(t2_end, idx_start) if idx_start != -1 else -1

    if idx_start == -1 or idx_end == -1:
        print("[ERROR] Target component code blocks not found.")
        sys.exit(1)

    t2 = js[idx_start:idx_end + len(t2_end)]

    r2 = (
        'get items(){const t=[],s=new Array(16).fill(!1);this.itemsCopy=[];const cat=window._q'
        'FilaCat||{},idm=window._qIdMap||{};for(let m=0;m<this.boxCount*4;m++){const g=this.va'
        'riables.slot[m],v=Math.floor(m/4+1)+String.fromCharCode(m%4+65),y=((this.$store.state'
        '.printer.printer[`box_stepper slot${m}`]||{}).rfid_state)||"";let C="#00000000",w="",'
        'S="";if(g!==0){C=(this.variables.colorHexes&&this.variables.colorHexes[m])||((this.of'
        'ficialFilasListDictData&&this.officialFilasListDictData.colordict)?this.officialFilas'
        'ListDictData.colordict[String(this.variables.colorSlot[m])]:"#00000000");const qid=th'
        'is.variables.filamentRaw&&this.variables.filamentRaw[m];if(qid&&idm[qid]){S=idm[qid]['
        '0],w=idm[qid][1]}else{const W="fila"+this.variables.filamentSlot[m];w=(this.officialF'
        'ilasListDictData&&this.officialFilasListDictData[W]&&this.officialFilasListDictData[W'
        '].filament)||(String(qid)||"");S=(this.officialFilasListDictData&&this.officialFilasL'
        'istDictData.vendor_list&&this.officialFilasListDictData.vendor_list[this.variables.ve'
        'ndorSlot[m]])||"Generic"}this.itemsCopy.push({label:v,color:C,filament:w,vendor:S,isR'
        'otating:!1})}const E=s[m]=y===1;t[m]={label:v,color:C,filament:w,vendor:S,isRotating:'
        'E}}let rC="#00000000",rW="",rS="";const rQid=this.variables.filamentRaw&&this.variabl'
        'es.filamentRaw[16];if(rQid&&idm[rQid]){rS=idm[rQid][0],rW=idm[rQid][1]}else{const n="'
        'fila"+this.variables.rackExtra[1];rW=(this.officialFilasListDictData&&this.officialFi'
        'lasListDictData[n]&&this.officialFilasListDictData[n].filament)||(String(rQid)||"");r'
        'S=(this.officialFilasListDictData&&this.officialFilasListDictData.vendor_list&&this.o'
        'fficialFilasListDictData.vendor_list[this.variables.rackExtra[2]])||"Generic"}rC=(thi'
        's.variables.colorHexes&&this.variables.colorHexes[16])||((this.officialFilasListDictD'
        'ata&&this.officialFilasListDictData.colordict)?this.officialFilasListDictData.colordi'
        'ct[this.variables.rackExtra[0]]:"#00000000");t[16]={label:this.$t("app.box.label.rack'
        '").toString(),color:rC,filament:rW,vendor:rS,isRotating:!1},t[17]={label:"",color:"#0'
        '0000000",filament:"",vendor:"",isRotating:!1};return t}get filamentItems(){const v=th'
        'is.selectedVendor||"QIDI",cat=window._qFilaCat||{};return cat[v]?Object.keys(cat[v]):'
        '(cat.QIDI?Object.keys(cat.QIDI):["PLA"])}get vendorItems(){return["QIDI","Generic","B'
        'ambu","Polymaker","HATCHBOX","Overture"]}get colorItems(){const t=new Set;if(!this.of'
        'ficialFilasListDictData)return[""];for(const s in this.officialFilasListDictData.colo'
        'rdict)t.add(this.officialFilasListDictData.colordict[s]);return Array.from(t)}get off'
        'icialFilasListDictData(){return this.$store.state.printer.officiallFilasList}get slot'
        'Sync(){if(typeof this.variables.slotSync=="string"){const s=this.variables.slotSync.m'
        'atch(/^slot(\\d+)$/);if(s){const n=parseInt(s[1],10);if(!isNaN(n))return n}}const t=th'
        'is.$store.state.printer.printer["filament_switch_sensor filament_switch_sensor"];retu'
        'rn this.variables.slotSync==="slot-1"&&t&&t.filament_detected?16:17}get humidity(){va'
        'r t;return this.$store.state.printer.printer["aht20_f heater_box"+(this.tab+1)]&&((t='
        'this.$store.state.printer.printer["aht20_f heater_box"+(this.tab+1)])==null?void 0:t.'
        'humidity)||0}get humidityLevel(){return this.humidity<40?["#FAFAFA","normal"]:this.hu'
        'midity<60?["#5475FF","high"]:["#FF4D4D","overHigh"]}get printerPrinting(){return this'
        '.printerState.toLowerCase()==="printing"}get isOperating(){const t=this.$store.state.'
        'printer.printer.box_extras,m=this.$store.state.printer.printer.multi_color_controller'
        ';return!!(t&&t.box_button_state||m&&m.task&&m.task.flow_id)}get buttonStatus(){const '
        't=new Array(3).fill(!0);if(this.selectIndex<16){const st=this.$store.state.printer.pr'
        'inter["box_stepper slot"+this.selectIndex],hasFila=st&&st.runout_button===0,isLoaded='
        'this.slotSync===this.selectIndex;t[0]=!hasFila,t[1]=!(hasFila&&!isLoaded),t[2]=!(hasF'
        'ila&&isLoaded)}return t}get autoReloadDetect(){return this.$store.getters["printer/ge'
        'tAutoSwitchState"][2]===1}get selectedVendor(){return(this.items[this.selectIndex]&&t'
        'his.items[this.selectIndex].vendor)||"QIDI"}set selectedVendor(t){if(!t)return;const '
        'cat=window._qFilaCat||{},firstFila=cat[t]?Object.keys(cat[t])[0]:"PLA Basic",qid=cat['
        't]?cat[t][firstFila]:"QFA00",vIdx=t==="Generic"?0:1;I.printerGcodeScript(`SAVE_VARIAB'
        'LE VARIABLE=vendor_slot${this.selectIndex} VALUE=${vIdx}\\nSAVE_VARIABLE VARIABLE=fila'
        'ment_slot${this.selectIndex} VALUE="\'${qid}\'"`)}get selectedFilament(){return(this.it'
        'ems[this.selectIndex]&&this.items[this.selectIndex].filament)||""}set selectedFilamen'
        't(t){if(!t)return;const cat=window._qFilaCat||{},v=this.selectedVendor;let qid=cat[v]'
        '&&cat[v][t];if(!qid){for(const k in cat){if(cat[k][t]){qid=cat[k][t];break}}}if(qid){'
        'I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=filament_slot${this.selectIndex} VALUE="'
        '\'${qid}\'"`)}}get selectedColor(){return(this.items[this.selectIndex]&&this.items[this'
        '.selectIndex].color)||""}set selectedColor(t){if(t){const hex=String(t).replace(/^#/,'
        '"").toUpperCase();I.printerGcodeScript(`SAVE_VARIABLE VARIABLE=color_slot${this.selec'
        'tIndex} VALUE="[\'${hex}\']"`)}}created(){this.$store.state.printer.officiallFilasList?'
        'console.log("officiallFilasList has been initialized"):this.getOfficiallFilasList().t'
        'hen(t=>{this.$store.commit("printer/setOfficiallFilasList",wn.configToDict(t))}).catc'
        'h(t=>{console.error("Failed to fetch official filas list dict:",t)})}handleColorClick'
        '(t){this.selectedColor=t}handleBoxButtonClick(){this.selectIndex=17}showConfig(){this'
        '.isConfig=!0}showAuto(){this.isAuto=!0}showHumidityDisplay(){this.isHumidityDisplay=!'
        '0}handleClick(t){this.selectIndex=t}handleButtonClick(t){const s=this.selectIndex;if('
        's===null){console.error("Invalid slot");return}const n=["EJECT_FILAMENT_CONTROL","LOA'
        'D_FILAMENT_CONTROL","UNLOAD_FILAMENT_CONTROL"];I.printerGcodeScript(`${n[t-1]} SLOT=$'
        '{s}`)}handleRfidClick(t){I.printerGcodeScript(`READ_RFID SLOT=${t}`),this.selectIndex'
        '=t}'
    )

    t3 = (
        'getVariables:r=>{var d,p,h,m;const e=((p=(d=r==null?void 0:r.printer)==null?void 0:d.'
        'save_variables)==null?void 0:p.variables)??{},t=e.box_count??0,s=[],n=[],i=[],a=new A'
        'rray(17).fill(0),o=[],l=e.slot_sync??"",c=[e.color_slot16,e.filament_slot16,e.vendor_'
        'slot16],u=parseInt(((h=e.last_load_slot)==null?void 0:h.replace("slot",""))??"0",10);'
        'for(const g in e)if(Object.prototype.hasOwnProperty.call(e,g)){if(g.startsWith("color'
        '_slot")){const v=parseInt(g.replace("color_slot",""),10);s[v]=parseInt(e[g]??"0",10)}'
        'else if(g.startsWith("filament_slot")){const v=parseInt(g.replace("filament_slot","")'
        ',10);n[v]=parseInt(e[g]??"0",10)}else if(g.startsWith("vendor_slot")){const v=parseIn'
        't(g.replace("vendor_slot",""),10);i[v]=parseInt(e[g]??"0",10)}}for(let g=0;g<16;g++){'
        'const v=(m=r==null?void 0:r.printer)==null?void 0:m[`box_stepper slot${g}`];(v==null?'
        'void 0:v.runout_button)===0?a[g]=1:a[g]=0}return a[16]=1,{boxCount:t,colorSlot:s,fila'
        'mentSlot:n,vendorSlot:i,slot:a,valueSlot:o,slotSync:l,rackExtra:c,lastLoadSlot:u}}'
    )

    r3 = (
        'getVariables:r=>{window._qFilaCat={"QIDI":{"PLA Basic":"QFA00","PLA Matte Basic":"QFA'
        '01","PLA Rapido":"QFA02","PLA Rapido Matte":"QFA03","PLA Rapido Metal":"QFA04","PLA S'
        'ilk":"QFA05","WOOD Rapido":"QFA16","PLA-CF":"QFA50","ASA":"QFB01","ASA-Aero":"QFB02",'
        '"ABS-GF":"QFB50","ASA-CF20 Core":"QFB51","ABS Odorless":"QFB53","ABS Rapido":"QFB54",'
        '"ABS Rapido Metal":"QFB55","PC/ABS-FR":"QFC02","PETG Basic":"QFG00","PETG Rapido":"QF'
        'G02","PETG Tough":"QFG03","PETG Translucent":"QFG04","PETG-CF":"QFG50","PETG-GF":"QFG'
        '51","PAHT-CF":"QFN04","PA6-CF":"QFN05","PA12-CF":"QFN12","PAHT-GF":"QFN14","UltraPA":'
        '"QFN20","UltraPA-CF25":"QFN21","PPS-CF":"QFP01","PPS-GF":"QFP02","Support For PET/PA"'
        ':"QFS01","Support For PAHT":"QFS03","PET-CF":"QFT01","PET-GF":"QFT02","TPU-Aero":"QFU'
        '00","TPU 95A-HF":"QFU01","TPU-GF":"QFU02","PEBA 95A":"QFU03"},"Generic":{"ABS":"QFB91'
        '","PC":"QFC90","PETG":"QFG90","PLA":"QFA90","PLA Silk":"QFA92","PLA+":"QFA91","TPU 95'
        'A":"QFU91"},"Bambu":{"ABS":"QFL32","PETG":"QFL31","PLA":"QFL30"},"HATCHBOX":{"ABS":"Q'
        'FL12","PETG":"QFL11","PLA":"QFL10"},"Overture":{"ABS":"QFL62","PLA":"QFL60"},"Polymak'
        'er":{"ABS":"QFL22","PLA":"QFL20","PLA-HT":"QFL24"}};window._qIdMap={"QFA00":["QIDI","'
        'PLA Basic"],"QFA01":["QIDI","PLA Matte Basic"],"QFA02":["QIDI","PLA Rapido"],"QFA03":'
        '["QIDI","PLA Rapido Matte"],"QFA04":["QIDI","PLA Rapido Metal"],"QFA05":["QIDI","PLA '
        'Silk"],"QFA16":["QIDI","WOOD Rapido"],"QFA50":["QIDI","PLA-CF"],"QFB01":["QIDI","ASA"'
        '],"QFB02":["QIDI","ASA-Aero"],"QFB50":["QIDI","ABS-GF"],"QFB51":["QIDI","ASA-CF20 Cor'
        'e"],"QFB53":["QIDI","ABS Odorless"],"QFB54":["QIDI","ABS Rapido"],"QFB55":["QIDI","AB'
        'S Rapido Metal"],"QFC02":["QIDI","PC/ABS-FR"],"QFG00":["QIDI","PETG Basic"],"QFG02":['
        '"QIDI","PETG Rapido"],"QFG03":["QIDI","PETG Tough"],"QFG04":["QIDI","PETG Translucent'
        '"],"QFG50":["QIDI","PETG-CF"],"QFG51":["QIDI","PETG-GF"],"QFN04":["QIDI","PAHT-CF"],"'
        'QFN05":["QIDI","PA6-CF"],"QFN12":["QIDI","PA12-CF"],"QFN14":["QIDI","PAHT-GF"],"QFN20'
        '":["QIDI","UltraPA"],"QFN21":["QIDI","UltraPA-CF25"],"QFP01":["QIDI","PPS-CF"],"QFP02'
        '":["QIDI","PPS-GF"],"QFS01":["QIDI","Support For PET/PA"],"QFS03":["QIDI","Support Fo'
        'r PAHT"],"QFT01":["QIDI","PET-CF"],"QFT02":["QIDI","PET-GF"],"QFU00":["QIDI","TPU-Aer'
        'o"],"QFU01":["QIDI","TPU 95A-HF"],"QFU02":["QIDI","TPU-GF"],"QFU03":["QIDI","PEBA 95A'
        '"],"QFB91":["Generic","ABS"],"QFC90":["Generic","PC"],"QFG90":["Generic","PETG"],"QFA'
        '90":["Generic","PLA"],"QFA92":["Generic","PLA Silk"],"QFA91":["Generic","PLA+"],"QFU9'
        '1":["Generic","TPU 95A"],"QFL32":["Bambu","ABS"],"QFL31":["Bambu","PETG"],"QFL30":["B'
        'ambu","PLA"],"QFL12":["HATCHBOX","ABS"],"QFL11":["HATCHBOX","PETG"],"QFL10":["HATCHBO'
        'X","PLA"],"QFL62":["Overture","ABS"],"QFL60":["Overture","PLA"],"QFL22":["Polymaker",'
        '"ABS"],"QFL20":["Polymaker","PLA"],"QFL24":["Polymaker","PLA-HT"]};var d,p,h,m;const '
        'e=((p=(d=r==null?void 0:r.printer)==null?void 0:d.save_variables)==null?void 0:p.vari'
        'ables)??{},t=e.box_count??0,s=[],n=[],i=[],fRaw=[],cHex=[],a=new Array(17).fill(0),o='
        '[],l=e.slot_sync??"",u=parseInt(((h=e.last_load_slot)==null?void 0:h.replace("slot","'
        '"))??"0",10),qCols=["FAFAFA","060606","D9E3ED","5CF30F","63E492","2850FF","FE98FE","D'
        'FD628","228332","99DEFF","1714B0","CEC0FE","CADE4B","1353AB","5EA9FD","A878FF","FE717'
        'A","FF362D","E2DFCD","898F9B","6E3812","CAC59F","F28636","B87F2B"],parseCol=val=>{let'
        ' hx=(Array.isArray(val)?String(val[0]??""):String(val??"")).replace(/^#/,"").trim().t'
        'oUpperCase();if(/^\\d+$/.test(hx)){const num=parseInt(hx,10);if(num>=1&&num<=24&&hx.le'
        'ngth<=2)return[num,"#"+qCols[num-1]]}if(hx.length===6){const ex=qCols.indexOf(hx);if('
        'ex!==-1)return[ex+1,"#"+hx];return[1,"#"+hx]}return[1,"#FAFAFA"]};for(const g in e)if'
        '(Object.prototype.hasOwnProperty.call(e,g)){if(g.startsWith("color_slot")){const v=pa'
        'rseInt(g.replace("color_slot",""),10),[cIdx,cHx]=parseCol(e[g]);s[v]=cIdx,cHex[v]=cHx'
        '}else if(g.startsWith("filament_slot")){const v=parseInt(g.replace("filament_slot",""'
        '),10),raw=e[g];fRaw[v]=raw;if(typeof raw=="string"&&window._qIdMap[raw]){n[v]=1;i[v]='
        'window._qIdMap[raw][0]==="Generic"?0:1}else{n[v]=parseInt(raw??"1",10)||1}}else if(g.'
        'startsWith("vendor_slot")){const v=parseInt(g.replace("vendor_slot",""),10);if(i[v]=='
        '=void 0)i[v]=parseInt(e[g]??"0",10)}}const c=[s[16],n[16],i[16]];for(let g=0;g<16;g++'
        '){const v=(m=r==null?void 0:r.printer)==null?void 0:m[`box_stepper slot${g}`];(v==nul'
        'l?void 0:v.runout_button)===0?a[g]=1:a[g]=0}return a[16]=1,{boxCount:t,colorSlot:s,fi'
        'lamentSlot:n,vendorSlot:i,filamentRaw:fRaw,colorHexes:cHex,slot:a,valueSlot:o,slotSyn'
        'c:l,rackExtra:c,lastLoadSlot:u}}'
    )

    if js.count(t1) != 1 or js.count(t3) != 1:
        print("[ERROR] Target code blocks not found. Firmware version may differ.")
        sys.exit(1)

    patched = js.replace(t1, r1).replace(t2, r2).replace(t3, r3)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
        tmp.write(patched)
        tmp_path = tmp.name

    try:
        privileged_copy(tmp_path, target_file)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    print("[OK] Extended multi-vendor patch successfully applied.")
    print("[INFO] Supported vendors: QIDI, Generic, Bambu, Polymaker, HATCHBOX, Overture.")
    print("[INFO] Please hard-refresh your browser (Ctrl+F5).")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--restore", "-r", "restore"):
        restore()
    else:
        patch()
