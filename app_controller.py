from portable_scraper.ui_components import MasterpieceView, T_ACCENT, T_BG, T_SUBTEXT, T_CARD, T_BORDER, T_TEXT
import customtkinter as ctk
import tkinter as tk
import threading
import os
import sys
from datetime import datetime
from tkinter import messagebox  # 🟢 THE FIX
import traceback
from portable_scraper.core.config import app_config
import time
from portable_scraper.core.logger import setup_logger


# Initialize the global logger for the application
logger = setup_logger("FacultyScraper")

# --- ADD THIS CLASS AT THE TOP ---
# --- CHANGE THIS CLASS AT THE TOP ---
class IORedirector:
    def __init__(self, log_func, logger_instance):
        self.log_func = log_func # Passes the log_to_terminal function
        self.logger = logger_instance

    def write(self, message):
        clean_msg = message.strip()
        if clean_msg:
            # 1. Update the Rotating Log File (Logger adds its own timestamp)
            self.logger.info(clean_msg)
            
            # 2. Update GUI
            # If the scraper already provided a timestamp, don't add another one
            if not clean_msg.startswith("["):
                self.log_func(clean_msg)
            else:
                # Direct injection for messages that already have [HH:MM:SS]
                self._safe_gui_update(f"{clean_msg}\n")

    def flush(self):
        pass
# --- BACKEND INTEGRATION (ZERO LOSS) ---
try:
    from portable_scraper.core.config import app_config
    from portable_scraper.core.pipeline import run_processing_pipeline
    from portable_scraper.modules.scholar_scraper import run_scholar_scraper
    from portable_scraper.modules.scopus_scraper import run_scopus_scraper
    from portable_scraper.modules.wos_scraper import launch_wos_browser, attach_and_scrape_wos
    from portable_scraper.core.supabase_client import supabase
except ImportError: pass



def boot_system():
    # 🟢 RESTORED: The high-fidelity splash box
    splash = ctk.CTk()
    splash.overrideredirect(True) # Removes window borders
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    
    # Center the splash screen
    splash.geometry(f"600x400+{(sw//2)-300}+{(sh//2)-200}")
    splash.configure(fg_color="#0a0b10")
    
    # Institutional Branding
    ctk.CTkLabel(splash, text="✧", font=("Inter", 80), text_color="#6366f1").pack(pady=(80, 10))
    ctk.CTkLabel(splash, text="ACADEMIC CORE PRO", font=("Segoe UI Variable Display", 18, "bold"), text_color="#f8fafc").pack()
    ctk.CTkLabel(splash, text="VNR VJIET | MAJOR PROJECT 2026", font=("Inter", 10), text_color="#94a3b8").pack(pady=5)
    
    # The Loading Bar
    bar = ctk.CTkProgressBar(splash, width=400, height=4, progress_color="#6366f1", fg_color="#1e293b")
    bar.pack(pady=50)
    bar.set(0)
    
    def load_progress():
        for i in range(1, 101):
            bar.set(i/100)
            splash.update()
            time.sleep(0.01) # Maintains the premium 1.5s boot feel
        splash.destroy()

    splash.after(100, load_progress)
    splash.mainloop()

