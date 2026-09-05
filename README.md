# FlowCore Selection Program (Complete Edition)

โปรแกรมเลือกปั๊ม (Pump Selection Program) ของ FlowCore — standalone HTML
ใช้ React + Tailwind (CDN) ข้อมูลปั๊มฝังในไฟล์ เปิดด้วยเบราว์เซอร์ได้เลย

**เวอร์ชัน Complete:** ครอบคลุมทุกรุ่นที่มี performance curve จากแคตตาล็อก manufacturer
ใช้ **curve จริงของทุกขนาดใบพัด + interpolation ระหว่างใบพัด** — ไม่ใช้ Affinity Law ในการ trim ใบพัด
(รุ่นก่อนหน้าใช้ Affinity ในการ trim ซึ่งค่าจริงไม่เป็นไปตามนั้น)

## ฟีเจอร์หลัก

- ป้อน Duty Point (flow m³/h หรือ L/s, head, tolerance ฯลฯ) → ค้นหาปั๊มที่ครอบคลุม duty (interpolate ระหว่างใบพัด)
  (dropdown series แสดงคำอธิบายประเภทปั๊ม + กรองความถี่ 50/60 Hz; tolerance ±5/10/20/50%)
- แสดง curve ที่ **interpolate ตาม duty** (เส้น Operate หนา) + ค่า Eff/Power/NPSHr @ duty จากข้อมูลจริง
- รองรับปั๊ม 3 ประเภท: ใบพัดปรับได้ (EA/EAZ/EH/ES/EGM → หาเส้นผ่านศูนย์กลาง), ใบพัดตรึง (EJ → หาความเร็วรอบ), curve เดียว (FDL/FTD)
- **Dropdown "Curve Display" 3 โหมด** (หน้า Adjust Curve — แทนที่การแสดงเส้นใบพัดทุกใบ + checkbox VSD แบบเดิม):
  1. **Max / Min Impeller + Operating** — เส้นใบ Max/Min (เส้นประ) + เส้น Operate (เส้นทึบ)
  2. **Operating Curve only** — เส้น Operate เส้นเดียว
  3. **Operating + Inverter (60–90%)** — เส้น Operate (ทึบ) + เส้น Inverter 60/70/80/90% (เส้นประ)
     คำนวณด้วย Affinity Law: Q∝r, H∝r², P∝r³, η คงที่, NPSH∝r² — **วาดครบ H-Q / Efficiency / Power / NPSH**
- **Dropdown เลือกขนาดมอเตอร์ (kW)** — ค่าเริ่มต้น Auto = ขนาดที่แนะนำจากกำลังสูงสุดของ curve
  ถ้าเลือก kW เล็กลง จุดกราฟที่กำลังเกินมอเตอร์ = **เส้นประแดง** + เส้นระดับ kW
- ค่าไฟฟ้าโดยประมาณ IE1–IE4 (ใช้ efficiency ตาม class ของมอเตอร์แต่ละตัว)
- Datasheet พร้อม Assembly Drawing + Export HTML / Print PDF
  (กราฟใน Datasheet แสดงโหมด Max/Min + Operating เสมอ)
- โลโก้ FlowCore + บริษัท Siamraj Public Company Limited.

## วิธีใช้งาน

เปิด `index.html` ด้วยเบราว์เซอร์ (Chrome/Edge แนะนำ)

> ⚠️ ต้องเปิดจากที่อยู่เดียวกับโฟลเดอร์ `Pump Drawing/` ถึงจะเห็นรูป Assembly Drawing

### Host ขึ้นเว็บ (GitHub Pages / เว็บเซิร์ฟเวอร์)

อัปโหลดไฟล์และโฟลเดอร์ทั้งหมดด้วยกัน:

```
FlowCore-Selection-Program/
├── index.html
├── Pump Drawing/      # รูป Assembly Drawing (~1,283 ไฟล์)
├── db/
│   └── db_v2.json     # ฐานข้อมูล (สำหรับ rebuild)
├── README.md
├── CODE_GUIDE.md       # คู่มือสถาปัตยกรรมโค้ดสำหรับนักพัฒนา / AI agent
```

## โครงสร้างข้อมูล (db/db_v2.json)

```json
{
  "companyLogo": "data:image/png;base64,...",      // โลโก้ FlowCore
  "modelGroups": [
    {
      "id": "S2", "seriesId": 2, "modelName": "EA (1450 rpm)",
      "materials": [{ "code": "CBSM", "impeller": "...", "casing": "...", ... }],
      "seals": [{ "type": "Mechanical Seal", "material": "Carbon/SiC/Viton" }],
      "connections": ["GB/T17241.6 PN16"],
      "sizes": [
        {
          "size": "EA32/13", "displayName": "EA32-13", "pumpId": 1,
          "speed": 1450, "freq": 50, "maxDia": 139, "minDia": 100,
          "variantType": "dia",          // dia | speed | none
          "allow": { "minQ": 2.7, "maxQ": 10.8 },
          "bep": { "q": 8.36, "e": 61.6 },
          "vsdSpeeds": [1305, 1160, ...],
          "diaCurves": [
            { "dia": 139, "qh": [[Q,H],...], "qe": [[Q,E]], "qp": [[Q,P]], "npsh": [[Q,NPSH]] },
            { "dia": 130, "qh": [...], "qe": [...], "qp": [...] }, ...
          ],
          "drawing": "Pump Drawing/2_EA32-13.png"
        }
      ]
    }
  ]
}
```

- **Flow หน่วย L/s ภายใน** (×3.6 = m³/h)
- `variantType`: `dia` = ใบพัดปรับได้ (ค่า curve = mm) · `speed` = ใบพัดตรึง (ค่า curve = rpm เช่น EJ)
  · `none` = curve เดียว (FDL/FTD)
- `allow` = ช่วง Flow ที่วิ่งได้ (Allowable Region จาก manufacturer)
- E/P ของใบพัดกลาง = **ค่าจริง** (ไม่ประมาณ) — NPSH มีเฉพาะใบพัด max/min (มีกลไก fallback ไปใช้เส้นอ้างอิง)

## หมายเหตุ

- series EA(1450)/EA(2900) ฯลฯ ที่ซ้ำ = รุ่น drive type ต่างกัน ข้อมูลคนละชุด
- FDL/FTD (ปั๊มหลายชั้น/ท่อ) ไม่มีใบพัดปรับ — จับคู่ duty แบบ curve เดียว ± tolerance
- บางรุ่นไม่มีรูปในแคตตาล็อก — Datasheet ซ่อน section อัตโนมัติ
- สคริปต์สกัดข้อมูลเดิม: `/EIFEL-Extraction/` (phase1-7) ใช้ rebuild DB จากแคตตาล็อก manufacturer (อยู่เครื่อง ไม่ได้อยู่ใน repo นี้)

> 📖 นักพัฒนาหรือ AI agent ที่จะแก้โค้ด อ่าน **`CODE_GUIDE.md`** ก่อน — มีสถาปัตยกรรม ฟังก์ชันหลัก และกติกาการแก้/ทดสอบครบ
