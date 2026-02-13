import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def run_scopus_scraper(first_name, last_name, output_dir):
    EXCEL_OUTPUT = f"{output_dir}/scopus_{first_name}_{last_name}_documents.xlsx"

    options = Options()
    options.add_argument("--start-maximized")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get("https://www.scopus.com")

        print("\n🔐 PLEASE SIGN IN TO SCOPUS MANUALLY")
        print("⏳ Waiting 60 seconds for login...\n")

        time.sleep(60)

        print("Navigating to Author Search...")

        driver.get("https://www.scopus.com/freelookup/form/author.uri")

        time.sleep(5)

        print("Locating author name input fields...")

        last_name_box = wait.until(
            EC.presence_of_element_located((By.ID, "lastname"))
        )

        first_name_box = wait.until(
            EC.presence_of_element_located((By.ID, "firstname"))
        )

        last_name_box.clear()
        first_name_box.clear()

        last_name_box.send_keys(last_name)
        first_name_box.send_keys(first_name)

        search_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "authorSubmitBtn"))
        )

        search_btn.click()

        print("✅ Search submitted")

        time.sleep(8)

        print("Selecting author profile...")

        author_xpath = f"//a[contains(text(), '{last_name}')]"

        author_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, author_xpath))
        )

        author_link.click()

        print("✅ Author profile opened")

        time.sleep(5)

        try:
            edit_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(),'Edit profile')]")
                )
            )

            edit_btn.click()
            print("✅ Edit profile clicked")

        except:
            print("⚠ Edit profile not found or already open")

        time.sleep(10)

        try:
            cookie_btn = wait.until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_btn.click()
            print("✅ Cookie popup handled")
        except:
            pass

        time.sleep(5)

        try:
            docs_tab = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[contains(text(),'Documents')]")
                )
            )

            docs_tab.click()

            print("✅ Documents tab opened")

        except:
            print("⚠ Documents tab already open or not clickable")

        time.sleep(5)

        author_name = "Unknown"
        orcid = "Not Found"

        try:
            author_name = driver.find_element(By.CSS_SELECTOR, "h1").text
        except:
            pass

        try:
            orcid_element = driver.find_element(
                By.XPATH,
                "//span[contains(@class,'Typography')]"
            )
            orcid = orcid_element.text
        except:
            pass

        print("\nAUTHOR:", author_name)
        print("ORCID:", orcid)

        rows = driver.find_elements(By.CSS_SELECTOR, "tr")

        data = []

        for r in rows:
            cols = r.find_elements(By.TAG_NAME, "td")

            if len(cols) >= 4:
                try:
                    title = cols[0].text
                    authors = cols[1].text
                    source = cols[2].text
                    year = cols[3].text

                    data.append({
                        "Author Name": author_name,
                        "ORCID": orcid,
                        "Document Title": title,
                        "Authors": authors,
                        "Source": source,
                        "Year": year
                    })
                except:
                    pass

        print(f"\n✅ Found {len(data)} documents")

        df = pd.DataFrame(data)

        df.to_excel(EXCEL_OUTPUT, index=False)

        print(f"\n📁 Excel generated: {EXCEL_OUTPUT}")

        driver.quit()

        return EXCEL_OUTPUT

    except Exception as e:
        print("SCOPUS SCRAPER ERROR:", e)
        driver.quit()
        return None
