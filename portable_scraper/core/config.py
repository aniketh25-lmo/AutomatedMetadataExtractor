import json
import os

# Path to this file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

#print("CONFIG PATH:", CONFIG_FILE)


DEFAULT_CONFIG = {
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
        return json.load(f)
