import PyInstaller.__main__
import os
import customtkinter

# Find the location of the customtkinter library to include its theme files
ctk_path = os.path.dirname(customtkinter.__file__)

PyInstaller.__main__.run([
    # 🟢 TARGET ENTRY POINT: app_controller.py launches the main GUI
    "app_controller.py",
    
    "--name=AcademicPulsePro",
    "--onefile",
    "--console", # Prevents a black console window from popping up behind your GUI
    "--clean",

    # Core Logic & UI Hidden Imports
    "--hidden-import=customtkinter",
    "--hidden-import=selenium",
    "--hidden-import=webdriver_manager",
    "--hidden-import=webdriver_manager.chrome",
    "--hidden-import=pandas",
    "--hidden-import=openpyxl",
    "--hidden-import=PIL", # Required if you use icons/images in the GUI
    
    # Backend & Security Hidden Imports
    "--hidden-import=supabase",
    "--hidden-import=postgrest",
    "--hidden-import=rapidfuzz",
    "--hidden-import=requests", # Required for Scopus API node

    # --- DATA INCLUSION ---
    # Include your core scraper logic folder
    "--add-data=portable_scraper;portable_scraper",
    
    # 🟢 CRITICAL: Include CustomTkinter theme files or the UI will look broken
    f"--add-data={ctk_path};customtkinter",

    # 🟢 ICON: Ensure icon.ico is in your root directory
    "--icon=icon.ico",
])