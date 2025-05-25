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
    temp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile}")
    return webdriver.Chrome(options=options)
