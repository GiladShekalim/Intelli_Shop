# main.py
import json
from utils.browser import setup_driver
from scrapers.hot_scraper import scrape_hot
from scrapers.adif_scraper import scrape_adif
from config import SCRAPE_TARGET

def main():
    print(f"[*] Scraping from {SCRAPE_TARGET}")
    driver = setup_driver()
    #results = scrape_hot(driver)

    all_discounts = []

    # Mapping scrape sources to functions
    SCRAPE_FUNCTIONS = {
        "hot": scrape_hot,
        "adif": scrape_adif
    }

    # Define which sources to scrape
    sources_to_scrape = (
        ["hot", "adif"] if SCRAPE_TARGET == "both" 
        else [SCRAPE_TARGET] if SCRAPE_TARGET in SCRAPE_FUNCTIONS 
        else []
    )

    for source in sources_to_scrape:
        print(f"[*] Scraping {source.upper()}...")
        all_discounts.extend(SCRAPE_FUNCTIONS[source](driver))

    driver.quit()

    # Define output filename
    output_file_map = {
        "hot": "output/hot_discounts.json",
        "adif": "output/adif_discounts.json",
        "both": "output/all_discounts.json"
    }
    output_file = output_file_map.get(SCRAPE_TARGET, "output/discounts.json")

    # ✅ Validate output structure before saving
    assert isinstance(all_discounts, list), "[!] Output is not a list!"

    for i, discount in enumerate(all_discounts):
        if not isinstance(discount, dict):
            print(f"[!] Warning: Discount #{i} is not a dictionary – skipping")
            continue
        for key in ["title", "price", "discount_link"]:
            if key not in discount:
                print(f"[!] Warning: Missing '{key}' in discount #{i}")

    # Save to file only if passed validation
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_discounts, f, ensure_ascii=False, indent=2)

    print(f"\n[✔] Scraping complete. Results saved to {output_file}")


if __name__ == "__main__":
    main()