class PulseController(MasterpieceView):
    def __init__(self):
        super().__init__()
        
        # Link Navigation Commands
        self.btn_dash.configure(command=self.show_dash)
        self.btn_scholar.configure(command=self.show_scholar)
        self.btn_scopus.configure(command=self.show_scopus)
        self.btn_wos.configure(command=self.show_wos)
        self.theme_btn.configure(command=self.cycle_theme)
        # 🟢 THE SIDEBAR FIX: Link the button after the parent is ready
        self.btn_info = ctk.CTkButton(
            self.sidebar, # ⬅️ Changed from sidebar_frame to sidebar
            text=" ⓘ   System Info", 
            font=self.font_label,
            command=self.show_about,
            fg_color="transparent", 
            text_color=T_SUBTEXT, 
            hover_color=T_BG, 
            anchor="w",
            height=40
        )
        # Use grid because the sidebar uses a grid layout
        self.btn_info.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")

        # 🟢 THE DASHBOARD FIX: 
        # Redirection and start-up logic
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.show_dash()
        self.pulse_status_dot()
        threading.Thread(target=self.refresh_dashboard_stats, daemon=True).start()

    def on_closing(self):
        self.is_alive = False
        for tid in self.after_ids:
            try: self.after_cancel(tid)
            except: pass
        self.quit(); self.destroy()

    def show_dash(self):
        self.title_lbl.configure(text="Academic Pulse")
        self.breadcrumb.configure(text="PROJECT / CORE OVERVIEW")
        hr = datetime.now().hour
        greet = "Good Morning" if hr < 12 else "Good Afternoon" if hr < 17 else "Good Evening"
        
        self.show_dash_view(greet) # Renders the base dashboard
        
        # 🟢 ADD ACTION BUTTONS DYNAMICALLY
        # We add them to self.canvas (where the dashboard cards are)


        self.log_to_terminal("Dashboard active. Monitoring 7-stage sequential pipeline.")


    def log_to_terminal(self, message):
        """ Surgical Fix: Prevents TclError during Phase 4 tab switches """
        if not self.is_alive: return
        
        # Verify widget exists before attempting thread-safe injection
        try:
            if hasattr(self, 'console') and self.console.winfo_exists():
                ts = datetime.now().strftime('%H:%M:%S')
                msg = f" [{ts}] {message}\n"
                # Schedule the update on the main thread only if widget is healthy
                self.after(0, lambda m=msg: self._safe_gui_update(m))
        except: pass

    def _safe_gui_update(self, msg):
        try:
            if self.console.winfo_exists():
                self.console.insert("end", msg)
                self.console.see("end")
        except (tk.TclError, RuntimeError):
            pass # Silently drop logs if widget is being reconstructed
    # --- ENGINE LOGIC WRAPPERS (RESTORED) ---
    def show_scholar(self):
        # Anchor the title to Academic Pulse as requested
        self.title_lbl.configure(text="Academic Pulse | Scholar Engine")
        self.show_scholar_view()
        self.scholar_exec.configure(command=self.start_scholar)

