from portable_scraper.core.db import push_scholar_payload, push_scopus_payload, push_wos_payload
from portable_scraper.core.master_linker import run_targeted_linker
from portable_scraper.core.master_refiner import run_targeted_refiner

def run_processing_pipeline(source: str, payload: dict):
    """
    The central conveyor belt. Takes raw scraper payload, pushes to staging tables,
    links to Golden Records, and refines the final output.
    """
    if not payload or not payload.get("papers"):
        print("❌ Pipeline Aborted: No valid payload provided.")
        return False

    print(f"\n⚙️  INITIATING MASTER PIPELINE FOR: {source.upper()}")

    try:
        # Phase 1: Push to Raw/Staging Tables
        if source == "scholar":
            push_scholar_payload(payload)
        elif source == "scopus":
            push_scopus_payload(payload)
        elif source == "wos":
            push_wos_payload(payload)
        else:
            raise ValueError(f"Unknown source: {source}")

        # Phase 2: Entity Resolution & Master Table Creation
        master_uuid = run_targeted_linker(payload, source)

        # Phase 3: Intelligent Refinement
        run_targeted_refiner(master_uuid)
        
        print("\n🎉 MASTER PIPELINE FINISHED SUCCESSFULLY.")
        return True

    except Exception as e:
        print(f"\n❌ FATAL PIPELINE ERROR: {e}")
        return False