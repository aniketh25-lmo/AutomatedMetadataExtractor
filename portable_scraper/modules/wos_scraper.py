import os
import re
import sys
import time
import socket
import random
import shutil
import subprocess
import pandas as pd
from tkinter import messagebox  # 🟢 Added for UI-safe prompts
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# ==========================================
# 1. HELPER FUNCTIONS & SHIELDS
# ==========================================
def to_int(value):
    if value is None: return None
    s = str(value)
    s = re.sub(r"[^\d]", "", s)
    if s == "": return None
    return int(s)

def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

def human_delay(min_sec=2.0, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))

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
        if "activity looks suspicious" in page_text or "verify you are human" in page_text or "just a moment" in page_text:
            print("\n🚨 BROWSER FLAGGED! CLOUDFLARE SECURITY DETECTED 🚨")
            sound_alarm()
            print("   ⏳ The scraper is paused and will automatically resume once cleared...")
            
            while True:
                time.sleep(3)
                current_text = driver.find_element(By.TAG_NAME, "body").text.lower()
                if "activity looks suspicious" not in current_text and "verify you are human" not in current_text:
                    print("   ✅ CAPTCHA cleared! Resuming pipeline in 3 seconds...")
                    time.sleep(3)
                    break
    except Exception:
        pass 

KNOWN_DOC_TYPES = [
    "Article", "Proceedings Paper", "Conference Paper", "Review", 
    "Meeting Abstract", "Editorial Material", "Letter", "Correction", "Early Access"
]

# ==========================================
# 2. CROSS-PLATFORM & PROFILE ROTATION
# ==========================================
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
    return os.path.join(home_dir, "Portable_Scraper_WoS_Profile")

def clear_profile_locks(profile_path):
    locks = ['SingletonLock', 'SingletonCookie', 'SingletonSocket']
    for lock in locks:
        lock_file = os.path.join(profile_path, lock)
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except PermissionError:
                return False 
    return True

# 🟢 STAGE A: EXPOSED LAUNCH FUNCTION
def launch_wos_browser():
    """Launches the Chrome debugging profile and returns the port/process for the UI."""
    chrome_path = get_dynamic_chrome_path()
    if not chrome_path:
        print("❌ CRITICAL: Could not locate Google Chrome on this machine.")
        return None, None
        
    profile_path = get_active_profile_path()
    os.makedirs(profile_path, exist_ok=True)
    
    if not clear_profile_locks(profile_path):
        messagebox.showerror("System Lock", "A previous scraper session is stuck in the background.\n\nPlease open Task Manager and force close all 'chrome.exe' processes.")
        return None, None
    
    port = get_free_port()
    
    command = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_path}",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    
    try:
        chrome_process = subprocess.Popen(command)
        return port, chrome_process
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        return None, None

# ==========================================
# 3. PARSERS & FILE SAVING
# ==========================================
def parse_profile_text(raw_text):
    profile = {
        "Name": "", "Published Name": "", "Organization": "",
        "WoS_ID": "", "ORCID": "", "Subject Categories": "",
        "Total Documents": "0", "H-Index": "0", "Sum of Times Cited": "0",
        "Citing Articles": "0", "Verified Peer Reviews": "0", "Verified Editor Records": "0",
        "Profile URL": ""
    }
    
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    try:
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if "web of science researcherid" in line_lower:
                profile["WoS_ID"] = line.replace("Web of Science ResearcherID", "").strip()
            elif "orcid.org/" in line_lower:
                profile["ORCID"] = line.split("orcid.org/")[-1].strip()
            elif "published name" in line_lower and i + 1 < len(lines):
                profile["Published Name"] = lines[i+1]
            elif line_lower == "organization" and i + 1 < len(lines):
                profile["Organization"] = lines[i+1]
            elif "subject categories" in line_lower and i + 1 < len(lines):
                profile["Subject Categories"] = lines[i+1]
            elif line_lower == "total documents" and i - 1 >= 0:
                profile["Total Documents"] = lines[i-1] 
            elif line_lower == "h-index" and i - 1 >= 0:
                profile["H-Index"] = lines[i-1]
            elif line_lower == "sum of times cited" and profile["Sum of Times Cited"] == "0" and i - 1 >= 0:
                profile["Sum of Times Cited"] = lines[i-1]
            elif "citing articles" in line_lower and i - 1 >= 0:
                profile["Citing Articles"] = lines[i-1]
            elif "verified peer reviews" in line_lower and i - 1 >= 0:
                profile["Verified Peer Reviews"] = lines[i-1]
            elif "verified editor records" in line_lower and i - 1 >= 0:
                profile["Verified Editor Records"] = lines[i-1]
                
        for i, line in enumerate(lines[:30]):
            if "correction" in line.lower() and i + 1 < len(lines):
                profile["Name"] = lines[i+1]
                break
                
        if not profile["Name"]:
            profile["Name"] = "Unknown_Author"
            
    except Exception:
        pass
        
    return profile

