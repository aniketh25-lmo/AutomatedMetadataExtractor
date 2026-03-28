from portable_scraper.ui_components import MasterpieceView, T_ACCENT, T_BG
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


# --- ADD THIS CLASS AT THE TOP ---
class IORedirector:
    def __init__(self, log_func):
        self.log_func = log_func
    def write(self, text):
        if text.strip():
            self.log_func(text.strip())
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
        self.show_dash_view(greet)
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
        import sys
        sys.stdout = IORedirector(self.log_to_terminal)
        
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
        import sys
        sys.stdout = IORedirector(self.log_to_terminal)
        
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
            path, payload = attach_and_scrape_wos(port, process, app_config.output_folder)
            self.after(0, self.deiconify)
            if payload: run_processing_pipeline("wos", payload)
            self.log_to_terminal("WoS Sync Complete.")
        except Exception as e:
            self.after(0, self.deiconify)
            self.log_to_terminal(f"WoS Failure: {str(e)}")

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