import re
from rapidfuzz import fuzz
from portable_scraper.core.supabase_client import supabase
from portable_scraper.core.db import clean_to_int

def clean_author_name(name):
    if not name: return ""
    name = str(name).lower().strip()
    name = re.sub(r'^(dr\.|dr\s|prof\.|prof\s|mr\.|mrs\.)', '', name)
    name = re.sub(r'[^a-z\s]', ' ', name)
    return " ".join(name.split())

def resolve_master_author(profile_data, source):
    """Identifies or creates the Master Author via Waterfall check."""
    existing_id = None
    
    # 1. Map the incoming source ID to the correct database column
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

    # 2. Fallback to ORCID if exists
    if not existing_id and profile_data.get("ORCID"):
        res = supabase.table("master_authors").select("id").eq("orcid", profile_data["ORCID"]).execute()
        if res.data:
            existing_id = res.data[0]['id']

    incoming_name = profile_data.get("Name") or profile_data.get("name")
            
    # 3. Robust Fuzzy Name Matching Fallback
    if not existing_id and incoming_name:
        clean_inc = clean_author_name(incoming_name)
        
        all_authors_res = supabase.table("master_authors").select("id, canonical_name").execute()
        all_authors = all_authors_res.data if all_authors_res else []
        
        best_match_id = None
        best_score = 0
        
        for author in all_authors:
            current_name = author.get("canonical_name", "")
            clean_curr = clean_author_name(current_name)
            
            # Use token_sort_ratio to ignore word order (e.g. Baby Vadlana == Vadlana Baby)
            score = fuzz.token_sort_ratio(clean_inc, clean_curr)
            if score > best_score and score > 85: # High confidence threshold
                best_score = score
                best_match_id = author["id"]
                
        if best_match_id:
            existing_id = best_match_id
            print(f"   ♻️ Fuzzy Name Match Found: [{incoming_name}] resolved to Master UUID [{existing_id}] with score {best_score}%")

    m_auth = {
        "canonical_name": incoming_name,
        "department": "CSE", 
        "preferred_organization": profile_data.get("Organization") or profile_data.get("affiliation") or "VNR VJIET",
    }
    
    # 4. Map the specific ID and metrics based on the source we just scraped
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
        
        clean_inc_title = re.sub(r'[^a-z0-9]', '', title.lower())
        
        match = None
        for mp in existing_master:
            # Check hard DOI matching
            if doi and mp.get("doi") and str(doi).strip().lower() == str(mp.get("doi")).strip().lower():
                match = mp
                break
            
            # Check rigorous Title string matching
            curr_title = str(mp.get("title") or "")
            clean_curr_title = re.sub(r'[^a-z0-9]', '', curr_title.lower())
            
            if clean_inc_title and clean_curr_title:
                score = fuzz.ratio(clean_inc_title, clean_curr_title)
                if score > 92: # Aggressive matching score to catch trailing periods or typos
                    match = mp
                    break
        
        if match:
            # Update existing golden record with new source flags

            updates = {
                f"in_{source}": True, 
                f"{source}_citations": citations
            }
            if not match.get("doi") and doi: updates["doi"] = doi
            if not match.get("abstract") and p.get("Abstract"): updates["abstract"] = p.get("Abstract")
            
            if source == "wos":
                if p.get("Category"): updates["wos_category"] = p.get("Category")
                if p.get("Publisher_URL"): updates["publisher_url"] = p.get("Publisher_URL")
            
            if "id" in match:
                supabase.table("master_publications").update(updates).eq("id", match["id"]).execute()
                updated_count += 1
            else:
                match.update(updates)
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
            elif source == "wos":
                new_paper["wos_category"] = p.get("Category")
                new_paper["publisher_url"] = p.get("Publisher_URL")
            
            new_master_papers.append(new_paper)
            existing_master.append(new_paper) # Add to local memory so we don't duplicate within the same payload

    # 4. Insert entirely new records
    if new_master_papers: 
        supabase.table("master_publications").insert(new_master_papers).execute()
    
    print(f"   ✅ LINK COMPLETE: {len(new_master_papers)} new master papers created, {updated_count} existing updated.")
    return master_uuid