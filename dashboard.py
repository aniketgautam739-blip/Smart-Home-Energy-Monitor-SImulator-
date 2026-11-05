
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import math
import csv
import time
import os
from datetime import datetime

# ============================================================
# ANIKET'S SMART HOME ENERGY MONITOR
# Professional desktop IoT demonstration dashboard
# Python standard libraries only
# All sensor and city readings are SIMULATED.
# ============================================================

BG = "#0B1020"
SIDEBAR = "#0E1729"
PANEL = "#121E32"
CARD = "#17253B"
CARD2 = "#1C2D46"
BORDER = "#283B54"
GREEN = "#42E5AE"
BLUE = "#66A8FF"
PURPLE = "#B5A0FF"
ORANGE = "#FFBE70"
RED = "#FF7189"
WHITE = "#F3F7FC"
MUTED = "#93A5BC"

TARIFF = 10.0
MONTH_DAYS = 30
UPDATE_MS = 1000
CITY_LOG_SECONDS = 5

DEFAULT_APPLIANCES = [
    {"name": "LED Bulb", "power": 10, "hours": 6},
    {"name": "Ceiling Fan", "power": 100, "hours": 8},
    {"name": "Laptop", "power": 65, "hours": 5},
    {"name": "Television", "power": 100, "hours": 4},
    {"name": "Refrigerator", "power": 150, "hours": 8},
    {"name": "Water Pump", "power": 750, "hours": 1},
]

CITY_BASELINES = {
    "Kathmandu": 420,
    "Pokhara": 350,
    "Lalitpur": 390,
    "Biratnagar": 460,
    "Chitwan": 320,
}


class EnergyMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Aniket | Smart Home Energy Monitor")
        self.root.geometry("1450x900")
        self.root.minsize(1050, 700)
        self.root.configure(bg=BG)

        self.appliances = [a.copy() for a in DEFAULT_APPLIANCES]
        self.monitoring = True
        self.started_at = time.time()
        self.last_update = time.time()
        self.last_city_log = 0
        self.session_energy = 0.0

        self.current_power = 0.0
        self.current_voltage = 230.0
        self.current_current = 0.0
        self.current_time = datetime.now()

        self.power_history = []
        self.live_log = []
        self.city_log = []
        self.city_values = {}
        self.max_history = 60
        self.active_page = "Overview"

        self.setup_styles()
        self.build_shell()
        self.build_pages()
        self.show_page("Overview")
        self.refresh_appliance_table()
        self.update_live_data()

    # -------------------- STYLE --------------------

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=PANEL,
            foreground=WHITE,
            fieldbackground=PANEL,
            rowheight=38,
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background=CARD2,
            foreground=WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=10
        )
        style.map(
            "Treeview",
            background=[("selected", "#245849")],
            foreground=[("selected", WHITE)]
        )
        style.configure(
            "TCombobox",
            fieldbackground=CARD,
            background=CARD,
            foreground=WHITE
        )

    def label(self, parent, text, size=10, color=WHITE,
              bold=False, bg=None, **kwargs):
        return tk.Label(
            parent,
            text=text,
            bg=bg or parent.cget("bg"),
            fg=color,
            font=("Segoe UI", size, "bold" if bold else "normal"),
            **kwargs
        )

    def button(self, parent, text, command, color=CARD2,
               fg=WHITE, padx=15, pady=10):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=fg,
            activebackground=BORDER,
            activeforeground=WHITE,
            bd=0,
            relief="flat",
            padx=padx,
            pady=pady,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )

    def make_card(self, parent, title, value, detail, accent=GREEN):
        card = tk.Frame(
            parent, bg=CARD, padx=18, pady=17,
            highlightbackground=BORDER, highlightthickness=1
        )
        self.label(card, title.upper(), 9, MUTED, True).pack(anchor="w")

        value_label = self.label(
            card, value, 23, accent, True
        )
        value_label.pack(anchor="w", pady=(12, 5))

        detail_label = self.label(
            card, detail, 9, MUTED
        )
        detail_label.pack(anchor="w")

        return card, value_label, detail_label

    # -------------------- MAIN SHELL --------------------

    def build_shell(self):
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR, width=238)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=22, pady=(30, 28))

        self.label(brand, "◆  ANIKET", 20, GREEN, True).pack(anchor="w")
        self.label(brand, "SMART HOME ENERGY", 10, WHITE, True).pack(
            anchor="w", pady=(7, 0)
        )
        self.label(brand, "IoT MONITORING PLATFORM", 8, MUTED).pack(
            anchor="w", pady=(5, 0)
        )

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(
            fill="x", padx=18, pady=(0, 18)
        )

        self.nav_buttons = {}
        navigation = [
            ("Overview", "◈", "Overview"),
            ("Appliances", "▦", "Appliances"),
            ("City Monitor", "⌁", "City Monitor"),
            ("Smart Suggestions", "✦", "Smart Suggestions"),
            ("Reports", "▤", "Reports"),
        ]

        for page, icon, text in navigation:
            b = tk.Button(
                self.sidebar,
                text=f"   {icon}    {text}",
                anchor="w",
                bg=SIDEBAR,
                fg=MUTED,
                activebackground=CARD2,
                activeforeground=GREEN,
                bd=0,
                padx=15,
                pady=15,
                font=("Segoe UI", 10, "bold"),
                cursor="hand2",
                command=lambda p=page: self.show_page(p)
            )
            b.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[page] = b

        spacer = tk.Frame(self.sidebar, bg=SIDEBAR)
        spacer.pack(fill="both", expand=True)

        status_box = tk.Frame(
            self.sidebar, bg=PANEL, padx=14, pady=15
        )
        status_box.pack(fill="x", padx=13, pady=(0, 12))

        self.label(status_box, "SYSTEM STATUS", 9, MUTED, True).pack(
            anchor="w"
        )

        self.status_label = self.label(
            status_box, "● MONITORING", 10, GREEN, True
        )
        self.status_label.pack(anchor="w", pady=(9, 5))

        self.label(
            status_box, "Python simulation mode",
            9, MUTED, wraplength=180, justify="left"
        ).pack(anchor="w")

        self.label(
            self.sidebar, "PROJECT DEMONSTRATION  •  v2.0",
            8, MUTED
        ).pack(padx=10, pady=(0, 16))

        self.workspace = tk.Frame(self.root, bg=BG)
        self.workspace.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.workspace, bg=BG)
        header.pack(fill="x", padx=30, pady=(23, 17))

        self.page_title = self.label(header, "Overview", 23, WHITE, True)
        self.page_title.pack(side="left")

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")

        self.header_status = self.label(
            right, "● SIMULATION ACTIVE", 9, GREEN, True
        )
        self.header_status.pack(anchor="e")

        self.clock_label = self.label(right, "", 10, MUTED)
        self.clock_label.pack(anchor="e", pady=(6, 0))

        tk.Frame(
            self.workspace, bg=BORDER, height=1
        ).pack(fill="x", padx=30)

        self.container = tk.Frame(self.workspace, bg=BG)
        self.container.pack(
            fill="both", expand=True, padx=30, pady=(20, 25)
        )

        self.pages = {}

    def new_page(self, name):
        page = tk.Frame(self.container, bg=BG)
        self.pages[name] = page
        return page

    def show_page(self, name):
        for page in self.pages.values():
            page.pack_forget()

        self.pages[name].pack(fill="both", expand=True)
        self.active_page = name
        self.page_title.config(text=name)

        for page_name, button in self.nav_buttons.items():
            active = page_name == name
            button.config(
                bg=CARD2 if active else SIDEBAR,
                fg=GREEN if active else MUTED
            )

        if name == "Appliances":
            self.refresh_appliance_table()
        elif name == "City Monitor":
            self.refresh_city_table()
            self.draw_city_chart()
        elif name == "Smart Suggestions":
            self.refresh_suggestions()
        elif name == "Reports":
            self.refresh_report()

    def build_pages(self):
        self.build_overview()
        self.build_appliances()
        self.build_city_monitor()
        self.build_suggestions()
        self.build_reports()

    # -------------------- OVERVIEW --------------------

    def build_overview(self):
        page = self.new_page("Overview")

        self.label(page, "Your energy at a glance", 15, WHITE, True).pack(
            anchor="w"
        )
        self.label(
            page,
            "Monitor simulated household power, voltage and energy usage.",
            10, MUTED
        ).pack(anchor="w", pady=(5, 18))

        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", pady=(0, 18))

        for i in range(4):
            cards.columnconfigure(i, weight=1, uniform="metric")

        self.card_power, self.power_value, self.power_detail = self.make_card(
            cards, "Live Power", "0.0 W",
            "Current simulated load", GREEN
        )
        self.card_voltage, self.voltage_value, self.voltage_detail = self.make_card(
            cards, "Voltage", "230.0 V",
            "Simulated supply voltage", BLUE
        )
        self.card_current, self.current_value, self.current_detail = self.make_card(
            cards, "Current", "0.000 A",
            "Estimated from power / voltage", PURPLE
        )
        self.card_energy, self.energy_value, self.energy_detail = self.make_card(
            cards, "Session Energy", "0.000000 kWh",
            "Accumulated while running", ORANGE
        )

        for i, card in enumerate([
            self.card_power, self.card_voltage,
            self.card_current, self.card_energy
        ]):
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0 if i == 0 else 9, 0))

        chart_card = tk.Frame(
            page, bg=CARD, padx=18, pady=16,
            highlightbackground=BORDER, highlightthickness=1
        )
        chart_card.pack(fill="both", expand=True)

        chart_header = tk.Frame(chart_card, bg=CARD)
        chart_header.pack(fill="x")

        self.label(
            chart_header, "POWER CONSUMPTION", 11, WHITE, True
        ).pack(side="left")

        self.graph_status = self.label(
            chart_header, "● LIVE", 9, GREEN, True
        )
        self.graph_status.pack(side="right")

        self.chart = tk.Canvas(
            chart_card, bg=CARD, height=270,
            highlightthickness=0
        )
        self.chart.pack(fill="both", expand=True, pady=(12, 4))
        self.chart.bind("<Configure>", lambda e: self.draw_power_chart())

        footer = tk.Frame(page, bg=BG)
        footer.pack(fill="x", pady=(15, 0))

        self.monitor_button = self.button(
            footer, "Ⅱ  Pause Monitoring",
            self.toggle_monitoring, GREEN, "#07150F"
        )
        self.monitor_button.pack(side="left")

        self.button(
            footer, "↓  Export Live Data",
            self.export_live_data, CARD2
        ).pack(side="left", padx=10)

        self.reading_label = self.label(
            footer, "Waiting for first reading...", 9, MUTED
        )
        self.reading_label.pack(side="right")

    # -------------------- APPLIANCES --------------------

    def build_appliances(self):
        page = self.new_page("Appliances")

        self.label(page, "Appliance management", 15, WHITE, True).pack(
            anchor="w"
        )
        self.label(
            page,
            "Add, edit or remove devices. Energy and cost estimates recalculate automatically.",
            10, MUTED
        ).pack(anchor="w", pady=(5, 17))

        summary = tk.Frame(page, bg=BG)
        summary.pack(fill="x", pady=(0, 15))

        self.appliance_count_label = self.label(
            summary, "6 DEVICES", 10, GREEN, True
        )
        self.appliance_count_label.pack(side="left")

        self.appliance_total_label = self.label(
            summary, "", 10, MUTED
        )
        self.appliance_total_label.pack(side="right")

        table_box = tk.Frame(
            page, bg=CARD,
            highlightbackground=BORDER, highlightthickness=1
        )
        table_box.pack(fill="both", expand=True)

        columns = ("name", "power", "hours", "daily", "monthly", "cost")
        self.appliance_table = ttk.Treeview(
            table_box, columns=columns, show="headings",
            selectmode="browse"
        )

        headings = {
            "name": ("APPLIANCE", 205),
            "power": ("RATING (W)", 105),
            "hours": ("HOURS / DAY", 115),
            "daily": ("DAILY (kWh)", 120),
            "monthly": ("MONTHLY (kWh)", 135),
            "cost": ("MONTHLY COST", 145),
        }

        for col, (heading, width) in headings.items():
            self.appliance_table.heading(col, text=heading)
            self.appliance_table.column(
                col, width=width, minwidth=75, anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            table_box, orient="vertical",
            command=self.appliance_table.yview
        )
        self.appliance_table.configure(yscrollcommand=scrollbar.set)
        self.appliance_table.pack(
            side="left", fill="both", expand=True, padx=8, pady=8
        )
        scrollbar.pack(side="right", fill="y", pady=8)

        self.appliance_table.bind(
            "<Double-1>", lambda e: self.edit_appliance()
        )

        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="x", pady=(16, 12))

        self.button(
            actions, "+  Add Appliance", self.add_appliance,
            GREEN, "#07150F"
        ).pack(side="left")

        self.button(
            actions, "✎  Edit Selected", self.edit_appliance,
            BLUE
        ).pack(side="left", padx=10)

        self.button(
            actions, "−  Remove Selected", self.remove_appliance,
            "#592638"
        ).pack(side="left")

        self.appliance_summary = tk.Label(
            page, text="", bg=BG, fg=MUTED,
            font=("Segoe UI", 10), anchor="w", justify="left"
        )
        self.appliance_summary.pack(fill="x", pady=(4, 0))

    def refresh_appliance_table(self):
        if not hasattr(self, "appliance_table"):
            return

        for row in self.appliance_table.get_children():
            self.appliance_table.delete(row)

        for i, item in enumerate(self.appliances):
            daily = item["power"] * item["hours"] / 1000
            monthly = daily * MONTH_DAYS
            cost = monthly * TARIFF

            self.appliance_table.insert(
                "", "end", iid=str(i),
                values=(
                    item["name"],
                    f'{item["power"]:g}',
                    f'{item["hours"]:g}',
                    f"{daily:.3f}",
                    f"{monthly:.2f}",
                    f"Rs {cost:,.2f}"
                )
            )

        connected, daily, monthly, daily_cost, monthly_cost = (
            self.calculate_data()
        )

        self.appliance_count_label.config(
            text=f"{len(self.appliances)} CONFIGURED DEVICES"
        )
        self.appliance_total_label.config(
            text=f"CONNECTED RATING  {connected:,.0f} W"
        )
        self.appliance_summary.config(
            text=(
                f"Estimated daily usage: {daily:.3f} kWh     •     "
                f"Monthly usage: {monthly:.2f} kWh     •     "
                f"Monthly cost: Rs {monthly_cost:,.2f}\n"
                f"Illustrative tariff: Rs {TARIFF:.2f}/kWh. "
                "Actual electricity bills may use different tariff slabs."
            )
        )

    def appliance_editor(self, title, existing=None):
        editing = existing is not None

        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=BG)
        win.geometry("490x500")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        outer = tk.Frame(win, bg=BG, padx=28, pady=24)
        outer.pack(fill="both", expand=True)

        self.label(outer, title, 20, WHITE, True).pack(anchor="w")
        self.label(
            outer, "Enter the appliance details below.",
            10, MUTED
        ).pack(anchor="w", pady=(5, 20))

        fields = {}

        field_definitions = [
            ("name", "Appliance name", ""),
            ("power", "Rated power (watts)", ""),
            ("hours", "Daily usage (0–24 hours)", ""),
        ]

        for key, caption, default in field_definitions:
            self.label(
                outer, caption, 10, MUTED, True
            ).pack(anchor="w", pady=(8, 6))

            entry = tk.Entry(
                outer, bg=CARD, fg=WHITE,
                insertbackground=WHITE, relief="flat",
                font=("Segoe UI", 12),
                highlightthickness=1,
                highlightbackground=BORDER,
                highlightcolor=GREEN
            )
            entry.pack(fill="x", ipady=10)

            if editing:
                entry.insert(0, str(existing[key]))
            elif default:
                entry.insert(0, default)

            fields[key] = entry

        def save():
            name = fields["name"].get().strip()

            if not name:
                messagebox.showerror(
                    "Missing name",
                    "Please enter an appliance name.", parent=win
                )
                return

            try:
                power = float(fields["power"].get())
                hours = float(fields["hours"].get())
            except ValueError:
                messagebox.showerror(
                    "Invalid input",
                    "Power and hours must be valid numbers.", parent=win
                )
                return

            if not math.isfinite(power) or not 0 < power <= 100000:
                messagebox.showerror(
                    "Invalid power",
                    "Power must be above 0 and at most 100,000 W.",
                    parent=win
                )
                return

            if not math.isfinite(hours) or not 0 <= hours <= 24:
                messagebox.showerror(
                    "Invalid usage",
                    "Daily usage must be between 0 and 24 hours.",
                    parent=win
                )
                return

            new_item = {
                "name": name,
                "power": power,
                "hours": hours
            }

            if editing:
                index = self.appliances.index(existing)
                self.appliances[index] = new_item
            else:
                self.appliances.append(new_item)

            self.refresh_appliance_table()
            self.update_overview_values()
            win.destroy()

        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill="x", pady=(23, 0))

        self.button(
            footer, "Save Appliance", save,
            GREEN, "#07150F"
        ).pack(side="left")

        self.button(
            footer, "Cancel", win.destroy
        ).pack(side="left", padx=10)

        fields["name"].focus_set()

    def add_appliance(self):
        self.appliance_editor("Add New Appliance")

    def edit_appliance(self):
        selected = self.appliance_table.selection()
        if not selected:
            messagebox.showinfo(
                "Select a device",
                "Select an appliance from the table first."
            )
            return

        self.appliance_editor(
            "Edit Appliance",
            self.appliances[int(selected[0])]
        )

    def remove_appliance(self):
        selected = self.appliance_table.selection()

        if not selected:
            messagebox.showinfo(
                "Select a device",
                "Select an appliance to remove."
            )
            return

        index = int(selected[0])
        name = self.appliances[index]["name"]

        if messagebox.askyesno(
            "Remove appliance",
            f"Are you sure you want to remove {name}?"
        ):
            del self.appliances[index]
            self.refresh_appliance_table()
            self.update_overview_values()

    # -------------------- CITY MONITOR --------------------

    def build_city_monitor(self):
        page = self.new_page("City Monitor")

        self.label(
            page, "City energy comparison", 15, WHITE, True
        ).pack(anchor="w")

        self.label(
            page,
            "Compare illustrative city-level power demand and record timestamped readings.",
            10, MUTED
        ).pack(anchor="w", pady=(5, 14))

        warning = tk.Frame(page, bg="#332B20", padx=14, pady=11)
        warning.pack(fill="x", pady=(0, 15))

        self.label(
            warning,
            "DEMO DATA  •  City values are simulated, not official electricity statistics.",
            9, ORANGE, True
        ).pack(anchor="w")

        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", pady=(0, 15))

        for i in range(3):
            cards.columnconfigure(i, weight=1, uniform="city")

        self.city_avg_card, self.city_avg_value, self.city_avg_detail = (
            self.make_card(
                cards, "City Average", "0 W",
                "Mean of five simulated cities", BLUE
            )
        )
        self.city_max_card, self.city_max_value, self.city_max_detail = (
            self.make_card(
                cards, "Highest Reading", "—",
                "Current simulated leader", ORANGE
            )
        )
        self.city_records_card, self.city_records_value, self.city_records_detail = (
            self.make_card(
                cards, "Recorded Samples", "0",
                "Timestamped city records", PURPLE
            )
        )

        for i, card in enumerate([
            self.city_avg_card,
            self.city_max_card,
            self.city_records_card
        ]):
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0 if i == 0 else 9, 0))

        chartbox = tk.Frame(
            page, bg=CARD, padx=14, pady=12,
            highlightbackground=BORDER, highlightthickness=1
        )
        chartbox.pack(fill="both", expand=True, pady=(0, 13))

        self.label(
            chartbox, "AVERAGE SIMULATED POWER BY CITY", 10, WHITE, True
        ).pack(anchor="w")

        self.city_chart = tk.Canvas(
            chartbox, bg=CARD, height=175,
            highlightthickness=0
        )
        self.city_chart.pack(fill="both", expand=True, pady=(8, 0))
        self.city_chart.bind(
            "<Configure>", lambda e: self.draw_city_chart()
        )

        tablebox = tk.Frame(
            page, bg=CARD,
            highlightbackground=BORDER, highlightthickness=1
        )
        tablebox.pack(fill="both", expand=True)

        cols = ("city", "power", "voltage", "current", "updated")
        self.city_table = ttk.Treeview(
            tablebox, columns=cols, show="headings", height=5
        )

        for col, heading, width in [
            ("city", "CITY", 160),
            ("power", "AVG. POWER (W)", 145),
            ("voltage", "VOLTAGE (V)", 130),
            ("current", "CURRENT (A)", 130),
            ("updated", "LAST RECORDED", 220),
        ]:
            self.city_table.heading(col, text=heading)
            self.city_table.column(
                col, width=width, anchor="center"
            )

        self.city_table.pack(
            fill="both", expand=True, padx=6, pady=6
        )

        actions = tk.Frame(page, bg=BG)
        actions.pack(fill="x", pady=(12, 0))

        self.button(
            actions, "↓  Export City Records",
            self.export_city_data, BLUE
        ).pack(side="left")

        self.button(
            actions, "Clear Recorded History",
            self.clear_city_history, "#592638"
        ).pack(side="left", padx=10)

    def update_cities(self, now):
        for city, baseline in CITY_BASELINES.items():
            if city not in self.city_values:
                self.city_values[city] = {
                    "power": float(baseline),
                    "voltage": 230.0,
                    "current": 0.0,
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
                }

            old = self.city_values[city]["power"]
            # Small smooth changes create a demonstration time series.
            variation = random.uniform(-0.035, 0.035)
            cycle = 0.012 * math.sin(time.time() / 12 + baseline)
            power = max(20, old * (1 + variation + cycle))
            voltage = 230 + random.uniform(-1.5, 1.5)

            self.city_values[city] = {
                "power": power,
                "voltage": voltage,
                "current": power / voltage,
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
            }

        if time.time() - self.last_city_log >= CITY_LOG_SECONDS:
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

            for city, values in self.city_values.items():
                self.city_log.append({
                    "timestamp": timestamp,
                    "city": city,
                    "average_power_W": round(values["power"], 2),
                    "voltage_V": round(values["voltage"], 2),
                    "current_A": round(values["current"], 3),
                    "data_type": "SIMULATED"
                })

            self.last_city_log = time.time()

    def refresh_city_table(self):
        if not hasattr(self, "city_table"):
            return

        for row in self.city_table.get_children():
            self.city_table.delete(row)

        for city, v in self.city_values.items():
            self.city_table.insert(
                "", "end",
                values=(
                    city,
                    f'{v["power"]:.1f}',
                    f'{v["voltage"]:.1f}',
                    f'{v["current"]:.3f}',
                    v["timestamp"].split(" ")[1]
                )
            )

        if self.city_values:
            average = sum(
                v["power"] for v in self.city_values.values()
            ) / len(self.city_values)

            highest_city = max(
                self.city_values,
                key=lambda city: self.city_values[city]["power"]
            )

            self.city_avg_value.config(text=f"{average:.1f} W")
            self.city_max_value.config(
                text=highest_city,
                font=("Segoe UI", 17, "bold")
            )
            self.city_max_detail.config(
                text=f'{self.city_values[highest_city]["power"]:.1f} W'
            )
            self.city_records_value.config(text=str(len(self.city_log)))

    def draw_city_chart(self):
        if not hasattr(self, "city_chart"):
            return

        c = self.city_chart
        c.delete("all")
        w = max(c.winfo_width(), 350)
        h = max(c.winfo_height(), 130)

        if not self.city_values:
            c.create_text(
                w / 2, h / 2,
                text="Collecting simulated city readings...",
                fill=MUTED, font=("Segoe UI", 10)
            )
            return

        cities = list(self.city_values.keys())
        values = [self.city_values[x]["power"] for x in cities]
        maximum = max(values) * 1.25
        left, right = 15, w - 15
        usable = right - left
        gap = usable / len(cities)
        baseline = h - 29
        top = 10

        for i, city in enumerate(cities):
            xmid = left + gap * (i + 0.5)
            bar_width = gap * 0.42
            bar_height = (baseline - top) * values[i] / maximum
            x1, x2 = xmid - bar_width / 2, xmid + bar_width / 2
            y1 = baseline - bar_height

            c.create_rectangle(
                x1, y1, x2, baseline,
                fill=BLUE, outline=""
            )
            c.create_text(
                xmid, y1 - 10,
                text=f"{values[i]:.0f} W",
                fill=WHITE, font=("Segoe UI", 8, "bold")
            )
            c.create_text(
                xmid, baseline + 15,
                text=city, fill=MUTED,
                font=("Segoe UI", 8)
            )

    def export_city_data(self):
        if not self.city_log:
            messagebox.showinfo(
                "No city records",
                "Let the monitor run for at least five seconds first."
            )
            return

        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export City Monitor History",
            defaultextension=".csv",
            initialfile="city_energy_history.csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        self.write_csv(path, self.city_log)

    def clear_city_history(self):
        if not messagebox.askyesno(
            "Clear history",
            "Delete all recorded city readings from this session?"
        ):
            return

        self.city_log.clear()
        self.last_city_log = 0
        self.refresh_city_table()

    # -------------------- SMART SUGGESTIONS --------------------

    def build_suggestions(self):
        page = self.new_page("Smart Suggestions")

        self.label(
            page, "Your smart energy advisor", 15, WHITE, True
        ).pack(anchor="w")

        self.label(
            page,
            "Recommendations are generated from your appliance settings and estimated costs.",
            10, MUTED
        ).pack(anchor="w", pady=(5, 17))

        cards = tk.Frame(page, bg=BG)
        cards.pack(fill="x", pady=(0, 15))

        for i in range(3):
            cards.columnconfigure(i, weight=1, uniform="advice")

        self.advice_daily_card, self.advice_daily_value, _ = self.make_card(
            cards, "Daily Energy", "0 kWh",
            "Estimated household usage", GREEN
        )
        self.advice_cost_card, self.advice_cost_value, _ = self.make_card(
            cards, "Monthly Cost", "Rs 0",
            "At the configured tariff", ORANGE
        )
        self.advice_top_card, self.advice_top_value, _ = self.make_card(
            cards, "Largest Consumer", "—",
            "By estimated daily energy", PURPLE
        )

        for i, card in enumerate([
            self.advice_daily_card,
            self.advice_cost_card,
            self.advice_top_card
        ]):
            card.grid(row=0, column=i, sticky="nsew",
                      padx=(0 if i == 0 else 9, 0))

        body = tk.Frame(
            page, bg=CARD, padx=22, pady=20,
            highlightbackground=BORDER, highlightthickness=1
        )
        body.pack(fill="both", expand=True)

        self.label(
            body, "PERSONALIZED RECOMMENDATIONS", 11, WHITE, True
        ).pack(anchor="w")

        self.suggestion_text = tk.Text(
            body, bg=CARD, fg=WHITE,
            insertbackground=WHITE, relief="flat",
            font=("Segoe UI", 11), wrap="word",
            padx=2, pady=12, spacing1=5, spacing3=7,
            height=16, state="disabled"
        )
        self.suggestion_text.pack(fill="both", expand=True)

        self.button(
            page, "↻  Refresh Recommendations",
            self.refresh_suggestions, GREEN, "#07150F"
        ).pack(anchor="w", pady=(13, 0))

    def refresh_suggestions(self):
        if not hasattr(self, "suggestion_text"):
            return

        connected, daily, monthly, daily_cost, monthly_cost = (
            self.calculate_data()
        )

        ranked = sorted(
            self.appliances,
            key=lambda a: a["power"] * a["hours"],
            reverse=True
        )

        self.advice_daily_value.config(text=f"{daily:.2f} kWh")
        self.advice_cost_value.config(text=f"Rs {monthly_cost:,.0f}")

        if ranked:
            self.advice_top_value.config(
                text=ranked[0]["name"],
                font=("Segoe UI", 15, "bold")
            )
        else:
            self.advice_top_value.config(text="No devices")

        lines = [
            "YOUR ENERGY PROFILE",
            f"Configured appliance rating: {connected:,.0f} W",
            f"Estimated daily usage: {daily:.3f} kWh",
            f"Estimated monthly usage: {monthly:.2f} kWh",
            f"Estimated monthly bill: Rs {monthly_cost:,.2f}",
            "",
            "RECOMMENDED ACTIONS",
            ""
        ]

        if not ranked:
            lines.append(
                "Add some appliances to generate personalized suggestions."
            )
        else:
            for index, item in enumerate(ranked[:5], start=1):
                energy = item["power"] * item["hours"] / 1000
                cost = energy * MONTH_DAYS * TARIFF

                lines.append(
                    f"{index}. {item['name']} — review this appliance"
                )
                lines.append(
                    f"   Estimated use: {energy:.3f} kWh/day; "
                    f"monthly cost: Rs {cost:,.2f}."
                )

                if item["hours"] >= 6:
                    lines.append(
                        "   Consider whether its daily operating hours "
                        "can be reduced without affecting essential use."
                    )
                elif item["power"] >= 500:
                    lines.append(
                        "   This is a relatively high-power appliance. "
                        "Avoid unnecessary operation and standby use."
                    )
                else:
                    lines.append(
                        "   Check for avoidable operating time and "
                        "switch the device off when not needed."
                    )

                lines.append("")

        # Illustrative savings scenarios, not guaranteed savings.
        saving_10 = daily_cost * 0.10
        saving_15 = daily_cost * 0.15

        lines.extend([
            "ILLUSTRATIVE SAVINGS SCENARIOS",
            "",
            f"If total daily consumption fell by 10%, the estimated "
            f"saving would be Rs {saving_10 * MONTH_DAYS:,.2f} per month.",
            f"At a 15% reduction, the estimated saving would be "
            f"Rs {saving_15 * MONTH_DAYS:,.2f} per month.",
            "",
            "PRACTICAL ENERGY TIPS",
            "",
            "• Replace frequently used incandescent bulbs with suitable LEDs.",
            "• Avoid leaving computers, televisions and chargers running unnecessarily.",
            "• Check refrigerator door seals and allow adequate ventilation.",
            "• Use pumps and other high-power equipment only when required.",
            "• Compare these estimates with your actual electricity bill.",
            "",
            "IMPORTANT",
            "",
            "Recommendations use the configured wattage and operating hours. "
            "Savings are illustrative and depend on actual usage. "
            "The live sensor values in this project are simulated."
        ])

        self.suggestion_text.config(state="normal")
        self.suggestion_text.delete("1.0", "end")
        self.suggestion_text.insert("1.0", "\n".join(lines))
        self.suggestion_text.config(state="disabled")

    # -------------------- REPORTS --------------------

    def build_reports(self):
        page = self.new_page("Reports")

        self.label(
            page, "Reports & data centre", 15, WHITE, True
        ).pack(anchor="w")

        self.label(
            page,
            "Export your appliance configuration and timestamped demonstration readings.",
            10, MUTED
        ).pack(anchor="w", pady=(5, 18))

        box = tk.Frame(
            page, bg=CARD, padx=22, pady=22,
            highlightbackground=BORDER, highlightthickness=1
        )
        box.pack(fill="x", pady=(0, 15))

        self.label(
            box, "SESSION SUMMARY", 11, WHITE, True
        ).pack(anchor="w")

        self.report_summary = self.label(
            box, "", 11, MUTED, justify="left", anchor="w"
        )
        self.report_summary.pack(anchor="w", pady=(15, 0))

        self.label(
            page, "EXPORT OPTIONS", 11, WHITE, True
        ).pack(anchor="w", pady=(10, 12))

        self.button(
            page, "↓  Export Appliance Summary CSV",
            self.export_appliance_summary, GREEN, "#07150F"
        ).pack(anchor="w", pady=(0, 11))

        self.button(
            page, "↓  Export Timestamped Live Readings",
            self.export_live_data, BLUE
        ).pack(anchor="w", pady=(0, 11))

        self.button(
            page, "↓  Export City Monitor History",
            self.export_city_data, PURPLE
        ).pack(anchor="w", pady=(0, 11))

        note = tk.Frame(page, bg="#332B20", padx=15, pady=12)
        note.pack(fill="x", pady=(13, 0))

        self.label(
            note,
            "DATA INTEGRITY: live power, voltage, current and city readings "
            "are simulated. Appliance energy and cost are estimates.",
            9, ORANGE, wraplength=900, justify="left"
        ).pack(anchor="w")

    def refresh_report(self):
        if not hasattr(self, "report_summary"):
            return

        connected, daily, monthly, daily_cost, monthly_cost = (
            self.calculate_data()
        )
        elapsed = max(0, int(time.time() - self.started_at))
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.report_summary.config(
            text=(
                f"Project: Aniket's Smart Home Energy Monitor\n\n"
                f"Configured appliances: {len(self.appliances)}\n"
                f"Combined rated power: {connected:,.0f} W\n"
                f"Estimated daily consumption: {daily:.3f} kWh\n"
                f"Estimated monthly consumption: {monthly:.2f} kWh\n"
                f"Estimated daily cost: Rs {daily_cost:,.2f}\n"
                f"Estimated monthly cost: Rs {monthly_cost:,.2f}\n\n"
                f"Live sensor records: {len(self.live_log)}\n"
                f"City records: {len(self.city_log)}\n"
                f"Session duration: {hours:02d}:{minutes:02d}:{seconds:02d}\n"
                f"Monitoring: {'Running' if self.monitoring else 'Paused'}\n"
                f"Report generated: {datetime.now():%d %b %Y, %H:%M:%S}"
            )
        )

    # -------------------- CALCULATIONS --------------------

    def calculate_data(self):
        connected = sum(a["power"] for a in self.appliances)
        daily = sum(
            a["power"] * a["hours"] / 1000
            for a in self.appliances
        )
        monthly = daily * MONTH_DAYS
        daily_cost = daily * TARIFF
        monthly_cost = monthly * TARIFF

        return connected, daily, monthly, daily_cost, monthly_cost

    # -------------------- LIVE MONITOR --------------------

    def update_live_data(self):
        now = time.time()
        elapsed = max(0.0, min(now - self.last_update, 5.0))
        self.last_update = now
        self.current_time = datetime.now()

        connected, daily, monthly, daily_cost, monthly_cost = (
            self.calculate_data()
        )

        if self.monitoring:
            variation = random.uniform(0.94, 1.06)
            cycle = 1 + 0.025 * math.sin(now / 4)
            self.current_power = max(0, connected * variation * cycle)
            self.current_voltage = 230 + random.uniform(-2, 2)
            self.current_current = (
                self.current_power / max(self.current_voltage, 1)
            )

            self.session_energy += (
                self.current_power * elapsed / 3600000
            )

            self.power_history.append(
                (self.current_time, self.current_power)
            )
            self.power_history = self.power_history[-self.max_history:]

            if not hasattr(self, "last_live_log"):
                self.last_live_log = 0

            if now - self.last_live_log >= 5:
                self.live_log.append({
                    "timestamp": self.current_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "voltage_V": round(self.current_voltage, 2),
                    "current_A": round(self.current_current, 3),
                    "power_W": round(self.current_power, 2),
                    "session_energy_kWh": round(self.session_energy, 6),
                    "data_type": "SIMULATED"
                })
                self.last_live_log = now

            self.update_cities(self.current_time)

        self.update_overview_values()

        self.clock_label.config(
            text=self.current_time.strftime("%d %b %Y  |  %H:%M:%S")
        )
        self.reading_label.config(
            text=f"Last update: {self.current_time:%H:%M:%S}"
        )

        if self.active_page == "Appliances":
            self.refresh_appliance_table()

        elif self.active_page == "City Monitor":
            self.refresh_city_table()
            self.draw_city_chart()

        elif self.active_page == "Smart Suggestions":
            self.refresh_suggestions()

        elif self.active_page == "Reports":
            self.refresh_report()

        self.draw_power_chart()
        self.root.after(UPDATE_MS, self.update_live_data)

    def update_overview_values(self):
        self.power_value.config(text=f"{self.current_power:,.1f} W")
        self.voltage_value.config(text=f"{self.current_voltage:.1f} V")
        self.current_value.config(text=f"{self.current_current:.3f} A")
        self.energy_value.config(text=f"{self.session_energy:.6f} kWh")

        if self.monitoring:
            self.status_label.config(text="● MONITORING", fg=GREEN)
            self.header_status.config(text="● SIMULATION ACTIVE", fg=GREEN)
            self.graph_status.config(text="● LIVE", fg=GREEN)
            self.monitor_button.config(text="Ⅱ  Pause Monitoring")
        else:
            self.status_label.config(text="● PAUSED", fg=ORANGE)
            self.header_status.config(text="● MONITORING PAUSED", fg=ORANGE)
            self.graph_status.config(text="● PAUSED", fg=ORANGE)
            self.monitor_button.config(text="▶  Resume Monitoring")

    def toggle_monitoring(self):
        self.monitoring = not self.monitoring
        self.last_update = time.time()
        self.update_overview_values()

    # -------------------- POWER CHART --------------------

    def draw_power_chart(self):
        if not hasattr(self, "chart"):
            return

        c = self.chart
        c.delete("all")
        width = max(c.winfo_width(), 350)
        height = max(c.winfo_height(), 180)

        left, right = 55, width - 18
        top, bottom = 20, height - 34
        gw, gh = right - left, bottom - top

        if gw <= 0 or gh <= 0:
            return

        values = [v for _, v in self.power_history]
        maximum = max(max(values, default=100), 100) * 1.15

        for i in range(5):
            y = bottom - gh * i / 4
            c.create_line(
                left, y, right, y,
                fill=BORDER, dash=(3, 5)
            )
            c.create_text(
                left - 9, y,
                text=f"{maximum * i / 4:.0f}",
                fill=MUTED, anchor="e",
                font=("Segoe UI", 8)
            )

        c.create_text(
            13, top + gh / 2,
            text="Power (W)", fill=MUTED,
            font=("Segoe UI", 8), angle=90
        )

        if len(values) >= 2:
            points = []

            for i, value in enumerate(values):
                x = left + gw * i / (len(values) - 1)
                y = bottom - gh * value / maximum
                points.extend((x, y))

            c.create_line(
                *points, fill=GREEN, width=3, smooth=True
            )
            c.create_oval(
                points[-2] - 4, points[-1] - 4,
                points[-2] + 4, points[-1] + 4,
                fill=GREEN, outline=""
            )
        else:
            c.create_text(
                width / 2, height / 2,
                text="Collecting simulated readings...",
                fill=MUTED, font=("Segoe UI", 10)
            )

        c.create_text(
            left, height - 12,
            text="OLDER READINGS", fill=MUTED,
            font=("Segoe UI", 8), anchor="w"
        )
        c.create_text(
            right, height - 12,
            text="LATEST", fill=MUTED,
            font=("Segoe UI", 8), anchor="e"
        )

    # -------------------- CSV EXPORT --------------------

    def write_csv(self, path, rows):
        try:
            if not rows:
                messagebox.showinfo(
                    "No data", "There are no records to export."
                )
                return

            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f, fieldnames=list(rows[0].keys())
                )
                writer.writeheader()
                writer.writerows(rows)

            messagebox.showinfo(
                "Export successful",
                f"Your CSV report was saved successfully:\n{path}"
            )
        except (OSError, csv.Error) as error:
            messagebox.showerror("Export error", str(error))

    def export_live_data(self):
        if not self.live_log:
            messagebox.showinfo(
                "No readings yet",
                "Run the monitor for at least five seconds first."
            )
            return

        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Live Sensor Readings",
            defaultextension=".csv",
            initialfile="smart_home_live_readings.csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if path:
            self.write_csv(path, self.live_log)

    def export_appliance_summary(self):
        connected, daily, monthly, daily_cost, monthly_cost = (
            self.calculate_data()
        )

        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Appliance Report",
            defaultextension=".csv",
            initialfile="energy_report.csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        try:
            with open(
                path, "w", newline="", encoding="utf-8-sig"
            ) as f:
                writer = csv.writer(f)

                writer.writerow([
                    "Aniket's Smart Home Energy Monitor"
                ])
                writer.writerow([
                    "Report generated",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])
                writer.writerow(["Data type", "Estimated appliance usage"])
                writer.writerow([])
                writer.writerow([
                    "Appliance", "Rated Power (W)", "Hours Per Day",
                    "Daily Energy (kWh)", "Monthly Energy (kWh)",
                    "Estimated Monthly Cost (Rs)"
                ])

                for item in self.appliances:
                    energy = item["power"] * item["hours"] / 1000
                    writer.writerow([
                        item["name"], item["power"], item["hours"],
                        round(energy, 4),
                        round(energy * MONTH_DAYS, 4),
                        round(energy * MONTH_DAYS * TARIFF, 2)
                    ])

                writer.writerow([])
                writer.writerow(["Connected rating (W)", connected])
                writer.writerow(["Daily energy (kWh)", round(daily, 4)])
                writer.writerow(["Monthly energy (kWh)", round(monthly, 4)])
                writer.writerow(["Tariff (Rs/kWh)", TARIFF])
                writer.writerow(["Daily cost (Rs)", round(daily_cost, 2)])
                writer.writerow(["Monthly cost (Rs)", round(monthly_cost, 2)])
                writer.writerow([])
                writer.writerow([
                    "Note",
                    "Live sensor readings are simulated, not physical measurements."
                ])

            messagebox.showinfo(
                "Export successful",
                f"Appliance report saved:\n{path}"
            )
        except (OSError, csv.Error) as error:
            messagebox.showerror("Export error", str(error))


if __name__ == "__main__":
    root = tk.Tk()
    app = EnergyMonitorApp(root)
    root.mainloop()