def parse_record_text(raw_text, category_name):
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    if len(lines) < 2: return None
    
    paper = {
        "Category": category_name, 
        "Document Type": "Non-Indexed", "Title": "", "Authors": "",
        "Date/Year": None, "Source": "", "Abstract": "",
        "Citations": "0", "References": "0", "URL": ""
    }
    
    while lines:
        last_line = lines[-1].lower()
        if last_line == "references" and len(lines) >= 2 and lines[-2].isdigit():
            paper["References"] = lines[-2]
            lines = lines[:-2]
        elif last_line == "citations" and len(lines) >= 2 and lines[-2].isdigit():
            paper["Citations"] = lines[-2]
            lines = lines[:-2]
        elif last_line in ["references", "citations"]:
            lines.pop()
        elif "full text" in last_line or "free article" in last_line:
            lines.pop()
        elif lines[-1].startswith("URL"):
            paper["URL"] = lines[-1].replace("URL", "").strip()
            lines.pop()
        elif last_line == "page size" or last_line.isdigit() or last_line.startswith("of "):
            lines.pop()
        else:
            break
            
    if not lines: return paper
    
    if lines[0].isdigit():
        lines.pop(0)
        
    if not lines: return paper
    
    if any(dt.lower() in lines[0].lower() for dt in KNOWN_DOC_TYPES):
        paper["Document Type"] = lines.pop(0)
        
    if not lines: return paper
    
    paper["Title"] = lines.pop(0)
    
    date_idx = -1
    for i, line in enumerate(lines):
        match = re.search(r'\b(19|20)\d{2}\b', line)
        if match and len(line) <= 20:
            date_idx = i
            paper["Date/Year"] = match.group(0) 
            break
            
    if date_idx != -1:
        if date_idx > 0:
            paper["Authors"] = " | ".join(lines[:date_idx])
        if date_idx + 1 < len(lines):
            paper["Source"] = lines[date_idx + 1]
            if date_idx + 2 < len(lines):
                paper["Abstract"] = " ".join(lines[date_idx + 2:])
    else:
        if len(lines) == 1:
            paper["Authors"] = lines[0]
        elif len(lines) == 2:
            paper["Authors"] = lines[0]
            paper["Source"] = lines[1]
        elif len(lines) >= 3:
            paper["Authors"] = lines[0]
            paper["Source"] = lines[1]
            paper["Abstract"] = " ".join(lines[2:])
            
    if not paper["Authors"] or paper["Authors"].strip() == "":
        paper["Authors"] = ""
            
    return paper

def save_to_excel_with_retry(df, filepath):
    while True:
        try:
            df.to_excel(filepath, index=False)
            break 
        except PermissionError:
            print(f"\n❌ PERMISSION ERROR: Cannot overwrite '{os.path.basename(filepath)}'.")
            # 🟢 Replaced input() with a GUI-safe message box
            messagebox.showwarning(
                "File Open Error", 
                f"Cannot overwrite '{os.path.basename(filepath)}'.\n\nPlease close the file in Excel and click OK to try again."
            )
        except Exception as e:
            print(f"\n❌ Unexpected error while saving {os.path.basename(filepath)}: {e}")
            break

