# utils/browser.py
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config import HEADLESS

def setup_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )
    options.add_argument(f"user-agent={user_agent}")
    
    temp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile}")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)
    return driver
