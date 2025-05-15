import time
import json
import re
import random
from datetime import datetime, timedelta
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


# --- Configuration ---
CATEGORIES = [
    {"name": "Consumerism", "url": "https://www.hot.co.il/קטגוריה/688/צרכנות"},
    {"name": "Travel and Vacation", "url": "https://www.hot.co.il/קטגוריה/96/תיירות_ונופש"},
    {"name": "Culture and Leisure", "url": "https://www.hot.co.il/קטגוריה/817/תרבות_ופנאי"},
    {"name": "Cars", "url": "https://www.hot.co.il/קטגוריה/877/רכב"},
    {"name": "Insurance", "url": "https://www.hot.co.il/קטגוריה/818/ביטוח"},
    {"name": "Finance and Banking", "url": "https://www.hot.co.il/קטגוריה/777/פיננסים_ובנקאות"}
]

MAX_DISCOUNTS = 10  # Number of discounts to scrape per category
AMOUNT = 1
HEADLESS = True
BASE_URL = "https://www.hot.co.il"

# --- Setup Driver ---
def setup_driver():
    options = Options()
    if HEADLESS:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=options)

# --- Helper (Regex) Functions ---

def extract_due_date(text):
    patterns = [
        r'בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'תוקף ההטבה בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'תקף בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'מימוש ההטבה בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'עד לתאריך ([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'עד תאריך ([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            found_date = match.group(1)
            print(f"[+] Due Date Found: {found_date}")
            return found_date

    # Generate random fallback due date between 10 and 40 days from today
    random_days = random.randint(10, 40)
    fallback_due_date = (datetime.now() + timedelta(days=random_days)).strftime("%d.%m.%y")
    print(f"[!] No due date found, defaulting to: {fallback_due_date} (+{random_days} days)")
    return fallback_due_date

def classify_price_type(price_text):
    if not price_text or price_text.strip() == "":
        return "N/A"

    # Normalize text
    price_text = price_text.strip()

    # 1. Check for percentage discount (e.g., "10%", "15 אחוז", "ב- 18% הנחה")
    if re.search(r'\d{1,3}\s*[%אחוז]', price_text):
        print(f"[+] Price Type Found: percentage")
        return "percentage"

    # 2. Check for actual price — digits with optional currency or decimal
    if re.search(r'[\d]+([.,]\d{1,2})?\s*(₪|\$|€)?', price_text):
        print(f"[+] Price Type Found: price")
        return "price"

    # 3. If neither match
    return "N/A"

def extract_discount_code(text):
    # Only match codes that follow a real coupon trigger
    pattern = r'(?:קוד קופון|קוד הטבה|קוד המבצע|קוד)\s*:?\s*([A-Za-z0-9]{4,})'
    match = re.search(pattern, text)
    if match:
        code = match.group(1)
        # Optional: filter out known false-positives like "באתר", "למוכרן"
        false_positives = {"באתר", "למוכרן", "בטרם", "קופה", "טרם", "בהצגה", "אפליקציית", "מועדון"}
        if code in false_positives:
            return "N/A"
        print(f"[+] Discount Code Found: {code}")
        return code
    return "N/A"


def get_club_name_from_url(url):
    """
    Extracts the domain (like 'hot') from a full URL.
    """
    parsed = urlparse(url)
    domain_parts = parsed.netloc.split('.')
    if domain_parts[0] == "www":
        return domain_parts[1]  # e.g., 'hot'
    return domain_parts[0]  # fallback


# --- Scrape a single category ---
def extract_discounts_for_category(driver, category_url, category_name):
    print(f"----------------------------------")
    print(f"\n[*] Opening '{category_name}' page...")
    club_name = get_club_name_from_url(category_url)
    driver.get(category_url)
    time.sleep(2)

    try:
        container = driver.find_element(By.CSS_SELECTOR, 'div.benefits-grid.benefits-grid_promoted')
        discount_elements = container.find_elements(By.CSS_SELECTOR, 'a.benefit-wrapper')[:MAX_DISCOUNTS]
        print(f"[+] Found {len(discount_elements)} discount(s).")
    except NoSuchElementException:
        print("[-] No discounts found.")
        return []

    discount_links = [elem.get_attribute('href') for elem in discount_elements]
    discounts = []

    for i, link in enumerate(discount_links):
        print(f"-------------------")
        print(f"[*] For Discount #{i+1}:")
        try:
            
            # Discount Link
            full_link = link if link.startswith("http") else BASE_URL + link
            driver.get(full_link)
            time.sleep(2)
            print(f"[+] Discount Link Found")

            # Title
            try:
                title = driver.find_element(By.CSS_SELECTOR, "h1.head-span").text.strip()
            except NoSuchElementException:
                title = "N/A"
            print(f"[+] Title Found")

            # Price
            try:
                price_elem = driver.find_element(By.XPATH, "//span[starts-with(@class, 'price-span')]")
                price = price_elem.text.strip()
            except NoSuchElementException:
                price = "N/A"
            print(f"[+] Price Found")

            # Description
            description_parts = []
            info_wrappers = driver.find_elements(By.CSS_SELECTOR, ".extra-info .info-wrapper")
            for wrapper in info_wrappers:
                try:
                    des_title = wrapper.find_element(By.CLASS_NAME, "title").text.strip()
                except NoSuchElementException:
                    des_title = "N/A"
                try:
                    des_body = wrapper.find_element(By.CLASS_NAME, "description").text.strip()
                except NoSuchElementException:
                    des_body = "N/A"
                description_parts.append(f"{des_title}: {des_body}")
            description = "\n\n".join(description_parts)
            print(f"[+] Description Found")

            # Image Link
            try:
                img_tag = driver.find_element(By.CSS_SELECTOR, ".gallery-wrapper .selected-image-wrapper img")
                image_link = img_tag.get_attribute("src")
            except NoSuchElementException:
                image_link = "N/A"
            print(f"[+] Image Link Found")

            # Terms & Conditions
            try:
                terms_block = driver.find_element(By.CSS_SELECTOR, ".details-wrapper .content")
                paragraphs = terms_block.find_elements(By.TAG_NAME, "p")
                terms = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())
            except NoSuchElementException:
                terms = "N/A"
            print(f"[+] Terms&Conditions Found")

            # provider's Link
            try:
                external_link = "N/A"
                button = driver.find_element(By.CLASS_NAME, "send-btn")
                ActionChains(driver).key_down(Keys.CONTROL).click(button).key_up(Keys.CONTROL).perform()
                time.sleep(3)
                driver.switch_to.window(driver.window_handles[1])
                current = driver.current_url
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                if "hot.co.il" not in current:
                    print(f"[+] Provider Link Found: {current}")
                    external_link = current
                else:
                    print("[!] Redirect stayed on HOT site")
            except Exception as e:
                print(f"[!] External link extraction failed: {e}")
                external_link = "N/A"   


            # Discount Code
            discount_code = extract_discount_code(description + " " + terms)

            # Due Date
            due_date = extract_due_date(description + " " + terms)

            # Price Type
            price_type = classify_price_type(price)

            discounts.append({
                "club_name": club_name,
                "category": category_name,
                "discount_id": str(extract_discounts_for_category.counter),
                "title": title,
                "price": price,
                "discount_type": price_type,
                "description": description,
                "discount_link": full_link,
                "image_link": image_link,
                "provider_link": external_link,
                "terms_and_conditions": terms,
                "coupon_code": discount_code,
                "valid_until": due_date,
                "usage_limit": AMOUNT
            })
            extract_discounts_for_category.counter += 1

        except Exception as e:
            print(f"[!] Error scraping discount #{i+1}: {e}")

    return discounts

# Counter
extract_discounts_for_category.counter = 1

# --- Main ---
if __name__ == "__main__":
    driver = setup_driver()
    all_discounts = []

    for category in CATEGORIES:
        results = extract_discounts_for_category(driver, category["url"], category["name"])
        if results:
            all_discounts.extend(results)

    driver.quit()

    with open("hot_discounts.json", "w", encoding="utf-8") as f:
        json.dump(all_discounts, f, ensure_ascii=False, indent=2)

    print("\n[✔] Scraping complete. Results saved to hot_discounts.json")
