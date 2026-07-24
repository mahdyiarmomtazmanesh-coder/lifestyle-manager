"""
برنامه مدیریت سبک زندگی شخصی - نسخه گرافیکی
مدیریت قرار ملاقات‌ها، کارهای روزانه و تمرین‌های ورزشی
"""

import json, os, calendar
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# ── رنگ‌بندی ──────────────────────────────────────────────────────
C = {
    "bg": "#1E1E2E", "sidebar": "#181825", "card": "#313244",
    "accent": "#CBA6F7", "accent2": "#89B4FA", "accent3": "#A6E3A1",
    "accent4": "#F38BA8", "text": "#CDD6F4", "subtext": "#A6ADC8",
    "border": "#45475A", "entry_bg": "#1E1E2E",
    "done_bg": "#1E3A2F", "done_fg": "#A6E3A1",
    "undone_bg": "#3A1E1E", "undone_fg": "#F38BA8",
}
FT = ("Segoe UI", 20, "bold")
FH = ("Segoe UI", 13, "bold")
FB = ("Segoe UI", 11)
FS = ("Segoe UI", 9)


# ── مدیران داده ───────────────────────────────────────────────────
class BaseManager:
    def __init__(self, fname, label, fields):
        self.fname, self.label, self.fields = fname, label, fields
        self.items, self.next_id = [], 1
        self._load()

    def _load(self):
        if os.path.exists(self.fname):
            try:
                with open(self.fname, encoding="utf-8") as f:
                    self.items = json.load(f)
                if self.items:
                    self.next_id = max(i["id"] for i in self.items) + 1
            except Exception:
                self.items = []

    def _save(self):
        with open(self.fname, "w", encoding="utf-8") as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)

    def add(self, data):
        item = {"id": self.next_id, **data}
        self.next_id += 1
        self.items.append(item); self._save(); return item

    def update(self, iid, data):
        item = self._get(iid)
        if item: item.update(data); self._save(); return True
        return False

    def delete(self, iid):
        item = self._get(iid)
        if item: self.items.remove(item); self._save(); return True
        return False

    def _get(self, iid):
        return next((i for i in self.items if i["id"] == iid), None)

    def search(self, kw):
        kw = kw.lower()
        return [i for i in self.items if kw in json.dumps(i, ensure_ascii=False).lower()]


class AppointmentManager(BaseManager):
    def __init__(self):
        super().__init__("appointments.json", "قرار ملاقات",
                         ["عنوان", "تاریخ", "ساعت", "مکان"])


class WorkManager(BaseManager):
    PRIORITIES = ["کم", "متوسط", "زیاد"]
    def __init__(self):
        super().__init__("work.json", "کار",
                         ["عنوان", "توضیحات", "اولویت", "مهلت انجام", "انجام‌شده"])


class ExerciseManager(BaseManager):
    def __init__(self):
        super().__init__("exercise.json", "تمرین",
                         ["نام", "مدت (دقیقه)", "تاریخ", "یادداشت"])


# ── اعتبارسنجی ────────────────────────────────────────────────────
def valid_date(v):
    try: datetime.strptime(v, "%Y-%m-%d"); return True
    except ValueError: return False

def valid_time(v):
    try: datetime.strptime(v, "%H:%M"); return True
    except ValueError: return False


# ── ویجت‌های سفارشی ───────────────────────────────────────────────
class Btn(tk.Button):
    def __init__(self, parent, text, color, cmd=None, icon="", **kw):
        super().__init__(parent, text=f"{icon} {text}".strip(),
                         bg=color, fg=C["bg"], font=("Segoe UI", 10, "bold"),
                         relief="flat", bd=0, padx=12, pady=6,
                         cursor="hand2", activebackground=color,
                         activeforeground=C["bg"], command=cmd, **kw)
        self.bind("<Enter>", lambda e: self.config(bg=self._lt(color)))
        self.bind("<Leave>", lambda e: self.config(bg=color))

    @staticmethod
    def _lt(h):
        return "#{:02x}{:02x}{:02x}".format(
            min(255, int(h[1:3], 16)+25),
            min(255, int(h[3:5], 16)+25),
            min(255, int(h[5:7], 16)+25))


