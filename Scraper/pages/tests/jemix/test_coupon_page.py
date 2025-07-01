#!/usr/bin/env python3
"""
Test script for CouponPage functionality
Tests the extraction of coupon codes and provider links from various page structures
"""

import sys
import os
import time
import uuid

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.jemix.CouponPage import CouponPage
import json

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def test_coupon_extraction():
    """Test the CouponPage extraction functionality with anti-bot measures"""
    driver = None
    try:
        driver = setup_driver()
        
        # Test multiple coupon pages to ensure robustness
        test_urls = [
            "https://www.jemix.co.il/ho-coupon/",
            "https://www.jemix.co.il/addict-coupon/",
            "https://www.jemix.co.il/reserved-coupon/"
        ]
        
        coupon_page = CouponPage(driver)
        
        for i, test_url in enumerate(test_urls, 1):
            print(f"\n{'='*60}")
            print(f"TEST {i}: {test_url}")
            print(f"{'='*60}")
            
            try:
                # Extract coupon data
                result = coupon_page.extract_coupon_data(test_url)
                
                print(f"Coupon Code: {result['coupon_code']}")
                print(f"Provider Link: {result['provider_link']}")
                
                if result['warnings']:
                    print(f"Warnings: {result['warnings']}")
                
                # Validate the results
                required_fields = [
                    'discount_id', 'title', 'price', 'discount_type', 'description',
                    'image_link', 'discount_link', 'terms_and_conditions', 'club_name',
                    'category', 'coupon_code', 'provider_link', 'valid_until',
                    'usage_limit', 'source_url', 'consumer_statuses'
                ]
                
                for field in required_fields:
                    assert field in result, f"Missing required field: {field}"
                
                # Validate specific field types
                assert 'discount_id' in result, "Missing 'discount_id' in result!"
                try:
                    uuid.UUID(result['discount_id'])
                except Exception:
                    raise AssertionError(f"discount_id is not a valid UUID: {result['discount_id']}")
                
                assert isinstance(result['price'], int), f"Price must be integer, got: {type(result['price'])}"
                assert isinstance(result['usage_limit'], int), f"Usage limit must be integer, got: {type(result['usage_limit'])}"
                assert isinstance(result['club_name'], list), f"Club name must be list, got: {type(result['club_name'])}"
                assert isinstance(result['category'], list), f"Category must be list, got: {type(result['category'])}"
                assert isinstance(result['consumer_statuses'], list), f"Consumer statuses must be list, got: {type(result['consumer_statuses'])}"
                
                if result['coupon_code'] == "NO_CODE":
                    print("⚠️ No coupon code found")
                elif result['coupon_code'] == "html":
                    print("❌ Still extracting 'html' - anti-bot measures needed")
                else:
                    print(f"✅ Successfully extracted: {result['coupon_code']}")
                
                if result['provider_link'] and result['provider_link'] != "NO_LINK":
                    print(f"✅ Provider link found: {result['provider_link']}")
                else:
                    print("⚠️ No provider link found")
                    
            except Exception as e:
                print(f"❌ Error testing {test_url}: {str(e)}")
        
        # Test specific anti-bot extraction methods
        print(f"\n{'='*60}")
        print("TESTING ANTI-BOT EXTRACTION METHODS")
        print(f"{'='*60}")
        
        # Test with the H&O coupon page specifically
        test_url = "https://www.jemix.co.il/ho-coupon/"
        coupon_page.driver.get(test_url)
        time.sleep(2)
        
        # Test meta tag extraction
        print("\n1. Testing Meta Tag Extraction:")
        meta_result = coupon_page._extract_coupon_code_from_meta()
        print(f"   Result: {meta_result}")
        
        # Test text pattern extraction
        print("\n2. Testing Text Pattern Extraction:")
        page_text = coupon_page.driver.page_source
        text_result = coupon_page._find_coupon_code_in_text(page_text)
        print(f"   Result: {text_result}")
        
        # Test element search
        print("\n3. Testing Element Search:")
        element_result = coupon_page._find_coupon_code_in_elements()
        print(f"   Result: {element_result}")
        
        # Test copy button extraction
        print("\n4. Testing Copy Button Extraction:")
        copy_result = coupon_page._extract_coupon_code_via_copy_button()
        print(f"   Result: {copy_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_coupon_extraction()
    if success:
        print("\n🎉 All tests completed!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1) 