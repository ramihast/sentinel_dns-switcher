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
# داده‌های پیش‌فرض DNS
# --------------------------
DEFAULT_DNS = {
    "ایرانی": {
        "Shecan":    ["178.22.122.100", "185.51.200.2"],
        "Radar":     ["10.202.10.10", "10.202.10.11"],
        "Begzar":    ["185.55.226.26", "185.55.225.25"],
        "Electro":   ["78.157.42.100", "78.157.42.101"],
        "403Online": ["10.202.10.202", "10.202.10.102"],
        "Respina":   ["185.12.112.1",  "185.12.112.2"]
    },
    "جهانی": {
        "Google":     ["8.8.8.8",       "8.8.4.4"],
        "Cloudflare": ["1.1.1.1",       "1.0.0.1"],
        "Quad9":      ["9.9.9.9",       "149.112.112.112"],
        "OpenDNS":    ["208.67.222.222","208.67.220.220"],
        "AdGuard":    ["94.140.14.14",  "94.140.15.15"],
        "ControlD":   ["76.76.2.0",     "76.76.10.0"]
    },
    "موارد اضافه شده": {}
}

# --------------------------
# بازی‌ها + DNS های پیشنهادی
# --------------------------
DEFAULT_GAMES = {
    "Fortnite": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Google":     ["8.8.8.8", "8.8.4.4"],
        "Quad9":      ["9.9.9.9", "149.112.112.112"]
    },
    "Valorant": {
        "Google":     ["8.8.8.8", "8.8.4.4"],
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "OpenDNS":    ["208.67.222.222","208.67.220.220"]
    },
    "Counter-Strike 2": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Google":     ["8.8.8.8", "8.8.4.4"],
        "AdGuard":    ["94.140.14.14","94.140.15.15"]
    },
    "League of Legends": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Google":     ["8.8.8.8", "8.8.4.4"],
        "OpenDNS":    ["208.67.222.222","208.67.220.220"]
    },
    "Apex Legends": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Quad9":      ["9.9.9.9", "149.112.112.112"],
        "Google":     ["8.8.8.8", "8.8.4.4"]
    },
    "Warzone": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "OpenDNS":    ["208.67.222.222","208.67.220.220"],
        "Google":     ["8.8.8.8", "8.8.4.4"]
    },
    "PUBG": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Quad9":      ["9.9.9.9", "149.112.112.112"],
        "Google":     ["8.8.8.8", "8.8.4.4"]
    },
    "Rocket League": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "AdGuard":    ["94.140.14.14","94.140.15.15"],
        "Google":     ["8.8.8.8", "8.8.4.4"]
    },
    "Overwatch 2": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Google":     ["8.8.8.8", "8.8.4.4"],
        "Quad9":      ["9.9.9.9", "149.112.112.112"]
    },
    "GTA Online": {
        "Cloudflare": ["1.1.1.1", "1.0.0.1"],
        "Google":     ["8.8.8.8", "8.8.4.4"],
        "OpenDNS":    ["208.67.222.222","208.67.220.220"]
    }
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
    try:
        af_switch = "-6" if ":" in ip else "-4"
        args = ["ping", af_switch, "-n", "1", "-w", str(timeout_ms), ip]
        r = subprocess.run(args, capture_output=True, text=True,
                           encoding="utf-8", errors="ignore")
        if r.returncode != 0 and "TTL=" not in r.stdout.upper():
            return float("inf")
        s = r.stdout
        if re.search(r"<\s*1\s*ms", s, flags=re.IGNORECASE):
            return 1
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

        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass

        self.root.title(f"{RLM}🎮 DNS بهینه ساز")
        self.root.geometry("880x740")
        self.root.resizable(False, False)

        self.green = "#2fc973"
        self.dark = "#1e1e1e"
        self.darker = "#1b1b1b"
        self.card = "#2a2f2a"
        self.blue = "#3b82f6"

        self.font_title = ctk.CTkFont(family="Dana", size=22, weight="bold")
        self.font_header = ctk.CTkFont(family="Dana", size=15, weight="bold")
        self.font_normal = ctk.CTkFont(family="Dana", size=13, weight="bold")

        self.dns_data = load_json_safe(DNS_FILE, DEFAULT_DNS)
        self.games_data = load_json_safe(GAMES_FILE, DEFAULT_GAMES)

        self.interface_names = []
        self.selected_interface = ctk.StringVar(value=f"{RLM}(در حال بارگذاری...)")
        self.protocol_mode = ctk.StringVar(value="IPv4")

        self.setup_ui()
        self.update_interface_list()

    # ---------------- اینترفیس ----------------
    def get_all_interfaces(self):
        interfaces = []
        try:
            r = subprocess.run("netsh interface show interface", shell=True,
                               capture_output=True, text=True, encoding="utf-8")
            lines = r.stdout.splitlines()
            active_interfaces, all_interfaces = [], []

            for line in lines:
                line = line.strip()
                if not line or line.startswith(('=', '-')):
                    continue
                if 'Admin State' in line and 'State' in line:
                    continue

                parts = re.split(r'\s{2,}', line)
                if len(parts) >= 4:
                    name = parts[-1].strip('"\'')
                    if name and len(name) > 1:
                        state = "🔥 فعال" if "Connected" in line else "⚪ غیرفعال"
                        all_interfaces.append((name, state))
                        if "Connected" in line:
                            active_interfaces.append((name, state))

            interfaces = active_interfaces + [i for i in all_interfaces if i not in active_interfaces]
        except Exception:
            pass

        if not interfaces:
            interfaces = [("Wi-Fi", "🔥 فعال"),
                          ("Ethernet", "⚪ غیرفعال"),
                          ("Local Area Connection", "⚪ غیرفعال")]
        return interfaces[:20]

    def update_interface_list(self):
        all_interfaces = self.get_all_interfaces()
        active = [n for n, s in all_interfaces if "فعال" in s]
        inactive = [n for n, s in all_interfaces if "فعال" not in s]
        self.interface_names = active + inactive

        if not self.interface_names:
            self.interface_names = [f"{RLM}(هیچ اینترفیسی یافت نشد)"]

        if self.selected_interface.get() not in self.interface_names:
            self.selected_interface.set(self.interface_names[0])

        if hasattr(self, 'interface_menu'):
            self.interface_menu.configure(values=self.interface_names)

        if hasattr(self, 'status'):
            self.update_status_display()

    def update_status_display(self):
        net = self.selected_interface.get()
        proto = self.protocol_mode.get()
        self.status.configure(text=f"{RLM}🌐 {net} | {proto}", text_color=self.green)

    def on_interface_change(self, selection):
        self.selected_interface.set(selection)
        self.update_status_display()

    def on_protocol_change(self, selection):
        self.protocol_mode.set(selection)
        self.update_status_display()

    def refresh_interfaces(self):
        self.update_interface_list()
        self.status.configure(text=f"{RLM}✅ لیست تازه‌سازی شد", text_color=self.green)

    # ---------------- UI اصلی ----------------
    def setup_ui(self):
        title = ctk.CTkFrame(self.root, fg_color=self.dark)
        title.pack(fill="x", pady=10)
        ctk.CTkLabel(title, text=f"{RLM}🎮 DNS بهینه‌ساز",
                     text_color=self.green, font=self.font_title).pack()
        ctk.CTkLabel(title, text=f"{RLM}پینگ بهتری داشته باش",
                     text_color="#bfbfbf", font=self.font_normal).pack()

        topbar = ctk.CTkFrame(self.root, fg_color=self.darker)
        topbar.pack(fill="x", padx=15, pady=(5, 0))

        ctk.CTkButton(topbar, text=f"{RLM}➕ DNS جدید", width=140,
                      fg_color=self.green, hover_color="#23985d",
                      text_color=self.darker, font=self.font_normal,
                      command=self.open_add_dns_window).pack(side="left", padx=5, pady=6)

        ctk.CTkButton(topbar, text=f"{RLM}📡 پینگ همه", width=140,
                      fg_color=self.green, hover_color="#23985d",
                      text_color=self.darker, font=self.font_normal,
                      command=self.ping_all_dns).pack(side="left", padx=5, pady=6)

        ctk.CTkButton(topbar, text=f"{RLM}👁️ DNS فعلی", width=170,
                      fg_color=self.green, hover_color="#23985d",
                      text_color=self.darker, font=self.font_normal,
                      command=self.show_current_dns).pack(side="right", padx=10, pady=6)

        tabs = ctk.CTkTabview(self.root, width=820, height=540)
        tabs.pack(padx=15, pady=10)
        try:
            tabs._segmented_button.configure(font=self.font_header,
                                             fg_color="#1f1f1f",
                                             selected_color="#2b2b2b",
                                             text_color=self.green)
        except:
            pass

        self.tab_dns = tabs.add(f"{RLM}DNS")
        self.tab_games = tabs.add(f"{RLM}بازی‌ها")
        self.tab_settings = tabs.add(f"{RLM}⚙️ تنظیمات")

        self.frame_dns = ctk.CTkFrame(self.tab_dns, fg_color=self.dark)
        self.frame_games = ctk.CTkFrame(self.tab_games, fg_color=self.dark)
        self.frame_settings = ctk.CTkFrame(self.tab_settings, fg_color=self.dark)
        for frame in [self.frame_dns, self.frame_games, self.frame_settings]:
            frame.pack(fill="both", expand=True, pady=10)

        self.build_dns_tab()
        self.build_games_tab()
        self.build_settings_tab()

        self.status = ctk.CTkLabel(self.root, text=f"{RLM}✅ آماده",
                                   anchor="center", font=self.font_normal,
                                   text_color=self.green,
                                   fg_color=self.darker, height=36)
        self.status.pack(side="bottom", fill="x", pady=6)

    # ---------------- تب تنظیمات ----------------
    def build_settings_tab(self):
        main_frame = ctk.CTkFrame(self.frame_settings, fg_color=self.dark)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        net_card = ctk.CTkFrame(main_frame, fg_color=self.card, corner_radius=15)
        net_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(net_card, text=f"{RLM}🌐 کارت شبکه فعال",
                     font=self.font_header, text_color=self.green
                     ).pack(pady=(15, 10))

        self.interface_menu = ctk.CTkOptionMenu(
            net_card,
            variable=self.selected_interface,
            values=self.interface_names,
            fg_color=self.darker,
            button_color=self.green,
            button_hover_color="#23985d",
            text_color="#ffffff",
            font=self.font_normal,
            width=500,
            height=40,
            command=self.on_interface_change
        )
        self.interface_menu.pack(pady=(0, 15), padx=20)

        ctk.CTkButton(net_card, text=f"{RLM}🔄 تازه‌سازی",
                      fg_color=self.blue, hover_color="#2563eb",
                      text_color="white", font=self.font_normal,
                      width=120, command=self.refresh_interfaces).pack()

        proto_card = ctk.CTkFrame(main_frame, fg_color=self.card, corner_radius=15)
        proto_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(proto_card, text=f"{RLM}🔌 پروتکل",
                     font=self.font_header, text_color=self.green
                     ).pack(pady=(15, 10))

        self.protocol_menu = ctk.CTkOptionMenu(
            proto_card,
            variable=self.protocol_mode,
            values=["IPv4", "IPv6"],
            fg_color=self.darker,
            button_color=self.green,
            button_hover_color="#23985d",
            text_color="#ffffff",
            font=self.font_normal,
            width=200,
            height=40,
            command=self.on_protocol_change
        )
        self.protocol_menu.pack(pady=(0, 20), padx=20)

        tools_card = ctk.CTkFrame(main_frame, fg_color=self.card, corner_radius=15)
        tools_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(tools_card, text=f"{RLM}🛠️ ابزارهای سریع",
                     font=self.font_header, text_color=self.green
                     ).pack(pady=(15, 15))

        btn_frame = ctk.CTkFrame(tools_card, fg_color="transparent")
        btn_frame.pack(pady=0, padx=20)

        ctk.CTkButton(btn_frame, text=f"{RLM}🧹 پاک DNS",
                      fg_color="#3fb881", hover_color="#2fa668",
                      text_color=self.darker, font=self.font_normal,
                      width=140, command=self.flush_dns).pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text=f"{RLM}🔄 ریست شبکه",
                      fg_color="#f59e0b", hover_color="#d97706",
                      text_color="white", font=self.font_normal,
                      width=140, command=self.restart_network).pack(side="left", padx=10)
    # ---------------- تب DNS ----------------
    def build_dns_tab(self):
        self.dns_frame = ctk.CTkScrollableFrame(self.frame_dns, fg_color=self.dark)
        self.dns_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.refresh_dns_ui()

    def refresh_dns_ui(self):
        for w in self.dns_frame.winfo_children():
            w.destroy()

        for cat, servers in self.dns_data.items():
            ctk.CTkLabel(self.dns_frame, text=f"{RLM}📁 {cat}",
                         text_color=self.green, font=self.font_header,
                         anchor="e").pack(fill="x", pady=(8, 4))

            grid = ctk.CTkFrame(self.dns_frame, fg_color="transparent")
            grid.pack(pady=2, fill="x")

            row, col = 0, 0
            for name, ips in servers.items():
                card = ctk.CTkFrame(grid, fg_color=self.card, corner_radius=10)
                card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

                ctk.CTkLabel(card, text=f"{RLM}{name}",
                             font=self.font_header, text_color=self.green,
                             anchor="center").pack(pady=(4, 2))

                ctk.CTkLabel(card, text="\n".join(ips),
                             text_color="#ccc",
                             font=ctk.CTkFont(family="Dana", size=11, weight="bold"),
                             anchor="center").pack(pady=(0, 4))

                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(pady=(0, 4))

                ctk.CTkButton(btn_frame, text=f"{RLM}ست", width=55,
                              fg_color=self.green, hover_color="#23985d",
                              text_color=self.darker, font=self.font_normal,
                              command=lambda n=name, i=ips: self.apply_dns(n, i)
                              ).pack(side="left", padx=2)

                ctk.CTkButton(btn_frame, text=f"{RLM}پینگ", width=55,
                              fg_color="#555", hover_color="#444",
                              text_color=self.green, font=self.font_normal,
                              command=lambda n=name, i=ips: self.ping_single(n, i)
                              ).pack(side="left", padx=2)

                if cat == "موارد اضافه شده":
                    edit_frame = ctk.CTkFrame(card, fg_color="transparent")
                    edit_frame.pack(pady=(0, 4))
                    ctk.CTkButton(edit_frame, text=f"{RLM}✏️", width=30,
                                  fg_color=self.blue, hover_color="#2563eb",
                                  text_color="white", font=self.font_normal,
                                  command=lambda c=cat, n=name: self.open_edit_dns_window(c, n)
                                  ).pack(side="left", padx=2)
                    ctk.CTkButton(edit_frame, text=f"{RLM}🗑", width=30,
                                  fg_color="#ef4444", hover_color="#b91c1c",
                                  text_color="white", font=self.font_normal,
                                  command=lambda c=cat, n=name: self.delete_dns(c, n)
                                  ).pack(side="left", padx=2)

                col += 1
                if col == 4:
                    row += 1
                    col = 0

            grid.grid_columnconfigure((0, 1, 2, 3), weight=1)
    # ---------------- مدیریت DNS سفارشی ----------------
    def open_add_dns_window(self):
        w = ctk.CTkToplevel(self.root)
        w.title("➕ DNS جدید")
        w.geometry("420x320")
        w.configure(fg_color=self.dark)

        ctk.CTkLabel(w, text=f"{RLM}نام DNS", text_color=self.green,
                     font=self.font_normal).pack(pady=(15, 5))
        name = ctk.CTkEntry(w, width=350, font=self.font_normal, height=35)
        name.pack(pady=5)

        ctk.CTkLabel(w, text=f"{RLM}IP اصلی", text_color=self.green,
                     font=self.font_normal).pack(pady=(10, 5))
        ip1 = ctk.CTkEntry(w, width=350, font=self.font_normal, height=35)
        ip1.pack(pady=5)

        ctk.CTkLabel(w, text=f"{RLM}IP دوم (اختیاری)", text_color=self.green,
                     font=self.font_normal).pack(pady=(10, 5))
        ip2 = ctk.CTkEntry(w, width=350, font=self.font_normal, height=35)
        ip2.pack(pady=(0, 15))

        def save():
            n, i1, i2 = name.get().strip(), ip1.get().strip(), ip2.get().strip()
            if not n or not i1:
                return messagebox.showwarning("⚠️", "نام و IP اصلی الزامی است")
            self.dns_data.setdefault("موارد اضافه شده", {})
            if n in self.dns_data["موارد اضافه شده"]:
                return messagebox.showwarning("⚠️", "نام تکراری است")
            self.dns_data["موارد اضافه شده"][n] = [i1, i2] if i2 else [i1]
            save_json_safe(DNS_FILE, self.dns_data)
            self.refresh_dns_ui()
            self.status.configure(text=f"{RLM}✅ {n} اضافه شد", text_color=self.green)
            w.destroy()

        ctk.CTkButton(w, text=f"{RLM}💾 ذخیره", fg_color=self.green,
                     width=200, height=40, font=self.font_normal,
                     command=save).pack()

    def open_edit_dns_window(self, category, dns_name):
        if category != "موارد اضافه شده":
            return messagebox.showwarning("⚠️", "فقط DNS های اضافه شده قابل ویرایش هستند")
        current_ips = self.dns_data.get(category, {}).get(dns_name, [])

        w = ctk.CTkToplevel(self.root)
        w.title("✏️ ویرایش DNS")
        w.geometry("420x320")
        w.configure(fg_color=self.dark)

        ctk.CTkLabel(w, text=f"{RLM}نام DNS", text_color=self.green,
                     font=self.font_normal).pack(pady=(15, 5))
        name_entry = ctk.CTkEntry(w, width=350, font=self.font_normal, height=35)
        name_entry.pack(pady=5)
        name_entry.insert(0, dns_name)

        ctk.CTkLabel(w, text=f"{RLM}IP اصلی", text_color=self.green,
                     font=self.font_normal).pack(pady=(10, 5))
        ip1_entry = ctk.CTkEntry(w, width=350, font=self.font_normal, height=35)
        ip1_entry.pack(pady=5)
        if len(current_ips) >= 1:
            ip1_entry.insert(0, current_ips[0])

        ctk.CTkLabel(w, text=f"{RLM}IP دوم", text_color=self.green,
                     font=self.font_normal).pack(pady=(10, 5))
        ip2_entry = ctk.CTkEntry(w, width=350, font=self.font_normal, height=35)
        ip2_entry.pack(pady=(0, 15))
        if len(current_ips) >= 2:
            ip2_entry.insert(0, current_ips[1])

        def save_edit():
            new_name = name_entry.get().strip()
            i1, i2 = ip1_entry.get().strip(), ip2_entry.get().strip()
            if not new_name or not i1:
                return messagebox.showwarning("⚠️", "نام و IP اصلی الزامی است")

            cat_dict = self.dns_data.setdefault(category, {})
            if new_name != dns_name and new_name in cat_dict:
                return messagebox.showwarning("⚠️", "نام تکراری است")

            if new_name != dns_name:
                cat_dict.pop(dns_name, None)
            cat_dict[new_name] = [i1] + ([i2] if i2 else [])

            save_json_safe(DNS_FILE, self.dns_data)
            self.refresh_dns_ui()
            self.status.configure(text=f"{RLM}✅ {new_name} ویرایش شد",
                                  text_color=self.green)
            w.destroy()

        ctk.CTkButton(w, text=f"{RLM}💾 ذخیره", fg_color=self.green,
                     width=200, height=40, font=self.font_normal,
                     command=save_edit).pack()

    def delete_dns(self, category, dns_name):
        if category != "موارد اضافه شده":
            return messagebox.showwarning("⚠️", "فقط DNS های اضافه شده قابل حذف هستند")
        if not messagebox.askyesno("حذف", f"آیا از حذف {dns_name} مطمئنید؟"):
            return
        try:
            cat_dict = self.dns_data.get(category, {})
            if dns_name in cat_dict:
                cat_dict.pop(dns_name)
                save_json_safe(DNS_FILE, self.dns_data)
                self.refresh_dns_ui()
                self.status.configure(text=f"{RLM}🗑 {dns_name} حذف شد",
                                      text_color="#ff5555")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    # ---------------- اعمال DNS و پینگ ----------------
    def apply_dns(self, name, ips):
        interface = self.selected_interface.get()
        if "(هیچ" in interface or "(در حال" in interface:
            return messagebox.showwarning("⚠️", "لطفاً کارت شبکه مناسب انتخاب کنید")

        proto = self.protocol_mode.get().lower()
        try:
            subprocess.run(f'netsh interface {proto} delete dnsservers "{interface}" all',
                           shell=True, check=True)
            subprocess.run(f'netsh interface {proto} set dnsservers "{interface}" static {ips[0]} primary',
                           shell=True, check=True)
            if len(ips) > 1:
                subprocess.run(f'netsh interface {proto} add dnsservers "{interface}" {ips[1]} index=2',
                               shell=True, check=True)
            self.status.configure(text=f"{RLM}✅ {name} روی {interface} ست شد",
                                  text_color=self.green)
        except subprocess.CalledProcessError:
            messagebox.showerror("خطا", "تنظیم DNS ناموفق")
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def ping_single(self, name, ips):
        self.status.configure(text=f"{RLM}در حال پینگ {name}...", text_color=self.green)
        lat = ping_latency(ips[0])
        status_text = f"{lat} ms" if lat != float("inf") else "Timeout"
        self.status.configure(text=f"{RLM}پینگ {name}: {status_text} ✅",
                              text_color=self.green)

    def ping_all_dns(self):
        all_ips = [(n, i[0]) for c in self.dns_data.values() for n, i in c.items()]
        if not all_ips:
            return messagebox.showinfo("پینگ", "هیچ DNS ای موجود نیست")
        threading.Thread(target=self._ping_all_thread,
                         args=(all_ips,), daemon=True).start()

    def _ping_all_thread(self, dns_list):
        results = []
        total = len(dns_list)
        for idx, (n, ip) in enumerate(dns_list, start=1):
            self.root.after(0, lambda i=idx, name=n:
                            self.status.configure(text=f"{RLM}پینگ {i}/{total}: {name}",
                                                  text_color=self.green))
            lat = ping_latency(ip)
            results.append((n, ip, lat))

        self.root.after(0, lambda: self.show_ping_results(results))

    def show_ping_results(self, results):
        lines = []
        for name, ip, lat in results:
            val = f"{lat} ms" if lat != float("inf") else "Timeout"
            lines.append(f"{name}: {ip} → {val}")
        text = "\n".join(lines)

        self.status.configure(text=f"{RLM}✅ پینگ کامل شد", text_color=self.green)
        self.show_text_window("نتایج پینگ", "📊 نتایج پینگ DNS ها",
                              f"{len(results)} سرور تست شد", text, 640, 430)

    # ---------------- تب بازی‌ها (استایل شبیه DNS) ----------------
    def build_games_tab(self):
        self.games_frame = ctk.CTkScrollableFrame(self.frame_games, fg_color=self.dark)
        self.games_frame.pack(fill="both", expand=True, padx=15, pady=15)

        grid = ctk.CTkFrame(self.games_frame, fg_color="transparent")
        grid.pack(pady=2, fill="x")

        row, col = 0, 0
        for game in self.games_data.keys():
            card = ctk.CTkFrame(grid, fg_color=self.card, corner_radius=10)
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            ctk.CTkLabel(card, text=f"{RLM}🎮 {game}",
                         font=self.font_header, text_color=self.green,
                         anchor="center").pack(pady=(6, 2), padx=6)

            ctk.CTkButton(card, text=f"{RLM}🚀 بهترین DNS",
                          width=90, fg_color=self.green, hover_color="#23985d",
                          text_color=self.darker, font=self.font_normal,
                          command=lambda g=game: self.optimize_for_game(g)
                          ).pack(pady=(2, 6), padx=6)

            col += 1
            if col == 4:
                row += 1
                col = 0

        grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def optimize_for_game(self, game):
        dns_list = self.games_data.get(game, {})
        best, best_lat = None, float("inf")
        for name, ips in dns_list.items():
            lat = ping_latency(ips[0])
            if lat < best_lat:
                best_lat, best = lat, (name, ips)
        if best:
            self.apply_dns(best[0], best[1])
            messagebox.showinfo("🎯",
                                f"بهترین DNS برای {game}:\n{best[0]}\n{best[1][0]} → {best_lat}ms")
        else:
            messagebox.showwarning("⚠️", "DNS مناسب یافت نشد")

    # ---------------- پنجره متنی + ابزارها ----------------
    def show_text_window(self, win_title, header_text, subtitle,
                         body_text, width=560, height=420):
        w = ctk.CTkToplevel(self.root)
        w.title(win_title)
        w.geometry(f"{width}x{height}")
        w.configure(fg_color=self.dark)

        ctk.CTkLabel(w, text=f"{RLM}{header_text}",
                     text_color=self.green, font=self.font_title
                     ).pack(pady=(15, 5))
        if subtitle:
            ctk.CTkLabel(w, text=f"{RLM}{subtitle}",
                         text_color="#bfbfbf", font=self.font_normal
                         ).pack(pady=(0, 10))

        box = ctk.CTkTextbox(w, width=width-40, height=height-140,
                             fg_color=self.card, text_color="#f3f3f3",
                             font=self.font_normal)
        box.pack(padx=20, pady=(0, 15), fill="both", expand=True)
        box.insert("1.0", body_text)
        box.configure(state="disabled")

        ctk.CTkButton(w, text=f"{RLM}بستن",
                      fg_color=self.green, width=120, height=35,
                      font=self.font_normal, command=w.destroy).pack()

    def show_current_dns(self):
        interface = self.selected_interface.get()
        if "(هیچ" in interface or "(در حال" in interface:
            return messagebox.showwarning("⚠️", "کارت شبکه انتخاب کنید")

        proto = self.protocol_mode.get().lower()
        r = subprocess.run(f'netsh interface {proto} show dnsservers "{interface}"',
                           shell=True, capture_output=True, text=True)
        out = r.stdout.strip() or "هیچ DNS فعالی تنظیم نشده"

        self.show_text_window("DNS فعلی", "📡 DNS های فعلی",
                              f"{interface} | {proto.upper()}",
                              out, 620, 420)

    def flush_dns(self):
        try:
            subprocess.run("ipconfig /flushdns", shell=True, check=True)
            self.status.configure(text=f"{RLM}✅ کش DNS پاک شد",
                                  text_color=self.green)
        except:
            messagebox.showerror("خطا", "پاک‌سازی DNS ناموفق")

    def restart_network(self):
        if messagebox.askyesno("تأیید", "آیا از ریستارت اتصالات شبکه مطمئنید؟"):
            try:
                subprocess.run("netsh winsock reset", shell=True)
                subprocess.run("netsh int ip reset", shell=True)
                messagebox.showinfo("✅",
                                    "شبکه ریستارت شد. لطفاً سیستم را ریستارت کنید.")
            except:
                messagebox.showerror("خطا", "ریستارت شبکه ناموفق")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DNSGameOptimizer()
    app.run()
