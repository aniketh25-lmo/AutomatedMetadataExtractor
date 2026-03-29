import os
import re
import sys
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from portable_scraper.core.logger import setup_logger
logger = setup_logger("FacultyScraper") #

# ==========================================
# 1. CONFIGURATION & TIMEOUTS
# ==========================================
TIMEOUTS = {
    "INITIAL_SEARCH_WAIT": 30,
    "TAB_LOAD_WAIT": 3,
    "EXPANSION_WAIT": 2.5
}

# ==========================================
# 2. UTILITY SHIELDS
# ==========================================
def to_int(value):
    if value is None: return 0
    s = re.sub(r"[^\d]", "", str(value))
    return int(s) if s else 0

def sound_alarm():
    """Triggers a cross-platform alert sound."""
    try:
        if sys.platform == "win32":
            import winsound
            winsound.Beep(1000, 500)
        else:
            sys.stdout.write('\a')
            sys.stdout.flush()
    except:
        pass

def check_for_captcha(driver):
    """Monitors for Google's security triggers."""
    try:
        body_text = driver.page_source.lower()
        if any(msg in body_text for msg in ["not a robot", "suspicious activity", "unusual traffic"]):
            print("\n🚨 GOOGLE SECURITY TRIGGERED! 🚨")
            sound_alarm()
            print("   👉 ACTION REQUIRED: Solve the captcha in the browser window.")
            while True:
                time.sleep(3)
                if not any(msg in driver.page_source.lower() for msg in ["not a robot", "suspicious activity"]):
                    print("   ✅ Captcha cleared. Resuming pipeline...")
                    time.sleep(2)
                    break
    except:
        pass

