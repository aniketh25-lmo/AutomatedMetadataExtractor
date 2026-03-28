import re
import time
from portable_scraper.core.supabase_client import supabase


# ==========================================
# 1. UNIVERSAL TYPE CASTER & CLEANER
# ==========================================
def clean_to_int(value):
    """Safely extracts integers from strings (e.g., '1,234' -> 1234)."""
    if value is None:
        return None
    s = str(value)
    s = re.sub(r"[^\d]", "", s)  # keep digits only
    if s == "":
        return None
    return int(s)

def retry_db_call(func, max_attempts=3, delay=2):
    """Universal 3-Attempt Network Resilience Wrapper."""
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f"   ❌ DB operation failed after {max_attempts} attempts: {e}")
            else:
                time.sleep(delay)
    return None

# ==========================================
# 2. SCOPUS (HYBRID UPSERT)
# ==========================================
def push_scopus_payload(payload: dict):
    profile = payload["profile"]
    papers = payload["papers"]

    clean_scopus_id = profile.get("Scopus_ID")
    if not clean_scopus_id or clean_scopus_id.strip() == "":
        clean_scopus_id = None

    profile_clean = {
        "name": profile.get("Name"),
        "scopus_id": clean_scopus_id,
        "orcid": profile.get("ORCID"),
        "organization": profile.get("Organization"),
        "total_documents": clean_to_int(profile.get("Documents")),
        "h_index": clean_to_int(profile.get("H-Index")),
        "citations": clean_to_int(profile.get("Citations")),
        "profile_url": profile.get("Profile URL")
    }

    # 1. Smart Author Upsert (Handles missing IDs safely)
    def handle_scopus_author():
        if clean_scopus_id:
            # We have a unique ID, use fast upsert
            supabase.table("scopus_authors").upsert(profile_clean, on_conflict="scopus_id").execute()
        else:
            # Blind insert as fallback
            supabase.table("scopus_authors").insert(profile_clean).execute()
    
    retry_db_call(handle_scopus_author)

    # 2. Smart Paper Upsert (No Unique Constraints on Table, requires Select check)
    for p in papers:
        paper_clean = {
            "scopus_id": clean_scopus_id,
            "author_name": profile_clean["name"],
            "title": p.get("Title"),
            "authors": p.get("Authors"),
            "source": p.get("Source"),
            "year": clean_to_int(p.get("Year")),
            "citations": clean_to_int(p.get("Citations")),
            "url": p.get("URL")
        }

        def handle_scopus_paper():
            existing = supabase.table("scopus_papers").select("id")\
                .eq("title", paper_clean["title"])\
                .eq("author_name", paper_clean["author_name"]).execute()
            
            if existing.data:
                supabase.table("scopus_papers").update(paper_clean).eq("id", existing.data[0]["id"]).execute()
            else:
                supabase.table("scopus_papers").insert(paper_clean).execute()

        retry_db_call(handle_scopus_paper)
        



# ==========================================
# 3. SCHOLAR (NATIVE UPSERT)
# ==========================================
def push_scholar_payload(payload: dict):
    profile = payload["profile"]
    papers = payload["papers"]

    profile_clean = {
        "scholar_id": profile.get("Scholar_ID"),
        "name": profile.get("Name"),
        "organization": profile.get("Organization"),
        "total_citations": clean_to_int(profile.get("Citations")),
        "h_index": clean_to_int(profile.get("H-Index")),
        "i10_index": clean_to_int(profile.get("i10-Index")),
        "profile_url": profile.get("URL")
    }

    # 1. Author Upsert
    retry_db_call(lambda: supabase.table("scholar_authors").upsert(profile_clean, on_conflict="scholar_id").execute())

    # 2. Paper Upsert
    for p in papers:
        paper_clean = {
            "scholar_id": profile.get("Scholar_ID"),
            "author_name": profile.get("Name"),
            "title": p.get("Title"),
            "authors": p.get("Authors"),
            "source": p.get("Source"),
            "year": clean_to_int(p.get("Year")),
            "volume": p.get("Volume"),
            "issue": p.get("Issue"),
            "pages": p.get("Pages"),
            "publisher": p.get("Publisher"),
            "description": p.get("Description"),
            "citations": clean_to_int(p.get("Citations")),
            "url": p.get("URL")
        }

        retry_db_call(lambda: supabase.table("scholar_papers").upsert(paper_clean, on_conflict="scholar_id, title").execute())
        
 

# ==========================================
# 4. WEB OF SCIENCE (HYBRID UPSERT)
# ==========================================
def push_wos_payload(payload: dict):
    # 🟢 STANDARDIZED KEYS
    profile = payload["profile"]
    papers = payload["papers"]

    clean_wos_id = profile.get("WoS_ID")
    if not clean_wos_id or clean_wos_id.strip() == "":
        clean_wos_id = None

    profile_clean = {
        "name": profile.get("Name"),
        "published_name": profile.get("Published Name"),
        "organization": profile.get("Organization"),
        "wos_id": clean_wos_id,
        "orcid": profile.get("ORCID"),
        "subject_categories": profile.get("Subject Categories"),
        "total_documents": clean_to_int(profile.get("Total Documents")),
        "h_index": clean_to_int(profile.get("H-Index")),
        "sum_of_times_cited": clean_to_int(profile.get("Sum of Times Cited")),
        "citing_articles": clean_to_int(profile.get("Citing Articles")),
        "verified_peer_reviews": clean_to_int(profile.get("Verified Peer Reviews")),
        "verified_editor_records": clean_to_int(profile.get("Verified Editor Records")),
        "profile_url": profile.get("Profile URL")
    }

    # 1. Smart Author Upsert
    def handle_wos_author():
        if clean_wos_id:
            supabase.table("wos_authors").upsert(profile_clean, on_conflict="wos_id").execute()
        else:
            supabase.table("wos_authors").insert(profile_clean).execute()

    retry_db_call(handle_wos_author)

    # 2. Smart Paper Upsert
    for p in papers:
        paper_clean = {
            "wos_id": clean_wos_id,
            "author_name": profile_clean["name"],
            "category": p.get("Category"),
            "document_type": p.get("Document Type"),
            "title": p.get("Title"),
            "authors": p.get("Authors"),
            "source": p.get("Source"),
            "year": clean_to_int(p.get("Date/Year")),
            "abstract": p.get("Abstract"),
            "citations": clean_to_int(p.get("Citations")),
            "reference_count": clean_to_int(p.get("References")),
            "url": p.get("URL")
        }

        def handle_wos_paper():
            existing = supabase.table("wos_papers").select("id")\
                .eq("title", paper_clean["title"])\
                .eq("author_name", paper_clean["author_name"]).execute()
                
            if existing.data:
                supabase.table("wos_papers").update(paper_clean).eq("id", existing.data[0]["id"]).execute()
            else:
                supabase.table("wos_papers").insert(paper_clean).execute()
        
        retry_db_call(handle_wos_paper)
        
