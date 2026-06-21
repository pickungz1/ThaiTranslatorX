# -*- coding: utf-8 -*-
# ThaiTranslaterX V1.0
# For BlueStack | Developed by GoatPicnic
import sys, io, os, time, json, threading, subprocess, traceback, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr  = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image
import mss, cv2, numpy as np, pytesseract
from deep_translator import GoogleTranslator

APP_NAME    = "ThaiTranslaterX"
APP_VERSION = "V1.0"
DEVELOPER   = "GoatPicnic"
FOR_LABEL   = "For BlueStack"

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ADB — หา exe จากหลาย path
ADB_PATHS = [
    r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
    r"C:\Program Files (x86)\BlueStacks_nxt\HD-Adb.exe",
    r"C:\Program Files\BlueStacks\HD-Adb.exe",
    r"C:\ProgramData\BlueStacks_nxt\Engine\UserData\InputMapper\HD-Adb.exe",
    "adb",   # ถ้ามี Android SDK ใน PATH
]
def _find_adb():
    for p in ADB_PATHS:
        if p == "adb" or os.path.exists(p):
            return p
    return None
ADB_EXE = _find_adb() or ADB_PATHS[0]

ADB_HOST   = "127.0.0.1"
ADB_TARGET = f"{ADB_HOST}:5556"   # จะถูก override โดย auto-detect
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# port ที่ BlueStack มักใช้
ADB_SCAN_PORTS = [5555, 5556, 5557, 5558, 5559, 5037, 5554, 5560, 5600, 5700]

def adb_detect_port(on_progress=None):
    """
    สแกน port ที่ BlueStack ใช้ — คืน port ที่ทำงานได้ หรือ None
    on_progress(msg) เรียกระหว่างสแกน
    """
    global ADB_TARGET
    if not ADB_EXE or not os.path.exists(ADB_EXE) and ADB_EXE != "adb":
        return None

    for port in ADB_SCAN_PORTS:
        target = f"{ADB_HOST}:{port}"
        if on_progress:
            on_progress(f"Scanning port {port}...")
        try:
            # ลอง connect
            subprocess.run([ADB_EXE,"connect",target],
                           capture_output=True, timeout=3)
            # ลอง screencap เล็กๆ เพื่อยืนยัน
            r = subprocess.run(
                [ADB_EXE,"-s",target,"exec-out","screencap","-p"],
                capture_output=True, timeout=6)
            if r.stdout and len(r.stdout) > 500:
                ADB_TARGET = target
                print(f"[ADB] Found BlueStack on port {port}")
                return port
        except Exception:
            pass
    return None

# ── Language definitions ─────────────────────────────────────
# (display name, google-translate code, tesseract lang code)
LANGUAGES = {
    "English":            ("en",  "eng"),
    "Thai (ภาษาไทย)":    ("th",  "tha"),
    "Japanese (日本語)":  ("ja",  "jpn"),
    "Chinese (中文)":     ("zh-CN","chi_sim"),
    "Korean (한국어)":    ("ko",  "kor"),
    "French":             ("fr",  "fra"),
    "German":             ("de",  "deu"),
    "Spanish":            ("es",  "spa"),
    "Vietnamese":         ("vi",  "vie"),
}

LANG_NAMES   = list(LANGUAGES.keys())
DEFAULT_SRC  = "English"
DEFAULT_DEST = "Thai (ภาษาไทย)"

# ── Color palette (Gaming dark) ──────────────────────────────
BG     = "#080812"
PANEL  = "#0e0e20"
CARD   = "#14142a"
BORDER = "#1e1e42"
PURPLE = "#7c3aed"
PURPLH = "#9d5cf6"
CYAN   = "#22d3ee"
GREEN  = "#10b981"
RED    = "#ef4444"
AMBER  = "#f59e0b"
TEXT   = "#f1f5f9"
DIM    = "#475569"
GOLD   = "#fbbf24"

# ════════════════════════════════════════════════════════════
#  CAPTURE
# ════════════════════════════════════════════════════════════
def adb_grab(target=None):
    t = target or ADB_TARGET
    try:
        r = subprocess.run(
            [ADB_EXE,"-s",t,"exec-out","screencap","-p"],
            capture_output=True, timeout=8)
        if r.stdout and len(r.stdout) > 500:
            return Image.open(io.BytesIO(r.stdout)).convert("RGB")
    except Exception as e:
        print(f"[ADB] {e}")
    return None

