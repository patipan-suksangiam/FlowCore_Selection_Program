# CODE_GUIDE.md — คู่มือโค้ด FlowCore Selection Program

> สำหรับ **AI agent / นักพัฒนาที่จะแก้ไขโค้ด** ใน repo นี้ (รวมถึงอ่านเพื่อทำความเข้าใจ)
> อ่านจบก่อนแก้ไฟล์ `index.html` — ไฟล์ใหญ่พิเศษ มีกับดักหลายจุด (ดูหัวข้อ [กติกาแก้ไฟล์](#กติกาแก้ไฟล์-สำคัญมาก))

## TL;DR

- **โปรแกรมเดียวในไฟล์เดียว:** `index.html` (8.3 MB) = React 18 + Tailwind + Babel standalone (CDN ทั้งหมด) + ฐานข้อมูล JSON ฝังในไฟล์ + โค้ด JSX ทั้งแอปใน `<script type="text/babel">` — **ไม่มีการ build** เปิดเบราว์เซอร์ได้เลย
- หน้าที่: เลือกปั๊มหอยโข่ง FlowCore จาก duty point (Q, H) โดยเทียบ **performance curve จริงทุกขนาดใบพัด** + interpolation ระหว่างใบพัด
- หน่วย flow **ภายใน = L/s** เสมอ (UI แสดง m³/h ได้)
- แก้ UI/logic ใน babel script ส่วนเดียว; **ห้ามแตะ** `<script id="pump-db">` (JSON 8.2 MB อยู่บรรทัดเดียว)

## โครงสร้างไฟล์

```
├── index.html          # ทั้งแอป (โค้ด + ข้อมูล)
├── db/db_v2.json       # ฐานข้อมูลต้นทาง (ฝังใน index.html แล้ว) สำหรับ rebuild
├── Pump Drawing/       # รูป Assembly Drawing (~1,283 PNG) — path ถูกอ้างใน DB (size.drawing)
├── README.md           # ภาพรวมสำหรับผู้ใช้
└── CODE_GUIDE.md       # เอกสารนี้
```

`index.html` เรียงตามลำดับ:
1. `<head>`: Tailwind CDN, React 18 UMD, `@babel/standalone` (register preset `react-classic`), Font Awesome
2. `<div id="root">`
3. `<script type="application/json" id="pump-db">` — **JSON ฐานข้อมูล 8.2 MB ในบรรทัดเดียว** (โหลดด้วย `loadDb()`)
4. `<script type="text/babel" data-presets="react-classic,env">` — **โค้ดแอปทั้งหมด (~970 บรรทัด)** ที่นี่คือที่แก้

## โครงสร้างข้อมูล (DB)

```js
DB = { companyLogo: 'data:...', modelGroups: [ { id:'S2', seriesId, modelName:'EA (1450 rpm)',
  materials:[{code,impeller,casing,shaft,wearRing}], seals:[{type,material}], connections:['...'],
  sizes: [ { size:'EA32/13', displayName, pumpId, speed, freq, maxDia, minDia,
             variantType: 'dia'|'speed'|'none',
             allow:{minQ,maxQ},            // L/s — allowable region
             bep:{q,e},
             vsdSpeeds:[...],              // ความเร็ว VSD ของรุ่น (ข้อมูลเก่า ยังมี)
             diaCurves: [ { dia:139, qh:[[Q,H],...], qe:[[Q,E]], qp:[[Q,P]], npsh:[[Q,NPSH]] } ],
             drawing: 'Pump Drawing/2_EA32-13.png' } ] } ] }
```

- `variantType`: `dia` = ใบพัดปรับได้ (หา**ขนาดเส้นผ่านศูนย์กลาง** mm) · `speed` = ใบพัดตรึง (หา**rpm** เช่น EJ) · `none` = curve เดียว (FDL/FTD)
- `npsh` มีเฉพาะบางใบพัด (มักใบ Max) — มีระบบ fallback (ดู `npshRefOf`)
- Q ทุกค่าใน DB เป็น L/s

## ขั้นตอน UI (5 ขั้นตอน)

`App` → 2 views: `HomeView` (หน้าแรก นับ series/รุ่นจาก DB) และ `SelectionFlow` (โปรแกรมคัดเลือก)

`SelectionFlow` state: `step` (0–4), `duty` (flow/head/unit/tolerance/density/viscosity/npsha/elecRate/groups/freq), `cands`, `selGroup/selSize`, `motorKw`, `opts`
- **STEP_NAMES** = Duty Input → Select Model → Adjust Curve → Options → Datasheet

| ขั้น | Component | หน้าที่ |
|---|---|---|
| 1 | `DutyStep` | เลือก series (checkbox กลุ่ม + กรอง 50/60 Hz) + ใส่ Q, H, tolerance, density, viscosity, NPSHa, ค่าไฟ → `doSearch()` |
| 2 | `TableStep` | ตารางรุ่นที่เข้าได้ (เรียง efficiency จากมาก→น้อย, โชว์ทีละ 40) → `handleSelect(group,size)` |
| 3 | `CurveStep` | ปรับ Q/H ละเอียด + เลือก kW มอเตอร์ + **Dropdown Curve Display** + `PumpChart` |
| 4 | `OptionsStep` | เลือก Material / Seal / Connection |
| 5 | `DatasheetStep` | Datasheet + Performance Curve + Assembly Drawing + Export HTML/Print |

`doSearch()`: กลุ่มที่เลือก → `groupPumpsForDuty()` → เรียง eff → ถ้าไม่มี `cands` ขึ้นเตือนให้ปรับ duty

## แกนหลักการคัดเลือก (อ่านโค้ดก่อนแก้!)

ทุกฟังก์ชันอยู่ใน babel script ก่อน `UI Shell`:

1. **`normCurves(sz)`** → แปลง `diaCurves` เป็น `[{v, qh, qe, qp, npsh}]`, ลบจุด NaN, **เรียง v น้อย→มาก** (curves[0]=Min, [สุดท้าย]=Max)
2. **`findPair(curves, q, H, tol)`** — ใจกลาง:
   - head ที่ duty flow ของใบ Max = `hHi`; ถ้า `H > hHi` → **ไม่เข้า** (ต้องรุ่นใหญ่)
   - หาใบพัดคู่ที่ head คร่อม H (`hA ≤ H ≤ hB` ที่ flow q) → `t` = interpolate, `vReq` = dia/rpm ระหว่างคู่
   - curve เดียว / ช่วงขอบ (runout): ยอมภายใน tolerance (`H ≥ hHi*(2−tol)`) แล้วบังคับใช้ใบ Max
   - tol จาก UI = 1.05/1.1/1.2/1.5 (±5/10/20/50%)
3. **`buildSelCurve(A, B, t, npshRef)`** → curve Operate (interpolate qh ระหว่าง A/B แบบ index-aligned); `qe/qp/npsh` ยืมชุด A; ผลลัพธ์ `{qh, qe, qp, npsh, A, B, t, qEnd, npshRef}`
4. **`selVal(sel, q, 'e'|'p'|'n')`** → ค่า Eff/Power/NPSH ที่ flow q บน curve ที่เลือก (interpolate ระหว่าง A/B ของค่าจริงนั้น; NPSH fallback ไป `npshRef` ถ้าไม่มี)
5. **`evaluatePump(sz, q, H, tol)`** → ตรวจ `allow` window (allowable region) + เรียก findPair/buildSelCurve/selVal; **กฎ completeness: ถ้า eff/pwr/npsh ตัวใด null → รุ่นนั้นไม่เข้า** (Step 2 แสดงเฉพาะรุ่นข้อมูลครบ)
6. **`groupPumpsForDuty(groups, ...)`** → loop ทุกรุ่น → เก็บที่เข้า → เรียง eff มาก→น้อย

ตัวช่วย: `lin(a,b,t)`, `clamp(v,a,b)`, `interpXY(arr,x,clampLo)` (ไม่ extrapolate — NPSH clamp ด้าน low ได้), `hAt/eAt/pAt/nAt`, `curveEndQ/curveStartQ`, `npshRefOf(curves)` (เลือกเส้น npsh ของใบที่ใหญ่สุดที่มีข้อมูล)

## โหมดแสดงกราฟ (Curve Display) — แก้ไขล่าสุด 2026-09-05

เดิมเคย: วาด curve **ทุกใบพัด** (รก ~5–47 เส้น) + checkbox "VSD Curve Preview"
ปัจจุบัน (CurveStep): **dropdown `curveMode`** = `'maxmin' | 'operate' | 'inverter'` (default `maxmin`):

| โหมด | วาดอะไร |
|---|---|
| `maxmin` | ใบ Min (เส้นประเทา `#64748b`) + ใบ Max (เส้นประน้ำเงิน `#2563eb`) + เส้น Operate (ทึบดำ `#0f172a`) |
| `operate` | เส้น Operate อย่างเดียว |
| `inverter` | เส้น Operate (ทึบ) + เส้น Inverter ที่ 60/70/80/90% (เส้นประส้ม `#f59e0b`) |

**Inverter คำนวณจาก Affinity Law** (`invCurves` ใน `PumpChart`, ratios `[0.9, 0.8, 0.7, 0.6]` บน curve Operate):
- Q′ = Q·r · H′ = H·r² · P′ = P·r³ · **η′ ≈ η (คงที่)** · NPSH′ = NPSH·r²
- วาดครบ 4 panel: H-Q (dash `2 4`, opacity .8, มีป้าย %) + Eff/Power/NPSH (dash `1 3`, opacity .6)
- หมายเหตุ: เป็นค่าประมาณ Affinity (ต่างจากตัวหลักที่ใช้ curve จริง) — โหมดนี้มีไว้พรีวิว

`PumpChart` รับ prop `curveMode`; Datasheet (Step 5) ส่ง `curveMode="maxmin"` เสมอ
Legend ใต้กราฟปรับตามโหมด; mode `maxmin` ใช้ `curves[0]`/`curves[length-1]` เป็น Min/Max (ต้องเชื่อว่า normCurves เรียงแล้ว)

## PumpChart — แผนผังพิกัด (ถ้าจะแก้กราฟ)

SVG viewBox `620 × (bottomY+30)`; panel ซ้อนกันแนวตั้ง:
- Head: `headH=170`, ล่าง `headBot=210` · Eff: `effH=90`, ล่าง `effBot=330` · Power: `powH=90`, ล่าง `powBot=450` · NPSH: `npshH=55`, ล่าง `npshBot=535`
- `toX(q)`: L/s→พิกัด (scale x = Q·3.6/maxFlow); `toYH/toYE/toYP/toYN`: ค่า→พิกัด y ของแต่ละ panel
- แกน x = Flow (m³/h), y หลัก = Head; tick ใช้ step กลม (1/2/5×10ⁿ)
- **Red zone มอเตอร์:** `segs(pts, xy)` แยก path เป็น run (เส้นทึบ/สีปกติ) vs over-motor (เส้นประแดง `#ef4444`) เทียบ `effMotor`; มีเส้นระดับ "Motor X kW"
- เส้น Operate หนา 2.6 สี `#0f172a`; duty point = จุดกลมแดง + crosshair + วงกลมเล็กบน Eff/Power/NPSH panel

## มอเตอร์

- `IEC_MOTORS` = ขนาดมาตรฐาน IEC; `getRecMotor(kw)` = เลือกตัวที่เล็กที่สุด ≥ กำลังที่ต้องการ
- กำลังสูงสุดของ curve Operate (`maxP`) → `recMotor`; UI: dropdown เลือกเองได้ (Auto = recMotor)
- `motorEffApprox(kw, cls)` = ประมาณ eff มอเตอร์ IE1–IE4 (log fit) ใช้คิดค่าไฟรายชั่วโมง

## ฟอร์แมต/สไตล์

- JSX inline ใน babel script — **indent 2 spaces**, ฟังก์ชัน component ชื่อ CamelCase, state ผ่าน `useState` ใน `SelectionFlow` ส่ง props ลงลูก
- ข้อความ UI ภาษาอังกฤษ; คอมเมนต์/เอกสารภาษาไทยได้
- ตัวเลขที่อ่านจาก curve เป็น float จริง; อย่าไปปัดกลางทาง (ปัดตอนแสดงผล)

## กติกาแก้ไฟล์ (สำคัญมาก)

1. **`index.html` ใหญ่ 8.3 MB — ห้ามอ่าน/เขียนทั้งไฟล์แบบ dumb edit** (เช่น sed ทั่วไฟล์). ใช้ targeted edit (ค้น anchor สั้นๆ ที่ unique แล้วแทนที่) เสมอ
2. **ห้ามแตะ `<script id="pump-db">`** — JSON 8.2 MB อยู่บรรทัดเดียว; ถ้าเปิดอ่านทั้งไฟล์จะกิน context มหาศาล — ใช้ slice เฉพาะช่วง หรือ grep เฉพาะคำ
3. **โค้ดแก้แล้วต้องตรวจ syntax ทุกครั้ง** เพราะไม่มี build step กันพลาด:
   ```bash
   # extract babel script แล้ว transform ผ่าน @babel/preset-react — ต้องไม่มี error
   python3 -c 'import re;d=open("index.html",encoding="utf-8").read();m=re.search(r"<script type=\"text/babel\"[^>]*>(.*?)</script>",d,re.DOTALL);open("/tmp/app.jsx","w").write(m.group(1))'
   npx --yes @babel/cli --presets @babel/preset-react /tmp/app.jsx -o /tmp/app.out.js
   ```
4. **ทดสอบจริงในเบราว์เซอร์** (เปิด file:// หรือ local server) — โหลด CDN ต้องมีเน็ตครั้งแรก; ต้องอยู่คู่โฟลเดอร์ `Pump Drawing/` ถึงเห็น drawing
5. หลังแก้ ตรวจด้วย diff ว่าเปลี่ยนเฉพาะที่ตั้งใจ (ไฟล์มี backup ประวัติใน `.gitignore`: `*_BACKUP*.html`, `index.backup-*.html`)
6. commit message ใช้ conventional style ภาษาอังกฤษสั้นๆ (ตัวอย่าง: `feat: ...`, `fix: ...`)

## ประวัติการแก้ที่เกี่ยวข้อง (2026-09-05)

- **`feat`:** เปลี่ยนหน้า Adjust Curve จาก (วาดทุกใบ + checkbox VSD) → **dropdown Curve Display 3 โหมด**; โหมด inverter ใช้ Affinity 60/70/80/90% และวาด Eff/Power/NPSH ของ inverter ด้วย
- **`feat`:** Datasheet กราฟใช้โหมด maxmin เสมอ
- (ก่อนหน้า) `fix:` ค่าไฟ datasheet IE1–IE4 คิด per-class แทนค่าเดียว

## หมายเหตุพิเศษสำหรับ agent ที่จะ "ทำความเข้าใจ"

- ตอนอ่านโค้ด ให้ **แยก babel script ออกมาก่อน** (คำสั่งข้อ 3) แล้วอ่านเฉพาะส่วนนั้น — อย่าอ่านทั้ง index.html
- ถ้าจะแก้เรื่อง curve ระวัง: เส้นที่ "interpolate ระหว่างใบพัด" (Operate) คำนวณจาก **head** เป็นหลัก; Eff/Power ใช้วิธี `selVal` (interpolate ค่าจริงระหว่างใบ A/B ณ flow เดียวกัน) — ไม่ใช่ Affinity (ยกเว้นโหมด inverter preview)
- การเรียงผลลัพธ์ในตารางใช้ efficiency @ duty; ถ้าแก้เกณฑ์นี้ ระวัง `groupPumpsForDuty` บรรทัด sort
