import PyInstaller.__main__
import os
import customtkinter

# Find the location of the customtkinter library
ctk_path = os.path.dirname(customtkinter.__file__)

PyInstaller.__main__.run([
    "app_controller.py",
    "--name=AcademicPulsePro",
    "--onefile",
    "--windowed", # 🟢 THE FIX: Hides the black console window for a "Pro" feel
    "--clean",

    # Core Logic & UI Hidden Imports
    "--hidden-import=customtkinter",
    "--hidden-import=selenium",
    "--hidden-import=webdriver_manager",
    "--hidden-import=webdriver_manager.chrome",
    "--hidden-import=pandas",
    "--hidden-import=openpyxl",
    "--hidden-import=PIL",
    "--hidden-import=PIL._tkinter_finder", # 🟢 THE FIX: Required for CTkImage in .exe
    
    # Backend & Security Hidden Imports
    "--hidden-import=supabase",
    "--hidden-import=postgrest",
    "--hidden-import=gotrue",
    "--hidden-import=storage3",
    "--hidden-import=realtime",
    "--hidden-import=websockets",
    "--hidden-import=rapidfuzz",
    "--hidden-import=requests",
    "--copy-metadata=webdriver_manager",

    # --- DATA INCLUSION ---
    "--add-data=portable_scraper;portable_scraper",
    f"--add-data={ctk_path};customtkinter",
    
    # 🟢 THE FIX: Bundle your architecture diagram inside the .exe
    "--add-data=architecture.png;.", 
    
    "--icon=icon.ico",
])