# FlowCore Selection Program

โปรแกรมเลือกปั๊ม (Pump Selection Program) ของ FlowCore — standalone HTML ไฟล์เดียว
ใช้ React + Tailwind (CDN) ข้อมูลปั๊ม (DB) ฝังอยู่ในไฟล์ ไม่ต้องติดตั้งอะไร เปิดด้วยเบราว์เซอร์ได้เลย

ฟีเจอร์หลัก:
- ป้อน Duty Point (flow, head, NPSHa ฯลฯ) → เลือกรุ่น → ปรับกราฟ → เลือก Option → **Datasheet**
- **เลือกขนาดมอเตอร์ (kW) ได้จาก Dropdown** — ค่าเริ่มต้นเป็น Auto (ขนาดที่แนะนำจาก Max Curve Power) ถ้าเลือก kW เล็กลง (แข่งราคา) จุดบนกราฟที่กำลังเกินมอเตอร์จะแสดงเป็น**เส้นประแดง** + เส้นระดับ kW บน Power panel
- Datasheet พร้อม **Assembly Drawing แนบอัตโนมัติ** (ดูหัวข้อด้านล่าง)
- Export Datasheet เป็น PDF (ปุ่ม Print) หรือ HTML (ปุ่ม Save HTML)

## วิธีใช้งาน

เปิด `index.html` ด้วยเบราว์เซอร์ (Chrome/Edge แนะนำ)

> ⚠️ ต้องเปิดจากที่อยู่เดียวกับโฟลเดอร์ `* Drawing/` ถึงจะเห็นรูป Assembly Drawing
> (โปรแกรมอ้างอิงรูปด้วย relative path)

### Host ขึ้นเว็บ (GitHub Pages / เว็บเซิร์ฟเวอร์)

ต้องอัปโหลดไฟล์และโฟลเดอร์ทั้งหมดด้วยกัน:

```
FlowCore-Selection-Program/
├── index.html
├── EA Drawing/
├── EAZ Drawing/
├── EJ Drawing/
└── ES Drawing/
```

## โครงสร้าง

```
├── index.html                     # ตัวโปรแกรม (ไฟล์เดียวจบ)
├── EA Drawing/                    # รูป Assembly Drawing รุ่น EA (มี 2900/, 1450/, Bare Pump/)
├── EAZ Drawing/                   # รุ่น EAZ
├── EJ Drawing/                    # รุ่น EJ
├── ES Drawing/                    # รุ่น ES (มี 2900/, 1450/, Bare Pump/)
├── db/
│   └── flowcore_db.json           # ฐานข้อมูลอ้างอิง (ตัวโปรแกรมฝัง DB ไว้แล้ว)
└── scripts/
    └── build_drawing_index.py     # สคริปต์สร้าง DRAWING_INDEX จากโฟลเดอร์รูป
```

## ระบบแนบ Assembly Drawing

- โปรแกรมมี `DRAWING_INDEX` ฝังใน `index.html` — map **รุ่นปั๊ม → path รูป** (สร้างอัตโนมัติจากโฟลเดอร์รูป)
- Datasheet แสดง section **"6. Assembly Drawing"** ขึ้นหน้า A4 ใหม่ (แยกจากตาราง/กราฟ)
- กติกาการจับคู่รุ่นกับรูป:
  - EA/EAZ: size ในโปรแกรมใช้ `/` (เช่น `EA250/40`) ↔ ชื่อไฟล์ใช้ `_` (`EA250_40_Assembly Drawing.png`)
  - EJ/ES: ใช้ `-` เหมือนกันทั้งสองฝั่ง (เช่น `ES125-230`)
  - ไฟล์ที่ลงท้าย `2900` / `1450` = รูปสำหรับความเร็วรอบนั้น (เลือกตาม RPM ที่เลือกในโปรแกรม)
  - ชอบรูป `(unit)` (ชุดมีมอเตอร์) ก่อนรูปตัวเปล่า
  - รุ่นที่ลงท้าย N/G/H/A ถ้าหารูปตรงตัวไม่ได้ → fallback ใช้รูปตัว base (เช่น `ES125-230N` → รูป `ES125-230`)
  - **รุ่นที่ไม่มีรูป → ซ่อน section อัตโนมัติ** (ไม่โชว์กล่องว่าง)

### เพิ่ม/แก้ไขรูป Drawing

1. วาง PNG ลงในโฟลเดอร์ตามรุ่น (ตั้งชื่อตามกติกาด้านบน)
2. รันเพื่อ rebuild index:

   ```bash
   python3 scripts/build_drawing_index.py
   ```

   (ใช้ `--dry-run` เพื่อดูผลลัพธ์ก่อน inject)

## หมายเหตุ

- ไฟล์เวอร์ชันเก่า, ไฟล์ PDF ขนาดใหญ่ (เช่น E-Catalog ~60MB), และไฟล์ทำงานอื่น ๆ **ไม่ได้อยู่ใน repo นี้**
  (GitHub จำกัดไฟล์ใหญ่สุด 100MB — ถ้าอยากเก็บ PDF ใช้ [Git LFS](https://git-lfs.com/) หรือ GitHub Releases แทน)
- รูป PNG บางไฟล์ใหญ่ (~7MB) ถ้าอยากให้เว็บโหลดเร็วขึ้น แนะนำบีบอัด/ลดขนาดรูปก่อนอัปโหลด
- ข้อมูลบริษัท/โลโก้อยู่ใน `companyLogo` ฝังใน DB ในตัวไฟล์ (แก้ใน Management Flow ของโปรแกรม)