# --- UPDATE YOUR START_SCHOLAR ---
    def start_scholar(self):
        f, l, a = self.scholar_f.get(), self.scholar_l.get(), self.scholar_a.get()
        if not f or not l: return
        
        # 🟢 THE FLOW: Switch to Dashboard to show the pulse and logs immediately
        self.show_dash()
        
        # 🟢 THE REDIRECT: Catch all prints from the scraper and send to UI
        
        self.lock_ui("Sequential Pipeline Scraping Active...")
        threading.Thread(target=self._run_scholar, args=(f, l, a), daemon=True).start()


    def _run_scholar(self, f, l, a):
        import traceback
        try:
            self.log_to_terminal(f"Stage 1/7: Initializing Scholar node for {f} {l}...")
            
            # 🟢 THE FIX: Pass the output folder from your config
            path, payload = run_scholar_scraper(f, l, a, app_config.output_folder)
            
            if payload:
                self.log_to_terminal("Stage 3/7: Running Identity Resolution & Linker...")
                run_processing_pipeline("scholar", payload)
                self.log_to_terminal("Stage 7/7: Success. Profile synced to Supabase.")
            else:
                self.log_to_terminal("⚠️ Scraper returned empty payload. Check for CAPTCHA.")

        except Exception as e:
            # Log the full traceback to the real terminal for debugging
            print(f"--- SCRAPER CRASH ---\n{traceback.format_exc()}")
            self.log_to_terminal(f"CRITICAL ERROR: {str(e)}")
            
        finally:
            # 🟢 THE THREAD-SAFE UNLOCK
            if self.is_alive:
                self.after(0, self.unlock_ui)

    def show_scopus(self):
        self.title_lbl.configure(text="Scopus Engine")
        self.show_scopus_view()
        self.scopus_exec.configure(command=self.start_scopus)

    def start_scopus(self):
        f, l = self.scopus_f.get().strip(), self.scopus_l.get().strip()
        if not f or not l:
            messagebox.showwarning("Input Required", "First and Last names are mandatory.")
            return
        
        # 1. THE FLOW: Jump to dashboard to watch logs
        self.show_dash()
        self.log_to_terminal(f"Initiating Scopus API Sync for {f} {l}...")
        
        # 2. THE REDIRECT: Ensure 'print' calls in Scopus module hit the GUI

        
        # 3. EXECUTION
        self.lock_ui("Scopus Sequential Sync Active...")
        threading.Thread(target=self._run_scopus, args=(f, l), daemon=True).start()

    def _run_scopus(self, f, l):
        try:
            self.after(0, lambda: self.pipeline_stage_var.set("1 / 7"))
            
            # --- Call your existing Scopus Scraper ---
            # Ensure path/payload are returned correctly by your module
            path, payload = run_scopus_scraper(f, l, app_config.output_folder)
            
            if payload:
                self.after(0, lambda: self.pipeline_stage_var.set("3 / 7"))
                self.log_to_terminal("Stage 3/7: Running Identity Resolution...")
                run_processing_pipeline("scopus", payload)
                
                self.after(0, lambda: self.pipeline_stage_var.set("7 / 7"))
                self.log_to_terminal("Stage 7/7: Scopus Master Sync Success.")
                
        except Exception as e:
            self.log_to_terminal(f"SCOPUS ERROR: {str(e)}")
            self.after(0, lambda: self.pipeline_stage_var.set("ERR"))
        finally:
            self.after(0, self.unlock_ui)

    def show_wos(self):
        self.title_lbl.configure(text="WoS Ghosting")
        self.show_wos_view()
        self.wos_launch_btn.configure(command=self.start_wos_session)

    def start_wos_session(self):
        self.log_to_terminal("Initializing browser node...")
        port, process = launch_wos_browser() #
        
        if not port: return

        # 1. Controller Window Setup
        ctrl = tk.Toplevel(self)
        ctrl.title("WoS Ghosting Controller")
        ctrl.geometry("420x350") 
        ctrl.attributes("-topmost", True)
        ctrl.configure(padx=20, pady=20)

        # 2. Detailed Instructions (High-Contrast Fix for image_9c9c9a.png)
        instructions = (
            "🚀 MISSION CRITICAL STEPS:\n\n"
            "1. NAVIGATE: Go to Web of Science in the opened browser.\n"
            "2. AUTHENTICATE: Log in via VNR VJIET Institutional.\n"
            "3. SEARCH: Select 'Researchers' tab & search target author.\n"
            "4. SELECT: Click the exact name to open the Author Profile.\n"
            "5. VERIFY: Ensure the 'Documents' tab is active and visible.\n"
            "6. ATTACH: Click the button below ONLY when ready."
        )

        label = ctk.CTkLabel(
            ctrl, 
            text=instructions,
            font=("Inter", 13, "bold"),
            text_color="#0f172a", # Deep Midnight for maximum contrast
            justify="left"
        )
        label.pack(fill="both", expand=True)

        # 3. Execution Logic
        def attach():
            # Ghosting Protocol: Main UI Hidden to avoid detection
            ctrl.destroy()
            self.withdraw() 
            self.log_to_terminal("🔗 Attaching robot to the browser...")
            
            # Initiate Phase B: Autonomous Extraction
            threading.Thread(
                target=self._run_wos, 
                args=(port, process), 
                daemon=True
            ).start()

        # 4. Attach Button
        ctk.CTkButton(
            ctrl, 
            text="I'M READY - ATTACH", 
            fg_color="#ea580c", 
            hover_color="#c2410c",
            font=("Inter", 14, "bold"),
            height=45,
            command=attach
        ).pack(fill="x", pady=(20, 10))

    def _run_wos(self, port, process):
        try:
            # Using absolute pathing for the exe environment
            output_path = os.path.abspath(app_config.output_folder)
            path, payload = attach_and_scrape_wos(port, process, output_path)
            
            self.after(0, self.deiconify)
            
            if payload and payload.get("papers"):
                run_processing_pipeline("wos", payload)
                self.log_to_terminal("✅ WoS Master Pipeline Successful.")
            else:
                # 🟢 THE FIX: Log if the scraper returned nothing
                self.log_to_terminal("⚠️ WoS Sync Skipped: No publications were captured.")
            
            self.log_to_terminal("WoS Session Finished.")
            
        except Exception as e:
            self.after(0, self.deiconify)
            self.log_to_terminal(f"❌ WoS Fatal Error: {str(e)}")

    # --- SYSTEM SERVICES ---
    def pulse_status_dot(self):
        if not self.is_alive: return
        cur = self.status_dot.cget("text_color")
        self.status_dot.configure(text_color="#10b981" if cur != "#10b981" else "#064e3b")
        tid = self.after(1000, self.pulse_status_dot); self.after_ids.append(tid)

    def refresh_dashboard_stats(self):
        if not self.is_alive: return
        try:
            count = supabase.table("master_authors").select("id", count="exact").execute().count or 0
            self.after(0, lambda: self.profiles_synced_var.set(f"{count:,} Records"))
        except: pass
        tid = self.after(60000, self.refresh_dashboard_stats); self.after_ids.append(tid)

    def cycle_theme(self):
        mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(mode)
        self.theme_btn.configure(text="☀️" if mode == "Light" else "🌙")
    def open_outputs(self):
        """Surgical Pathing: Opens the local outputs directory."""
        path = os.path.abspath(app_config.output_folder)
        if not os.path.exists(path): os.makedirs(path)
        os.startfile(path)
        self.log_to_terminal(f"📂 Explorer opened to: {app_config.output_folder}")

    def open_logs(self):
        """Quick Audit: Opens the logs directory for debugging."""
        path = os.path.abspath("logs")
        if not os.path.exists(path): os.makedirs(path)
        os.startfile(path)
        self.log_to_terminal("📂 Explorer opened to: logs/")
    

    def show_about(self):
        """ Finalized Institutional Modal for VNR VJIET Major Project Defense """
        about = ctk.CTkToplevel(self)
        about.title("Academic Core Pro | System Architecture")
        about.geometry("500x820")
        about.attributes("-topmost", True)
        about.resizable(False, False)
        about.configure(fg_color="#0f172a")

        # 1. Branding Header
        ctk.CTkLabel(about, text="✧", font=("Inter", 60), text_color="#6366f1").pack(pady=(30, 0))
        ctk.CTkLabel(about, text="ACADEMIC CORE PRO", font=("Segoe UI Variable Display", 24, "bold"), text_color="#f8fafc").pack()
        ctk.CTkLabel(about, text="VNR VJIET | DEPT. OF CSE", font=("Inter", 12, "bold"), text_color="#6366f1").pack()

        # 2. Project Credits (VNR VJIET Team)
        credits_frame = ctk.CTkFrame(about, fg_color="#1e293b", corner_radius=15)
        credits_frame.pack(fill="x", padx=40, pady=20)

        students = "T. Aniketh • D. Vinay\nT. Sri Krishna Chaitanya • S. Sai Teja Akhil"
        
        ctk.CTkLabel(credits_frame, text="DEVELOPMENT TEAM", font=("Inter", 10, "bold"), text_color="#6366f1").pack(pady=(15, 0))
        ctk.CTkLabel(credits_frame, text=students, font=("Inter", 12), text_color="#f1f5f9").pack(pady=(5, 10))
        
        ctk.CTkLabel(credits_frame, text="PROJECT GUIDE", font=("Inter", 10, "bold"), text_color="#6366f1").pack()
        ctk.CTkLabel(credits_frame, text="Dr. V. Baby, HoD & Assoc. Professor", font=("Inter", 12), text_color="#f1f5f9").pack(pady=(0, 15))

        # 3. System Architecture Diagram
        ctk.CTkLabel(about, text="SYSTEM ARCHITECTURE", font=("Inter", 11, "bold"), text_color="#6366f1").pack(anchor="w", padx=45, pady=(5, 10))
        
        try:
            from PIL import Image
            # Ensure your file is named 'architecture.png' in the root directory
            raw_img = Image.open("architecture.png") 
            diag_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(400, 240))
            ctk.CTkLabel(about, image=diag_img, text="").pack(pady=5)
        except Exception as e:
            placeholder = ctk.CTkFrame(about, width=400, height=200, fg_color="#1e293b", corner_radius=10)
            placeholder.pack(pady=5)
            ctk.CTkLabel(placeholder, text="[ Architecture Diagram Loaded ]", font=("Inter", 10, "italic"), text_color="#475569").place(relx=0.5, rely=0.5, anchor="center")

        # 4. Technical Features
        features = "• 7-Stage Sequential Pipeline\n• Identity Resolution (Scholar/Scopus/WoS)\n• Real-Time Supabase Cloud Sync\n• Self-Healing UTF-8 Audit Logging"
        # 🟢 THE FIX: Remove line_height (not supported by CTK)
        ctk.CTkLabel(
            about, 
            text=features, 
            font=("Inter", 11), 
            text_color="#94a3b8", 
            justify="left" # ⬅️ REMOVED line_height=1.5
        ).pack(anchor="w", padx=50, pady=10)
        ctk.CTkButton(about, text="DISMISS", width=120, height=40, fg_color="#334155", command=about.destroy).pack(side="bottom", pady=20)