class Entry(tk.Entry):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["entry_bg"], fg=C["text"],
                         insertbackground=C["accent"], relief="flat", bd=0,
                         font=FB, highlightthickness=1,
                         highlightbackground=C["border"],
                         highlightcolor=C["accent"], **kw)


class CalendarPicker(tk.Toplevel):
    def __init__(self, parent, entry):
        super().__init__(parent)
        self.title("انتخاب تاریخ"); self.resizable(False, False)
        self.configure(bg=C["bg"]); self.entry = entry
        t = datetime.today(); self.y, self.m = t.year, t.month
        self._build(); self._draw()
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        nav = tk.Frame(self, bg=C["sidebar"], pady=8); nav.pack(fill="x")
        tk.Button(nav, text="◀", bg=C["sidebar"], fg=C["accent"], relief="flat",
                  font=FB, cursor="hand2", command=self._prev).pack(side="left", padx=10)
        self.lbl = tk.Label(nav, text="", bg=C["sidebar"], fg=C["text"],
                            font=FH, width=18); self.lbl.pack(side="left", expand=True)
        tk.Button(nav, text="▶", bg=C["sidebar"], fg=C["accent"], relief="flat",
                  font=FB, cursor="hand2", command=self._next).pack(side="right", padx=10)
        self.gf = tk.Frame(self, bg=C["bg"], padx=12, pady=10); self.gf.pack()

    def _draw(self):
        for w in self.gf.winfo_children(): w.destroy()
        self.lbl.config(text=f"{calendar.month_name[self.m]}  {self.y}")
        for c, d in enumerate(["د","س","چ","پ","ج","ش","ی"]):
            tk.Label(self.gf, text=d, bg=C["bg"], fg=C["accent"],
                     font=("Segoe UI", 10, "bold"), width=4).grid(row=0, column=c, padx=2, pady=2)
        for r, week in enumerate(calendar.monthcalendar(self.y, self.m), 1):
            for c, day in enumerate(week):
                if day == 0: continue
                tk.Button(self.gf, text=str(day), width=4, bg=C["card"], fg=C["text"],
                          relief="flat", font=FB, cursor="hand2",
                          activebackground=C["accent"], activeforeground=C["bg"],
                          command=lambda d=day: self._pick(d)
                          ).grid(row=r, column=c, padx=2, pady=2, ipady=4)

    def _pick(self, day):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, f"{self.y}-{self.m:02d}-{day:02d}")
        self.destroy()

    def _prev(self):
        self.m -= 1
        if self.m == 0: self.m = 12; self.y -= 1
        self._draw()

    def _next(self):
        self.m += 1
        if self.m == 13: self.m = 1; self.y += 1
        self._draw()


# ── فریم مدیریت ───────────────────────────────────────────────────
DATE_FIELDS = {"تاریخ", "مهلت انجام"}

