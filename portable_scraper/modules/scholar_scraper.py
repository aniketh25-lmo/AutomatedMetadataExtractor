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

    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        logger.info(f"Starting Scholar scrape for: {faculty_name}")

        # =====================================================
        # STEP 1: GOOGLE SEARCH
        # =====================================================
        driver.get("https://www.google.com")

        search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
        )

        search_box.send_keys(f"{faculty_name} Google Scholar")
        search_box.submit()

        logger.info("Google search submitted")

        # 🔴 WAIT FOR CAPTCHA / PAGE LOAD
        logger.info("Waiting 30 seconds for CAPTCHA solving if needed...")
        time.sleep(30)

        # =====================================================
        # STEP 2: FIND SCHOLAR PROFILE LINK
        # =====================================================
        logger.info("Locating Scholar profile link...")

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

        time.sleep(20)

        # =====================================================
        # STEP 3: PROFILE METRICS
        # =====================================================
        profile_stats = {}

        try:
            stats = driver.find_elements(By.CSS_SELECTOR, "td.gsc_rsb_std")

            labels = [
                "Total Citations",
                "Citations Since 2019",
                "h-index",
                "h-index Since 2019",
                "i10-index",
                "i10-index Since 2019"
            ]

            for label, stat in zip(labels, stats):
                profile_stats[label] = stat.text

        except:
            logger.warning("Could not extract profile metrics")

        # =====================================================
        # STEP 4: LOAD ALL PUBLICATIONS
        # =====================================================
        logger.info("Loading all publications...")

        while True:
            try:
                more_btn = driver.find_element(By.ID, "gsc_bpf_more")

                if more_btn.is_enabled():
                    more_btn.click()
                    time.sleep(1.5)
                else:
                    break

            except:
                break

        # =====================================================
        # STEP 5: SCRAPE ALL PAPERS
        # =====================================================
        logger.info("Scraping publication table...")

        papers = []

        rows = driver.find_elements(By.CSS_SELECTOR, "tr.gsc_a_tr")

        for row in rows:
            try:
                title = row.find_element(By.CLASS_NAME, "gsc_a_at").text
                authors = row.find_elements(By.CLASS_NAME, "gs_gray")[0].text
                venue = row.find_elements(By.CLASS_NAME, "gs_gray")[1].text
                citations = row.find_element(By.CLASS_NAME, "gsc_a_c").text
                year = row.find_element(By.CLASS_NAME, "gsc_a_y").text

                papers.append({
                    "Faculty Name": faculty_name,
                    "Title": title,
                    "Authors": authors,
                    "Venue": venue,
                    "Citations": citations,
                    "Year": year,
                    **profile_stats
                })

            except Exception as e:
                logger.error(f"Row parse error: {e}")

        # =====================================================
        # STEP 6: SAVE EXCEL
        # =====================================================
        logger.info("Saving Excel output...")

        df = pd.DataFrame(papers)

        filename = f"{faculty_name.replace(' ', '_')}_Scholar.xlsx"
        output_path = os.path.join(output_dir, filename)

        df.to_excel(output_path, index=False)

        logger.info(f"Saved successfully: {output_path}")
        return output_path

    finally:
        driver.quit()
