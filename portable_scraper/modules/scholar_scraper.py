import time
import os
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from portable_scraper.core.driver_manager import get_driver
from portable_scraper.core.logger import setup_logger

logger = setup_logger("scholar_scraper")


def run_scholar_scraper(faculty_name: str, output_dir: str):
    """
    Scrapes Google Scholar profile.

    Excel → ONLY publications table (clean & presentable)
    DB payload → full profile + metrics + papers
    """

    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        logger.info(f"Starting Scholar scrape for: {faculty_name}")

        # =====================================================
        # STEP 1: GOOGLE SEARCH (ROBUST ENTRY)
        # =====================================================
        driver.get("https://www.google.com")

        search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
        )

        search_box.send_keys(f"{faculty_name} Google Scholar")
        search_box.submit()

        logger.info("Google search submitted")
        logger.info("Waiting 30 seconds for CAPTCHA/manual solve...")
        time.sleep(30)

        # =====================================================
        # STEP 2: FIND SCHOLAR PROFILE LINK
        # =====================================================
        profile_url = None
        links = driver.find_elements(By.CSS_SELECTOR, "a")

        for link in links:
            href = link.get_attribute("href")
            if href and "scholar.google.com/citations?user=" in href:
                profile_url = href
                break

        if not profile_url:
            raise Exception("Scholar profile link not found")

        logger.info(f"Profile found: {profile_url}")
        driver.get(profile_url)
        time.sleep(5)

        # =====================================================
        # STEP 3: PROFILE METADATA (FOR DB)
        # =====================================================
        profile = {}

        try:
            profile["name"] = driver.find_element(By.ID, "gsc_prf_in").text
        except:
            profile["name"] = faculty_name

        try:
            profile["affiliation"] = driver.find_element(
                By.CLASS_NAME, "gsc_prf_il"
            ).text
        except:
            profile["affiliation"] = ""

        try:
            profile["email"] = driver.find_element(
                By.ID, "gsc_prf_ivh"
            ).text
        except:
            profile["email"] = ""

        try:
            profile["interests"] = ", ".join(
                [i.text for i in driver.find_elements(By.CLASS_NAME, "gsc_prf_inta")]
            )
        except:
            profile["interests"] = ""

        try:
            profile["photo_url"] = driver.find_element(
                By.ID, "gsc_prf_pup-img"
            ).get_attribute("src")
        except:
            profile["photo_url"] = ""

        # Metrics
        try:
            stats = driver.find_elements(By.CSS_SELECTOR, "td.gsc_rsb_std")
            profile["citations_all"] = stats[0].text
            profile["citations_recent"] = stats[1].text
            profile["hindex_all"] = stats[2].text
            profile["hindex_recent"] = stats[3].text
            profile["i10_all"] = stats[4].text
            profile["i10_recent"] = stats[5].text
        except:
            logger.warning("Metrics extraction failed")

        # =====================================================
        # STEP 4: LOAD ALL PUBLICATIONS
        # =====================================================
        logger.info("Loading all publications...")

        while True:
            try:
                more_btn = driver.find_element(By.ID, "gsc_bpf_more")
                if more_btn.is_enabled():
                    driver.execute_script("arguments[0].click();", more_btn)
                    time.sleep(1.5)
                else:
                    break
            except:
                break

        # =====================================================
        # STEP 5: SCRAPE PUBLICATIONS
        # =====================================================
        logger.info("Scraping publications table...")

        excel_rows = []   # clean Excel
        db_papers = []    # full DB payload

        rows = driver.find_elements(By.CSS_SELECTOR, "tr.gsc_a_tr")

        for row in rows:
            try:
                title_el = row.find_element(By.CLASS_NAME, "gsc_a_at")
                title = title_el.text
                paper_url = title_el.get_attribute("href")

                gray = row.find_elements(By.CLASS_NAME, "gs_gray")
                authors = gray[0].text if len(gray) > 0 else ""
                venue = gray[1].text if len(gray) > 1 else ""

                citations = row.find_element(By.CLASS_NAME, "gsc_a_c").text
                year = row.find_element(By.CLASS_NAME, "gsc_a_y").text

                # ---------- Excel row ----------
                excel_rows.append({
                    "Title": title,
                    "Authors": authors,
                    "Venue": venue,
                    "Citations": citations,
                    "Year": year
                })

                # ---------- DB payload ----------
                db_papers.append({
                    "title": title,
                    "authors": authors,
                    "venue": venue,
                    "citations": citations,
                    "year": year,
                    "scholar_url": paper_url
                })

            except Exception as e:
                logger.warning(f"Row parse error: {e}")

        # =====================================================
        # STEP 6: SAVE CLEAN EXCEL
        # =====================================================
        df = pd.DataFrame(excel_rows)

        filename = f"{faculty_name.replace(' ', '_')}_Scholar.xlsx"
        output_path = os.path.join(output_dir, filename)

        df.to_excel(output_path, index=False)

        logger.info(f"Excel saved: {output_path}")

        # =====================================================
        # STEP 7: RETURN DB PAYLOAD
        # =====================================================
        db_payload = {
            "profile": profile,
            "papers": db_papers
        }

        return output_path, db_payload

    finally:
        driver.quit()
