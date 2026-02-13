import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import threading

from portable_scraper.modules.scholar_scraper import run_scholar_scraper
from portable_scraper.modules.scopus_scraper import run_scopus_scraper


class ModernGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Research Publication Scraper")
        self.root.geometry("900x680")
        self.root.configure(bg="#0b1221")

        self.output_directory = None

        # ----------- HEADER SECTION ------------
        header = tk.Frame(root, bg="#0b1221")
        header.pack(fill="x", pady=10)

        title = tk.Label(
            header,
            text="Faculty Research Data Scraper",
            font=("Segoe UI", 22, "bold"),
            bg="#0b1221",
            fg="#3b82f6"
        )
        title.pack()

        subtitle = tk.Label(
            header,
            text="Automated Extraction from Google Scholar & Scopus",
            font=("Segoe UI", 10),
            bg="#0b1221",
            fg="#cbd5e1"
        )
        subtitle.pack()

        # ----------- OUTPUT DIRECTORY ------------
        out_frame = tk.Frame(root, bg="#0b1221")
        out_frame.pack(pady=15)

        tk.Button(
            out_frame,
            text="Choose Output Folder",
            font=("Segoe UI", 10),
            bg="#111827",
            fg="white",
            activebackground="#1f2937",
            width=22,
            command=self.choose_folder
        ).grid(row=0, column=0, padx=10)

        self.folder_label = tk.Label(
            out_frame,
            text="No folder selected",
            bg="#0b1221",
            fg="#94a3b8",
            font=("Segoe UI", 9)
        )
        self.folder_label.grid(row=0, column=1)

        # ----------- SCHOLAR FRAME ------------
        scholar_frame = tk.LabelFrame(
            root,
            text=" Google Scholar ",
            font=("Segoe UI", 12, "bold"),
            bg="#0b1221",
            fg="#22c55e",
            padx=20,
            pady=15
        )
        scholar_frame.pack(fill="x", padx=30, pady=10)

        tk.Label(
            scholar_frame,
            text="Faculty Full Name:",
            bg="#0b1221",
            fg="white",
            font=("Segoe UI", 10)
        ).grid(row=0, column=0, sticky="w")

        self.scholar_name = tk.Entry(
            scholar_frame,
            width=45,
            font=("Segoe UI", 10)
        )
        self.scholar_name.grid(row=0, column=1, padx=10, pady=5)

        self.scholar_btn = tk.Button(
            scholar_frame,
            text="Scrape Scholar Data",
            bg="#16a34a",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=22,
            command=self.start_scholar
        )
        self.scholar_btn.grid(row=1, column=0, columnspan=2, pady=10)

        # ----------- SCOPUS FRAME ------------
        scopus_frame = tk.LabelFrame(
            root,
            text=" Scopus ",
            font=("Segoe UI", 12, "bold"),
            bg="#0b1221",
            fg="#eab308",
            padx=20,
            pady=15
        )
        scopus_frame.pack(fill="x", padx=30, pady=10)

        tk.Label(scopus_frame, text="First Name:", bg="#0b1221", fg="white").grid(row=0, column=0, sticky="w")
        self.scopus_first = tk.Entry(scopus_frame, width=35, font=("Segoe UI", 10))
        self.scopus_first.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(scopus_frame, text="Last Name:", bg="#0b1221", fg="white").grid(row=1, column=0, sticky="w")
        self.scopus_last = tk.Entry(scopus_frame, width=35, font=("Segoe UI", 10))
        self.scopus_last.grid(row=1, column=1, padx=10, pady=5)

        self.scopus_btn = tk.Button(
            scopus_frame,
            text="Scrape Scopus Data",
            bg="#d97706",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=22,
            command=self.start_scopus
        )
        self.scopus_btn.grid(row=2, column=0, columnspan=2, pady=10)

        # ----------- BOTH SOURCES BUTTON ------------
        self.both_btn = tk.Button(
            root,
            text="SCRAPE BOTH SOURCES",
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=30,
            command=self.start_both
        )
        self.both_btn.pack(pady=10)

        # ----------- STATUS PANEL ------------
        status_frame = tk.LabelFrame(
            root,
            text=" Activity Log ",
            bg="#0b1221",
            fg="#3b82f6",
            font=("Segoe UI", 12, "bold"),
            padx=10,
            pady=10
        )
        status_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self.log_box = scrolledtext.ScrolledText(
            status_frame,
            bg="#020617",
            fg="#e2e8f0",
            height=12,
            font=("Consolas", 9)
        )
        self.log_box.pack(fill="both", expand=True)

        footer = tk.Label(
            root,
            text="Portable Scraper v1.0 – Designed for Academic Analytics",
            bg="#0b1221",
            fg="#475569",
            font=("Segoe UI", 9)
        )
        footer.pack(pady=5)

    # ---------------- FUNCTIONS ----------------

    def log(self, message):
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_directory = folder
            self.folder_label.config(text=folder)

    def disable_buttons(self):
        self.scholar_btn.config(state="disabled")
        self.scopus_btn.config(state="disabled")
        self.both_btn.config(state="disabled")

    def enable_buttons(self):
        self.scholar_btn.config(state="normal")
        self.scopus_btn.config(state="normal")
        self.both_btn.config(state="normal")

    def start_scholar(self):
        threading.Thread(target=self.run_scholar).start()

    def start_scopus(self):
        threading.Thread(target=self.run_scopus).start()

    def start_both(self):
        threading.Thread(target=self.run_both).start()

    # ----------- SCRAPER EXECUTION ------------

    def run_scholar(self):
        if not self.output_directory:
            messagebox.showerror("Error", "Select output folder first")
            return

        name = self.scholar_name.get().strip()

        if not name:
            messagebox.showerror("Error", "Enter faculty name")
            return

        self.disable_buttons()
        self.log("Starting Google Scholar scraping...")

        try:
            excel_path, payload = run_scholar_scraper(name, self.output_directory)

            self.log(f"Scholar scraping completed: {excel_path}")
            messagebox.showinfo("Success", "Google Scholar scraping completed!")

        except Exception as e:
            self.log(f"Scholar Error: {e}")
            messagebox.showerror("Error", str(e))

        self.enable_buttons()

    def run_scopus(self):
        if not self.output_directory:
            messagebox.showerror("Error", "Select output folder first")
            return

        first = self.scopus_first.get().strip()
        last = self.scopus_last.get().strip()

        if not first or not last:
            messagebox.showerror("Error", "Enter first and last name")
            return

        self.disable_buttons()
        self.log("Starting Scopus scraping...")

        try:
            file = run_scopus_scraper(first, last, self.output_directory)
            self.log(f"Scopus scraping completed: {file}")
            messagebox.showinfo("Success", "Scopus scraping completed!")
        except Exception as e:
            self.log(f"Scopus Error: {e}")
            messagebox.showerror("Error", str(e))

        self.enable_buttons()

    def run_both(self):
        self.run_scholar()
        self.run_scopus()


def main():
    root = tk.Tk()
    ModernGUI(root)
    root.mainloop()
