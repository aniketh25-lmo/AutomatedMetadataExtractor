import os
import re
import sys
import time
import socket
import random
import shutil
import subprocess
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from portable_scraper.core.logger import setup_logger
logger = setup_logger("FacultyScraper") #

# ==========================================
# 1. GLOBAL CONFIGURATION
# ==========================================
TIMEOUTS = {
    "LOGIN_WAIT": 30,          
    "SEARCH_RESULTS_WAIT": 10, 
    "PROFILE_LOAD_WAIT": 10,   
    "TAB_SWITCH_WAIT": 5,      
    "HUMAN_DELAY_MIN": 2.0,    
    "HUMAN_DELAY_MAX": 4.5     
}

# ==========================================
# 2. HELPER FUNCTIONS & SHIELDS
# ==========================================
def to_int(value):
    if value is None: return None
    s = str(value)
    s = re.sub(r"[^\d]", "", s)
    if s == "": return None
    return int(s)

def human_delay():
    time.sleep(random.uniform(TIMEOUTS["HUMAN_DELAY_MIN"], TIMEOUTS["HUMAN_DELAY_MAX"]))

def sound_alarm():
    try:
        import winsound
        winsound.Beep(1000, 500) 
    except ImportError:
        print("\a", end="") 
        sys.stdout.flush()

def check_for_captcha(driver):
    try:
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        if any(msg in page_text for msg in ["activity looks suspicious", "verify you are human", "unusual traffic"]):
            print("\n🚨 BROWSER FLAGGED! SECURITY DETECTED 🚨")
            sound_alarm()
            print("   👉 ACTION REQUIRED: Please solve the CAPTCHA in the Chrome window.")
            print("   ⏳ The scraper is paused and will automatically resume once cleared...")
            
            while True:
                time.sleep(3)
                current_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                if not any(msg in current_text for msg in ["suspicious", "human", "traffic"]):
                    print("   ✅ CAPTCHA cleared! Resuming pipeline...")
                    time.sleep(3)
                    break
    except Exception:
        pass 

def safe_click(wait, by, value):
    elem = wait.until(EC.element_to_be_clickable((by, value)))
    elem.click()
    return elem

def save_to_excel_with_retry(df, filepath):
    """ RESTORED: Logic from standalone. Replaced input() with logging to prevent GUI deadlock. """
    try:
        df.to_excel(filepath, index=False)
    except PermissionError:
        print(f"\n❌ PERMISSION ERROR: Cannot overwrite '{os.path.basename(filepath)}'.")
        print("   👉 ACTION REQUIRED: Close the file in Excel before the next sync.")
    except Exception as e:
        print(f"\n❌ Unexpected error while saving {os.path.basename(filepath)}: {e}")
        logger.error(f"FATAL ERROR in Scopus Engine: {str(e)}", exc_info=True)

# ==========================================
# 4. CROSS-PLATFORM SYSTEM LOGIC
# ==========================================
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def get_dynamic_chrome_path():
    if sys.platform == "win32":
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for p in paths:
            if os.path.exists(p): return p
    elif sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else:
        return shutil.which("google-chrome") or shutil.which("chrome")
    return None

def get_active_profile_path():
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, "Portable_Scraper_Scopus_Profile")

def launch_chrome():
    chrome_path = get_dynamic_chrome_path()
    if not chrome_path:
        print("❌ CRITICAL: Could not locate Google Chrome.")
        return None, None
        
    profile_path = get_active_profile_path()
    os.makedirs(profile_path, exist_ok=True)
    
    port = get_free_port()
    command = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_path}",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized"
    ]
    
    try:
        chrome_process = subprocess.Popen(command)
        return port, chrome_process
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        logger.error(f"❌ Failed to launch Chrome: {str(e)}", exc_info=True)
        return None, None

