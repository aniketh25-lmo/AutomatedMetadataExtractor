from supabase import create_client
from portable_scraper.core.config import load_config

config = load_config()

supabase = create_client(
    config["supabase_url"],
    config["supabase_key"]
)
