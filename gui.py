"""
AI Health Centre Project - Clinic Visit Sorter
Interactive Dark-Themed Desktop GUI for Nurse Triage & Faculty Showcase

Features:
- Premium Dark Healthcare Theme (#0f172a / #1e293b)
- Live Triage KPI Metric Cards (Total, See Now, Today, Routine)
- Prioritized Interactive Table (Color-coded rows for high-urgency patients)
- Real-Time Live Patient Note Simulator (For live faculty demonstration)
- Detailed Patient Inspection Pane
- One-Click Batch Triage & CSV Export
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from dotenv import load_dotenv
from groq import Groq
import main

# Colors Palette (Modern Dark Slate / Cyber-Clinical)
BG_MAIN = "#0f172a"        # Dark slate background
BG_PANEL = "#1e293b"       # Card / container background
BG_HEADER = "#111827"      # Header background
FG_PRIMARY = "#f8fafc"     # High-contrast white text
FG_SECONDARY = "#94a3b8"   # Subtle muted grey text
BORDER_COLOR = "#334155"   # Clean border stroke

# Urgency Badges
COLOR_SEE_NOW = "#ef4444"  # Vibrant Red
COLOR_TODAY = "#f59e0b"    # Warm Amber
COLOR_ROUTINE = "#10b981"  # Emerald Green
COLOR_ACCENT = "#38bdf8"   # Electric Sky Blue


class ClinicSorterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Health Centre - Clinic Visit Sorter (Triage Dashboard)")
        self.root.geometry("1280x820")
        self.root.minsize(1050, 700)
        self.root.configure(bg=BG_MAIN)

        # Application state
        self.processed_records = []
        self.client = None
        self.system_prompt = ""

        # Load environment & prompt
        self.initialize_ai()

        # Build UI layout
        self.setup_styles()
        self.create_header()
        self.create_kpi_cards()
        self.create_main_content()
        self.create_status_bar()

        # Automatically load visits on startup
        self.root.after(300, self.load_initial_data)

    def initialize_ai(self):
        """Loads Groq API key and 5-Role prompt."""
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                self.client = Groq(api_key=api_key)
            except Exception as e:
                print(f"Error initializing Groq client: {e}")
        
        prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()

    def setup_styles(self):
        """Configures ttk styles for the modern dark theme."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure Treeview table
        style.configure(
            "Dark.Treeview",
            background=BG_PANEL,
            foreground=FG_PRIMARY,
            fieldbackground=BG_PANEL,
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=BG_HEADER,
            foreground="#38bdf8",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=8
        )
        style.map("Dark.Treeview", background=[("selected", "#334155")])

    def create_header(self):
        """Top banner with system title and medical boundary disclaimer."""
        header_frame = tk.Frame(self.root, bg=BG_HEADER, height=75, padx=24, pady=12)
        header_frame.pack(fill="x", side="top")

        title_label = tk.Label(
            header_frame,
            text="🏥 AI Health Centre: Clinic Visit Sorter",
            font=("Segoe UI", 16, "bold"),
            fg=FG_PRIMARY,
            bg=BG_HEADER
        )
        title_label.pack(side="left")

        sub_label = tk.Label(
            header_frame,
            text="AI-Assisted Triage Queue  |  Nurse Retains 100% Medical Decision Authority",
            font=("Segoe UI", 9, "italic"),
            fg=COLOR_ACCENT,
            bg=BG_HEADER
        )
        sub_label.pack(side="left", padx=(15, 0), pady=(4, 0))

        # Action Buttons in Header
        btn_frame = tk.Frame(header_frame, bg=BG_HEADER)
        btn_frame.pack(side="right")

        self.btn_reprocess = tk.Button(
            btn_frame,
            text="⚡ Run Full Triage",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.trigger_full_triage 
        )
        self.btn_reprocess.pack(side="left", padx=6)

    def create_kpi_cards(self):
        """Dashboard overview cards displaying patient statistics."""
        kpi_frame = tk.Frame(self.root, bg=BG_MAIN, padx=20, pady=12)
        kpi_frame.pack(fill="x")

        self.card_total = self._build_kpi_card(kpi_frame, "TOTAL VISITS", "0", FG_PRIMARY)
        self.card_see_now = self._build_kpi_card(kpi_frame, "SEE NOW (EMERGENCY)", "0", COLOR_SEE_NOW)
        self.card_today = self._build_kpi_card(kpi_frame, "TODAY (URGENT)", "0", COLOR_TODAY)
        self.card_routine = self._build_kpi_card(kpi_frame, "ROUTINE (ADMIN / MILD)", "0", COLOR_ROUTINE)

        self.card_total.pack(side="left", fill="x", expand=True, padx=6)
        self.card_see_now.pack(side="left", fill="x", expand=True, padx=6)
        self.card_today.pack(side="left", fill="x", expand=True, padx=6)
        self.card_routine.pack(side="left", fill="x", expand=True, padx=6)

    def _build_kpi_card(self, parent, title, initial_val, color):
        card = tk.Frame(parent, bg=BG_PANEL, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=16, pady=10)
        
        lbl_title = tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), fg=FG_SECONDARY, bg=BG_PANEL)
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(card, text=initial_val, font=("Segoe UI", 20, "bold"), fg=color, bg=BG_PANEL)
        lbl_val.pack(anchor="w", pady=(2, 0))

        card.value_label = lbl_val
        return card

    def create_main_content(self):
        """Split layout: Queue Table on Left, Live Tester & Details on Right."""
        content_frame = tk.Frame(self.root, bg=BG_MAIN, padx=20, pady=4)
        content_frame.pack(fill="both", expand=True)

        # ---------------- LEFT: QUEUE TABLE ----------------
        left_frame = tk.Frame(content_frame, bg=BG_PANEL, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        table_header = tk.Frame(left_frame, bg=BG_PANEL, padx=12, pady=10)
        table_header.pack(fill="x")

        tk.Label(table_header, text="📋 Prioritized Patient Queue", font=("Segoe UI", 12, "bold"), fg=FG_PRIMARY, bg=BG_PANEL).pack(side="left")
        
        # Legend badges
        tk.Label(table_header, text="■ SEE_NOW", font=("Segoe UI", 8, "bold"), fg=COLOR_SEE_NOW, bg=BG_PANEL).pack(side="right", padx=6)
        tk.Label(table_header, text="■ TODAY", font=("Segoe UI", 8, "bold"), fg=COLOR_TODAY, bg=BG_PANEL).pack(side="right", padx=6)
        tk.Label(table_header, text="■ ROUTINE", font=("Segoe UI", 8, "bold"), fg=COLOR_ROUTINE, bg=BG_PANEL).pack(side="right", padx=6)

        # Treeview Scrollbar
        scroll_y = ttk.Scrollbar(left_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(left_frame, orient="horizontal")

        columns = ("q_num", "id", "time", "priority", "category", "summary")
        self.tree = ttk.Treeview(
            left_frame,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        # Column configuration
        self.tree.heading("q_num", text="Q#")
        self.tree.heading("id", text="ID")
        self.tree.heading("time", text="Time")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("category", text="Category")
        self.tree.heading("summary", text="Symptom Summary")

        self.tree.column("q_num", width=45, anchor="center")
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("time", width=65, anchor="center")
        self.tree.column("priority", width=100, anchor="center")
        self.tree.column("category", width=100, anchor="center")
        self.tree.column("summary", width=340, anchor="w")

        # Configure color tags
        self.tree.tag_configure("see_now", foreground="#f87171", background="#2a1215")
        self.tree.tag_configure("today", foreground="#fbbf24", background="#231d10")
        self.tree.tag_configure("routine", foreground="#34d399", background="#11241a")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_record)

        # ---------------- RIGHT: INSPECTION & LIVE TESTER ----------------
        right_frame = tk.Frame(content_frame, bg=BG_MAIN, width=380)
        right_frame.pack(side="right", fill="both")

        # 1. LIVE NOTE SIMULATOR CARD (For Viva Showcase)
        live_card = tk.Frame(right_frame, bg=BG_PANEL, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=14, pady=12)
        live_card.pack(fill="x", pady=(0, 10))

        tk.Label(live_card, text="🧪 Live Student Arrival Simulator", font=("Segoe UI", 11, "bold"), fg=COLOR_ACCENT, bg=BG_PANEL).pack(anchor="w")
        tk.Label(live_card, text="Enter any note in English, Tamil, or Tanglish:", font=("Segoe UI", 8), fg=FG_SECONDARY, bg=BG_PANEL).pack(anchor="w", pady=(2, 6))

        self.txt_sim_input = tk.Entry(live_card, font=("Segoe UI", 10), bg="#0f172a", fg="white", insertbackground="white", bd=1, relief="solid")
        self.txt_sim_input.pack(fill="x", pady=4)
        self.txt_sim_input.insert(0, "Nenju vali and moochu thinaral since 1 hour")

        sim_btn_frame = tk.Frame(live_card, bg=BG_PANEL)
        sim_btn_frame.pack(fill="x", pady=(6, 0))

        self.btn_triage_live = tk.Button(
            sim_btn_frame,
            text="⚡ Triage Live Note",
            font=("Segoe UI", 9, "bold"),
            bg="#0284c7",
            fg="white",
            activebackground="#0369a1",
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.triage_live_note
        )
        self.btn_triage_live.pack(side="right")

        # 2. PATIENT DETAILS INSPECT PANE
        details_card = tk.Frame(right_frame, bg=BG_PANEL, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1, padx=14, pady=12)
        details_card.pack(fill="both", expand=True)

        tk.Label(details_card, text="🔍 Patient Clinical Inspection", font=("Segoe UI", 11, "bold"), fg=FG_PRIMARY, bg=BG_PANEL).pack(anchor="w")

        self.lbl_inspect_id = tk.Label(details_card, text="Select a patient from the queue to view full notes.", font=("Segoe UI", 9), fg=FG_SECONDARY, bg=BG_PANEL)
        self.lbl_inspect_id.pack(anchor="w", pady=(4, 8))

        # Text area for original note
        tk.Label(details_card, text="Original Student Arrival Note:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg=BG_PANEL).pack(anchor="w")
        self.txt_inspect_note = tk.Text(details_card, height=5, font=("Segoe UI", 10), bg="#0f172a", fg="#e2e8f0", wrap="word", relief="flat", padx=8, pady=8)
        self.txt_inspect_note.pack(fill="x", pady=(2, 10))

        # AI Analysis Breakdown
        tk.Label(details_card, text="AI Analysis & Guardrail Decision:", font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg=BG_PANEL).pack(anchor="w")
        self.txt_inspect_analysis = tk.Text(details_card, height=7, font=("Consolas", 9), bg="#0f172a", fg="#38bdf8", wrap="word", relief="flat", padx=8, pady=8)
        self.txt_inspect_analysis.pack(fill="both", expand=True, pady=(2, 6))

    def create_status_bar(self):
        """Bottom status bar with real-time logs and status."""
        self.status_bar = tk.Label(
            self.root,
            text="System Ready  •  Connected to Groq (qwen/qwen3.8-27b)  •  Bilingual Guardrails Active",
            font=("Segoe UI", 8),
            fg=FG_SECONDARY,
            bg=BG_HEADER,
            anchor="w",
            padx=16,
            pady=6
        )
        self.status_bar.pack(fill="x", side="bottom")

    def load_initial_data(self):
        """Loads records from visits.csv or nurse_queue.csv if already run."""
        queue_path = "nurse_queue.csv"
        if os.path.exists(queue_path):
            self.load_from_csv(queue_path)
            self.status_bar.config(text=f"Loaded {len(self.processed_records)} prioritized records from 'nurse_queue.csv'.")
        else:
            self.trigger_full_triage()

    def load_from_csv(self, filepath):
        """Populates the treeview table from a CSV file."""
        import csv
        self.processed_records.clear()
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.processed_records.append(row)
        self.refresh_table()

    def refresh_table(self):
        """Refreshes the Treeview and updates metric counters."""
        self.tree.delete(*self.tree.get_children())
        
        see_now_count = 0
        today_count = 0
        routine_count = 0

        for idx, r in enumerate(self.processed_records, start=1):
            prio = r.get("priority", "routine")
            if prio == "see_now":
                see_now_count += 1
                tag = "see_now"
            elif prio == "today":
                today_count += 1
                tag = "today"
            else:
                routine_count += 1
                tag = "routine"

            self.tree.insert(
                "",
                "end",
                values=(
                    idx,
                    r.get("id", f"V{idx:02d}"),
                    r.get("time", "12:00"),
                    prio.upper(),
                    r.get("category", "other"),
                    r.get("summary", "")
                ),
                tags=(tag,)
            )

        # Update KPI Cards
        total = len(self.processed_records)
        self.card_total.value_label.config(text=str(total))
        self.card_see_now.value_label.config(text=str(see_now_count))
        self.card_today.value_label.config(text=str(today_count))
        self.card_routine.value_label.config(text=str(routine_count))

    def on_select_record(self, event):
        """Shows detailed information when a user selects a table row."""
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        q_idx = item["values"][0] - 1
        if 0 <= q_idx < len(self.processed_records):
            rec = self.processed_records[q_idx]
            
            v_id = rec.get("id", "N/A")
            v_time = rec.get("time", "N/A")
            v_prio = rec.get("priority", "N/A").upper()
            v_cat = rec.get("category", "N/A")
            v_sum = rec.get("summary", "N/A")
            v_note = rec.get("original_note", "No note text.")

            self.lbl_inspect_id.config(text=f"Selected Patient: {v_id} (Arrived {v_time})  •  Priority: {v_prio}")
            
            self.txt_inspect_note.delete("1.0", tk.END)
            self.txt_inspect_note.insert(tk.END, v_note)

            analysis_text = (
                f"Triage Urgency : {v_prio}\n"
                f"Symptom Category: {v_cat}\n"
                f"Safe Summary   : {v_sum}\n\n"
                f"Guardrail Note  : Nurse reviews this note. Tool never diagnoses."
            )
            self.txt_inspect_analysis.delete("1.0", tk.END)
            self.txt_inspect_analysis.insert(tk.END, analysis_text)

    def trigger_full_triage(self):
        """Runs the complete classification batch in a background thread."""
        self.btn_reprocess.config(state="disabled", text="⏳ Processing...")
        self.status_bar.config(text="Running full LLM classification pipeline across visits.csv...")

        def worker():
            try:
                visits = main.load_visits("visits.csv")
                processed = []
                for v in visits:
                    llm_res = main.classify(self.client, v["note"], self.system_prompt)
                    final_prio = main.raise_priority(v["note"], llm_res["priority"])
                    final_sum = main.remove_diagnosis(llm_res["summary"])
                    processed.append({
                        "id": v["id"],
                        "time": v["time"],
                        "priority": final_prio,
                        "category": llm_res["category"],
                        "summary": final_sum,
                        "original_note": v["note"]
                    })
                
                # Sort and write reports
                sorted_records = main.write_reports(processed)
                
                def on_done():
                    self.processed_records = sorted_records
                    self.refresh_table()
                    self.btn_reprocess.config(state="normal", text="⚡ Run Full Triage")
                    self.status_bar.config(text="Full run completed! nurse_queue.csv and summary.txt updated.")
                    messagebox.showinfo("Triage Complete", f"Successfully triaged {len(sorted_records)} student visits!\nNurse queue is up to date.")
                
                self.root.after(0, on_done)
            except Exception as e:
                def on_error():
                    self.btn_reprocess.config(state="normal", text="⚡ Run Full Triage")
                    self.status_bar.config(text=f"Error during triage: {e}")
                    messagebox.showerror("Error", f"Failed to run triage:\n{e}")
                self.root.after(0, on_error)

        threading.Thread(target=worker, daemon=True).start()

    def triage_live_note(self):
        """Classifies a user-typed note in real-time and inserts it into the queue."""
        note_text = self.txt_sim_input.get().strip()
        if not note_text:
            messagebox.showwarning("Input Required", "Please enter a student note to triage.")
            return

        self.btn_triage_live.config(state="disabled", text="Triaging...")
        self.status_bar.config(text=f"Triaging live input: \"{note_text[:40]}...\"")

        def worker():
            try:
                import datetime
                current_time = datetime.datetime.now().strftime("%H:%M")
                new_id = f"V{len(self.processed_records)+1:02d}"

                # 1. LLM classification
                llm_res = main.classify(self.client, note_text, self.system_prompt)
                
                # 2. Red-flag escalation
                final_prio = main.raise_priority(note_text, llm_res["priority"])
                
                # 3. No-diagnosis scrubbing
                final_sum = main.remove_diagnosis(llm_res["summary"])

                new_record = {
                    "id": new_id,
                    "time": current_time,
                    "priority": final_prio,
                    "category": llm_res["category"],
                    "summary": final_sum,
                    "original_note": note_text
                }

                # Add and re-sort
                self.processed_records.append(new_record)
                self.processed_records.sort(
                    key=lambda r: (main.PRIORITY_RANK.get(r["priority"], 3), r["time"])
                )

                # Re-write queue file
                main.write_reports(self.processed_records)

                def on_done():
                    self.refresh_table()
                    self.btn_triage_live.config(state="normal", text="⚡ Triage Live Note")
                    self.status_bar.config(text=f"Live note triaged as [{final_prio.upper()}] and slotted into the queue.")
                    # Select the newly added item
                    for item in self.tree.get_children():
                        if self.tree.item(item)["values"][1] == new_id:
                            self.tree.selection_set(item)
                            self.tree.see(item)
                            self.on_select_record(None)
                            break
                    messagebox.showinfo(
                        "Live Triage Result",
                        f"Student ID: {new_id}\n"
                        f"Assigned Priority: {final_prio.upper()}\n"
                        f"Category: {llm_res['category']}\n"
                        f"Summary: {final_sum}\n\n"
                        f"Slotted into Nurse Queue according to urgency!"
                    )

                self.root.after(0, on_done)
            except Exception as e:
                def on_error():
                    self.btn_triage_live.config(state="normal", text="⚡ Triage Live Note")
                    self.status_bar.config(text=f"Live triage error: {e}")
                    messagebox.showerror("Error", f"Failed to triage note:\n{e}")
                self.root.after(0, on_error)

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ClinicSorterGUI(root)
    root.mainloop()