# ==========================================
# 3. MAIN SCRAPER ENGINE
# ==========================================
def run_scholar_scraper(first_name, last_name, affiliation="", output_dir=""):
    print("\n" + "="*65)
    print("🚀 FINALIZED GOOGLE SCHOLAR DEEP EXTRACTOR")
    print("="*65)
    
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    # Path handling
    if not output_dir:
        output_dir = os.getcwd()

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        # --- PHASE 1: ENTRY ---
        search_query = f"{first_name} {last_name} Google Scholar {affiliation}".strip()
        driver.get(f"https://www.google.com/search?q={search_query.replace(' ', '+')}")
        print(f"🌐 PHASE 1: Direct Entry. Waiting {TIMEOUTS['INITIAL_SEARCH_WAIT']}s...")
        time.sleep(TIMEOUTS["INITIAL_SEARCH_WAIT"])
        
        try:
            profile_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "h3")))
            profile_link.click()
        except Exception:
            print("❌ Profile not found.")
            return None, None

        main_window = driver.current_window_handle
        check_for_captcha(driver)

        # --- PHASE 2: EXPANSION ---
        print("⏬ PHASE 2: Expanding publications...")
        prev_count = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            rows = driver.find_elements(By.CLASS_NAME, "gsc_a_tr")
            curr_count = len(rows)
            try:
                more_btn = driver.find_element(By.ID, "gsc_bpf_more")
                if more_btn.is_enabled() and more_btn.get_attribute("disabled") is None and curr_count > prev_count:
                    prev_count = curr_count
                    driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(TIMEOUTS["EXPANSION_WAIT"])
                else: 
                    break
            except Exception: 
                break
        print(f"   ✅ Total {len(rows)} papers visible.")

        # --- PHASE 3: HEADER ---
        profile = {
            "Name": driver.find_element(By.ID, "gsc_prf_in").text,
            "Organization": driver.find_element(By.CLASS_NAME, "gsc_prf_il").text,
            "Scholar_ID": re.search(r'user=([^&]+)', driver.current_url).group(1),
            "URL": driver.current_url
        }
        stats = driver.find_elements(By.CSS_SELECTOR, "td.gsc_rsb_std")
        profile.update({
            "Citations": stats[0].text if stats else "0", 
            "H-Index": stats[2].text if len(stats)>2 else "0", 
            "i10-Index": stats[4].text if len(stats)>4 else "0"
        })

        # --- PHASE 4: MULTI-TAB EXHAUSTIVE SCRAPE ---
        print(f"⚙️   PHASE 4: Executing Tabbed Extraction...")
        papers = []
        link_elements = driver.find_elements(By.CLASS_NAME, "gsc_a_at")
        all_urls = [el.get_attribute("href") for el in link_elements]
        total_count = len(all_urls)

        for i, paper_url in enumerate(all_urls):
            try:
                check_for_captcha(driver)
                print(f"   📄 [{i+1}/{total_count}] Extracting Detailed Metadata...")
                
                # Open detail page in a new tab
                driver.execute_script(f"window.open('{paper_url}', '_blank');")
                
                # Sync: Wait for the browser to register the new tab
                start_t = time.time()
                while len(driver.window_handles) <= 1 and (time.time() - start_t) < 5:
                    time.sleep(0.2)
                
                driver.switch_to.window(driver.window_handles[-1])
                
                # Extraction: Wait for the metadata table
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#gsc_oci_table, #gsc_vcd_table")))
                is_full = len(driver.find_elements(By.ID, "gsc_oci_table")) > 0
                pre = "oci" if is_full else "vcd"
                
                p_data = {
                    "Title": driver.find_element(By.ID, f"gsc_{pre}_title").text,
                    "Authors": None, "Source": None, "Year": None, "Volume": None, 
                    "Issue": None, "Pages": None, "Publisher": None, "Description": None,
                    "Citations": "0", "URL": paper_url
                }
                
                # Parse metadata fields
                fields = driver.find_elements(By.CLASS_NAME, "gs_scl")
                for field in fields:
                    try:
                        lbl = field.find_element(By.CLASS_NAME, f"gsc_{pre}_field").text.lower()
                        val = field.find_element(By.CLASS_NAME, f"gsc_{pre}_value").text
                        
                        if "authors" in lbl: p_data["Authors"] = val
                        elif "date" in lbl: p_data["Year"] = val.split('/')[0]
                        elif any(k in lbl for k in ["journal", "source", "conference"]): p_data["Source"] = val
                        elif "volume" in lbl: p_data["Volume"] = val
                        elif "issue" in lbl: p_data["Issue"] = val
                        elif "pages" in lbl: p_data["Pages"] = val
                        elif "publisher" in lbl: p_data["Publisher"] = val
                        elif "description" in lbl: p_data["Description"] = val
                        elif "total citations" in lbl: p_data["Citations"] = val.split('\n')[0].replace("Cited by ", "")
                    except:
                        continue

                papers.append(p_data)
                
                # Cleanup detail tab
                driver.close()
                driver.switch_to.window(main_window)
                
            except Exception as e:
                print(f"   ⚠️ Skip Paper {i+1}: {str(e)}")
                if len(driver.window_handles) > 1:
                    driver.close()
                driver.switch_to.window(main_window)
                continue

        print(f"   ✅ Extraction Complete. Processed {len(papers)} papers.")

        # 🟢 PHASE 5: Generating Dual Excels & Preparing Payload
        print("💾 PHASE 5: Generating Excel Backups...")
        if papers:
            os.makedirs(output_dir, exist_ok=True)
            # Standardized naming for Scholar
            clean_name = f"{last_name}_{first_name[0]}" # Matches Scholar_V_Baby style
            
            profile_path = os.path.join(output_dir, f"Scholar_{clean_name}_Profile.xlsx")
            papers_path = os.path.join(output_dir, f"Scholar_{clean_name}_Exhaustive.xlsx")
            
            # Save both for a full local audit trail
            pd.DataFrame([profile]).to_excel(profile_path, index=False)
            pd.DataFrame(papers).to_excel(papers_path, index=False)
            
            print(f"   📊 Saved Profile to: {profile_path}")
            print(f"   📊 Saved Publications to: {papers_path}")
            
            payload = {"profile": profile, "papers": papers}
            return papers_path, payload


    except Exception as outer_e:
        print(f"❌ CRITICAL SCRAPER ERROR: {outer_e}")
        logger.error(f"❌ CRITICAL SCRAPER ERROR: {str(outer_e)}", exc_info=True)
        return None, None

    finally:
        # Final cleanup ensures browser closes even on fatal crash
        try:
            driver.quit()
        except:
            pass

# ==========================================
# 4. STANDALONE TEST BLOCK
# ==========================================
if __name__ == "__main__":
    # Test execution for VNR VJIET faculty validation
    run_scholar_scraper(
        first_name="Baby", 
        last_name="Vadlana", 
        affiliation="VNR VJIET", 
        output_dir=os.getcwd()
    )