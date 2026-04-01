import customtkinter as ctk
import tkinter as tk
from datetime import datetime

# --- ELITE DESIGN TOKENS (Sealed from Masterpiece UI) ---
T_BG = ("#EBF4DD", "#02040a")
T_SIDEBAR = ("#90AB8B", "#0a0b10")
T_CARD = ("#F7FBF2", "#0f172a")
T_BORDER = ("#90AB8B", "#1e293b")
T_ACCENT = ("#5A7863", "#6366f1")
T_TEXT = ("#3B4953", "#f8fafc")
T_SUBTEXT = ("#5A7863", "#DCD6F7")
T_TERMINAL = ("#000000", "#000000")

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tw: return
        x = self.widget.winfo_rootx() - 380
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_attributes("-topmost", True)
        self.tw.wm_geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(self.tw, fg_color="#0f172a", corner_radius=8, border_width=1, border_color="#6366f1")
        frame.pack(fill="both", expand=True)
        
        lbl = ctk.CTkLabel(frame, text=self.text, font=("Inter", 12), text_color="#f8fafc", justify="left")
        lbl.pack(padx=20, pady=15)

    def hide(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

class MasterpieceView(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. CRITICAL INITIALIZATION (Prevents AttributeError)
        self.is_alive = True
        self.after_ids = []
        self.nav_btns = []
        self.sidebar_collapsed = False
        
        # 2. WINDOW CONFIG
        self.title("Academic Pulse Pro | v21.0")
        self.geometry("1400x900")
        self.configure(fg_color=T_BG)

        # 3. MASTER TYPOGRAPHY
        self.font_h1 = ctk.CTkFont(family="Segoe UI Variable Display", size=36, weight="bold")
        self.font_h2 = ctk.CTkFont(family="Segoe UI Variable Display", size=22, weight="bold")
        self.font_body = ctk.CTkFont(family="Inter", size=14)
        self.font_nav = ctk.CTkFont(family="Inter", size=20) 
        self.font_label = ctk.CTkFont(family="Inter", size=11, weight="bold")
        self.font_mono = ctk.CTkFont(family="Consolas", size=12)

        # 4. DASHBOARD VARIABLES
        self.profiles_synced_var = tk.StringVar(value="...")
        self.pipeline_stage_var = tk.StringVar(value="0 / 7")
        self.match_conf_var = tk.StringVar(value="88.4%")
        self.master_index_var = tk.StringVar(value="...")
        self.institution_var = tk.StringVar(value="VNR VJIET")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_viewport()

    def lock_ui(self, status_msg):
        """ Prevents interaction but keeps the dashboard 'live' """
        self.is_alive_processing = True # Internal flag
        if hasattr(self, 'status_lbl'):
            self.status_lbl.configure(text=status_msg, text_color=T_ACCENT)
        # Disable only the nav buttons, keeping the terminal active
        for btn in self.nav_btns:
            btn.configure(state="disabled")

    def unlock_ui(self):
        """ Restores buttons after Stage 7/7 """
        self.is_alive_processing = False
        if hasattr(self, 'status_lbl'):
            self.status_lbl.configure(text="SUPABASE ACTIVE", text_color=T_SUBTEXT)
        for btn in self.nav_btns:
            btn.configure(state="normal")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=T_SIDEBAR, border_width=1, border_color=T_BORDER)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(10, weight=1)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, pady=(40, 30), padx=20, sticky="ew")
        self.toggle_btn = ctk.CTkButton(brand, text="☰", width=45, height=45, fg_color="transparent", 
                                        font=self.font_nav, text_color=T_TEXT, hover_color=T_BG, command=self.toggle_sidebar)
        self.toggle_btn.pack(side="left")
        self.logo_text = ctk.CTkLabel(brand, text=" ANALYTICS", font=self.font_h2, text_color=T_TEXT)
        self.logo_text.pack(side="left", padx=10)

        # Navigation Links
        self.btn_dash = self.create_nav("Dashboard", "📊", 1)
        self.btn_scholar = self.create_nav("Scholar Engine", "🎓", 2)
        self.btn_scopus = self.create_nav("Scopus Engine", "🔬", 3)
        self.btn_wos = self.create_nav("WoS Ghosting", "🕸", 4)

        self.status_pill = ctk.CTkFrame(self.sidebar, fg_color=T_BG, corner_radius=15, height=40)
        self.status_pill.grid(row=11, column=0, padx=20, pady=30, sticky="ew")
        self.status_dot = ctk.CTkLabel(self.status_pill, text="●", text_color="#10b981", font=self.font_nav)
        self.status_dot.pack(side="left", padx=(10, 5))
        self.status_lbl = ctk.CTkLabel(self.status_pill, text="SUPABASE ACTIVE", font=self.font_label, text_color=T_SUBTEXT)
        self.status_lbl.pack(side="left")

        # 🟢 Institutional Info (VNR VJIET Branding)
 

    def create_nav(self, text, icon, row):
        btn = ctk.CTkButton(self.sidebar, text=f"  {icon}   {text}", anchor="w", font=self.font_nav, 
                            height=60, fg_color="transparent", text_color=T_TEXT, 
                            hover_color=T_BG, corner_radius=12)
        btn.grid(row=row, column=0, padx=15, pady=8, sticky="ew")
        btn.full_text = f"  {icon}   {text}"; btn.icon = icon
        self.nav_btns.append(btn)
        return btn

    def toggle_sidebar(self):
        if not self.sidebar_collapsed:
            self.sidebar.configure(width=90); self.logo_text.pack_forget(); self.status_lbl.pack_forget()
            for b in self.nav_btns: b.configure(text=f" {b.icon}")
            self.sidebar_collapsed = True
            self.btn_info.configure(text=" ⓘ") # Shrink to icon
            self.sidebar_collapsed = True
        else:
            self.sidebar.configure(width=280); self.logo_text.pack(side="left", padx=10); self.status_lbl.pack(side="left")
            for b in self.nav_btns: b.configure(text=b.full_text)
            self.sidebar_collapsed = False
            self.btn_info.configure(text=" ⓘ   System Info") # Expand to text
            self.sidebar_collapsed = False

    def _build_main_viewport(self):
        """ Master Scrollable Viewport: Fully scrolls log card naturally. """
        self.viewport = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.viewport.grid(row=0, column=1, sticky="nsew")
        
        # A. Slim Header
        self.header = ctk.CTkFrame(self.viewport, height=70, fg_color="transparent")
        self.header.pack(fill="x", padx=60, pady=(20, 0)) # Reduced from 30
        self.breadcrumb = ctk.CTkLabel(self.header, text="PROJECT / OVERVIEW", font=self.font_label, text_color=T_ACCENT)
        self.breadcrumb.pack(anchor="w")
        self.title_lbl = ctk.CTkLabel(self.header, text="Academic Pulse", font=self.font_h1, text_color=T_TEXT)
        self.title_lbl.pack(anchor="w")
        
        # 🟢 Header Buttons Frame
        self.hdr_btns = ctk.CTkFrame(self.header, fg_color="transparent")
        self.hdr_btns.place(relx=1.0, rely=0.5, anchor="e")

        # 🟢 RESTORED: Theme Toggle (Fixed the AttributeError)
        self.theme_btn = ctk.CTkButton(self.hdr_btns, text="🌙", width=40, height=40, corner_radius=10,
                                        fg_color=T_CARD, border_width=1, border_color=T_BORDER, font=("Inter", 16))
        self.theme_btn.pack(side="right")

        # 🟢 Pipeline Info Toggle & Tooltip
        self.info_btn = ctk.CTkButton(self.hdr_btns, text="ℹ", width=40, height=40, corner_radius=10,
                                        fg_color=T_CARD, border_width=1, border_color=T_BORDER, font=("Inter", 18))
        # Initialized but explicitly hidden on the generic Dashboard viewport
        self.info_tooltip = ToolTip(self.info_btn, "")
        
        # B. Dynamic Canvas (Sits seamlessly in scrollable viewport without expanding forcefully)
        self.canvas = ctk.CTkFrame(self.viewport, fg_color="transparent", corner_radius=0)
        self.canvas.pack(fill="x", padx=60, pady=5)

        # C. Permanent Audit Feed (Now nested normally at the bottom of the scroll)
        self.log_card = ctk.CTkFrame(self.viewport, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=20, height=250)
        self.log_card.pack_propagate(False)
        self.log_card.pack(fill="x", padx=60, pady=(0, 20))
        
        ctk.CTkLabel(self.log_card, text="Live Pipeline Audit Feed", font=self.font_label, text_color=T_ACCENT).pack(anchor="w", padx=25, pady=(10, 0))
        self.console = ctk.CTkTextbox(self.log_card, fg_color=T_TERMINAL, font=self.font_mono, text_color="#10b981", corner_radius=12)
        self.console.pack(fill="both", expand=True, padx=20, pady=(5, 15))

    def show_dash_view(self, greeting_txt):
        """ High-Density Dashboard: No double-scrollbars """
        for w in self.canvas.winfo_children(): w.destroy()
        self.info_btn.pack_forget() # Hide the icon globally
        
        greet_frame = ctk.CTkFrame(self.canvas, fg_color="transparent")
        greet_frame.pack(fill="x", pady=(5, 10))
        ctk.CTkLabel(greet_frame, text=f"{greeting_txt}, Analyst.", font=self.font_h2, text_color=T_TEXT).pack(anchor="w")
        ctk.CTkLabel(greet_frame, text="VNR VJIET Sequential Pipeline Data Scraping System", font=self.font_body, text_color=T_SUBTEXT).pack(anchor="w")

        # Pulse Metrics (Shrunk to 70px)
        pulse = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=15, height=70)
        pulse.pack(fill="x", pady=0); pulse.pack_propagate(False)
        
        m = [("SYNCED", self.profiles_synced_var), ("STAGE", self.pipeline_stage_var), ("ACCURACY", self.match_conf_var), ("INSTITUTION", self.institution_var)]
        for lbl, var in m:
            f = ctk.CTkFrame(pulse, fg_color="transparent")
            f.pack(side="left", expand=True)
            ctk.CTkLabel(f, text=lbl, font=self.font_label, text_color=T_ACCENT).pack()
            ctk.CTkLabel(f, textvariable=var, font=self.font_body, text_color=T_TEXT).pack()
        
        # 🟢 Explorer Hub: Quick Access to Scraped Data
        # 🟢 EXPLORER HUB: High-Contrast Sidebar Matching
        actions = ctk.CTkFrame(self.canvas, fg_color="transparent")
        actions.pack(fill="x", pady=(15, 5))

        # Shared styling for both buttons
        btn_props = {
            "fg_color": T_CARD,
            "border_width": 1,
            "border_color": T_BORDER,
            "text_color": T_TEXT,
            "hover_color": T_ACCENT,
            "height": 55, # Premium Height
            "font": ctk.CTkFont(family="Inter", size=13, weight="bold")
        }

