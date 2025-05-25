# scrapers/adif_scraper.py
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CATEGORIES_ADIF, BASE_URL_ADIF, AMOUNT, LOCATION, MAX_DISCOUNTS
from utils.helpers import *

def scrape_adif(driver):
    all_discounts = []
    extract_discounts_for_category.counter = 1

    for category in CATEGORIES_ADIF:
        discounts = extract_discounts_for_category(driver, category["url"], category["name"])
        all_discounts.extend(discounts)
        print("[⏳] Waiting before next category...")
        time.sleep(random.uniform(3, 6))

    return all_discounts

def extract_discounts_for_category(driver, category_url, category_name):
    print(f"----------------------------------")
    print(f"\n[*] Opening '{category_name}' page...")
    club_name = get_club_name_from_url(category_url)
    
    #print(f"[DEBUG] Category URL: {category_url}")
    #print("[DEBUG] Navigating to category URL")
    driver.get(category_url)

    #print("[DEBUG] Waiting for discount elements to load...")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-12.col-md-3.mb-4"))
    )
    #print("[DEBUG] Discount elements loaded")



    # Search for Set of Discounts for chosen category:    
    try:
        discount_elements = driver.find_elements(By.CSS_SELECTOR, "div.col-12.col-md-3.mb-4")[:MAX_DISCOUNTS]
        print(f"[+] Found {len(discount_elements)} discount(s).")
    except NoSuchElementException:
        print("[-] No discount cards found.")
        return []

    # Saving set of discounts to go through each one:
    discount_links = []
    for elem in discount_elements:
        try:
            href = elem.find_element(By.TAG_NAME, "a").get_attribute("href")
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

            # --- Discount Link ---
            full_link = link if link.startswith("http") else BASE_URL_ADIF + link
            #print(f"[🔗] Trying to open link: {full_link}")

            try:
                driver.get(full_link)
                time.sleep(2.5)  # Allow page and possible popup to load
                #print("[✓] Page loaded successfully")
            except Exception as e:
                print(f"[!] Error loading discount page: {type(e).__name__}: {e}")
                continue  # Skip this discount
            
            # --- Title (Adif: supports multiple layouts) ---
            try:
                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, ".name-price-coupon .title")
                    #print("[DEBUG] Title found in .name-price-coupon .title")
                except NoSuchElementException:
                    title_element = driver.find_element(By.CSS_SELECTOR, ".blockA .title")
                    #print("[DEBUG] Title found in .blockA .title")

                title = title_element.text.strip()
                print("[+] Title Found")
            except NoSuchElementException:
                title = "N/A"
                print("[-] No Title Element Found in any known structure")
            except Exception as e:
                title = "N/A"
                print(f"[!] Error while extracting title: {type(e).__name__}: {e}")


            # Image Link
            try:
                img_tag = driver.find_element(By.CSS_SELECTOR, ".watermarked-image img")
                image_link = img_tag.get_attribute("src").strip()
                print(f"[+] Image Link Found")
            except NoSuchElementException:
                image_link = "N/A"
                print("[-] No Image Link Found")
            except Exception as e:
                image_link = "N/A"
                print(f"[!] Error while extracting image link: {type(e).__name__}: {e}")

            # Description
            try:
                description_parts = []

                # ננסה קודם את description ואם לא נמצא ננסה את desc
                try:
                    desc_wrapper = driver.find_element(By.CLASS_NAME, "description")
                    #print("[DEBUG] Found .description block")
                except NoSuchElementException:
                    desc_wrapper = driver.find_element(By.CLASS_NAME, "desc")
                    #print("[DEBUG] Found .desc block instead")

                paragraphs = desc_wrapper.find_elements(By.TAG_NAME, "p")
                for p in paragraphs:
                    text = p.text.strip()
                    if text:
                        description_parts.append(text)

                description = "\n".join(description_parts)

                if description:
                    print("[+] Description Found:")
                else:
                    description = "N/A"
                    print("[-] Description block found but empty")
            except NoSuchElementException:
                description = "N/A"
                print("[-] No Description Block Found (.description or .desc)")
            except Exception as e:
                description = "N/A"
                print(f"[!] Error while extracting description: {type(e).__name__}: {e}")

            # Terms and Conditions
            try:
                accordion_blocks = driver.find_elements(By.CSS_SELECTOR, "div.accordion-tab-content")
                #print(f"[DEBUG] Found {len(accordion_blocks)} accordion block(s)")

                terms_parts = []
                for block in accordion_blocks:
                    # Get all text from inside the block including nested spans etc.
                    raw_html = block.get_attribute("innerText").strip()
                    if raw_html:
                        terms_parts.append(raw_html)

                if terms_parts:
                    terms = "\n\n".join(terms_parts)
                    print(f"[+] Terms And Conditions Found")
                else:
                    terms = "N/A"
                    print("[-] Accordion blocks found but no terms text inside")
            except Exception as e:
                terms = "N/A"
                print(f"[!] Error extracting terms: {type(e).__name__}: {e}")

            # Price:
            price = "N/A"
            try:
                price_element = driver.find_element(By.CLASS_NAME, "price-num")
                price = price_element.text.strip()
                print(f"[+] Price Found")
            except NoSuchElementException:
                #print("[-] Price element not found — checking fallback")
                price = extract_price_fallback(description, terms)
                if price != "N/A":
                    print(f"[+] Price Found")
                else:
                    print("[-] No price found - even in fallback")


            # Price Type
            price_type = classify_price_type(price)


            # Extract from combined description and terms
            combined_text = f"{description}\n{terms}"

            # Due Date
            valid_until = extract_valid_until(combined_text)
            
            # Discount Code
            coupon_code = extract_coupon_code(combined_text)

            # Provider's link:  
            provider_link = "N/A"
            try:
                # Try locating the block (either .desc or .description)
                try:
                    desc_block = driver.find_element(By.CLASS_NAME, "desc")
                except NoSuchElementException:
                    desc_block = driver.find_element(By.CLASS_NAME, "description")

                p_tags = desc_block.find_elements(By.TAG_NAME, "p")

                for p in p_tags:
                    try:
                        a_tag = p.find_element(By.TAG_NAME, "a")
                        href = a_tag.get_attribute("href")
                        if href and href.strip():
                            provider_link = href
                            print(f"[+] Provider Link Found: {provider_link}")
                            break  # Stop after the first valid one
                    except NoSuchElementException:
                        continue

                if provider_link == "N/A":
                    print("[-] No <a> tag with href found inside <p> in description block")
            except NoSuchElementException:
                print("[-] No description block found for provider link search")



            # Placeholder for rest
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
                "provider_link": provider_link,
                
                "coupon_code": coupon_code,
                "valid_until": valid_until,

                "usage_limit": AMOUNT,
                "location": LOCATION
            })
            extract_discounts_for_category.counter += 1

        # If got here - wasn't able to scrape the discount:
        except Exception as e:
            print(f"[!] Error scraping discount #{i+1}: {e}")

    # return total discounts:
    return discounts