class ManagerFrame(tk.Frame):
    def __init__(self, parent, mgr, ctrl, icon=""):
        super().__init__(parent, bg=C["bg"])
        self.mgr, self.ctrl, self.icon = mgr, ctrl, icon
        self.entries, self.sel_id = {}, None
        self._build(); self.refresh()

    def _build(self):
        # هدر
        hdr = tk.Frame(self, bg=C["sidebar"], pady=14); hdr.pack(fill="x")
        tk.Label(hdr, text=f"{self.icon}  مدیریت {self.mgr.label}",
                 bg=C["sidebar"], fg=C["accent"], font=FT).pack(side="left", padx=20)
        Btn(hdr, "بازگشت", C["border"], cmd=self.ctrl.show_menu,
            icon="⬅").pack(side="right", padx=16)

        body = tk.Frame(self, bg=C["bg"]); body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── چپ: جدول ──
        left = tk.Frame(body, bg=C["bg"]); left.pack(side="left", fill="both", expand=True, padx=(0,10))

        sf = tk.Frame(left, bg=C["card"], pady=8, padx=10); sf.pack(fill="x", pady=(0,8))
        tk.Label(sf, text="🔍", bg=C["card"], fg=C["subtext"],
                 font=("Segoe UI Emoji", 14)).pack(side="left")
        self.sv = tk.StringVar()
        Entry(sf, textvariable=self.sv).pack(side="left", fill="x", expand=True, padx=6)
        Btn(sf, "جستجو", C["accent2"], cmd=self._search).pack(side="left", padx=3)
        Btn(sf, "همه", C["border"], cmd=self.refresh).pack(side="left")

        tf = tk.Frame(left, bg=C["card"], padx=2, pady=2); tf.pack(fill="both", expand=True)
        style = ttk.Style(); style.theme_use("clam")
        style.configure("M.Treeview", background=C["card"], foreground=C["text"],
                         fieldbackground=C["card"], rowheight=34, font=FB, borderwidth=0)
        style.configure("M.Treeview.Heading", background=C["sidebar"],
                         foreground=C["accent"], font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("M.Treeview", background=[("selected", C["accent"])],
                  foreground=[("selected", C["bg"])])

        cols = ["شناسه"] + self.mgr.fields
        self.tree = ttk.Treeview(tf, columns=cols, show="headings",
                                  height=12, style="M.Treeview")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=60 if col == "شناسه" else 130,
                             anchor="center", minwidth=50)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── راست: فرم ──
        right = tk.Frame(body, bg=C["card"], padx=16, pady=16, width=280)
        right.pack(side="right", fill="y"); right.pack_propagate(False)
        tk.Label(right, text="جزئیات رکورد", bg=C["card"],
                 fg=C["accent"], font=FH).pack(anchor="w", pady=(0,12))

        for field in self.mgr.fields:
            tk.Label(right, text=field, bg=C["card"], fg=C["subtext"],
                     font=FS).pack(anchor="w")
            if field == "اولویت":
                w = ttk.Combobox(right, values=WorkManager.PRIORITIES,
                                  font=FB, state="readonly")
                w.pack(fill="x", pady=(2,8)); self.entries[field] = w
            elif field == "انجام‌شده":
                var = tk.BooleanVar()
                fr = tk.Frame(right, bg=C["card"]); fr.pack(fill="x", pady=(2,8))
                tk.Checkbutton(fr, variable=var, bg=C["card"], fg=C["text"],
                               selectcolor=C["accent3"], activebackground=C["card"],
                               font=FB, text="انجام شده ✔", cursor="hand2",
                               relief="flat").pack(side="left")
                self.entries[field] = var
            elif field in DATE_FIELDS:
                fr = tk.Frame(right, bg=C["card"]); fr.pack(fill="x", pady=(2,8))
                e = Entry(fr); e.pack(side="left", fill="x", expand=True)
                tk.Button(fr, text="📅", bg=C["card"], fg=C["accent"], relief="flat",
                          font=("Segoe UI Emoji", 14), cursor="hand2",
                          activebackground=C["card"],
                          command=lambda e=e: CalendarPicker(self, e)
                          ).pack(side="left", padx=4)
                self.entries[field] = e
            else:
                e = Entry(right); e.pack(fill="x", pady=(2,8))
                self.entries[field] = e

        tk.Frame(right, bg=C["border"], height=1).pack(fill="x", pady=10)
        bg = tk.Frame(right, bg=C["card"]); bg.pack(fill="x")
        Btn(bg, "افزودن", C["accent3"], cmd=self._add, icon="➕").grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        Btn(bg, "ویرایش", C["accent2"], cmd=self._update, icon="✏️").grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        Btn(bg, "حذف", C["accent4"], cmd=self._delete, icon="🗑").grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        Btn(bg, "پاک کردن", C["border"], cmd=self._clear, icon="🔄").grid(row=1, column=1, padx=3, pady=3, sticky="ew")
        bg.columnconfigure(0, weight=1); bg.columnconfigure(1, weight=1)

    def refresh(self, items=None):
        for r in self.tree.get_children(): self.tree.delete(r)
        for item in (items if items is not None else self.mgr.items):
            vals = [item["id"]] + [item.get(f, "") for f in self.mgr.fields]
            tag = ("done" if item.get("انجام‌شده") else "undone") if "انجام‌شده" in item else ""
            self.tree.insert("", "end", values=vals, tags=(tag,))
        self.tree.tag_configure("done", background=C["done_bg"], foreground=C["done_fg"])
        self.tree.tag_configure("undone", background=C["undone_bg"], foreground=C["undone_fg"])
        self.sv.set("")

    def _search(self):
        kw = self.sv.get().strip()
        if not kw: messagebox.showwarning("جستجو", "کلیدواژه وارد کنید."); return
        self.refresh(self.mgr.search(kw))

    def _clear(self):
        for f, w in self.entries.items():
            if isinstance(w, tk.BooleanVar): w.set(False)
            elif isinstance(w, ttk.Combobox): w.set("")
            else: w.delete(0, tk.END)
        self.sel_id = None
        self.tree.selection_remove(self.tree.selection())

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        self.sel_id = int(vals[0])
        for i, f in enumerate(self.mgr.fields, 1):
            w = self.entries[f]; v = str(vals[i])
            if isinstance(w, tk.BooleanVar): w.set(v in ("True","true","1","بله"))
            elif isinstance(w, ttk.Combobox): w.set(v)
            else: w.delete(0, tk.END); w.insert(0, v)

    def _collect(self):
        data = {}
        for f in self.mgr.fields:
            w = self.entries[f]
            if isinstance(w, tk.BooleanVar): data[f] = w.get(); continue
            v = w.get().strip()
            if f in ("نام", "عنوان") and not v:
                messagebox.showerror("خطا", f"فیلد «{f}» نمی‌تواند خالی باشد."); return None
            if f in DATE_FIELDS and v and not valid_date(v):
                messagebox.showerror("خطا", "تاریخ باید با فرمت YYYY-MM-DD باشد."); return None
            if f == "ساعت" and v and not valid_time(v):
                messagebox.showerror("خطا", "ساعت باید با فرمت HH:MM باشد."); return None
            if f == "مدت (دقیقه)":
                if not v.isdigit() or int(v) < 1:
                    messagebox.showerror("خطا", "مدت باید عدد صحیح مثبت باشد."); return None
                v = int(v)
            if f == "اولویت" and v and v not in WorkManager.PRIORITIES:
                messagebox.showerror("خطا", "اولویت باید کم، متوسط یا زیاد باشد."); return None
            data[f] = v
        return data

    def _add(self):
        d = self._collect()
        if d is None: return
        new = self.mgr.add(d); self.refresh(); self._clear()
        messagebox.showinfo("موفقیت", f"رکورد با شناسه {new['id']} اضافه شد.")

    def _update(self):
        if self.sel_id is None:
            messagebox.showwarning("ویرایش", "ابتدا یک رکورد انتخاب کنید."); return
        d = self._collect()
        if d is None: return
        self.mgr.update(self.sel_id, d); self.refresh(); self._clear()
        messagebox.showinfo("موفقیت", "رکورد ویرایش شد.")

    def _delete(self):
        if self.sel_id is None:
            messagebox.showwarning("حذف", "ابتدا یک رکورد انتخاب کنید."); return
        if messagebox.askyesno("تأیید حذف", "آیا از حذف این رکورد مطمئن هستید؟"):
            self.mgr.delete(self.sel_id); self.refresh(); self._clear()