# ==========================================
# 5. MAIN SCRAPER EXECUTION
# ==========================================
def run_scopus_scraper(first_name: str, last_name: str, output_dir: str):
    print("\n=================================================================")
    print("🚀 INITIALIZING AUTOMATED SCOPUS EXTRACTION PROTOCOL")
    print("=================================================================")
    
    debug_port, chrome_process = launch_chrome()
    if not debug_port:
        return None, None

    driver = None
    scrape_successful = False

    try:
        time.sleep(3)
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)

        # ---------------------------------------------------------
        # PHASE 1: STEALTH LAUNCH & AUTHENTICATION
        # ---------------------------------------------------------
        print(f"\n🌐 PHASE 1: Opening Scopus.")
        print("   👉 Please log in using your institutional credentials.")
        print(f"   ⏳ You have {TIMEOUTS['LOGIN_WAIT']} seconds before the sequence begins...")
        driver.get("https://www.scopus.com")
        time.sleep(TIMEOUTS["LOGIN_WAIT"])

        check_for_captcha(driver)

        # ---------------------------------------------------------
        # PHASE 2: AUTOMATED SEARCH & NAVIGATION
        # ---------------------------------------------------------
        print("\n🔍 PHASE 2: Navigating to Author Search...")
        driver.get("https://www.scopus.com/freelookup/form/author.uri")
        time.sleep(5)
        
        try:
            driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
        except:
            pass

        print(f"⌨️  Injecting Queries: [First: {first_name}] | [Last: {last_name}]")
        last_box = wait.until(EC.presence_of_element_located((By.ID, "lastname")))
        first_box = wait.until(EC.presence_of_element_located((By.ID, "firstname")))
        
        last_box.clear()
        first_box.clear()
        last_box.send_keys(last_name)
        first_box.send_keys(first_name)
        
        safe_click(wait, By.ID, "authorSubmitBtn")
        time.sleep(TIMEOUTS["SEARCH_RESULTS_WAIT"])

        check_for_captcha(driver)

        print("\n🖱️ Selecting target Author Profile...")
        try:
            # 🟢 GENERALIZED FUZZY MATCH: 
            # We translate the entire link text to lowercase and check for BOTH 
            # the first and last name components anywhere in that string.
            low_text = "translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
            f_low = first_name.lower().strip()
            l_low = last_name.lower().strip()
            
            # This XPath translates to: "Find a link that contains both name parts"
            author_xpath = f"//a[contains({low_text}, '{l_low}') and contains({low_text}, '{f_low}')]"
            
            try:
                # 1. Primary: Intelligent Name Match (Handles "Last, First" or "First Last")
                elem = wait.until(EC.element_to_be_clickable((By.XPATH, author_xpath)))
                elem.click()
            except:
                # 2. Fallback: If names are abbreviated (e.g., "Vadlana, B."), 
                # we grab the first author result based on Scopus's internal test ID.
                print("   ℹ️ Fuzzy match failed. Falling back to primary result selector...")
                elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-testid='author-link'], a[href*='authorId=']")))
                elem.click()
                
        except Exception as e:
            print(f"❌ ERROR: Automation failed to click the profile: {e}")
            logger.error(f"ERROR: Automation failed to click the profile:  {str(e)}", exc_info=True)
            return None, None
            
        time.sleep(TIMEOUTS["PROFILE_LOAD_WAIT"])
        check_for_captcha(driver)

        # ---------------------------------------------------------
        # PHASE 3: STAGE 1 EXTRACTION (The Initial Profile)
        # ---------------------------------------------------------
        print("\n👤 PHASE 3: Extracting Initial Profile Metadata...")
        profile = {
            "Name": "", "Scopus_ID": "", "ORCID": "", "Organization": "",
            "Documents": "0", "Citations": "0", "H-Index": "0", "Profile URL": driver.current_url
        }

        try:
            name_elem = driver.find_element(By.CSS_SELECTOR, "strong[data-testid='author-profile-name']")
            profile["Name"] = name_elem.text.strip()
        except:
            profile["Name"] = f"{last_name}, {first_name}"
            
        match = re.search(r'authorId=(\d+)', driver.current_url)
        if match: profile["Scopus_ID"] = match.group(1)

        try:
            orcid_elem = driver.find_element(By.XPATH, "//span[contains(text(),'0000-')]")
            profile["ORCID"] = orcid_elem.text.strip()
        except:
            pass

        try:
            org_elem = driver.find_elements(By.CSS_SELECTOR, "ul.affiliation-list, span.author-affiliation")
            if org_elem:
                profile["Organization"] = org_elem[0].text.strip().replace("\n", ", ")
        except:
            pass

        print("   📊 Extracting Metrics from Initial View...")
        try:
            raw_text = driver.find_element(By.TAG_NAME, "body").text.lower()
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            
            for i, line in enumerate(lines):
                if line == "documents":
                    if i > 0 and lines[i-1].isdigit(): profile["Documents"] = lines[i-1]
                    elif i + 1 < len(lines) and lines[i+1].isdigit(): profile["Documents"] = lines[i+1]
                elif "citations by" in line or line == "citations":
                    if i > 0 and lines[i-1].isdigit(): profile["Citations"] = lines[i-1]
                    elif i + 1 < len(lines) and lines[i+1].isdigit(): profile["Citations"] = lines[i+1]
                elif "h-index" in line:
                    if i > 0 and lines[i-1].isdigit(): profile["H-Index"] = lines[i-1]
                    elif i + 1 < len(lines) and lines[i+1].isdigit(): profile["H-Index"] = lines[i+1]
        except Exception as e:
            print(f"   ⚠️ Warning parsing metrics: {e}")

        print(f"   ✅ Initial Profile mapped for: {profile['Name']}")

        # ---------------------------------------------------------
        # PHASE 4: STAGE 2 EXTRACTION (The Metrics Unlock)
        # ---------------------------------------------------------
        # RESTORED: This entire logical block was previously missing
        print("\n🔓 PHASE 4: Clicking 'Edit profile' (Optional verification step)...")
        try:
            safe_click(wait, By.XPATH, "//span[contains(text(),'Edit profile')]")
            print("   🚨 ACTION REQUIRED: An 'Edit Profile' wizard/popup has appeared.")
            print("   👉 Please MANUALLY CLOSE or handle this popup now.")
            print("   ⏳ You have 10 seconds before the scraper resumes...")
            time.sleep(10)
        except:
            print("   ℹ️ 'Edit profile' button not found. Scraping current view.")

        try:
            driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
            time.sleep(1)
        except:
            pass

        check_for_captcha(driver)

        # ---------------------------------------------------------
        # PHASE 5: STAGE 3 EXTRACTION (The Documents Pagination)
        # ---------------------------------------------------------
        print("\n📄 PHASE 5: Activating 'Documents' tab...")
        try:
            doc_tab = driver.find_elements(By.XPATH, "//a[contains(., 'Documents') or contains(., 'documents')] | //span[contains(., 'Documents') or contains(., 'documents')]")
            if doc_tab:
                driver.execute_script("arguments[0].click();", doc_tab[0])
                time.sleep(TIMEOUTS["TAB_SWITCH_WAIT"])
        except:
            print("   ℹ️ Could not explicitly click Documents tab. Attempting scrape anyway.")

        print("⚙️ Beginning autonomous pagination loop...")
        papers = []
        seen_titles = set()
        page_num = 1
        
        while True:
            check_for_captcha(driver) 
            print(f"   📄 Scraping Page {page_num}...")
            time.sleep(4) 
            
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            
            for row in rows:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) < 4:
                        continue 

                    title_text = cols[0].text.replace("Remove from profile", "").strip()
                    title = title_text.split("\n")[0].strip()
                    
                    url = ""
                    link_elem = cols[0].find_elements(By.TAG_NAME, "a")
                    if link_elem:
                        url = link_elem[0].get_attribute("href")

                    paper = {
                        "Title": title, "Authors": cols[1].text.strip(), 
                        "Year": cols[3].text.strip(), "Source": cols[2].text.strip(), 
                        "Citations": cols[4].text.strip() if len(cols) > 4 else "0", 
                        "URL": url
                    }
                    
                    if paper["Title"] and paper["Title"] not in seen_titles:
                        seen_titles.add(paper["Title"])
                        papers.append(paper)
                except:
                    continue

            try:
                # RESTORED: Full ActionChains logic from standalone.py
                next_btn_selectors = ["button[aria-label='Next page']", "button[data-testid='pagination-next']"]
                clicked_next = False
                for selector in next_btn_selectors:
                    btn = driver.find_elements(By.CSS_SELECTOR, selector)
                    if btn and btn[0].is_enabled() and btn[0].get_attribute("disabled") is None:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn[0])
                        human_delay() 
                        ActionChains(driver).move_to_element(btn[0]).click().perform()
                        time.sleep(TIMEOUTS["TAB_SWITCH_WAIT"])
                        page_num += 1
                        clicked_next = True
                        break
                if not clicked_next: break 
            except:
                break 

        print(f"\n   ✅ Done! Captured {len(papers)} TOTAL unique Scopus publications.")

        # ---------------------------------------------------------
        # PHASE 6: CONSOLIDATION & PAYLOAD PACKAGING
        # ---------------------------------------------------------
        print("\n💾 PHASE 6: Saving Data...")
        if papers:
            os.makedirs(output_dir, exist_ok=True)
            # Use a standardized clean name for the file
            clean_name = "".join(x for x in profile['Name'] if x.isalnum() or x in " _-")
            
            profile_path = os.path.join(output_dir, f"Scopus_{clean_name}_Profile.xlsx")
            papers_path = os.path.join(output_dir, f"Scopus_{clean_name}_Publications.xlsx")
            
            # 🟢 THE FIX: Save the Profile Excel explicitly
            save_to_excel_with_retry(pd.DataFrame([profile]), profile_path)
            save_to_excel_with_retry(pd.DataFrame(papers), papers_path)
            
            print(f"   📊 Saved Profile to: {profile_path}")
            print(f"   📊 Saved Publications to: {papers_path}")
            
            payload = {"profile": profile, "papers": papers}
            scrape_successful = True 
            return papers_path, payload

    except Exception as general_error:
        print(f"\n❌ A fatal error interrupted the scraper: {general_error}")
        logger.error(f"\n❌ A fatal error interrupted the scraper: {str(general_error)}", exc_info=True)
        return None, None

    finally:
        print("\n🧹 Initiating system cleanup...")
        if driver:
            try: driver.quit() 
            except: pass 
        if chrome_process:
            try:
                chrome_process.terminate() 
                chrome_process.wait(timeout=3)
            except:
                try: chrome_process.kill() 
                except: pass
        print("   ✅ Browser successfully closed.")