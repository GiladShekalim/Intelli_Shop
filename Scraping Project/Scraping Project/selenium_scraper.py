import time
import json
import re
import random
from datetime import datetime, timedelta
from urllib.parse import urlparse

import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import tempfile
from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



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
        options.add_argument("--headless=new")

    options.add_argument('--disable-gpu')
    options.add_argument('--disable-application-cache')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    # Temporary user profile to avoid disk bloat and corrupted cache
    temp_profile = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_profile}")

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
        print(f"[-] No Price Type Found")
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
    print(f"[-] No Price Type Found")
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
            print(f"[-] No Discount Code Found")
            return "N/A"
        print(f"[+] Discount Code Found: {code}")
        return code
    print(f"[-] No Discount Code Found")
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

    # Search for Set of Discounts for chosen category:
    try:
        container = driver.find_element(By.CSS_SELECTOR, 'div.benefits-grid.benefits-grid_promoted')
        discount_elements = container.find_elements(By.CSS_SELECTOR, 'a.benefit-wrapper')[:MAX_DISCOUNTS]
        print(f"[+] Found {len(discount_elements)} discount(s).")
    except NoSuchElementException:
        print("[-] No discounts found.")
        return []

    # Saving set of discounts to go through each one:
    discount_links = []
    for elem in discount_elements:
        href = elem.get_attribute("href")
        if href and href.strip():
            discount_links.append(href)
        else:
            print("[!] Skipping discount block with missing href")

    
    # Loop to go over them and extract info per discount:
    discounts = []
    for i, link in enumerate(discount_links):
        print(f"-------------------")
        print(f"[*] For Discount #{i+1}:")
        # try to scrape a discount:
        try:
            
            # Discount Link
            full_link = link if link.startswith("http") else BASE_URL + link
            try:
                driver.get(full_link)
                WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.head-span")))
                print(f"[+] Discount Link Found")
            except Exception as e:
                print(f"[!] Error loading page: {e}")
                continue  # skip this discount
            except NoSuchElementException:
                full_link = "N/A"
                print(f"[-] No Discount Link Found")
            
            # Image Link
            try:
                img_tag = driver.find_element(By.CSS_SELECTOR, ".gallery-wrapper .selected-image-wrapper img")
                image_link = img_tag.get_attribute("src")
                print(f"[+] Image Link Found")
            except NoSuchElementException:
                image_link = "N/A"
                print(f"[-] No Image Link Found")
            

            # --- External Link (detect tel via button text or content before clicking) ---
            external_link = "N/A"
            try:
                buttons = driver.find_elements(By.CLASS_NAME, "send-btn")

                if buttons:
                    button = buttons[0]
                    button_text = button.text.strip()
                    button_html = button.get_attribute("outerHTML") or ""
                    href = button.get_attribute("href") or button.get_attribute("data-href") or ""

                    # Phone detection logic
                    is_tel = False
                    if "tel:" in button_html.lower():
                        is_tel = True
                    elif re.search(r"\b0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}\b", button_text):
                        is_tel = True
                    elif "להזמנה" in button_text or "להזמנות" in button_text:
                        is_tel = True
                    elif href.lower().startswith("tel:"):
                        is_tel = True

                    if is_tel:
                        external_link = "TEL"
                        print(f"[✓] No external link — this discount uses a phone number button ({button_text})")

                    else:
                        original_tabs = driver.window_handles.copy()
                        driver.execute_script("arguments[0].click();", button)
                        print("[*] Clicked send button, waiting...")

                        time.sleep(2.5)  # allow time for tab or form to react

                        new_tabs = driver.window_handles
                        if len(new_tabs) > len(original_tabs):
                            new_tab = [tab for tab in new_tabs if tab not in original_tabs][0]
                            driver.switch_to.window(new_tab)
                            print("[*] Switched to new tab")

                            try:
                                current = driver.execute_script("return window.location.href;")
                                print(f"[*] JS returned current URL: {current}")
                            except Exception:
                                current = "N/A"
                                print("[!] JS failed to read URL")

                            if current and "hot.co.il" not in current and not current.startswith("data:"):
                                external_link = current
                                print(f"[+] Provider Link Found: {external_link}")
                            else:
                                print("[!] Redirect stayed on HOT or was invalid")

                            driver.close()
                            driver.switch_to.window(original_tabs[0])
                            print("[*] Closed tab and returned")
                        else:
                            external_link = "FORM"
                            print("[✓] No external link — this discount uses a form")

                else:
                    print("[✓] No send button exists on this discount")

            except Exception as e:
                print(f"[!] External link extraction failed: {type(e).__name__}: {e}")











            # Title
            try:
                title = driver.find_element(By.CSS_SELECTOR, "h1.head-span").text.strip()
                print(f"[+] Title Found")
            except NoSuchElementException:
                title = "N/A"
                print(f"[-] No Title Found")

            # Price
            try:
                price_elem = driver.find_element(By.XPATH, "//span[starts-with(@class, 'price-span')]")
                price = price_elem.text.strip()
                print(f"[+] Price Found")
            except NoSuchElementException:
                price = "N/A"
                print(f"[-] No Price Found")
            
            # Price Type
            price_type = classify_price_type(price)

            # Description
            try:
                description_parts = []
                info_wrappers = driver.find_elements(By.CSS_SELECTOR, ".extra-info .info-wrapper")
                for wrapper in info_wrappers:
                    try:
                        des_title = wrapper.find_element(By.CLASS_NAME, "title").text.strip()
                    except NoSuchElementException:
                        des_title = "N/A"
                        print(f"[-] No Desc Title Found")
                    try:
                        des_body = wrapper.find_element(By.CLASS_NAME, "description").text.strip()
                    except NoSuchElementException:
                        des_body = "N/A"
                        print(f"[-] No Desc Body Found")
                    
                    description_parts.append(f"{des_title}: {des_body}")
                description = "\n\n".join(description_parts)
                print(f"[+] Description Found")
            except NoSuchElementException:
                print(f"[-] No Description Found")
 
            # Terms & Conditions
            try:
                terms_block = driver.find_element(By.CSS_SELECTOR, ".details-wrapper .content")
                paragraphs = terms_block.find_elements(By.TAG_NAME, "p")
                terms = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())
                print(f"[+] Terms And Conditions Found")
            except NoSuchElementException:
                terms = "N/A"
                print(f"[-] No Terms And Conditions Found")

            # Discount Code
            discount_code = extract_discount_code(description + " " + terms)

            # Due Date
            due_date = extract_due_date(description + " " + terms)

            # adding all extracted info per discount into List:
            discounts.append({
                "club_name": club_name,
                "category": category_name,

                "discount_id": str(extract_discounts_for_category.counter),
                "title": title,

                "price": price,
                "discount_type": price_type,

                "description": description,
                "terms_and_conditions": terms,

                "discount_link": full_link,
                "image_link": image_link,
                "provider_link": external_link,
                
                "coupon_code": discount_code,
                "valid_until": due_date,

                "usage_limit": AMOUNT
            })
            extract_discounts_for_category.counter += 1
        
        # wasn't able to scrape the discount:    
        except Exception as e:
            print(f"[!] Error scraping discount #{i+1}: {e}")
    
    # return total discounts:
    return discounts

# Counter
extract_discounts_for_category.counter = 1

# Add delay between discounts:
print("[⏳] Waiting before next discount...")
time.sleep(random.uniform(1.5, 3.5))  # small human-like pause


# --- Main ---
if __name__ == "__main__":
    driver = setup_driver()
    all_discounts = []

    for category in CATEGORIES:
        results = extract_discounts_for_category(driver, category["url"], category["name"])
        if results:
            all_discounts.extend(results)

    # Add pause between categories (optional: log it too)
    print("[⏳] Waiting before next category...")
    time.sleep(random.uniform(4, 7))  # Slightly longer than between discounts

    driver.quit()

    with open("hot_discounts.json", "w", encoding="utf-8") as f:
        json.dump(all_discounts, f, ensure_ascii=False, indent=2)

    print("\n[✔] Scraping complete. Results saved to hot_discounts.json")