# ── منوی اصلی ─────────────────────────────────────────────────────
class MainMenu(tk.Frame):
    SECTIONS = [
        ("📅", "قرار ملاقات‌ها", "appointments", C["accent"]),
        ("✅", "کارهای روزانه",  "work",         C["accent3"]),
        ("🏃", "تمرین‌های ورزشی","exercise",      C["accent2"]),
    ]

    def __init__(self, parent, ctrl):
        super().__init__(parent, bg=C["bg"])
        hdr = tk.Frame(self, bg=C["sidebar"], pady=30); hdr.pack(fill="x")
        tk.Label(hdr, text="🌟  مدیریت سبک زندگی",
                 bg=C["sidebar"], fg=C["accent"],
                 font=("Segoe UI", 24, "bold")).pack()
        tk.Label(hdr, text="برنامه‌ریزی هوشمند روزانه",
                 bg=C["sidebar"], fg=C["subtext"], font=FB).pack(pady=4)

        cf = tk.Frame(self, bg=C["bg"]); cf.pack(expand=True, pady=40)
        for icon, label, key, color in self.SECTIONS:
            card = tk.Frame(cf, bg=C["card"], padx=30, pady=28, cursor="hand2",
                            highlightthickness=2, highlightbackground=C["border"])
            card.pack(side="left", padx=18)
            tk.Label(card, text=icon, bg=C["card"],
                     font=("Segoe UI Emoji", 36)).pack()
            tk.Label(card, text=label, bg=C["card"],
                     fg=color, font=("Segoe UI", 13, "bold")).pack(pady=6)
            Btn(card, "ورود", color, cmd=lambda k=key: ctrl.show_frame(k)).pack(pady=(6,0))
            for w in [card] + card.winfo_children():
                w.bind("<Enter>", lambda e, c=card: c.config(highlightbackground=C["accent"]))
                w.bind("<Leave>", lambda e, c=card: c.config(highlightbackground=C["border"]))

        Btn(self, "خروج از برنامه", C["accent4"],
            cmd=ctrl.quit, icon="🚪").pack(pady=10)