# ==========================================
# 4. STAGE B: ATTACH AND SCRAPE
# ==========================================
def attach_and_scrape_wos(debug_port, chrome_process, output_dir: str):
    """Takes the existing debug port, attaches Selenium, extracts data, and returns the payload."""
    driver = None
    scrape_successful = False 
    
    try:
        print("\n🔗 Attaching robot to the browser...")
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(f"❌ Failed to attach to Chrome: {e}")
            return None, None

        # 🟢 BRING WINDOW TO FRONT (CLOUD-FLARE SAFE) 🟢
        try:
            driver.switch_to.window(driver.current_window_handle)
            driver.maximize_window() 
            driver.execute_script("window.focus();")
        except Exception:
            pass 

        check_for_captcha(driver) 

        print("\n👤 Extracting Author Profile...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        profile_data = parse_profile_text(body_text)
        profile_data["Profile URL"] = driver.current_url
        print(f"   ✅ Profile found for: {profile_data['Name']}")

        seen_records = set()
        papers_data = []
        
        print("\n⚙️ Beginning autonomous category iteration and pagination...")
        
        try:
            category_chips = driver.find_elements(By.CSS_SELECTOR, "button.round-chip")
            num_chips = len(category_chips)
            print(f"   🔎 Found {num_chips} category tabs.")
        except:
            num_chips = 0
            print("   ⚠️ Could not find category tabs. Will scrape current view only.")

        if num_chips > 0:
            for i in range(num_chips):
                check_for_captcha(driver)
                
                current_chips = driver.find_elements(By.CSS_SELECTOR, "button.round-chip")
                if i >= len(current_chips): break
                
                chip = current_chips[i]
                chip_text = chip.text.strip()
                    
                print(f"\n   🖱️ Auto-Clicking tab: [{chip_text}]")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", chip)
                human_delay(1, 2)
                
                try:
                    ActionChains(driver).move_to_element(chip).click().perform()
                except:
                    driver.execute_script("arguments[0].click();", chip) 
                    
                human_delay(5, 8) 
                active_category = re.sub(r'\(\d+\)', '', chip_text).strip()
                
                check_for_captcha(driver)
                
                print("   ⚙️ Attempting to set 50 records per page...")
                try:
                    page_size_btn = driver.find_elements(By.CSS_SELECTOR, "mat-select[aria-label='Items per page']")
                    if page_size_btn:
                        try:
                            ActionChains(driver).move_to_element(page_size_btn[0]).click().perform()
                        except:
                            driver.execute_script("arguments[0].click();", page_size_btn[0])
                            
                        human_delay(1, 2)
                        option_50 = driver.find_elements(By.XPATH, "//mat-option//span[contains(text(), '50')]")
                        if option_50:
                            try:
                                ActionChains(driver).move_to_element(option_50[-1]).click().perform()
                            except:
                                driver.execute_script("arguments[0].click();", option_50[-1])
                            
                            human_delay(5, 8) 
                            print("   ✅ Set to 50 items per page.")
                except Exception:
                    print("   ⚠️ Could not set 50 items per page. Defaulting to current view.")

                print(f"   ⬇️ Incrementally scrolling and paginating to extract publications...")
                
                page_num = 1
                while True:
                    check_for_captcha(driver) 
                    
                    print(f"   📄 Scraping Page {page_num}...")
                    driver.execute_script("window.scrollTo(0, 0);")
                    human_delay(2, 3)

                    current_scroll = 0
                    scroll_step = 500  
                    
                    while True:
                        records = driver.find_elements(By.CSS_SELECTOR, "app-record")
                        for record in records:
                            text = record.get_attribute("innerText").strip()
                            if not text or "loading" in text.lower(): continue
                            
                            actual_link = ""
                            try:
                                link_elems = record.find_elements(By.CSS_SELECTOR, "a[href*='/wos/'], a[href*='/record/']")
                                if link_elems:
                                    actual_link = link_elems[0].get_attribute("href")
                            except Exception:
                                pass
                                
                            unique_id = text[:50] 
                            if unique_id not in seen_records:
                                seen_records.add(unique_id)
                                parsed_paper = parse_record_text(text, active_category)
                                
                                if parsed_paper:
                                    if actual_link:
                                        parsed_paper["URL"] = actual_link
                                    papers_data.append(parsed_paper)
                        
                        current_scroll += scroll_step
                        driver.execute_script(f"window.scrollTo(0, {current_scroll});")
                        human_delay(1.5, 3.0) 
                        
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if current_scroll >= new_height:
                            human_delay(2, 4)
                            break
                            
                    try:
                        next_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Next page'], button.mat-mdc-paginator-navigation-next")
                        
                        if next_buttons:
                            next_btn = next_buttons[0]
                            if next_btn.is_enabled() and next_btn.get_attribute("disabled") is None and next_btn.get_attribute("aria-disabled") != "true":
                                try:
                                    ActionChains(driver).move_to_element(next_btn).click().perform()
                                except:
                                    driver.execute_script("arguments[0].click();", next_btn)
                                human_delay(6, 9) 
                                page_num += 1
                            else:
                                break 
                        else:
                            break 
                    except Exception:
                        print("   ⚠️ Pagination detection issue. Stopping at current page.")
                        break

        print(f"\n   ✅ Done! Captured {len(papers_data)} TOTAL unique publications.")

        # 🟢 FINAL HANDOFF LAYER
        if papers_data:
            os.makedirs(output_dir, exist_ok=True)
            clean_name = "".join(x for x in profile_data['Name'] if x.isalnum() or x in " _-")
            
            profile_path = os.path.join(output_dir, f"WoS_{clean_name}_Profile.xlsx")
            papers_path = os.path.join(output_dir, f"WoS_{clean_name}_Publications.xlsx")
            
            save_to_excel_with_retry(pd.DataFrame([profile_data]), profile_path)
            save_to_excel_with_retry(pd.DataFrame(papers_data), papers_path)
            
            print(f"\n📊 Saved Profile to: {profile_path}")
            print(f"📊 Saved Publications to: {papers_path}")
            
            # 🟢 STANDARDIZED KEYS: Changed to "profile" and "papers"
            payload = {"profile": profile_data, "papers": papers_data}
            scrape_successful = True 
            
            return papers_path, payload
        
        
        else:
            print("❌ No publications were scraped. Exiting without saving.")
            return None, None

    except Exception as general_error:
        print(f"\n❌ A fatal error interrupted the scraper: {general_error}")
        return None, None

    finally:
        print("\n🧹 Initiating system cleanup...")
        if driver:
            try: driver.quit() 
            except Exception: pass 
                
        if chrome_process:
            try:
                chrome_process.terminate() 
                chrome_process.wait(timeout=3)
            except Exception:
                try: chrome_process.kill() 
                except: pass
                
        print("   ✅ Browser successfully closed and background ports released.")

        # 🟢 Replaced terminal input() with GUI-safe messagebox for Profile Rotation
        if not scrape_successful:
            rotate = messagebox.askyesno(
                "Profile Rotation Required?", 
                "The scraping session did not complete successfully.\n\nDid Cloudflare permanently block this profile?\nClick 'Yes' to rotate to a brand new browser fingerprint for the next launch."
            )
            if rotate:
                print("\n♻️ Retiring the tainted Chrome profile...")
                time.sleep(2) 
                active_profile = get_active_profile_path()
                tainted_profile = f"{active_profile}_Tainted_{int(time.time())}"
                try:
                    os.rename(active_profile, tainted_profile)
                    print("   ✅ Profile rotated. The next launch will use a brand new, clean fingerprint.")
                except Exception as e:
                    print(f"   ⚠️ Could not automatically rotate the profile: {e}")