def mss_grab(region):
    try:
        with mss.mss() as s:
            l,t,r,b = region
            shot = s.grab({"left":l,"top":t,"width":r-l,"height":b-t})
            return Image.frombytes('RGB', shot.size, shot.rgb)
    except Exception as e:
        print(f"[MSS] {e}")
        return None

def grab(region, use_adb=True):
    if use_adb:
        img = adb_grab()
        if img:
            l,t,r,b = region
            W,H = img.size
            return img.crop((max(0,l), max(0,t), min(r,W), min(b,H)))
    return mss_grab(region)

# ════════════════════════════════════════════════════════════
#  OCR
# ════════════════════════════════════════════════════════════
def do_ocr(img, src_lang="English"):
    """อ่านตัวอักษรจากภาพ — รองรับหลายภาษา"""
    try:
        tess_lang = LANGUAGES.get(src_lang, ("en","eng"))[1]
        arr  = np.array(img)
        arr  = cv2.resize(arr, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        _, thr     = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        thr_inv    = cv2.bitwise_not(thr)

        best = ""
        for img_arr, psm in [(thr,6),(thr_inv,6),(thr,7),(thr_inv,7)]:
            try:
                raw = pytesseract.image_to_string(
                    Image.fromarray(img_arr),
                    config=f"--oem 3 --psm {psm} -l {tess_lang}"
                )
                lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 2]
                text  = " ".join(lines).strip()
                if len(text) > len(best):
                    best = text
            except Exception:
                # fallback ถ้า language pack ไม่มี
                try:
                    raw = pytesseract.image_to_string(
                        Image.fromarray(img_arr),
                        config=f"--oem 3 --psm {psm} -l eng"
                    )
                    lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 2]
                    text  = " ".join(lines).strip()
                    if len(text) > len(best):
                        best = text
                except Exception:
                    pass

        # ล้าง noise characters
        best = re.sub(r"[^\w\s.,!?'\"()\-:;\u0e00-\u0e7f\u3000-\u9fff\uac00-\ud7a3]","",best)
        best = " ".join(best.split())
        print(f"[OCR] lang={tess_lang} -> '{best}'")
        return best
    except Exception as e:
        print(f"[OCR Error] {e}")
        return ""

# ════════════════════════════════════════════════════════════
#  TRANSLATE
# ════════════════════════════════════════════════════════════
_cache = {}
def translate(text, src="en", dest="th"):
    if not text.strip():
        return ""
    key = f"{src}>{dest}:{text}"
    if key in _cache:
        return _cache[key]
    try:
        r = GoogleTranslator(source=src, target=dest).translate(text)
        if r:
            _cache[key] = r
            return r
        return "[ไม่ได้รับผลการแปล]"
    except Exception as e:
        return f"[แปลไม่ได้: {e}]"

# ════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════
def load_cfg():
    d = {"region":None,"use_adb":True,"interval":2.5,
         "src_lang":DEFAULT_SRC,"dest_lang":DEFAULT_DEST}
    if os.path.exists(CONFIG_FILE):
        try: d.update(json.load(open(CONFIG_FILE,encoding='utf-8')))
        except: pass
    return d

def save_cfg(d):
    json.dump(d, open(CONFIG_FILE,'w',encoding='utf-8'),
              ensure_ascii=False, indent=2)

# ════════════════════════════════════════════════════════════
#  REGION SELECTOR
# ════════════════════════════════════════════════════════════
def pick_region(root):
    result = [None]
    root.withdraw()
    time.sleep(0.15)
    top = tk.Toplevel()
    top.attributes('-fullscreen',True,'-alpha',0.2,'-topmost',True)
    top.configure(bg='black')
    canvas = tk.Canvas(top, bg='black', cursor='crosshair', highlightthickness=0)
    canvas.pack(fill='both', expand=True)
    tk.Label(top,
        text="Drag mouse over the dialog box  ·  ESC to cancel",
        font=('Segoe UI',13,'bold'), fg='#00ffcc', bg='black'
    ).place(relx=0.5, rely=0.05, anchor='center')
    st = {"x0":0,"y0":0,"rect":None}
    def press(e):  st["x0"],st["y0"]=e.x,e.y
    def drag(e):
        if st["rect"]: canvas.delete(st["rect"])
        st["rect"]=canvas.create_rectangle(st["x0"],st["y0"],e.x,e.y,
            outline='#00ffcc',width=2,fill='#00ffcc',stipple='gray25')
    def release(e):
        x1,y1=min(st["x0"],e.x),min(st["y0"],e.y)
        x2,y2=max(st["x0"],e.x),max(st["y0"],e.y)
        if abs(x2-x1)>15 and abs(y2-y1)>15:
            result[0]=(x1,y1,x2,y2)
        top.destroy()
    canvas.bind('<ButtonPress-1>',press)
    canvas.bind('<B1-Motion>',drag)
    canvas.bind('<ButtonRelease-1>',release)
    top.bind('<Escape>',lambda e: top.destroy())
    top.wait_window()
    root.deiconify()
    return result[0]

