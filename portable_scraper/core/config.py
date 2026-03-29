import json
import os
import sys
from types import SimpleNamespace

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "supabase_url": "https://your-url.supabase.co",
    "supabase_key": "your-key",
    "login_wait_time": 30,
    "page_load_wait": 10,
    "output_folder": "outputs",
    "headless": False
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)

    with open(CONFIG_FILE, "r") as f:
        config_dict = json.load(f)
    
    # Use this to find the real directory of the .exe
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    # Ensure the output folder is tied to the exe location, not the temp folder
    output_path = os.path.join(application_path, "outputs")
    # Ensures folder exists relative to project root
    os.makedirs(output_path, exist_ok=True)
    
    return SimpleNamespace(**config_dict)

app_config = load_config()