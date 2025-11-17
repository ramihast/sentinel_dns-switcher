import customtkinter as ctk
from tkinter import messagebox
import subprocess, os, sys, json, re, ctypes, threading

# --------------------------
# اجرای برنامه با دسترسی ادمین
# --------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    script = sys.executable
    params = " ".join([f'"{a}"' for a in sys.argv])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", script, params, None, 1)
    sys.exit()

# --------------------------
# مسیرها و تنظیمات اولیه
# --------------------------
base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
font_path = os.path.join(base_path, "assets", "Dana-Regular.ttf")
icon_path = os.path.join(base_path, "assets", "icon.ico")
DNS_FILE = os.path.join(base_path, "dns_list.json")
GAMES_FILE = os.path.join(base_path, "games_list.json")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# --------------------------
# فونت فارسی Dana
# --------------------------
try:
    ctk.FontManager.load_font(font_path)
except:
    pass

# راست‌چین برای متن‌های ترکیبی
RLM = "\u200f"

# --------------------------
# داده‌های پیش‌فرض
# --------------------------
DEFAULT_DNS = {
    "ایرانی": {
        "Shecan": ["178.22.122.100", "185.51.200.2"],
        "Radar": ["10.202.10.10", "10.202.10.11"]
    },
    "جهانی": {
        "Google": ["8.8.8.8", "8.8.4.4"],
        "Cloudflare": ["1.1.1.1", "1.0.0.1"]
    },
    "موارد اضافه شده": {}
}

DEFAULT_GAMES = {
    "Valorant": {"Google": ["8.8.8.8", "8.8.4.4"], "Cloudflare": ["1.1.1.1", "1.0.0.1"]},
    "CS2": {"Shecan": ["178.22.122.100", "185.51.200.2"], "Radar": ["10.202.10.10", "10.202.10.11"]}
}

# --------------------------
# توابع کمکی
# --------------------------
def load_json_safe(path, default):
    try:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json_safe(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def ping_latency(ip, timeout_ms=2000):
    """
    پینگ یک IP و برگرداندن latency به میلی‌ثانیه.
    در صورت ناموفق: float('inf')
    """
    try:
        # تشخیص نسخه IP برای سوییچ مناسب
        af_switch = "-6" if ":" in ip else "-4"

        # ساخت آرگومان‌ها: گزینه‌ها قبل از IP
        args = ["ping", af_switch, "-n", "1", "-w", str(timeout_ms), ip]

        r = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",     # خروجی یونیکد
            errors="ignore"       # اگر کانال کدنویسی متفاوت بود، کرش نکن
        )

        # اگر کد خروجی غیر صفره، احتمال زیاد پینگ شکست خورده
        if r.returncode != 0:
            # بازم یک شانس می‌دیم: اگر TTL دیدیم یعنی پاسخ بوده ولی returncode عجیبه
            if "TTL=" not in r.stdout.upper():
                return float("inf")

        s = r.stdout

        # حالت خاص: <1ms
        if re.search(r"<\s*1\s*ms", s, flags=re.IGNORECASE):
            return 1

        # عمومی‌ترین الگو روی ویندوز: هر جایی که «عدد + ms» بیاد
        m = re.search(r"(\d+)\s*ms", s, flags=re.IGNORECASE)
        return int(m.group(1)) if m else float("inf")

    except Exception:
        return float("inf")


