# scrapers/hot_scraper.py
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CATEGORIES_HOT, BASE_URL_HOT, MAX_DISCOUNTS, AMOUNT, LOCATION
from utils.helpers import *

def scrape_hot(driver):
    all_discounts = []
    extract_discounts_for_category.counter = 1
    
    for category in CATEGORIES_HOT:
        discounts = extract_discounts_for_category(driver, category["url"], category["name"])
        all_discounts.extend(discounts)
        print("[⏳] Waiting before next category...")
        time.sleep(random.uniform(4, 7))

    return all_discounts

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
        try:
            href = elem.get_attribute("href")
            if href and href.strip():
                discount_links.append(href)
        except NoSuchElementException:
            print("[!] Card without link – skipping")
    
    # Loop over them and extract info per discount:
    discounts = []
    for i, link in enumerate(discount_links):
        print(f"-------------------")
        print(f"[*] For Discount #{i+1}:")
        
        # try to scrape a discount:
        try:
            
            # Discount Link
            full_link = link if link.startswith("http") else BASE_URL_HOT + link
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
            

            # External Link
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
            discount_code = extract_coupon_code(description + " " + terms)

            # Due Date
            due_date = extract_valid_until(description + " " + terms)

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

                "usage_limit": AMOUNT,
                "location": LOCATION
            })
            extract_discounts_for_category.counter += 1
        # If got here - wasn't able to scrape the discount:    
        except Exception as e:
            print(f"[!] Error scraping discount #{i+1}: {e}")
    
    # return total discounts:
    return discounts
