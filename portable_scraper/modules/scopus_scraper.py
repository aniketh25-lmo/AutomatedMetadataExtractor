import os
import time
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from portable_scraper.core.driver_manager import get_driver
from portable_scraper.core.logger import setup_logger

logger = setup_logger("scopus_scraper")


# ==========================================
# SAFE ELEMENT GETTERS
# ==========================================

def safe_text(driver, by, value):
    try:
        return driver.find_element(by, value).text.strip()
    except:
        return ""


def safe_click(wait, by, value):
    elem = wait.until(EC.element_to_be_clickable((by, value)))
    elem.click()
    return elem


# ==========================================
# MAIN SCRAPER
# ==========================================

def run_scopus_scraper(first_name: str, last_name: str, output_dir: str):
    logger.info("Starting Scopus scraping")

    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        # ============================
        # STEP 1: OPEN SCOPUS
        # ============================
        driver.get("https://www.scopus.com")

        logger.info("Waiting 30s for manual login")
        time.sleep(30)

        # ============================
        # STEP 2: AUTHOR SEARCH PAGE
        # ============================
        driver.get("https://www.scopus.com/freelookup/form/author.uri")
        time.sleep(5)

        # ============================
        # STEP 3: ENTER AUTHOR NAME
        # ============================
        last_box = wait.until(EC.presence_of_element_located((By.ID, "lastname")))
        first_box = wait.until(EC.presence_of_element_located((By.ID, "firstname")))

        last_box.clear()
        first_box.clear()

        last_box.send_keys(last_name)
        first_box.send_keys(first_name)

        safe_click(wait, By.ID, "authorSubmitBtn")
        logger.info("Author search submitted")

        time.sleep(8)

        # ============================
        # STEP 4: SELECT AUTHOR
        # ============================
        author_xpath = f"//a[contains(text(), '{last_name}')]"
        safe_click(wait, By.XPATH, author_xpath)
        logger.info("Author profile opened")

        time.sleep(6)

        # ============================
        # STEP 5: CLICK EDIT PROFILE
        # ============================
        try:
            safe_click(wait, By.XPATH, "//span[contains(text(),'Edit profile')]")
            logger.info("Edit profile clicked")
        except:
            logger.info("Edit profile not needed")

        logger.info("Waiting 10s for popup/manual handling")
        time.sleep(10)

        # ============================
        # STEP 6: COOKIE POPUP
        # ============================
        try:
            safe_click(wait, By.ID, "onetrust-accept-btn-handler")
        except:
            pass

        time.sleep(5)

        # ============================
        # STEP 7: DOCUMENTS TAB
        # ============================
        try:
            safe_click(wait, By.XPATH, "//span[contains(text(),'Documents')]")
            logger.info("Documents tab opened")
        except:
            logger.info("Documents tab already open")

        time.sleep(5)

        # ============================
        # STEP 8: PROFILE METADATA
        # ============================
        profile = {}

        profile["name"] = safe_text(driver, By.CSS_SELECTOR, "h1")

        # ORCID (avoid label text)
        profile["orcid"] = ""
        try:
            orcid_elem = driver.find_element(By.XPATH, "//span[contains(text(),'0000-')]")
            txt = orcid_elem.text.strip()
            if txt.startswith("0000"):
                profile["orcid"] = txt
        except:
            pass

        # Metrics (from Edit Profile page)
        try:
            metrics = driver.find_elements(By.CSS_SELECTOR, "div.metricsSection div")

            if len(metrics) >= 3:
                profile["documents"] = metrics[0].text.strip()
                profile["citations"] = metrics[1].text.strip()
                profile["h_index"] = metrics[2].text.strip()
            else:
                profile["documents"] = ""
                profile["citations"] = ""
                profile["h_index"] = ""

        except:
            profile["documents"] = ""
            profile["citations"] = ""
            profile["h_index"] = ""

        # ============================
        # STEP 9: DOCUMENT TABLE
        # ============================
        papers = []

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        for r in rows:
            cols = r.find_elements(By.TAG_NAME, "td")
            if len(cols) < 4:
                continue

            title = cols[0].text.replace("Remove from profile", "").strip()
            title = title.split("\n")[0].strip()

            authors = cols[1].text.strip()
            source = cols[2].text.strip()
            year = cols[3].text.strip()

            papers.append({
                "title": title,
                "authors": authors,
                "source": source,
                "year": year
            })

        logger.info(f"Scraped {len(papers)} documents")


        # ============================
        # STEP 10: SAVE EXCEL
        # ============================
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(
            output_dir,
            f"Scopus_{first_name}_{last_name}_documents.xlsx"
        )

        df = pd.DataFrame(papers)
        df.to_excel(file_path, index=False)

        logger.info(f"Excel saved: {file_path}")

        payload = {
            "profile": profile,
            "papers": papers
        }

        return file_path, payload

    finally:
        driver.quit()
