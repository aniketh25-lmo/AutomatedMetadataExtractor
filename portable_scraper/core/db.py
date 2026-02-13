from supabase import create_client
from portable_scraper.core.config import load_config

config = load_config()

supabase = create_client(
    config["supabase_url"],
    config["supabase_key"]  # service_role
)


#-----------type caster ----------
def to_int(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except:
        return None


# ---------- SCOPUS ----------
def insert_scopus_payload(payload: dict):
    profile = payload["profile"]
    papers = payload["papers"]

    profile_clean = {
        "name": profile.get("name"),
        "orcid": profile.get("orcid"),
        "affiliation": profile.get("affiliation"),
        "documents": to_int(profile.get("documents")),
        "citations": to_int(profile.get("citations")),
        "h_index": to_int(profile.get("h_index")),
    }

    supabase.table("scopus_authors").insert(profile_clean).execute()

    for p in papers:
        paper_clean = {
            "author_name": profile_clean["name"],
            "title": p.get("title"),
            "authors": p.get("authors"),
            "source": p.get("source"),
            "year": to_int(p.get("year")),
        }

        supabase.table("scopus_papers").insert(paper_clean).execute()



# ---------- SCHOLAR ----------
def insert_scholar_payload(payload: dict):
    profile = payload["profile"]
    papers = payload["papers"]

    profile_clean = {
        "name": profile.get("name"),
        "affiliation": profile.get("affiliation"),
        "email": profile.get("email"),
        "interests": profile.get("interests"),
        "citations_all": to_int(profile.get("citations_all")),
        "citations_recent": to_int(profile.get("citations_recent")),
        "hindex_all": to_int(profile.get("hindex_all")),
        "hindex_recent": to_int(profile.get("hindex_recent")),
        "i10_all": to_int(profile.get("i10_all")),
        "i10_recent": to_int(profile.get("i10_recent")),
    }

    supabase.table("scholar_authors").insert(profile_clean).execute()

    for p in papers:
        paper_clean = {
            "author_name": profile_clean["name"],
            "title": p.get("title"),
            "authors": p.get("authors"),
            "venue": p.get("venue"),
            "citations": to_int(p.get("citations")),
            "year": to_int(p.get("year")),
            "scholar_url": p.get("scholar_url"),
        }

        supabase.table("scholar_papers").insert(paper_clean).execute()

