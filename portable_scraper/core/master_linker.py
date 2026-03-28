import re
from rapidfuzz import fuzz
from portable_scraper.core.supabase_client import supabase
from portable_scraper.core.db import clean_to_int

def resolve_master_author(profile_data, source):
    """Identifies or creates the Master Author via Waterfall check."""
    existing_id = None
    
    # Map the incoming source ID to the correct database column
    id_mapping = {
        "scholar": ("scholar_id", profile_data.get("Scholar_ID")),
        "scopus": ("scopus_id", profile_data.get("Scopus_ID")),
        "wos": ("wos_id", profile_data.get("WoS_ID"))
    }
    
    check_field, check_val = id_mapping.get(source, (None, None))
    
    if check_val:
        res = supabase.table("master_authors").select("id").eq(check_field, check_val).execute()
        if res.data:
            existing_id = res.data[0]['id']

    # Fallback to ORCID if exists
    if not existing_id and profile_data.get("ORCID"):
        res = supabase.table("master_authors").select("id").eq("orcid", profile_data["ORCID"]).execute()
        if res.data:
            existing_id = res.data[0]['id']

    m_auth = {
        "canonical_name": profile_data.get("Name") or profile_data.get("name"),
        "department": "CSE", 
        "preferred_organization": profile_data.get("Organization") or profile_data.get("affiliation") or "VNR VJIET",
    }
    
    # Map the specific ID and metrics based on the source we just scraped
# 🟢 Using the universal helper for consistent data
    if source == "scholar":
        m_auth["scholar_id"] = profile_data.get("Scholar_ID")
        m_auth["scholar_citations"] = clean_to_int(profile_data.get("Citations"))
    elif source == "scopus":
        m_auth["scopus_id"] = profile_data.get("Scopus_ID")
        m_auth["scopus_citations"] = clean_to_int(profile_data.get("Citations"))
    elif source == "wos":
        m_auth["wos_id"] = profile_data.get("WoS_ID")
        m_auth["wos_citations"] = clean_to_int(profile_data.get("Sum of Times Cited"))
        
    if existing_id:
        print(f"   ♻️  Match Found via {source}. Updating Master UUID: {existing_id}")
        m_auth["id"] = existing_id 
        supabase.table("master_authors").upsert(m_auth).execute()
        return existing_id
    else:
        print(f"   🆕 No match found. Creating a fresh Golden Record for {m_auth['canonical_name']}.")
        res = supabase.table("master_authors").insert(m_auth).execute()
        return res.data[0]['id']

def run_targeted_linker(payload: dict, source: str):
    print("\n" + "="*60)
    print(f"🧠 STARTING IDENTITY RESOLUTION ({source.upper()})")
    print("="*60)

    profile = payload["profile"]
    papers = payload["papers"]

    # 1. Resolve the Master Author
    master_uuid = resolve_master_author(profile, source)

    # 2. Fetch EXISTING Master Papers for Deduplication
    existing_master = supabase.table("master_publications").select("*").eq("master_author_id", master_uuid).execute().data
    
    new_master_papers = []
    updated_count = 0

    print(f"   🔎 Cross-referencing {len(papers)} incoming papers against {len(existing_master)} existing master records...")

    # 3. Deduplicate and Merge
    for p in papers:
        title = p.get("Title", p.get("title", "")).strip()
        if not title: continue
        
        doi = p.get("DOI", p.get("doi"))
        citations = int(re.sub(r"[^\d]", "", str(p.get("Citations", 0))) or 0)
        year = int(re.sub(r"[^\d]", "", str(p.get("Year", p.get("Date/Year", 0)))) or 0)
        

        # Match by DOI or High Title Similarity (Safeguarded against NULL titles)
        match = next((mp for mp in existing_master if (doi and mp.get("doi") == doi) or (fuzz.ratio(title.lower(), str(mp.get("title") or "").lower()) > 88)), None)
        
        if match:
            # Update existing golden record with new source flags

            updates = {
                f"in_{source}": True, 
                f"{source}_citations": citations
            }
            if not match.get("doi") and doi: updates["doi"] = doi
            if not match.get("abstract") and p.get("Abstract"): updates["abstract"] = p.get("Abstract")
            
            supabase.table("master_publications").update(updates).eq("id", match["id"]).execute()
            updated_count += 1
        else:
            # Stage a brand new golden record
            new_paper = {
                "master_author_id": master_uuid, 
                "title": title, 
                "doi": doi,
                "publication_year": year, 
                "source_name": p.get("Source", p.get("source")),
                "authors_list": p.get("Authors", p.get("authors")), 
                "abstract": p.get("Abstract", p.get("description")),
                f"in_{source}": True, 
                f"{source}_citations": citations,
                "academic_year": "2024-2025", 
                "department": "CSE"
            }
            if source == "scholar":
                new_paper["volume_issue_pages"] = f"Vol: {p.get('Volume', '')}, Iss: {p.get('Issue', '')}, Pgs: {p.get('Pages', '')}"
            
            new_master_papers.append(new_paper)
            existing_master.append(new_paper) # Add to local memory so we don't duplicate within the same payload

    # 4. Insert entirely new records
    if new_master_papers: 
        supabase.table("master_publications").insert(new_master_papers).execute()
    
    print(f"   ✅ LINK COMPLETE: {len(new_master_papers)} new master papers created, {updated_count} existing updated.")
    return master_uuid