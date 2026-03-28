from supabase import create_client
from portable_scraper.core.config import app_config as config

# 🟢 Dot notation is mandatory for SimpleNamespace objects
supabase = create_client(
    config.supabase_url, 
    config.supabase_key
)