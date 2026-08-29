#!/usr/bin/env python3
"""
build_drawing_index.py — สร้าง DRAWING_INDEX สำหรับแนบ Assembly Drawing ใน datasheet

สแกนโฟลเดอร์ * Drawing (EA, EAZ, EJ, ES) แล้วสร้าง index:
    รุ่นปั๊ม (key ตาม size ในโปรแกรม) -> list ของ [relative_path, speed]

วิธีใช้:
    python3 scripts/build_drawing_index.py            # rebuild + inject เข้า index.html
    python3 scripts/build_drawing_index.py --dry-run  # แสดงผลอย่างเดียว ไม่แก้ไฟล์

กติกาการจับคู่:
  - EA/EAZ: size ในโปรแกรม "EA250/40" (slash) ↔ ชื่อไฟล์ "EA250_40" (underscore)
  - EJ/ES : size "EJ40-110" / "ES125-230" ใช้ hyphen เหมือนชื่อไฟล์
  - suffix "2900"/"1450" ท้ายชื่อไฟล์ = รูปสำหรับความเร็วรอบนั้น
  - รูป "(unit)" = ชุดสมบูรณ์มีมอเตอร์ (เลือกก่อนรูปตัวเปล่า)
  - fallback ในตัวโปรแกรม: รุ่นลงท้าย N/G/H/A จะลองหารูปตัว base
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(ROOT, "index.html")
FOLDERS = ["EA Drawing", "EAZ Drawing", "EJ Drawing", "ES Drawing"]

START_MARKER = "// ============ DRAWING ATTACH (generated"
END_MARKER = "// ============ /DRAWING ATTACH ============"


def build_index():
    index = {}  # key -> list of [relpath, speed]
    for folder in FOLDERS:
        fdir = os.path.join(ROOT, folder)
        if not os.path.isdir(fdir):
            continue
        for root, _dirs, files in os.walk(fdir):
            for f in sorted(files):
                if not f.lower().endswith(".png"):
                    continue
                rel = os.path.relpath(os.path.join(root, f), ROOT).replace(os.sep, "/")
                speed = ""
                if f.endswith("2900.png") or "/2900/" in rel:
                    speed = "2900"
                elif f.endswith("1450.png") or "/1450/" in rel:
                    speed = "1450"
                unit = "(unit)" in f
                base = re.sub(r"\s*\(.*?\)", "", f)
                base = re.sub(r"2900|1450", "", base)
                base = re.sub(r"_Assembly Drawing.*$", "", base).strip()
                m = re.match(r"^(EAZ?\d+)_(\d.*)$", base)
                key = f"{m.group(1)}/{m.group(2)}" if m else base
                index.setdefault(key, []).append([rel, speed, unit])
    for key in index:
        index[key].sort(key=lambda c: (0 if c[1] else 1, 0 if c[2] else 1))
        index[key] = [[c[0], c[1]] for c in index[key]]
    return index


def render_js(index):
    index_json = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    return f"""
{START_MARKER} {os.path.basename(__file__)}) ============
const DRAWING_INDEX = {index_json};

function resolveDrawingPath(size, speedRpm) {{
  if (!size) return null;
  let list = DRAWING_INDEX[size];
  if (!list) {{
    const stripped = String(size).replace(/[NGHA]$/, '');
    if (stripped !== size) list = DRAWING_INDEX[stripped];
  }}
  if (!list || !list.length) return null;
  const sp = String(speedRpm || '');
  let hit = list.find(c => c[1] === sp) || list.find(c => !c[1]);
  return (hit || list[0])[0];
}}
{END_MARKER}
"""


def inject(html, js):
    if START_MARKER in html:
        start = html.index(START_MARKER)
        end = html.index(END_MARKER) + len(END_MARKER)
        return html[:start] + js.strip() + html[end:]
    anchor = "function SelectionDatasheet({ db, data, setStep, updateData }) {"
    if anchor not in html:
        raise RuntimeError("anchor not found in index.html")
    return html.replace(anchor, js.strip() + "\n\n" + anchor, 1)


def main():
    dry = "--dry-run" in sys.argv
    index = build_index()
    js = render_js(index)
    total = sum(len(v) for v in index.values())
    print(f"index keys: {len(index)} | file entries: {total}")
    if dry:
        print(js[:300] + "...")
        return
    html = open(INDEX_HTML, encoding="utf-8").read()
    open(INDEX_HTML, "w", encoding="utf-8").write(inject(html, js))
    print(f"injected into {INDEX_HTML}")


if __name__ == "__main__":
    main()
