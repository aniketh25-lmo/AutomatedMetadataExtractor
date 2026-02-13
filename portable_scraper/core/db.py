from supabase import create_client
from portable_scraper.core.config import load_config

config = load_config()

SUPABASE_URL = config["supabase_url"]
SUPABASE_KEY = config["supabase_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
