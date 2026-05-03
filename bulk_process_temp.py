import time
from portable_scraper.core.supabase_client import supabase
from portable_scraper.core.master_linker import run_targeted_linker
from portable_scraper.core.master_refiner import run_targeted_refiner

def fetch_all(table_name):
    print(f"Fetching all records from {table_name}...")
    all_data = []
    limit = 1000
    offset = 0
    while True:
        res = supabase.table(table_name).select("*").range(offset, offset + limit - 1).execute()
        if not res.data:
            break
        all_data.extend(res.data)
        if len(res.data) < limit:
            break
        offset += limit
    print(f"Fetched {len(all_data)} records from {table_name}.")
    return all_data

def process_scholar():
    print("\n--- Processing Scholar ---")
    authors = fetch_all("scholar_authors")
    papers = fetch_all("scholar_papers")
    
    papers_by_id = {}
    for p in papers:
        sid = p.get("scholar_id")
        if sid not in papers_by_id:
            papers_by_id[sid] = []
        papers_by_id[sid].append(p)
        
    for auth in authors:
        sid = auth.get("scholar_id")
        auth_papers = papers_by_id.get(sid, [])
        
        # reconstruct payload for linker
        profile = {
            "Scholar_ID": sid,
            "Name": auth.get("name"),
            "Organization": auth.get("organization"),
            "Citations": auth.get("total_citations"),
            "URL": auth.get("profile_url")
        }
        
        papers_payload = []
        for p in auth_papers:
            papers_payload.append({
                "Title": p.get("title"),
                "Authors": p.get("authors"),
                "Source": p.get("source"),
                "Year": p.get("year"),
                "Volume": p.get("volume"),
                "Issue": p.get("issue"),
                "Pages": p.get("pages"),
                "Description": p.get("description"),
                "Citations": p.get("citations"),
                "URL": p.get("url")
            })
            
        payload = {"profile": profile, "papers": papers_payload}
        print(f"Running linker for Scholar Author: {auth.get('name')}")
        master_uuid = run_targeted_linker(payload, "scholar")
        run_targeted_refiner(master_uuid)

def process_scopus():
    print("\n--- Processing Scopus ---")
    authors = fetch_all("scopus_authors")
    papers = fetch_all("scopus_papers")
    
    papers_by_id = {}
    for p in papers:
        sid = p.get("scopus_id")
        if not sid:
            sid = "NAME:" + str(p.get("author_name"))
        if sid not in papers_by_id:
            papers_by_id[sid] = []
        papers_by_id[sid].append(p)
        
    for auth in authors:
        sid = auth.get("scopus_id")
        key = sid if sid else "NAME:" + str(auth.get("name"))
        auth_papers = papers_by_id.get(key, [])
        
        profile = {
            "Scopus_ID": sid,
            "Name": auth.get("name"),
            "ORCID": auth.get("orcid"),
            "Organization": auth.get("organization"),
            "Documents": auth.get("total_documents"),
            "H-Index": auth.get("h_index"),
            "Citations": auth.get("citations")
        }
        
        papers_payload = []
        for p in auth_papers:
            papers_payload.append({
                "Title": p.get("title"),
                "Authors": p.get("authors"),
                "Source": p.get("source"),
                "Year": p.get("year"),
                "Citations": p.get("citations"),
                "URL": p.get("url")
            })
            
        payload = {"profile": profile, "papers": papers_payload}
        print(f"Running linker for Scopus Author: {auth.get('name')}")
        master_uuid = run_targeted_linker(payload, "scopus")
        run_targeted_refiner(master_uuid)

def process_wos():
    print("\n--- Processing Web of Science ---")
    authors = fetch_all("wos_authors")
    papers = fetch_all("wos_papers")
    
    papers_by_id = {}
    for p in papers:
        sid = p.get("wos_id")
        if not sid:
            sid = "NAME:" + str(p.get("author_name"))
        if sid not in papers_by_id:
            papers_by_id[sid] = []
        papers_by_id[sid].append(p)
        
    for auth in authors:
        sid = auth.get("wos_id")
        key = sid if sid else "NAME:" + str(auth.get("name"))
        auth_papers = papers_by_id.get(key, [])
        
        profile = {
            "WoS_ID": sid,
            "Name": auth.get("name"),
            "ORCID": auth.get("orcid"),
            "Organization": auth.get("organization"),
            "Sum of Times Cited": auth.get("sum_of_times_cited")
        }
        
        papers_payload = []
        for p in auth_papers:
            papers_payload.append({
                "Title": p.get("title"),
                "Authors": p.get("authors"),
                "Source": p.get("source"),
                "Date/Year": p.get("year"),
                "Abstract": p.get("abstract"),
                "Citations": p.get("citations"),
                "URL": p.get("url"),
                "Publisher_URL": p.get("publisher_url"),
                "DOI": p.get("doi"),
                "Category": p.get("category")
            })
            
        payload = {"profile": profile, "papers": papers_payload}
        print(f"Running linker for WoS Author: {auth.get('name')}")
        master_uuid = run_targeted_linker(payload, "wos")
        run_targeted_refiner(master_uuid)

if __name__ == "__main__":
    print("🚀 Starting Bulk Process of Staging Data to Master Tables...")
    try:
        process_scholar()
        process_scopus()
        process_wos()
        print("\n✅ Bulk processing complete!")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
