from portable_scraper.core.supabase_client import supabase
from portable_scraper.core.deduplicator import normalize_title


#-----------Numerical type caster ----------
import re

import re

def to_int(value):
    if value is None:
        return None

    s = str(value)
    s = re.sub(r"[^\d]", "", s)  # keep digits only

    if s == "":
        return None

    return int(s)



#----------- PUBLICATION MASTER UPSERT ----------
def upsert_publication(paper: dict, source: str, faculty_name: str):
    title = paper.get("title")
    year = to_int(paper.get("year"))   # ✅ FIXED

    title_norm = normalize_title(title)

    # search existing
    query = (
        supabase.table("publications_master")
        .select("*")
        .eq("title_norm", title_norm)
        .eq("faculty_name", faculty_name)
    )

    if year is not None:
        query = query.eq("year", year)

    res = query.limit(1).execute()


    if res.data:
        row = res.data[0]
        update_fields = {}

        if source == "scopus":
            update_fields["source_scopus"] = True
            update_fields["citations_scopus"] = to_int(paper.get("citations"))

        if source == "scholar":
            update_fields["source_scholar"] = True
            update_fields["citations_scholar"] = to_int(paper.get("citations"))

        if source == "wos":
            update_fields["source_wos"] = True
            update_fields["citations_wos"] = to_int(paper.get("citations"))

        supabase.table("publications_master") \
            .update(update_fields) \
            .eq("id", row["id"]) \
            .execute()

    else:
        insert_data = {
            "faculty_name": faculty_name,
            "title": title,
            "title_norm": title_norm,
            "authors": paper.get("authors"),
            "venue": paper.get("venue") or paper.get("source"),
            "year": year,   # ✅ CLEAN INT
        }

        if source == "scopus":
            insert_data["source_scopus"] = True
            insert_data["citations_scopus"] = to_int(paper.get("citations"))

        if source == "scholar":
            insert_data["source_scholar"] = True
            insert_data["citations_scholar"] = to_int(paper.get("citations"))

        if source == "wos":
            insert_data["source_wos"] = True
            insert_data["citations_wos"] = to_int(paper.get("citations"))

        supabase.table("publications_master").insert(insert_data).execute()
