

```
╔════════════════════════════════════════════╗
║                                            ║
║       T H A I T R A N S L A T E R X        ║
║                                            ║
╚════════════════════════════════════════════╝
```

### 🎮 Real-time screen translator for BlueStacks via ADB

**Capture → OCR → Translate → Overlay** — automatically, in your language of choice.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](#)
[![BlueStacks](https://img.shields.io/badge/For-BlueStacks-7c3aed?style=for-the-badge)](#)
[![Status](https://img.shields.io/badge/Status-Active-10b981?style=for-the-badge)](#)
[![Author](https://img.shields.io/badge/Made%20by-GoatPicnic-fbbf24?style=for-the-badge)](#)

</div>

---

## ◈ ABOUT

> **ThaiTranslaterX** เป็นเครื่องมือแปลภาษาแบบเรียลไทม์ ออกแบบมาเพื่อใช้กับเกมหรือแอปที่รันบน **BlueStacks**
> มันจะ**จับภาพหน้าจอ**ผ่าน ADB, **อ่านตัวอักษร**ด้วย OCR, **แปลภาษา**อัตโนมัติ แล้วโชว์ผลลัพธ์เป็น**แถบลอย (overlay)** ทับหน้าจอแบบไม่รบกวนการเล่น

ไม่ต้องก้มไปแคปหน้าจอ ไม่ต้อง copy-paste ไปแปลเอง — เลือกกรอบสนทนาทีเดียว แล้วให้มันทำงานของมันไป

---

## ◈ FEATURES

```diff
+ 📡  Auto-detect ADB port ของ BlueStacks (สแกนหา port ที่ใช้งานได้อัตโนมัติ)
+ 📸  Capture หน้าจอผ่าน ADB (เร็ว, แม่นยำ) หรือผ่าน MSS (สำรอง)
+ 🔍  OCR หลายภาษา ด้วย Tesseract (EN / TH / JP / CN / KR / FR / DE / ES / VI)
+ 🌐  แปลภาษาอัตโนมัติด้วย Google Translate (deep-translator)
+ 🪟  Overlay แถบลอย แสดงผลแปล แบบ topmost, ลากย้ายตำแหน่งได้
+ 🖱️  เลือกกรอบ (region) ของกล่องข้อความได้ด้วยตัวเอง แบบลากเมาส์
+ ⚙️  ปรับ interval การสแกน, จำ config อัตโนมัติ (config.json)
+ 🎨  UI ธีม Dark / Gaming สไตล์ Cyberpunk
```

---

## ◈ TECH STACK

| ส่วนประกอบ | เครื่องมือ |
|---|---|
| ภาษาหลัก | `Python 3.14` |
| GUI | `tkinter` / `ttk` |
| Screen Capture | `mss`, `ADB (HD-Adb.exe)` |
| Image Processing | `OpenCV`, `Pillow`, `NumPy` |
| OCR | `pytesseract` (Tesseract-OCR) |
| Translation | `deep-translator` (Google Translate) |
| Target Platform | `BlueStacks` (Windows) |

---

## ◈ REQUIREMENTS

ก่อนรัน ต้องมีของพวกนี้ติดตั้งไว้ในเครื่องก่อน:

- **Python 3.14+** → https://www.python.org/downloads/
- **BlueStacks** (BlueStacks 5 แนะนำ, เปิด Android Debug Bridge ใน Settings)
- **Tesseract-OCR** สำหรับ Windows → ติดตั้งที่ `C:\Program Files\Tesseract-OCR\tesseract.exe`
  - ดาวน์โหลด: https://github.com/UB-Mannheim/tesseract/wiki
  - อย่าลืมติดตั้ง **language pack** ของภาษาที่จะใช้ (เช่น `tha`, `jpn`, `chi_sim`)

---

## ◈ INSTALLATION

```bash
# 1. Clone โปรเจคนี้
git clone https://github.com/GoatPicnic/ThaiTranslaterX.git
cd ThaiTranslaterX

# 2. ติดตั้ง dependencies
pip install -r requirements.txt
```

**requirements.txt**
```
mss
Pillow
pytesseract
deep-translator
pywin32
numpy
opencv-python
```

---

## ◈ SETUP — BLUESTACKS ADB

1. เปิด BlueStacks → **Settings → Advanced → Android Debug Bridge** → เปิดใช้งาน
2. จด **port** ที่ BlueStacks แสดง (ปกติคือ `5555` หรือ `5556`)
3. เปิดโปรแกรมนี้ แล้วกด **🔍 Auto-Detect** — มันจะสแกนหา port ให้อัตโนมัติ
4. หรือใส่ port เองที่ช่อง **ADB Port**

> 💡 ถ้าเปิด BlueStacks หลาย instance พร้อมกัน แต่ละตัวจะใช้ port ต่างกัน (5555, 5557, 5559, ...)

---

## ◈ USAGE

```bash
python translator_app.py
```

หรือบน Windows ดับเบิลคลิก:

```bash
run.bat
```

### วิธีใช้งาน

```
┌─────────────────────────────────────────────┐
│  1. เลือกภาษาต้นทาง → ภาษาปลายทาง            │
│  2. กด "Select Region" แล้วลากเมาส์          │
│     คลุมกล่องข้อความ/บทสนทนาในเกม            │
│  3. ตั้งค่า ADB port (หรือ Auto-Detect)      │
│  4. ปรับ scan interval ตามต้องการ            │
│  5. กด ▶ RUN — แล้วรอผลแปลที่แถบลอยด้านบน    │
└─────────────────────────────────────────────┘
```

โปรแกรมจะ capture → OCR → translate วนลูปตาม interval ที่ตั้งไว้ และแสดงผลเฉพาะเมื่อข้อความเปลี่ยน (ไม่แปลซ้ำข้อความเดิม)

---

## ◈ CONFIGURATION

ตั้งค่าทั้งหมดจะถูกบันทึกอัตโนมัติไว้ที่ `config.json`:

```json
{
  "region": [393, 629, 1132, 770],
  "use_adb": true,
  "interval": 2.0,
  "src_lang": "English",
  "dest_lang": "Thai (ภาษาไทย)",
  "adb_port": "5556"
}
```

| คีย์ | คำอธิบาย |
|---|---|
| `region` | กรอบพิกัดหน้าจอ `[left, top, right, bottom]` ที่จะ capture |
| `use_adb` | `true` = capture ผ่าน ADB (เร็วกว่า), `false` = capture ผ่าน MSS |
| `interval` | ความถี่ในการสแกนหน้าจอ (วินาที) |
| `src_lang` / `dest_lang` | ภาษาต้นทาง / ปลายทาง |
| `adb_port` | port ของ BlueStacks ADB |

---

## ◈ SUPPORTED LANGUAGES

```
English  ·  ภาษาไทย  ·  日本語  ·  中文  ·  한국어  ·  Français  ·  Deutsch  ·  Español  ·  Vietnamese
```

---

## ◈ PROJECT STRUCTURE

```
ThaiTranslaterX/
├── translator_app.py     # โค้ดหลัก — GUI, capture, OCR, translate, overlay
├── config.json            # การตั้งค่าที่บันทึกอัตโนมัติ
├── requirements.txt        # Python dependencies
└── run.bat                 # สคริปต์รันด่วนบน Windows
```

---

## ◈ TROUBLESHOOTING

| ปัญหา | วิธีแก้ |
|---|---|
| Auto-Detect หา port ไม่เจอ | เช็คว่าเปิด ADB ใน BlueStacks Settings แล้ว, ลองใส่ port เอง |
| OCR อ่านข้อความไม่ออก / ผิด | ตรวจสอบว่าติดตั้ง language pack ของ Tesseract ตรงกับภาษาต้นทาง |
| แปลแล้วได้ error | เน็ตหลุด หรือ Google Translate จำกัด request ชั่วคราว ลองใหม่อีกครั้ง |
| Capture ไม่ติด | ลองสลับ `Use ADB` ปิด/เปิด เพื่อใช้ MSS แทน |

---

<div align="center">

```
◈ ThaiTranslaterX V1.0 · For BlueStacks · Developed by GoatPicnic ◈
```

**Made with ☕ and too many ADB ports**

</div>