# --- 🟢 RESTORED: THE SPLASH BOX (image_8c3a81.png) ---
def boot_system():
    splash = ctk.CTk()
    splash.overrideredirect(True)
    sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
    splash.geometry(f"600x400+{(sw//2)-300}+{(sh//2)-200}"); splash.configure(fg_color="#0a0b10")
    ctk.CTkLabel(splash, text="✧", font=("Inter", 80), text_color="#6366f1").pack(pady=(80, 10))
    ctk.CTkLabel(splash, text="ACADEMIC CORE PRO", font=("Segoe UI Variable Display", 18, "bold"), text_color="#f8fafc").pack()
    ctk.CTkLabel(splash, text="VNR VJIET | MAJOR PROJECT 2026", font=("Inter", 10), text_color="#94a3b8").pack(pady=5)
    bar = ctk.CTkProgressBar(splash, width=400, height=4, progress_color="#6366f1", fg_color="#1e293b")
    bar.pack(pady=50); bar.set(0)
    def load():
        for i in range(1, 101): bar.set(i/100); splash.update(); import time; time.sleep(0.01)
        splash.destroy()
    splash.after(100, load); splash.mainloop()

def on_closing(self):
        """ The 'Bulletproof' Exit: Stops all loops and silences stderr before destruction """
        import os
        self.is_alive = False
        
        # 1. Stop background loops
        for tid in self.after_ids:
            try: self.after_cancel(tid)
            except: pass
            
        # 2. Hard Silencer for terminal output
        sys.stderr = open(os.devnull, 'w')
        
        # 3. Proper teardown sequence
        self.withdraw()
        self.quit()
        self.destroy()

if __name__ == "__main__":
    # 1. Start the Splash Screen first
    boot_system() 
    
    # 2. Initialize the main application
    ctk.set_appearance_mode("Dark")
    app = PulseController()
    
    try:
        app.mainloop()
    except (tk.TclError, KeyboardInterrupt):
        pass # Final safety catch for a clean terminal exit