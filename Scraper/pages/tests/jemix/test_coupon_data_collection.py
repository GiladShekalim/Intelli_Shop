"""
Test module for comprehensive coupon data collection from Jemix.

This module collects all coupon information from every category and provider
on the Jemix website, following the specified JSON schema structure.
"""

import unittest
import platform
import os
import tempfile
import json
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

from Scraper.pages.jemix.CategoryPage import CategoryPage
from Scraper.pages.jemix.ProviderPage import ProviderPage
from Scraper.config.settings import PAGES

class TestCouponDataCollection(unittest.TestCase):
    """Test suite for comprehensive coupon data collection from Jemix."""
    
    # JSON Schema for coupon data validation
    JSON_SCHEMA = {
        "discount_id": "string",
        "title": "string", 
        "price": "integer",
        "discount_type": "enum",
        "description": "string",
        "image_link": "string",
        "discount_link": "string",
        "terms_and_conditions": "string",
        "club_name": ["string"],
        "category": ["string"],
        "valid_until": "string",
        "usage_limit": "integer",
        "coupon_code": "string",
        "provider_link": "string",
        "consumer_statuses": ["string"],
        "favorites": ["string"]
    }
    
    @classmethod
    def setUpClass(cls):
        """Class-level setup - runs once before all tests."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.user_data_dir = os.path.join(cls.temp_dir, "chrome_test_profile")
        cls.all_coupons = []
        cls.collection_stats = {
            "total_categories": 0,
            "total_providers": 0,
            "total_coupons": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "categories_processed": [],
            "providers_processed": []
        }

    def setUp(self):
        """Method-level setup - runs before each test method."""
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Use headless mode in WSL or CI environments
            if platform.system() == "Linux" and "microsoft" in platform.uname().release.lower():
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--headless=new")

            # Initialize Chrome driver with automatic ChromeDriver management
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
        except Exception as e:
            raise

    def validate_coupon_schema(self, coupon_data):
        """Validate coupon data against the JSON schema"""
        required_fields = [
            "discount_id", "title", "price", "discount_type", "description",
            "image_link", "discount_link", "terms_and_conditions", "club_name",
            "category", "valid_until", "usage_limit", "coupon_code", 
            "provider_link", "consumer_statuses", "favorites"
        ]
        
        for field in required_fields:
            if field not in coupon_data:
                return False, f"Missing required field: {field}"
        
        # Validate data types
        if not isinstance(coupon_data["discount_id"], str):
            return False, "discount_id must be string"
        if not isinstance(coupon_data["price"], int):
            return False, "price must be integer"
        if not isinstance(coupon_data["usage_limit"], int):
            return False, "usage_limit must be integer"
        if not isinstance(coupon_data["club_name"], list):
            return False, "club_name must be list"
        if not isinstance(coupon_data["category"], list):
            return False, "category must be list"
        if not isinstance(coupon_data["consumer_statuses"], list):
            return False, "consumer_statuses must be list"
        if not isinstance(coupon_data["favorites"], list):
            return False, "favorites must be list"
        
        return True, "Valid"

    def collect_coupons_from_category(self, category_name, category_url):
        """Collect all coupons from a specific category"""
        print(f"\nProcessing category: {category_name}")
        
        try:
            # Initialize category page
            category_page = CategoryPage(self.driver, category_url, category_name)
            category_page.navigate_to_category()
            
            # Get all provider links from the category
            providers = category_page.get_provider_links()
            print(f"Found {len(providers)} providers in {category_name}")
            
            self.collection_stats["total_providers"] += len(providers)
            self.collection_stats["categories_processed"].append(category_name)
            
            # Process each provider
            for provider in providers:
                try:
                    print(f"  Processing provider: {provider['name']}")
                    
                    # Initialize provider page
                    provider_page = ProviderPage(
                        self.driver, 
                        provider['url'], 
                        category_name
                    )
                    
                    # Extract coupon data
                    coupon_data = provider_page.extract_coupon_data()
                    
                    # Validate schema
                    is_valid, validation_message = self.validate_coupon_schema(coupon_data)
                    
                    if is_valid:
                        self.all_coupons.append(coupon_data)
                        self.collection_stats["successful_extractions"] += 1
                        self.collection_stats["providers_processed"].append(provider['name'])
                        print(f"    ✓ Successfully extracted coupon data")
                    else:
                        print(f"    ✗ Schema validation failed: {validation_message}")
                        self.collection_stats["failed_extractions"] += 1
                    
                    self.collection_stats["total_coupons"] += 1
                    
                except Exception as e:
                    print(f"    ✗ Error processing provider {provider['name']}: {str(e)}")
                    self.collection_stats["failed_extractions"] += 1
                    continue
            
        except Exception as e:
            print(f"Error processing category {category_name}: {str(e)}")

    def test_comprehensive_coupon_collection(self):
        """Test comprehensive collection of all coupon data from Jemix"""
        try:
            print("Starting comprehensive coupon data collection...")
            
            # Process each category
            for page in PAGES:
                if 'tag' in page['url']:  # Only process category pages
                    self.collection_stats["total_categories"] += 1
                    self.collect_coupons_from_category(page['name'], page['url'])
            
            # Generate final JSON output
            self.generate_coupon_json()
            
            # Print collection statistics
            self.print_collection_stats()
            
            # Assertions
            self.assertGreater(len(self.all_coupons), 0, "No coupons were collected")
            self.assertGreater(self.collection_stats["successful_extractions"], 0, "No successful extractions")
            
        except Exception as e:
            raise

    def generate_coupon_json(self):
        """Generate JSON file with all collected coupon data"""
        output_data = {
            "metadata": {
                "collection_date": datetime.now().isoformat(),
                "total_coupons": len(self.all_coupons),
                "source": "Jemix",
                "schema_version": "1.0"
            },
            "coupons": self.all_coupons
        }
        
        # Write to file
        output_file = "jemix_coupons_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nCoupon data saved to: {output_file}")

    def print_collection_stats(self):
        """Print collection statistics"""
        print("\n" + "="*50)
        print("COLLECTION STATISTICS")
        print("="*50)
        print(f"Total Categories Processed: {self.collection_stats['total_categories']}")
        print(f"Total Providers Found: {self.collection_stats['total_providers']}")
        print(f"Total Coupons Attempted: {self.collection_stats['total_coupons']}")
        print(f"Successful Extractions: {self.collection_stats['successful_extractions']}")
        print(f"Failed Extractions: {self.collection_stats['failed_extractions']}")
        print(f"Success Rate: {(self.collection_stats['successful_extractions']/max(self.collection_stats['total_coupons'], 1)*100):.1f}%")
        
        print(f"\nCategories Processed:")
        for category in self.collection_stats['categories_processed']:
            print(f"  - {category}")
        
        print(f"\nProviders Processed:")
        for provider in self.collection_stats['providers_processed']:
            print(f"  - {provider}")

    def tearDown(self):
        """Method-level cleanup - runs after each test method."""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        """Class-level cleanup - runs once after all tests."""
        import shutil
        try:
            shutil.rmtree(cls.temp_dir, ignore_errors=True)
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main() 