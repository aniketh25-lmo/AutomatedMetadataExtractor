from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from .logger import setup_logger
from .config import load_config

logger = setup_logger("driver_manager")


def get_driver():

    config = load_config()

    logger.info("Initializing WebDriver")

    options = Options()
    options.add_argument("--start-maximized")

    # Make Selenium less detectable
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Performance & stability flags
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if config.get("headless", False):
        options.add_argument("--headless=new")

    # === METHOD 1: Automatic ChromeDriver Download ===
    try:
        logger.info("Attempting automatic ChromeDriver setup")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        logger.info("ChromeDriver initialized via WebDriver Manager")
        return driver

    except Exception as e:
        logger.warning(f"WebDriver Manager setup failed: {str(e)}")

    # === METHOD 2: System Installed ChromeDriver ===
    try:
        logger.info("Trying system-installed ChromeDriver")

        driver = webdriver.Chrome(options=options)

        logger.info("ChromeDriver initialized from system PATH")
        return driver

    except Exception as e2:
        logger.error(f"System ChromeDriver failed: {str(e2)}")

    # === FINAL FAILURE ===
    logger.critical("All ChromeDriver initialization methods failed")
    raise Exception(
        "Could not initialize ChromeDriver. "
        "Please ensure Google Chrome is installed."
    )
