# main.py
import json
from pathlib import Path

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

    # Determine the central data directory (../mysite/intellishop/data)
    webpage_root = Path(__file__).resolve().parent.parent  # .. / WebpageTest
    data_dir = webpage_root / "mysite" / "intellishop" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Map scrape target → output file inside the data directory
    output_file_map = {
        "hot": data_dir / "hot_discounts.json",
        "adif": data_dir / "adif_discounts.json",
        "both": data_dir / "all_discounts.json",
    }
    output_file = output_file_map.get(SCRAPE_TARGET, data_dir / "discounts.json")

    # Save the results
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_discounts, f, ensure_ascii=False, indent=2)

    print(f"\n[✔] Scraping complete. Results saved to {output_file}")


if __name__ == "__main__":
    main()
