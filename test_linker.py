import pandas as pd
import math
from portable_scraper.core.master_linker import run_targeted_linker
from portable_scraper.core.master_refiner import run_targeted_refiner

def clean_dict(d):
    """Sanitize pandas dict to remove NaNs and keep clean strings/ints"""
    clean_d = {}
    for k, v in d.items():
        if pd.isna(v):
            clean_d[k] = ""
        else:
            clean_d[k] = v
    return clean_d

def test_pipeline(profile_path, papers_path, source):
    print(f"\n=============================================")
    print(f"🛠️  OFFLINE INJECTION TEST: {source.upper()}")
    print(f"=============================================")
    
    try:
        # Reconstruct exactly what the live scraper arrays look like
        profile_df = pd.read_excel(profile_path)
        papers_df = pd.read_excel(papers_path)
        
        profile_dict = clean_dict(profile_df.iloc[0].to_dict()) if not profile_df.empty else {}
        papers_list = [clean_dict(p) for p in papers_df.to_dict('records')]
        
        payload = {
            "profile": profile_dict,
            "papers": papers_list
        }
        
        # Manually pump the offline payload through our new upgraded rules
        master_uuid = run_targeted_linker(payload, source)
        run_targeted_refiner(master_uuid)
        
    except FileNotFoundError:
        print(f"⚠️ Could not find the Excel outputs for {source.upper()}. Verify the path exists.")

if __name__ == "__main__":
    # 1. Run Scholar (Should resolve to the active Scholar Golden Record or match the fuzzy name)
    test_pipeline(
        "outputs/Scholar_Kanakala_S_Profile.xlsx",
        "outputs/Scholar_Kanakala_S_Exhaustive.xlsx",
        "scholar"
    )
    
    # 2. Run Scopus (Should confidently match the Scholar Golden Record via >85 Fuzzy Match)
    test_pipeline(
        "outputs/Scopus_Kanakala Srinivas_Profile.xlsx",
        "outputs/Scopus_Kanakala Srinivas_Publications.xlsx",
        "scopus"
    )
    
    # 3. Run WoS (Should confidently match the exact same unified record)
    test_pipeline(
        "outputs/WoS_SRINIVAS KANAKALA_Profile.xlsx",
        "outputs/WoS_SRINIVAS KANAKALA_Publications.xlsx",
        "wos"
    )

    print("\n✅ Offline Data Pipeline Test Complete!")