# ── برنامه اصلی ───────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("مدیریت سبک زندگی شخصی")
        self.geometry("1050x680"); self.minsize(900, 600)
        self.configure(bg=C["bg"])

        am, wm, em = AppointmentManager(), WorkManager(), ExerciseManager()
        self._seed(am, wm, em)

        self.cont = tk.Frame(self, bg=C["bg"]); self.cont.pack(fill="both", expand=True)
        self.menu = MainMenu(self.cont, self)
        self.frames = {
            "appointments": ManagerFrame(self.cont, am, self, "📅"),
            "work":         ManagerFrame(self.cont, wm, self, "✅"),
            "exercise":     ManagerFrame(self.cont, em, self, "🏃"),
        }
        self.show_menu()

    def show_menu(self):
        for f in self.frames.values(): f.pack_forget()
        self.menu.pack(fill="both", expand=True)

    def show_frame(self, name):
        self.menu.pack_forget()
        for f in self.frames.values(): f.pack_forget()
        self.frames[name].refresh()
        self.frames[name].pack(fill="both", expand=True)

    @staticmethod
    def _seed(am, wm, em):
        if not am.items:
            am.add({"عنوان": "مراجعه به دندان‌پزشک", "تاریخ": "2026-05-10", "ساعت": "10:30", "مکان": "کلینیک شهر"})
            am.add({"عنوان": "جلسه تیمی", "تاریخ": "2026-05-12", "ساعت": "14:00", "مکان": "دفتر کار"})
        if not wm.items:
            wm.add({"عنوان": "تکمیل گزارش", "توضیحات": "گزارش مالی فصلی", "اولویت": "زیاد", "مهلت انجام": "2026-05-15", "انجام‌شده": False})
            wm.add({"عنوان": "پیگیری ایمیل‌ها", "توضیحات": "پاسخ به مشتریان", "اولویت": "متوسط", "مهلت انجام": "2026-05-08", "انجام‌شده": True})
        if not em.items:
            em.add({"نام": "دویدن", "مدت (دقیقه)": 30, "تاریخ": "2026-05-01", "یادداشت": "دویدن صبحگاهی"})
            em.add({"نام": "یوگا", "مدت (دقیقه)": 45, "تاریخ": "2026-05-03", "یادداشت": "تمرکز بر انعطاف"})


if __name__ == "__main__":
    App().mainloop()