# 🟢 THE FIX: Use winfo_toplevel() to find the Controller
        self.btn_outputs = ctk.CTkButton(
            actions, text="📁   VIEW OUTPUTS", 
            command=lambda: self.winfo_toplevel().open_outputs(), # ⬅️ Updated
            **btn_props
        )
        self.btn_outputs.pack(side="left", padx=(0, 10), expand=True, fill="x")

        self.btn_logs = ctk.CTkButton(
            actions, text="📄   VIEW LOGS", 
            command=lambda: self.winfo_toplevel().open_logs(), # ⬅️ Updated
            **btn_props
        )
        self.btn_logs.pack(side="left", expand=True, fill="x")
    # --- VIEW RENDERERS (REPLACING THE ENDLESS TO-AND-FRO) ---
    def clear_canvas(self):
        for w in self.canvas.winfo_children(): w.destroy()

    

    def show_scholar_view(self):
        self.clear_canvas()
        self.info_btn.pack(side="right", padx=(0, 15))
        self.info_tooltip.text = (
            "Google Scholar Pipeline:\n\n"
            "1. Node Init: Submits author parameters to Scholar search.\n"
            "2. Scrape Layer: Browser navigates profiles & bypasses captchas.\n"
            "3. Extraction: Parses h-index, citations, and publication metrics.\n"
            "4. Identity Linker: Fuzzy matches author affiliations/titles.\n"
            "5. Refiner: Cleans HTML artifacts into standard UTF-8 format.\n"
            "6. Backup: Stores cached JSON payload locally in '/outputs'.\n"
            "7. Supabase Sync: Upserts structured records to Cloud DB."
        )
        form = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=24)
        form.pack(pady=(10, 20), padx=20, ipadx=40, ipady=10, fill="x")

        ctk.CTkLabel(form, text="Google Scholar Target Configuration", font=self.font_h2, text_color=T_TEXT).pack(pady=(20, 5))
        
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", padx=40, pady=(10, 5))
        f1 = ctk.CTkFrame(r1, fg_color="transparent")
        f1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(f1, text="FIRST NAME", font=self.font_label, text_color=T_SUBTEXT).pack(anchor="w", pady=(0, 5))
        self.scholar_f = ctk.CTkEntry(f1, height=45, corner_radius=10, fg_color=T_TERMINAL, border_color=T_BORDER, text_color="#10b981")
        self.scholar_f.pack(fill="x")

        f2 = ctk.CTkFrame(r1, fg_color="transparent")
        f2.pack(side="left", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(f2, text="LAST NAME", font=self.font_label, text_color=T_SUBTEXT).pack(anchor="w", pady=(0, 5))
        self.scholar_l = ctk.CTkEntry(f2, height=45, corner_radius=10, fg_color=T_TERMINAL, border_color=T_BORDER, text_color="#10b981")
        self.scholar_l.pack(fill="x")
        
        r2 = ctk.CTkFrame(form, fg_color="transparent")
        r2.pack(fill="x", padx=40, pady=5)
        ctk.CTkLabel(r2, text="AFFILIATION / UNIVERSITY", font=self.font_label, text_color=T_SUBTEXT).pack(anchor="w", pady=(0, 5))
        self.scholar_a = ctk.CTkEntry(r2, height=45, corner_radius=10, fg_color=T_TERMINAL, border_color=T_BORDER, text_color="#10b981")
        self.scholar_a.pack(fill="x")

        self.scholar_exec = ctk.CTkButton(form, text="EXECUTE SCHOLAR PIPELINE", height=55, font=self.font_h2, 
                                          fg_color=T_ACCENT, text_color=T_BG[1], corner_radius=12)
        self.scholar_exec.pack(pady=(30, 20), padx=50, fill="x")

        flow_panel = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=2, border_color=T_ACCENT, corner_radius=24)
        flow_panel.pack(pady=20, padx=20, fill="x")

        header_btn = ctk.CTkButton(flow_panel, text="▶ ⚡ Execution Flow Pipeline (Click to Expand)", 
                                   font=self.font_h2, text_color=T_ACCENT, fg_color="transparent", 
                                   hover_color=T_BG, anchor="center", height=50)
        header_btn.pack(pady=(15, 10), padx=20, fill="x")

        content_box = ctk.CTkFrame(flow_panel, fg_color="transparent")
        flow_panel.is_expanded = False
        
        def toggle_flow():
            if flow_panel.is_expanded:
                content_box.pack_forget()
                header_btn.configure(text="▶ ⚡ Execution Flow Pipeline (Click to Expand)")
                flow_panel.is_expanded = False
            else:
                content_box.pack(fill="both", expand=True, padx=40, pady=(0, 25))
                header_btn.configure(text="▼ ⚡ Execution Flow Pipeline (Click to Collapse)")
                flow_panel.is_expanded = True
                
        header_btn.configure(command=toggle_flow)
        
        def add_header(txt, color=T_ACCENT): ctk.CTkLabel(content_box, text=txt, font=("Inter", 16, "bold"), text_color=color, anchor="w").pack(fill="x", pady=(15, 5))
        def add_step(num, desc):
            f = ctk.CTkFrame(content_box, fg_color="transparent")
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=num, font=("Inter", 14, "bold"), text_color=T_TEXT, anchor="nw", width=55).pack(side="left")
            lbl = ctk.CTkLabel(f, text=desc, font=("Inter", 14, "italic"), text_color=T_SUBTEXT, anchor="nw", justify="left")
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 15))
            lbl.bind("<Configure>", lambda e, l=lbl: l.configure(wraplength=max(100, e.width - 15)) if e.width > 20 else None)

        add_header("▶ Scraping Phase (Browser Interaction):", "#ea580c")
        add_step("1)", "The Browser Runs a search of the given author's Detals")
        add_step("2)", "Any Captachas appearing on the website should be handled by the user manually")
        add_step("3)", "Once, the profile page in Scholar has been opened firsty we will expand the show more tab to render all papers of the authors")
        add_step("4)", "once all papers have been rendered, each paper will be opened in a separate tab and it will be scraped individually and this will happen for all papers")
        add_step("5)", "once the scraping for all papers is done, the browser is closed")

        add_header("▶ 7-Stage Pipeline Execution:", T_ACCENT)
        add_step("6)", "Stage 1 (Raw Payload Verification): The scraped textual payloads and metadata are authenticated internally before moving forward.")
        add_step("7)", "Stage 2/3 (Ingestion): The validated scholar payload is comprehensively pushed to the intermediate staging tables in the remote database.")
        add_step("8)", "Stage 4 (Master Initialization - Linker): The backend initiates the Master Database run and prepares for matching.")
        add_step("9)", "Stage 5 (Entity Resolution): The pipeline determines the Golden Record and accurately links the scraped Author ID to existing database registries.")
        add_step("10)", "Stage 6 (Intelligent Refinement): The run_targeted_refiner efficiently cleans, standardizes, and strictly deduplicates the retrieved papers.")
        add_step("11)", "Stage 7 (State Sync & Success): The Master Sync definitively pushes all the normalized data to the master_authors index, updating the global state.")

    def show_scopus_view(self):
        self.clear_canvas()
        self.info_btn.pack(side="right", padx=(0, 15))
        self.info_tooltip.text = (
            "Scopus API Pipeline:\n\n"
            "1. Node Init: Passes target names to Elsevier endpoint.\n"
            "2. Scrape Layer: Fetches heavily structured API responses.\n"
            "3. Extraction: Extracts exact DOI, ISSN, and Scopus citations.\n"
            "4. Identity Linker: Validates strict author IDs using RapidFuzz.\n"
            "5. Refiner: Prunes duplicate metadata payloads.\n"
            "6. Backup: Dumps immutable JSON structure directly to '/outputs'.\n"
            "7. Supabase Sync: Pushes validated records directly to Master DB."
        )
        form = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=24)
        form.pack(pady=(10, 20), padx=20, ipadx=40, ipady=10, fill="x")

        ctk.CTkLabel(form, text="Scopus Pipeline Configuration", font=self.font_h2, text_color=T_TEXT).pack(pady=(20, 5))
        
        r1 = ctk.CTkFrame(form, fg_color="transparent")
        r1.pack(fill="x", padx=40, pady=(10, 5))
        
        f1 = ctk.CTkFrame(r1, fg_color="transparent")
        f1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(f1, text="FIRST NAME", font=self.font_label, text_color=T_SUBTEXT).pack(anchor="w", pady=(0, 5))
        self.scopus_f = ctk.CTkEntry(f1, height=45, corner_radius=10, fg_color=T_TERMINAL, border_color=T_BORDER, text_color="#10b981")
        self.scopus_f.pack(fill="x")

        f2 = ctk.CTkFrame(r1, fg_color="transparent")
        f2.pack(side="left", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(f2, text="LAST NAME", font=self.font_label, text_color=T_SUBTEXT).pack(anchor="w", pady=(0, 5))
        self.scopus_l = ctk.CTkEntry(f2, height=45, corner_radius=10, fg_color=T_TERMINAL, border_color=T_BORDER, text_color="#10b981")
        self.scopus_l.pack(fill="x")
        
        self.scopus_exec = ctk.CTkButton(form, text="START SCOPUS SYNC", height=55, font=self.font_h2, 
                                         fg_color=T_ACCENT, text_color=T_BG[1], corner_radius=12)
        self.scopus_exec.pack(pady=(30, 20), padx=50, fill="x")

        flow_panel = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=2, border_color=T_ACCENT, corner_radius=24)
        flow_panel.pack(pady=20, padx=20, fill="x")

        header_btn = ctk.CTkButton(flow_panel, text="▶ ⚡ Execution Flow Pipeline (Click to Expand)", 
                                   font=self.font_h2, text_color=T_ACCENT, fg_color="transparent", 
                                   hover_color=T_BG, anchor="center", height=50)
        header_btn.pack(pady=(15, 10), padx=20, fill="x")

        content_box = ctk.CTkFrame(flow_panel, fg_color="transparent")
        flow_panel.is_expanded = False
        
        def toggle_flow():
            if flow_panel.is_expanded:
                content_box.pack_forget()
                header_btn.configure(text="▶ ⚡ Execution Flow Pipeline (Click to Expand)")
                flow_panel.is_expanded = False
            else:
                content_box.pack(fill="both", expand=True, padx=40, pady=(0, 25))
                header_btn.configure(text="▼ ⚡ Execution Flow Pipeline (Click to Collapse)")
                flow_panel.is_expanded = True
                
        header_btn.configure(command=toggle_flow)
        
        def add_header(txt, color=T_ACCENT): ctk.CTkLabel(content_box, text=txt, font=("Inter", 16, "bold"), text_color=color, anchor="w").pack(fill="x", pady=(15, 5))
        def add_step(num, desc):
            f = ctk.CTkFrame(content_box, fg_color="transparent")
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=num, font=("Inter", 14, "bold"), text_color=T_TEXT, anchor="nw", width=55).pack(side="left")
            lbl = ctk.CTkLabel(f, text=desc, font=("Inter", 14, "italic"), text_color=T_SUBTEXT, anchor="nw", justify="left")
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 15))
            lbl.bind("<Configure>", lambda e, l=lbl: l.configure(wraplength=max(100, e.width - 15)) if e.width > 20 else None)

        add_header("▶ Scraping Phase (Browser Interaction):", "#ea580c")
        add_step("1)", "The broswer will open in the home page of Scopus(elsevier)")
        add_step("2)", "The user has to manually login with their credentials")
        add_step("3)", "Now the engine will automatically navigate to the author search page")
        add_step("4)", "Here we will perform author search based on author's details provided as input by the user")
        add_step("5)", "Out all the fetched profiles, the closest profile window is opened")
        add_step("6)", "Now all the metadata provided on the profile page is scraped")
        add_step("7)", "We click Edit profile on the author's page")
        add_step("8)", "This takes us to the author's Documents tab, a dialog box will pop up, where it will ask whether to proceed or not, and the user has to select ok.")
        add_step("9)", "Now automatically the documents tab is expanded and all available papers (typically 10 papers only will be visible in preview) will be scraped.")
        add_step("10)", "The browser will close automatically.")

        add_header("▶ 7-Stage Pipeline Execution:", T_ACCENT)
        add_step("11)", "Stage 1 (Raw Payload Verification): The engine intercepts the scraped Scopus DOIs, citations, and demographic data.")
        add_step("12)", "Stage 2/3 (Ingestion): The metadata is confidently dispatched into into the scopus-specific staging containers.")
        add_step("13)", "Stage 4 (Master Initialization - Linker): The robust processing subsystem locks the active stream.")
        add_step("14)", "Stage 5 (Entity Resolution): Utilizing identity heuristics, Scopus IDs and profiles are rigorously mapped to the core unified directory.")
        add_step("15)", "Stage 6 (Intelligent Refinement): run_targeted_refiner performs normalization to cleanly fuse multi-source data points.")
        add_step("16)", "Stage 7 (State Sync & Success): Global commits successfully integrate the extracted papers directly with Supabase, indicating a finalized cycle.")

    def show_wos_view(self):
        self.clear_canvas()
        self.info_btn.pack(side="right", padx=(0, 15))
        self.info_tooltip.text = (
            "WoS Ghosting Pipeline:\n\n"
            "1. Node Init: Attaches robot to an authenticated browser port.\n"
            "2. Scrape Layer: Extracts structured document tree across active pages.\n"
            "3. Extraction: Captures WoS indexing metrics & Clarivate analytics.\n"
            "4. Identity Linker: Reconciles author identity via heuristics.\n"
            "5. Refiner: Standardizes deep payload into precise UTF-8 schema.\n"
            "6. Backup: Localized memory snapshots are saved safely.\n"
            "7. Supabase Sync: The unified profile is securely pushed to Supabase."
        )
        card = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=24)
        card.pack(pady=(10, 20), padx=20, ipadx=40, ipady=10, fill="x")

        ctk.CTkLabel(card, text="Web of Science Session", font=self.font_h2, text_color=T_TEXT).pack(pady=(30, 10))
        ctk.CTkLabel(card, text="WoS requires manual login to bypass Cloudflare detection.\nClicking launch will temporarily hide this UI.", 
                     font=self.font_body, text_color=T_SUBTEXT).pack(pady=10)
        self.wos_launch_btn = ctk.CTkButton(card, text="LAUNCH WOS BROWSER", height=60, font=self.font_h2, 
                                            fg_color="#ea580c", text_color="white", corner_radius=12)
        self.wos_launch_btn.pack(pady=40, padx=50, fill="x")

        flow_panel = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=2, border_color=T_ACCENT, corner_radius=24)
        flow_panel.pack(pady=20, padx=20, fill="x")

        header_btn = ctk.CTkButton(flow_panel, text="▶ ⚡ Execution Flow Pipeline (Click to Expand)", 
                                   font=self.font_h2, text_color=T_ACCENT, fg_color="transparent", 
                                   hover_color=T_BG, anchor="center", height=50)
        header_btn.pack(pady=(15, 10), padx=20, fill="x")

        content_box = ctk.CTkFrame(flow_panel, fg_color="transparent")
        flow_panel.is_expanded = False
        
        def toggle_flow():
            if flow_panel.is_expanded:
                content_box.pack_forget()
                header_btn.configure(text="▶ ⚡ Execution Flow Pipeline (Click to Expand)")
                flow_panel.is_expanded = False
            else:
                content_box.pack(fill="both", expand=True, padx=40, pady=(0, 25))
                header_btn.configure(text="▼ ⚡ Execution Flow Pipeline (Click to Collapse)")
                flow_panel.is_expanded = True
                
        header_btn.configure(command=toggle_flow)
        
        def add_header(txt, color=T_ACCENT): ctk.CTkLabel(content_box, text=txt, font=("Inter", 16, "bold"), text_color=color, anchor="w").pack(fill="x", pady=(15, 5))
        def add_step(num, desc):
            f = ctk.CTkFrame(content_box, fg_color="transparent")
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=num, font=("Inter", 14, "bold"), text_color=T_TEXT, anchor="nw", width=55).pack(side="left")
            lbl = ctk.CTkLabel(f, text=desc, font=("Inter", 14, "italic"), text_color=T_SUBTEXT, anchor="nw", justify="left")
            lbl.pack(side="left", fill="x", expand=True, padx=(0, 15))
            lbl.bind("<Configure>", lambda e, l=lbl: l.configure(wraplength=max(100, e.width - 15)) if e.width > 20 else None)

        add_header("▶ Scraping Phase (Browser Interaction / Ghosting):", "#ea580c")
        add_step("1)", "A debugging port browser is opened.")
        add_step("2)", "The user has to manually search for Web of Science author search in Google.")
        add_step("3)", "Once the site is opened, the user has to manually login into their profile with their credentials.")
        add_step("4)", "Now, user has to manually navigate to the author search page.")
        add_step("5)", "The user has to enter their author details and hit search to reach the author's profile page.")
        add_step("6)", "Now, automatically each available tab on WoS (i.e., all indexed, core collection, and others) will be selected, and all available data will be scraped along with the author's profile status.")
        add_step("7)", "Once scraping is done, the browser is closed.")

        add_header("▶ 7-Stage Pipeline Execution:", T_ACCENT)
        add_step("8)", "Stage 1 (Raw Payload Verification): Extracted WoS records are aggregated safely into the local memory payload.")
        add_step("9)", "Stage 2/3 (Ingestion): Core Web of Science statistics and indexes are immediately ported to the master backend integration staging pipeline.")
        add_step("10)", "Stage 4 (Master Initialization - Linker): Hand-off connects the payload to the deterministic resolution system.")
        add_step("11)", "Stage 5 (Entity Resolution): The complex backend securely correlates WoS author hashes and attributes against the central core records.")
        add_step("12)", "Stage 6 (Intelligent Refinement): run_targeted_refiner cleans overlaps, updates aggregate properties, and normalizes indexing syntax.")
        add_step("13)", "Stage 7 (State Sync & Success): Final synchronization commits all results securely into the overarching system state.")

    def _add_input(self, master, txt):
        ctk.CTkLabel(master, text=txt, font=self.font_label, text_color=T_SUBTEXT).pack(anchor="w", padx=40, pady=(15, 5))
        e = ctk.CTkEntry(master, width=600, height=45, corner_radius=10, fg_color=T_TERMINAL, border_color=T_BORDER, text_color="#10b981")
        e.pack(padx=40); return e