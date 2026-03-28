from portable_scraper.core.supabase_client import supabase

def intelligent_classify(source, title):
    s = str(source).upper() if source else ""
    t = str(title).upper() if title else ""
    
    if any(k in s or k in t for k in ["CONF", "PROC", "SYMP", "WORKSHOP", "INTL"]): return "Conference"
    if any(k in s or k in t for k in ["BOOK", "SPRINGER", "CHAPTER", "MONOGRAPH"]): return "Book/Chapter"
    return "Journal"

def run_targeted_refiner(master_uuid: str):
    print("\n" + "="*60)
    print("🧹 EXECUTING INTELLIGENT REFINEMENT")
    print("="*60)

    # 1. Author Metric Sync (Calculates aggregate H-Indexes safely)
    auth = supabase.table("master_authors").select("*").eq("id", master_uuid).execute().data[0]
    
    m_updates = {}
    if auth.get("wos_id"):
        wos_data = supabase.table("wos_authors").select("sum_of_times_cited, h_index").eq("wos_id", auth["wos_id"]).execute().data
        if wos_data: m_updates.update({"wos_citations": wos_data[0].get("sum_of_times_cited", 0), "wos_h_index": wos_data[0].get("h_index", 0)})
        
    if auth.get("scopus_id"):
        sc_data = supabase.table("scopus_authors").select("h_index").eq("scopus_id", auth["scopus_id"]).execute().data
        if sc_data: m_updates["scopus_h_index"] = sc_data[0].get("h_index", 0)
        
    if auth.get("scholar_id"):
        gs_data = supabase.table("scholar_authors").select("h_index").eq("scholar_id", auth["scholar_id"]).execute().data
        if gs_data: m_updates["scholar_h_index"] = gs_data[0].get("h_index", 0)

    if m_updates:
        supabase.table("master_authors").update(m_updates).eq("id", master_uuid).execute()
        print("   ✅ Golden Author metrics synchronized.")

    # 2. Publication Classification Fix (Targeted)
    papers = supabase.table("master_publications").select("id, source_name, title, publication_year").eq("master_author_id", master_uuid).execute().data
    
    print(f"   📄 Classifying {len(papers)} Golden Papers...")
    for p in papers:
        cat = intelligent_classify(p.get("source_name"), p.get("title"))
        updates = {
            "source_name": p.get("source_name").upper() if p.get("source_name") else "NOT PROVIDED BY SOURCE",
            "academic_year": f"{p['publication_year']}-{p['publication_year']+1}" if p.get('publication_year') else "N/A"
        }
        supabase.table("master_publications").update(updates).eq("id", p["id"]).execute()

    print("   ✅ REFINEMENT COMPLETE.")