import json
import os
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
    
    # Ensures folder exists relative to project root
    output_path = os.path.join(BASE_DIR, "..", "..", config_dict.get("output_folder", "outputs"))
    os.makedirs(output_path, exist_ok=True)
    
    return SimpleNamespace(**config_dict)

app_config = load_config()