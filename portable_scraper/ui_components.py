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
        else:
            self.sidebar.configure(width=280); self.logo_text.pack(side="left", padx=10); self.status_lbl.pack(side="left")
            for b in self.nav_btns: b.configure(text=b.full_text)
            self.sidebar_collapsed = False

    def _build_main_viewport(self):
        """ Compact Viewport: Fixes the scrollbar issue """
        self.viewport = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.viewport.grid(row=0, column=1, sticky="nsew")
        
        # A. Slim Header
        self.header = ctk.CTkFrame(self.viewport, height=70, fg_color="transparent")
        self.header.pack(fill="x", padx=60, pady=(20, 0)) # Reduced from 30
        self.breadcrumb = ctk.CTkLabel(self.header, text="PROJECT / OVERVIEW", font=self.font_label, text_color=T_ACCENT)
        self.breadcrumb.pack(anchor="w")
        self.title_lbl = ctk.CTkLabel(self.header, text="Academic Pulse", font=self.font_h1, text_color=T_TEXT)
        self.title_lbl.pack(anchor="w")
        
        # 🟢 RESTORED: Theme Toggle (Fixed the AttributeError)
        self.theme_btn = ctk.CTkButton(self.header, text="🌙", width=40, height=40, corner_radius=10,
                                        fg_color=T_CARD, border_width=1, border_color=T_BORDER, font=("Inter", 16))
        self.theme_btn.place(relx=1.0, rely=0.5, anchor="e")
        
        # B. Dynamic Canvas (Now fills only necessary X, not greedy on Y)
        self.canvas = ctk.CTkFrame(self.viewport, fg_color="transparent", corner_radius=0)
        self.canvas.pack(fill="x", padx=60, pady=5) # Slashed padding

        # C. Permanent Audit Feed (Shrunk to ensure visibility)
        self.log_card = ctk.CTkFrame(self.viewport, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=20)
        self.log_card.pack(fill="both", expand=True, padx=60, pady=(0, 20)) # This now takes the 'flex' space
        
        ctk.CTkLabel(self.log_card, text="Live Pipeline Audit Feed", font=self.font_label, text_color=T_ACCENT).pack(anchor="w", padx=25, pady=(10, 0))
        self.console = ctk.CTkTextbox(self.log_card, fg_color=T_TERMINAL, font=self.font_mono, text_color="#10b981", corner_radius=12)
        self.console.pack(fill="both", expand=True, padx=20, pady=(5, 15))

    def show_dash_view(self, greeting_txt):
        """ High-Density Dashboard: No double-scrollbars """
        for w in self.canvas.winfo_children(): w.destroy()
        
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
    # --- VIEW RENDERERS (REPLACING THE ENDLESS TO-AND-FRO) ---
    def clear_canvas(self):
        for w in self.canvas.winfo_children(): w.destroy()

    

    def show_scholar_view(self):
        self.clear_canvas()
        form = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=24)
        form.pack(pady=20, ipadx=40, ipady=10)
        ctk.CTkLabel(form, text="New Author Search", font=self.font_h2, text_color=T_TEXT).pack(pady=(30, 5))
        self.scholar_f = self._add_input(form, "FIRST NAME")
        self.scholar_l = self._add_input(form, "LAST NAME")
        self.scholar_a = self._add_input(form, "AFFILIATION / UNIVERSITY")
        self.scholar_exec = ctk.CTkButton(form, text="EXECUTE SCHOLAR PIPELINE", height=55, font=self.font_h2, 
                                          fg_color=T_ACCENT, text_color=T_BG[1], corner_radius=12)
        self.scholar_exec.pack(pady=40, padx=50, fill="x")

    def show_scopus_view(self):
        self.clear_canvas()
        form = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=24)
        form.pack(pady=20, ipadx=40, ipady=10)
        ctk.CTkLabel(form, text="Scopus API Extraction", font=self.font_h2, text_color=T_TEXT).pack(pady=(30, 5))
        self.scopus_f = self._add_input(form, "FIRST NAME")
        self.scopus_l = self._add_input(form, "LAST NAME")
        self.scopus_exec = ctk.CTkButton(form, text="START SCOPUS SYNC", height=55, font=self.font_h2, 
                                         fg_color=T_ACCENT, text_color=T_BG[1], corner_radius=12)
        self.scopus_exec.pack(pady=40, padx=50, fill="x")

    def show_wos_view(self):
        self.clear_canvas()
        # 🟢 RESTORED: The WoS Content Card (image_98e5ea.png)
        card = ctk.CTkFrame(self.canvas, fg_color=T_CARD, border_width=1, border_color=T_BORDER, corner_radius=24)
        card.pack(pady=50, padx=50, fill="x")
        ctk.CTkLabel(card, text="Web of Science Session", font=self.font_h2, text_color=T_TEXT).pack(pady=(30, 10))
        ctk.CTkLabel(card, text="WoS requires manual login to bypass Cloudflare detection.\nClicking launch will temporarily hide this UI.", 
                     font=self.font_body, text_color=T_SUBTEXT).pack(pady=10)
        self.wos_launch_btn = ctk.CTkButton(card, text="LAUNCH WOS BROWSER", height=60, font=self.font_h2, 
                                            fg_color="#ea580c", text_color="white", corner_radius=12)
        self.wos_launch_btn.pack(pady=40, padx=50, fill="x")

    def _add_input(self, master, txt):
        ctk.CTkLabel(master, text=txt, font=self.font_label, text_color=T_SUBTEXT).pack(anchor="w", padx=50, pady=(15, 5))
        e = ctk.CTkEntry(master, width=600, height=45, corner_radius=10, fg_color=T_TERMINAL, border_color=T_BORDER, text_color="#10b981")
        e.pack(padx=50); return e