# --------------------------
# کلاس اصلی
# --------------------------
class DNSGameOptimizer:
    def __init__(self):
        self.root = ctk.CTk()

        # آیکون برنامه
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print("⚠️ آیکون لود نشد:", e)

        self.root.title(f"{RLM}🎮 DNS بهینه ساز")
        self.root.geometry("880x740")
        self.root.resizable(False, False)

        # 🎨 رنگ‌ها
        self.green = "#2fc973"
        self.dark = "#1e1e1e"
        self.darker = "#1b1b1b"
        self.card = "#2a2f2a"

        # 🔤 فونت‌ها (همه بولد)
        self.font_normal = ctk.CTkFont(family="Dana", size=13, weight="bold")
        self.font_bold = ctk.CTkFont(family="Dana", size=22, weight="bold")

        # 📂 داده‌ها
        self.dns_data = load_json_safe(DNS_FILE, DEFAULT_DNS)
        self.games_data = load_json_safe(GAMES_FILE, DEFAULT_GAMES)
        self.selected_interface = ctk.StringVar(value=self.detect_active_interface() or f"{RLM}(یافت نشد)")
        self.protocol_mode = ctk.StringVar(value="IPv4")

        self.setup_ui()

    # --------------------------
    # رابط کاربری
    # --------------------------
    def setup_ui(self):
        title = ctk.CTkFrame(self.root, fg_color=self.dark)
        title.pack(fill="x", pady=10)
        ctk.CTkLabel(title, text=f"{RLM}🎮 DNS بهینه‌ ساز ", text_color=self.green,
                     font=self.font_bold).pack()
        ctk.CTkLabel(title, text=f"{RLM} پینگ بهتری داشته باش", text_color="#bfbfbf",
                     font=self.font_normal).pack()

        # نوار بالا
        topbar = ctk.CTkFrame(self.root, fg_color=self.darker)
        topbar.pack(fill="x", padx=15, pady=(5, 0))

        self.btn_add = ctk.CTkButton(topbar, text=f"{RLM}DNS افزودن", width=140,
                                     fg_color=self.green, hover_color="#23985d",
                                     text_color=self.darker, font=self.font_normal,
                                     command=self.open_add_dns_window)
        self.btn_add.pack(side="left", padx=5, pady=6)

        self.btn_pingall = ctk.CTkButton(topbar, text=f"{RLM} پینگ همگانی", width=140,
                                         fg_color=self.green, hover_color="#23985d",
                                         text_color=self.darker, font=self.font_normal,
                                         command=self.ping_all_dns)
        self.btn_pingall.pack(side="left", padx=5, pady=6)

        # دکمه «📡 نمایش DNS فعلی» در نوار بالا
        self.btn_show_dns = ctk.CTkButton(topbar, text=f"{RLM}فعلی DNS نمایش", width=170,
                                          fg_color=self.green, hover_color="#23985d",
                                          text_color=self.darker, font=self.font_normal,
                                          command=self.show_current_dns)
        self.btn_show_dns.pack(side="right", padx=10, pady=6)

        # تب‌ها
        tabs = ctk.CTkTabview(self.root, width=820, height=540)
        tabs.pack(padx=15, pady=10)

        # استایل تب‌ها
        try:
            tabs._segmented_button.configure(
                font=ctk.CTkFont(family="Dana", size=13, weight="bold"),
                fg_color="#1f1f1f",
                selected_color="#2b2b2b",
                selected_hover_color="#333333",
                text_color=self.green,
                unselected_text_color="#dddddd"
            )
        except Exception:
            tabs._segmented_button.configure(
                font=ctk.CTkFont(family="Dana", size=13, weight="bold"),
                fg_color="#1f1f1f",
                selected_color="#2b2b2b",
                selected_hover_color="#333333",
                text_color=self.green
            )

        # تب‌ها
        self.tab_dns = tabs.add(f"{RLM} DNS")
        self.tab_games = tabs.add(f"{RLM} بازی‌ها")
        self.tab_settings = tabs.add(f"{RLM} تنظیمات")

        # فریم‌های اصلی تب‌ها
        self.frame_dns = ctk.CTkFrame(self.tab_dns, fg_color=self.dark, width=790, height=470)
        self.frame_games = ctk.CTkFrame(self.tab_games, fg_color=self.dark, width=790, height=470)
        self.frame_settings = ctk.CTkFrame(self.tab_settings, fg_color=self.dark, width=790, height=470)
        for frame in [self.frame_dns, self.frame_games, self.frame_settings]:
            frame.pack(pady=10)

        self.build_dns_tab()
        self.build_games_tab()
        self.build_settings_tab()

        # وضعیت پایین
        self.status = ctk.CTkLabel(self.root, text=f"{RLM}✅ آماده", anchor="center",
                                   font=self.font_normal, text_color=self.green,
                                   fg_color=self.darker, height=36)
        self.status.pack(side="bottom", fill="x", pady=6)

    # --------------------------
    # DNS TAB
    # --------------------------
    def build_dns_tab(self):
        self.dns_frame = ctk.CTkScrollableFrame(self.frame_dns, width=760, height=400, fg_color=self.dark)
        self.dns_frame.pack(pady=10)
        self.refresh_dns_ui()

    def refresh_dns_ui(self):
        for w in self.dns_frame.winfo_children():
            w.destroy()

        for cat, servers in self.dns_data.items():
            ctk.CTkLabel(
                self.dns_frame,
                text=f"{RLM}📁 {cat}",
                text_color=self.green,
                font=ctk.CTkFont(family="Dana", size=15, weight="bold"),
                anchor="e"
            ).pack(fill="x", pady=(8, 4))

            grid = ctk.CTkFrame(self.dns_frame, fg_color="transparent")
            grid.pack(padx=10, pady=4, fill="x")

            row, col = 0, 0
            for name, ips in servers.items():
                card = ctk.CTkFrame(grid, fg_color=self.card, corner_radius=12)
                card.grid(row=row, column=col, padx=8, pady=8)

                ctk.CTkLabel(
                    card,
                    text=f"{RLM}{name}",
                    font=ctk.CTkFont(family="Dana", size=14, weight="bold"),
                    text_color=self.green,
                    anchor="center"
                ).pack(pady=(6, 0))

                ctk.CTkLabel(
                    card,
                    text="\n".join(ips),
                    text_color="#ccc",
                    font=self.font_normal,
                    anchor="center"
                ).pack(pady=(0, 6))

                # ردیف دکمه‌های ست و پینگ
                row_btn = ctk.CTkFrame(card, fg_color="transparent")
                row_btn.pack(pady=4)
                ctk.CTkButton(
                    row_btn,
                    text=f"{RLM}ست",
                    width=70,
                    fg_color=self.green,
                    hover_color="#23985d",
                    text_color=self.darker,
                    font=self.font_normal,
                    command=lambda n=name, i=ips: self.apply_dns(n, i)
                ).pack(side="left", padx=3)
                ctk.CTkButton(
                    row_btn,
                    text=f"{RLM}پینگ",
                    width=70,
                    fg_color="#555",
                    hover_color="#444",
                    text_color=self.green,
                    font=self.font_normal,
                    command=lambda n=name, i=ips: self.ping_single(n, i)
                ).pack(side="left", padx=3)

                # فقط برای «موارد اضافه شده» دکمه ویرایش / حذف نشان بده
                if cat == "موارد اضافه شده":
                    row_btn2 = ctk.CTkFrame(card, fg_color="transparent")
                    row_btn2.pack(pady=(0, 6))
                    ctk.CTkButton(
                        row_btn2,
                        text=f"{RLM}✏️ ویرایش",
                        width=70,
                        fg_color="#3b82f6",
                        hover_color="#2563eb",
                        text_color="white",
                        font=self.font_normal,
                        command=lambda c=cat, n=name: self.open_edit_dns_window(c, n)
                    ).pack(side="left", padx=3)
                    ctk.CTkButton(
                        row_btn2,
                        text=f"{RLM}🗑 حذف",
                        width=70,
                        fg_color="#ef4444",
                        hover_color="#b91c1c",
                        text_color="white",
                        font=self.font_normal,
                        command=lambda c=cat, n=name: self.delete_dns(c, n)
                    ).pack(side="left", padx=3)

                col += 1
                if col == 3:
                    row += 1
                    col = 0

    # --------------------------
    # افزودن DNS جدید
    # --------------------------
    def open_add_dns_window(self):
        w = ctk.CTkToplevel(self.root)
        w.title("جدید DNS افزودن")
        w.geometry("420x300")
        w.configure(fg_color=self.dark)

        ctk.CTkLabel(w, text="نام DNS", text_color=self.green, font=self.font_normal).pack(pady=(10, 2))
        name = ctk.CTkEntry(w, width=320, font=self.font_normal, justify="center")
        name.pack(pady=(0, 8))

        ctk.CTkLabel(w, text="اصلی IP", text_color=self.green, font=self.font_normal).pack(pady=(5, 2))
        ip1 = ctk.CTkEntry(w, width=320, font=self.font_normal, justify="center")
        ip1.pack(pady=(0, 8))

        ctk.CTkLabel(w, text="ثانویه IP", text_color=self.green, font=self.font_normal).pack(pady=(5, 2))
        ip2 = ctk.CTkEntry(w, width=320, font=self.font_normal, justify="center")
        ip2.pack(pady=(0, 10))

        def save():
            n, i1, i2 = name.get().strip(), ip1.get().strip(), ip2.get().strip()
            if not n or not i1:
                messagebox.showwarning("⚠️ خطا", "لطفاً نام و IP اصلی را وارد کنید.")
                return
            # ذخیره در دسته «موارد اضافه شده»
            self.dns_data.setdefault("موارد اضافه شده", {})
            if n in self.dns_data["موارد اضافه شده"]:
                messagebox.showwarning("⚠️ خطا", "DNS دیگری با این نام در موارد اضافه شده وجود دارد.")
                return
            self.dns_data["موارد اضافه شده"][n] = [i1, i2] if i2 else [i1]
            save_json_safe(DNS_FILE, self.dns_data)
            self.refresh_dns_ui()
            self.status.configure(text=f"✅ DNS {n} اضافه شد", text_color=self.green)
            w.destroy()

        ctk.CTkButton(w, text="💾 ذخیره", fg_color=self.green, hover_color="#23985d",
                      text_color=self.darker, width=160, font=self.font_normal,
                      command=save).pack(pady=(10, 15))

    # --------------------------
    # ویرایش DNS کاربر
    # --------------------------
    def open_edit_dns_window(self, category, dns_name):
        # فقط روی موارد اضافه شده منطقی است، ولی برای اطمینان چک می‌کنیم
        if category != "موارد اضافه شده":
            messagebox.showwarning("⚠️", "فقط DNS های اضافه شده توسط کاربر قابل ویرایش هستند.")
            return

        current_ips = self.dns_data.get(category, {}).get(dns_name, [])

        w = ctk.CTkToplevel(self.root)
        w.title("ویرایش DNS")
        w.geometry("420x300")
        w.configure(fg_color=self.dark)

        ctk.CTkLabel(w, text="نام DNS", text_color=self.green, font=self.font_normal).pack(pady=(10, 2))
        name_entry = ctk.CTkEntry(w, width=320, font=self.font_normal, justify="center")
        name_entry.pack(pady=(0, 8))
        name_entry.insert(0, dns_name)

        ctk.CTkLabel(w, text="اصلی IP", text_color=self.green, font=self.font_normal).pack(pady=(5, 2))
        ip1_entry = ctk.CTkEntry(w, width=320, font=self.font_normal, justify="center")
        ip1_entry.pack(pady=(0, 8))
        if len(current_ips) >= 1:
            ip1_entry.insert(0, current_ips[0])

        ctk.CTkLabel(w, text="ثانویه IP", text_color=self.green, font=self.font_normal).pack(pady=(5, 2))
        ip2_entry = ctk.CTkEntry(w, width=320, font=self.font_normal, justify="center")
        ip2_entry.pack(pady=(0, 10))
        if len(current_ips) >= 2:
            ip2_entry.insert(0, current_ips[1])

        def save_edit():
            new_name = name_entry.get().strip()
            i1 = ip1_entry.get().strip()
            i2 = ip2_entry.get().strip()

            if not new_name or not i1:
                messagebox.showwarning("⚠️ خطا", "لطفاً نام و IP اصلی را وارد کنید.")
                return

            cat_dict = self.dns_data.setdefault(category, {})

            # اگر نام عوض شده، بررسی تکراری بودن
            if new_name != dns_name and new_name in cat_dict:
                messagebox.showwarning("⚠️ خطا", "DNS دیگری با این نام در موارد اضافه شده وجود دارد.")
                return

            # به‌روزرسانی
            if new_name != dns_name:
                cat_dict.pop(dns_name, None)
            cat_dict[new_name] = [i1] + ([i2] if i2 else [])

            self.dns_data[category] = cat_dict
            save_json_safe(DNS_FILE, self.dns_data)
            self.refresh_dns_ui()
            self.status.configure(text=f"✅ DNS {new_name} ویرایش شد", text_color=self.green)
            w.destroy()

        ctk.CTkButton(
            w,
            text="💾 ذخیره تغییرات",
            fg_color=self.green,
            hover_color="#23985d",
            text_color=self.darker,
            width=180,
            font=self.font_normal,
            command=save_edit
        ).pack(pady=(10, 15))

    # --------------------------
    # حذف DNS کاربر
    # --------------------------
    def delete_dns(self, category, dns_name):
        if category != "موارد اضافه شده":
            messagebox.showwarning("⚠️", "فقط DNS های اضافه شده توسط کاربر قابل حذف هستند.")
            return

        if not messagebox.askyesno("حذف DNS", f"آیا از حذف {dns_name} مطمئن هستید؟"):
            return

        try:
            cat_dict = self.dns_data.get(category, {})
            if dns_name in cat_dict:
                cat_dict.pop(dns_name)
                self.dns_data[category] = cat_dict
                save_json_safe(DNS_FILE, self.dns_data)
                self.refresh_dns_ui()
                self.status.configure(text=f"🗑 DNS {dns_name} حذف شد", text_color="#ff5555")
            else:
                messagebox.showwarning("⚠️", "این DNS دیگر وجود ندارد.")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    # --------------------------
    # منطق DNS
    # --------------------------
    def detect_active_interface(self):
        try:
            r = subprocess.run("netsh interface show interface", shell=True, capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if "Connected" in line:
                    return " ".join(line.split()[3:])
        except:
            return None

    def apply_dns(self, name, ips):
        interface = self.selected_interface.get()
        proto = self.protocol_mode.get().lower()
        try:
            subprocess.run(f'netsh interface {proto} delete dnsservers name="{interface}" all', shell=True)
            subprocess.run(f'netsh interface {proto} set dnsservers name="{interface}" static {ips[0]} primary', shell=True)
            if len(ips) > 1:
                subprocess.run(f'netsh interface {proto} add dnsservers name="{interface}" {ips[1]} index=2', shell=True)
            self.status.configure(text=f"✅ DNS {name} ست شد", text_color=self.green)
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def ping_single(self, name, ips):
        self.status.configure(text=f"{RLM}در حال پینگ {name}...", text_color=self.green)
        lat = ping_latency(ips[0])
        self.status.configure(text=f"{RLM}پینگ {name}: {lat if lat != float('inf') else 'Timeout'} ms ✅", text_color=self.green)

    def ping_all_dns(self):
        all_ips = [(n, i[0]) for c in self.dns_data.values() for n, i in c.items()]
        if not all_ips:
            messagebox.showinfo("پینگ", "هیچ DNS ای برای پینگ وجود ندارد.")
            return
        threading.Thread(target=self._ping_all_thread, args=(all_ips,), daemon=True).start()

    def _ping_all_thread(self, dns_list):
        results = []
        total = len(dns_list)

        for idx, (n, ip) in enumerate(dns_list, start=1):
            # آپدیت وضعیت در ترد اصلی
            def update_status(i=idx, name=n):
                self.status.configure(
                    text=f"{RLM}در حال پینگ {i}/{total}: {name}",
                    text_color=self.green
                )
            self.root.after(0, update_status)

            lat = ping_latency(ip)
            results.append((n, ip, lat))

        # بعد از اتمام پینگ‌ها، نتایج را در پنجره‌ی شیک نشان بده
        def show_results():
            if not results:
                text = "هیچ DNS ای برای پینگ یافت نشد."
            else:
                lines = []
                for name, ip, lat in results:
                    val = f"{lat} ms" if lat != float("inf") else "Timeout"
                    lines.append(f"{name}: {ip} → {val}")
                text = "\n".join(lines)

            self.status.configure(
                text=f"{RLM}✅ پینگ همه DNS ها تمام شد",
                text_color=self.green
            )

            self.show_text_window(
                "نتایج پینگ",
                "📊 نتایج پینگ همه DNS ها",
                f"{len(results)} سرور بررسی شد",
                text,
                width=640,
                height=430
            )

        # اجرا در ترد اصلی
        self.root.after(0, show_results)

    # --------------------------
    # تب بازی‌ها
    # --------------------------
    def build_games_tab(self):
        frame = ctk.CTkScrollableFrame(self.frame_games, width=760, height=420, fg_color=self.dark)
        frame.pack(padx=10, pady=10)
        for g, d in self.games_data.items():
            box = ctk.CTkFrame(frame, fg_color=self.card, corner_radius=10)
            box.pack(fill="x", padx=8, pady=8)
            ctk.CTkLabel(box, text=g, text_color=self.green,
                         font=ctk.CTkFont(family="Dana", size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)
            ctk.CTkButton(box, text="🚀 پیدا کردن سریع‌ترین DNS", fg_color=self.green,
                          hover_color="#23985d", text_color=self.darker,
                          font=self.font_normal,
                          command=lambda game=g: self.optimize_for_game(game)).pack(padx=10, pady=5)

    def optimize_for_game(self, game):
        dns_list = self.games_data.get(game, {})
        best, best_lat = None, float("inf")
        for name, ips in dns_list.items():
            lat = ping_latency(ips[0])
            if lat < best_lat:
                best_lat, best = lat, (name, ips)
        if best:
            self.apply_dns(best[0], best[1])
            messagebox.showinfo("🎯 نتیجه", f"بهترین DNS برای {game}:\n{best[0]} ({best[1][0]}) → {best_lat}ms")
        else:
            messagebox.showwarning("⚠️", "هیچ DNS مناسبی یافت نشد.")

    # --------------------------
    # تب تنظیمات
    # --------------------------
    def build_settings_tab(self):
        frame = ctk.CTkFrame(self.frame_settings, fg_color=self.dark)
        frame.pack(fill="both", expand=True, pady=20)

        ctk.CTkLabel(frame, text="کارت شبکه:", font=self.font_normal, text_color=self.green).pack()
        self.interface_menu = ctk.CTkOptionMenu(frame, variable=self.selected_interface,
                                                values=[self.selected_interface.get()],
                                                fg_color=self.green, button_color="#23985d",
                                                text_color=self.darker, font=self.font_normal)
        self.interface_menu.pack(pady=5)

        ctk.CTkLabel(frame, text="پروتکل:", font=self.font_normal, text_color=self.green).pack()
        self.protocol_menu = ctk.CTkOptionMenu(frame, variable=self.protocol_mode,
                                               values=["IPv4", "IPv6"],
                                               fg_color=self.green, button_color="#23985d",
                                               text_color=self.darker, font=self.font_normal)
        self.protocol_menu.pack(pady=5)

        ctk.CTkButton(frame, text="🧹 پاک‌سازی کش DNS", fg_color="#3fb881",
                      hover_color="#2fa668", text_color=self.darker, font=self.font_normal,
                      command=lambda: subprocess.run("ipconfig /flushdns", shell=True)).pack(pady=5)

    # --------------------------
    # پنجره‌ی متنی شیک عمومی
    # --------------------------
    def show_text_window(self, win_title, header_text, subtitle, body_text,
                         width=560, height=420):
        w = ctk.CTkToplevel(self.root)
        w.title(win_title)
        w.geometry(f"{width}x{height}")
        w.configure(fg_color=self.dark)

        # هدر
        ctk.CTkLabel(
            w,
            text=f"{RLM}{header_text}",
            text_color=self.green,
            font=self.font_bold
        ).pack(pady=(12, 4))

        # توضیح زیر هدر (اختیاری)
        if subtitle:
            ctk.CTkLabel(
                w,
                text=f"{RLM}{subtitle}",
                text_color="#bfbfbf",
                font=self.font_normal
            ).pack(pady=(0, 6))

        # باکس متن (اسکرول‌دار)
        box = ctk.CTkTextbox(
            w,
            width=width - 40,
            height=height - 140,
            fg_color=self.card,
            text_color="#f3f3f3",
            font=self.font_normal,
            activate_scrollbars=True
        )
        box.pack(padx=15, pady=(5, 10), fill="both", expand=True)
        box.insert("1.0", body_text)
        box.configure(state="disabled")

        # دکمه بستن
        ctk.CTkButton(
            w,
            text=f"{RLM}بستن",
            width=100,
            fg_color=self.green,
            hover_color="#23985d",
            text_color=self.darker,
            font=self.font_normal,
            command=w.destroy
        ).pack(pady=(0, 10))

    # --------------------------
    # نمایش DNS فعلی با پنجره شیک
    # --------------------------
    def show_current_dns(self):
        interface = self.selected_interface.get()
        proto = self.protocol_mode.get().lower()

        r = subprocess.run(
            f'netsh interface {proto} show dnsservers name="{interface}"',
            shell=True,
            capture_output=True,
            text=True
        )
        out = r.stdout.strip() or "هیچ DNS فعالی نیست."

        subtitle = f"{interface}  |  {proto.upper()}"
        self.show_text_window(
            "DNS فعلی",
            "📡 DNS فعلی",
            subtitle,
            out,
            width=620,
            height=420
        )

    # --------------------------
    # اجرا
    # --------------------------
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DNSGameOptimizer()
    app.run()
