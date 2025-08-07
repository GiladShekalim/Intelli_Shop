# utils/browser.py
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from config import HEADLESS


def setup_driver():
    """Return a configured Chrome WebDriver.

    Uses webdriver_manager to download / locate a compatible chromedriver so
    the host system only needs the Chrome/Chromium browser binary installed.
    """

    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")

    # Hardening flags for container / CI environments
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    # Isolate chrome profile so parallel runs do not collide
    temp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile}")

    # webdriver-manager will ensure the correct driver version is used
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    return webdriver.Chrome(service=service, options=options)