# ════════════════════════════════════════════════════════════
#  OVERLAY  (floating translation bar)
# ════════════════════════════════════════════════════════════
class Overlay(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.overrideredirect(True)
        self.attributes('-topmost',True,'-alpha',0.93)
        self.configure(bg="#050510")
        sw = self.winfo_screenwidth()
        w, h = 860, 74
        self.geometry(f"{w}x{h}+{(sw-w)//2}+4")

        outer = tk.Frame(self, bg="#050510")
        outer.pack(fill='both', expand=True, padx=2, pady=2)

        # Top accent line
        tk.Frame(outer, bg=PURPLE, height=2).pack(fill='x')

        inner = tk.Frame(outer, bg=PANEL, padx=10, pady=5)
        inner.pack(fill='both', expand=True)

        top_row = tk.Frame(inner, bg=PANEL)
        top_row.pack(fill='x')

        self.badge = tk.Label(top_row,
            text=f"◈ {APP_NAME}",
            font=('Segoe UI',7,'bold'), fg=PURPLE, bg=PANEL)
        self.badge.pack(side='left')

        self.lang_badge = tk.Label(top_row,
            text="EN → TH",
            font=('Segoe UI',7,'bold'), fg=CYAN, bg=PANEL, padx=6)
        self.lang_badge.pack(side='left')

        self.en_var = tk.StringVar(value="")
        tk.Label(top_row, textvariable=self.en_var,
                 font=("Segoe UI",7,"italic"), fg=DIM, bg=PANEL,
                 anchor='e').pack(side='right')

        # Main translation
        self.th_var = tk.StringVar(value="⏳  Waiting for scan...")
        tk.Label(inner, textvariable=self.th_var,
                 font=("Sarabun",12,"bold"), fg="#93c5fd", bg=PANEL,
                 anchor='w', wraplength=840, justify='left'
                 ).pack(fill='both', expand=True)

        # Drag
        for w in [inner, top_row]:
            w.bind('<ButtonPress-1>',  lambda e: setattr(self,'_dx',e.x_root-self.winfo_x()) or setattr(self,'_dy',e.y_root-self.winfo_y()))
            w.bind('<B1-Motion>',      lambda e: self.geometry(f"+{e.x_root-self._dx}+{e.y_root-self._dy}"))
        self._dx = self._dy = 0

    def update(self, en, th, src_name="EN", dest_name="TH"):
        short = en[:100]+"..." if len(en)>100 else en
        self.en_var.set(f"src: {short}" if en else "")
        self.th_var.set(th or "⏳  Waiting...")
        self.lang_badge.config(text=f"{src_name} → {dest_name}")

# ════════════════════════════════════════════════════════════
#  MAIN APP
# ════════════════════════════════════════════════════════════
class App:
    def __init__(self, root):
        self.root    = root
        self.cfg     = load_cfg()
        self.region  = tuple(self.cfg["region"]) if self.cfg["region"] else None
        self.running = False
        self.ov      = Overlay(root)
        self._build()
        self._refresh_lbl()

    # ─── BUILD UI ───────────────────────────────────────────
    def _build(self):
        r = self.root
        r.title(f"{APP_NAME} {APP_VERSION}")
        r.configure(bg=BG)
        r.geometry("480x660")
        r.resizable(False, False)

        # ── HEADER ──────────────────────────────────────────
        hdr = tk.Frame(r, bg=PURPLE, height=58)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)

        left_hdr = tk.Frame(hdr, bg=PURPLE)
        left_hdr.pack(side='left', padx=14, pady=6)

        tk.Label(left_hdr, text=f"◈  {APP_NAME}",
                 font=('Segoe UI', 16, 'bold'),
                 fg='white', bg=PURPLE).pack(anchor='w')
        tk.Label(left_hdr, text=f"{APP_VERSION}  ·  {FOR_LABEL}",
                 font=('Segoe UI', 8),
                 fg='#ddd6fe', bg=PURPLE).pack(anchor='w')

        tk.Label(hdr, text="🎮", font=('Segoe UI', 22), bg=PURPLE
                 ).pack(side='right', padx=14)

        # ── BODY ────────────────────────────────────────────
        body = tk.Frame(r, bg=BG)
        body.pack(fill='both', expand=True, padx=18, pady=12)

        # ── Language Selection ───────────────────────────────
        self._sec(body, "🌐  Language / ภาษา")

        lang_row = tk.Frame(body, bg=BG)
        lang_row.pack(fill='x', pady=(0,4))

        # Source language
        src_col = tk.Frame(lang_row, bg=BG)
        src_col.pack(side='left', fill='x', expand=True, padx=(0,6))
        tk.Label(src_col, text="Source (ภาษาต้นทาง)",
                 font=('Segoe UI',8), fg=DIM, bg=BG).pack(anchor='w')
        self.src_var = tk.StringVar(value=self.cfg.get("src_lang", DEFAULT_SRC))
        src_cb = ttk.Combobox(src_col, textvariable=self.src_var,
                               values=LANG_NAMES, state='readonly',
                               font=('Segoe UI',10), width=18)
        src_cb.pack(fill='x', pady=(2,0))

        # Arrow
        tk.Label(lang_row, text="→", font=('Segoe UI',14,'bold'),
                 fg=CYAN, bg=BG).pack(side='left', padx=4, pady=(14,0))

        # Dest language
        dst_col = tk.Frame(lang_row, bg=BG)
        dst_col.pack(side='left', fill='x', expand=True, padx=(6,0))
        tk.Label(dst_col, text="Translate to (แปลเป็น)",
                 font=('Segoe UI',8), fg=DIM, bg=BG).pack(anchor='w')
        self.dst_var = tk.StringVar(value=self.cfg.get("dest_lang", DEFAULT_DEST))
        dst_cb = ttk.Combobox(dst_col, textvariable=self.dst_var,
                               values=LANG_NAMES, state='readonly',
                               font=('Segoe UI',10), width=18)
        dst_cb.pack(fill='x', pady=(2,0))

        tk.Frame(body, bg=BORDER, height=1).pack(fill='x', pady=(10,14))

        # ── Dialog Region ────────────────────────────────────
        self._sec(body, "📍  Dialog Box Region")
        self.rlbl = tk.Label(body, text="Not selected",
                              font=('Segoe UI',9), fg=DIM, bg=BG, anchor='w')
        self.rlbl.pack(fill='x', pady=(0,6))
        self._btn(body, "🖱   Select Region  —  drag over dialog box",
                  self._pick).pack(fill='x', pady=(0,14))

        # ── ADB Connection ───────────────────────────────────
        self._sec(body, "🔌  BlueStack ADB Connection")

        adb_row = tk.Frame(body, bg=BG)
        adb_row.pack(fill='x', pady=(0,4))

        self.adb_var = tk.BooleanVar(value=self.cfg.get("use_adb", True))
        tk.Checkbutton(adb_row, text="Use ADB  (faster, recommended)",
                       variable=self.adb_var,
                       font=('Segoe UI',9), fg=TEXT, bg=BG,
                       selectcolor=CARD, activebackground=BG
                       ).pack(side='left')

        # Port input
        port_row = tk.Frame(body, bg=BG)
        port_row.pack(fill='x', pady=(0,4))
        tk.Label(port_row, text="ADB Port:",
                 font=('Segoe UI',9), fg=DIM, bg=BG).pack(side='left')
        self.port_var = tk.StringVar(value=str(self.cfg.get("adb_port", 5556)))
        port_entry = tk.Entry(port_row, textvariable=self.port_var,
                              font=('Segoe UI',10), bg=CARD, fg=TEXT,
                              insertbackground=TEXT, relief='flat',
                              width=7)
        port_entry.pack(side='left', padx=6)
        tk.Label(port_row,
                 text="(BlueStack 5: 5555/5556  |  multiple: 5557,5559...)",
                 font=('Segoe UI',7), fg=DIM, bg=BG).pack(side='left')

        # Auto-detect + status
        detect_row = tk.Frame(body, bg=BG)
        detect_row.pack(fill='x', pady=(0,2))
        self.adb_status = tk.Label(detect_row,
                text=f"Port: {self.port_var.get()}  (not verified)",
                font=('Segoe UI',8,'bold'), fg=AMBER, bg=BG)
        self.adb_status.pack(side='left')
        detect_btn = tk.Button(detect_row,
                text="🔍 Auto-Detect",
                command=self._auto_detect_adb,
                font=('Segoe UI',8), fg=TEXT, bg=CARD,
                activebackground=PURPLH, relief='flat',
                cursor='hand2', padx=8, pady=2)
        detect_btn.bind('<Enter>', lambda e: detect_btn.config(bg=PURPLH))
        detect_btn.bind('<Leave>', lambda e: detect_btn.config(bg=CARD))
        detect_btn.pack(side='right')

        tk.Frame(body, bg=BORDER, height=1).pack(fill='x', pady=(8,12))

        # ── Scan Interval ────────────────────────────────────
        iv_row = tk.Frame(body, bg=BG)
        iv_row.pack(fill='x', pady=(0,14))
        tk.Label(iv_row, text="Scan every",
                 font=('Segoe UI',9), fg=DIM, bg=BG).pack(side='left')
        self.iv = tk.DoubleVar(value=self.cfg.get("interval", 2.5))
        tk.Scale(iv_row, from_=1, to=6, resolution=0.5, orient='horizontal',
                 variable=self.iv, bg=BG, fg=TEXT, troughcolor=CARD,
                 highlightthickness=0, bd=0, length=160
                 ).pack(side='left', padx=6)
        tk.Label(iv_row, text="sec",
                 font=('Segoe UI',9), fg=DIM, bg=BG).pack(side='left')

        # ── Status ───────────────────────────────────────────
        self._sec(body, "📡  Status")
        self.slbl = tk.Label(body, text="● Ready",
                              font=('Segoe UI', 10, 'bold'),
                              fg=GREEN, bg=BG, anchor='w')
        self.slbl.pack(fill='x', pady=(0,10))

        # ── RUN button ───────────────────────────────────────
        self.rbtn = tk.Button(body,
            text="▶   RUN  —  Start Auto Translate",
            command=self._toggle,
            font=('Segoe UI', 13, 'bold'),
            fg='white', bg=GREEN,
            activebackground='#059669',
            relief='flat', cursor='hand2', pady=12)
        self.rbtn.pack(fill='x')

        # ── FOOTER ───────────────────────────────────────────
        foot = tk.Frame(r, bg=CARD, height=26)
        foot.pack(fill='x', side='bottom')
        foot.pack_propagate(False)
        tk.Label(foot,
            text=f"{APP_NAME} {APP_VERSION}  ·  {FOR_LABEL}  ·  Developed by {DEVELOPER}",
            font=('Segoe UI', 8), fg=DIM, bg=CARD
        ).pack(side='left', padx=12, pady=4)
        tk.Label(foot, text="◈", font=('Segoe UI',10),
                 fg=PURPLE, bg=CARD).pack(side='right', padx=12)

        # Style combobox
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox',
            fieldbackground=CARD, background=PANEL,
            foreground=TEXT, selectbackground=PURPLE,
            arrowcolor=CYAN)

    def _sec(self, p, title):
        tk.Label(p, text=title, font=('Segoe UI',9,'bold'),
                 fg=CYAN, bg=BG, anchor='w').pack(fill='x', pady=(0,3))
        tk.Frame(p, bg=BORDER, height=1).pack(fill='x', pady=(0,7))

    def _btn(self, p, text, cmd):
        b = tk.Button(p, text=text, command=cmd,
                      font=('Segoe UI',10), fg=TEXT, bg=CARD,
                      activebackground=PURPLH, relief='flat',
                      cursor='hand2', pady=7)
        b.bind('<Enter>', lambda e: b.config(bg=PURPLH))
        b.bind('<Leave>', lambda e: b.config(bg=CARD))
        return b

    # ─── REGION ─────────────────────────────────────────────
    def _pick(self):
        def _do():
            reg = pick_region(self.root)
            if reg:
                self.region = reg
                self.cfg["region"] = list(reg)
                save_cfg(self.cfg)
                self.root.after(0, self._refresh_lbl)
                self._sts("Region selected ✓  Press RUN to start", GREEN)
        threading.Thread(target=_do, daemon=True).start()

    def _refresh_lbl(self):
        if self.region:
            l,t,r,b = self.region
            self.rlbl.config(
                text=f"({l}, {t})  →  ({r}, {b})   |   {r-l} × {b-t} px",
                fg=GREEN)
        else:
            self.rlbl.config(text="Not selected — click button above", fg=AMBER)

    # ─── RUN / STOP ─────────────────────────────────────────
    def _toggle(self):
        if not self.running:
            if not self.region:
                messagebox.showwarning(APP_NAME,
                    "Please select the dialog box region first!\n"
                    "Click 'Select Region' and drag over the text box.")
                return
            self.running = True
            self.rbtn.config(text="⏹   STOP  —  Stop",
                             bg=RED, activebackground='#b91c1c')
            self._sts("Auto translate running...", CYAN)
            threading.Thread(target=self._loop, daemon=True).start()
        else:
            self.running = False
            self.rbtn.config(text="▶   RUN  —  Start Auto Translate",
                             bg=GREEN, activebackground='#059669')
            self._sts("Stopped", DIM)
            self.ov.update("", "⏹  Stopped")

    # ─── MAIN LOOP ──────────────────────────────────────────
    def _loop(self):
        last_en = ""
        while self.running:
            try:
                # อัปเดต port ตามที่กรอก
                global ADB_TARGET
                try:
                    ADB_TARGET = f"{ADB_HOST}:{int(self.port_var.get())}"
                except Exception:
                    pass

                src_name  = self.src_var.get()
                dest_name = self.dst_var.get()
                src_code  = LANGUAGES.get(src_name,  ("en","eng"))[0]
                dest_code = LANGUAGES.get(dest_name, ("th","tha"))[0]

                self._sts("📷  Capturing...", AMBER)
                img = grab(self.region, self.adb_var.get())
                if not img:
                    self._sts("Capture failed — retrying...", RED)
                    time.sleep(2); continue

                self._sts("🔍  Reading text...", AMBER)
                en = do_ocr(img, src_lang=src_name)
                if not en or len(en.strip()) < 3:
                    self._sts("No text found", DIM)
                    time.sleep(self.iv.get()); continue

                if en.strip() == last_en.strip():
                    self._sts("Same text — waiting...", DIM)
                    time.sleep(self.iv.get()); continue
                last_en = en

                self._sts("🌐  Translating...", CYAN)
                translated = translate(en, src=src_code, dest=dest_code)

                # แสดงชื่อภาษาสั้นๆ
                src_short  = src_name.split(" ")[0][:2].upper()
                dest_short = dest_name.split(" ")[0][:2].upper()

                self._sts(f"✓  Translated  ({src_name} → {dest_name})", GREEN)
                self.root.after(0, lambda e=en, t=translated, s=src_short, d=dest_short:
                    self.ov.update(e, t, s, d))

            except Exception as e:
                print(f"[Loop Error] {e}")
                self._sts(str(e)[:55], RED)
                time.sleep(2)

            time.sleep(self.iv.get())

    # ─── HELPERS ────────────────────────────────────────────
    def _sts(self, msg, color=GREEN):
        self.root.after(0, lambda: self.slbl.config(text=f"● {msg}", fg=color))

    def _auto_detect_adb(self):
        """สแกนหา port BlueStack อัตโนมัติ"""
        def _do():
            self.root.after(0, lambda: self.adb_status.config(
                text="Scanning ports...", fg=AMBER))
            self._sts("Scanning ADB ports...", AMBER)

            def _progress(msg):
                self.root.after(0, lambda m=msg: self.adb_status.config(
                    text=m, fg=AMBER))

            port = adb_detect_port(on_progress=_progress)

            if port:
                self.port_var.set(str(port))
                self.root.after(0, lambda p=port: self.adb_status.config(
                    text=f"✓  Found BlueStack on port {p}!", fg=GREEN))
                self._sts(f"ADB connected on port {port}!", GREEN)
            else:
                self.root.after(0, lambda: self.adb_status.config(
                    text="✗  Not found — enter port manually", fg=RED))
                self._sts("ADB not found — try manual port", RED)
        threading.Thread(target=_do, daemon=True).start()

    def on_close(self):
        self.running = False
        # อัปเดต ADB_TARGET ตาม port ที่กรอก
        try:
            port = int(self.port_var.get())
            import translator_app
            translator_app.ADB_TARGET = f"{ADB_HOST}:{port}"
        except Exception:
            pass
        self.cfg.update({
            "use_adb":   self.adb_var.get(),
            "interval":  self.iv.get(),
            "src_lang":  self.src_var.get(),
            "dest_lang": self.dst_var.get(),
            "adb_port":  self.port_var.get(),
        })
        if self.region:
            self.cfg["region"] = list(self.region)
        save_cfg(self.cfg)
        self.root.destroy()

# ════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════
if __name__ == '__main__':
    root = tk.Tk()
    try:
        app = App(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    except Exception as e:
        messagebox.showerror(APP_NAME, f"{e}\n\n{traceback.format_exc()[:400]}")
