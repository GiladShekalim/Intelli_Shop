#!/usr/bin/env python3
"""
Test script to verify coupon code extraction fix
Tests that the new CouponPage properly extracts coupon codes instead of "html"
"""

import sys
import os
import time
import uuid

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

def test_coupon_extraction_fix():
    """Test the enhanced coupon extraction with anti-bot measures"""
    driver = None
    try:
        driver = setup_driver()
        
        # Test URL - this should be a real Jemix coupon page
        test_url = "https://www.jemix.co.il/ho-coupon/"
        
        print(f"Testing coupon extraction from: {test_url}")
        
        # Create CouponPage instance
        coupon_page = CouponPage(driver)
        
        # Extract coupon data
        result = coupon_page.extract_coupon_data(test_url)
        
        print("\n=== EXTRACTION RESULTS ===")
        print(f"Coupon Code: {result['coupon_code']}")
        print(f"Provider Link: {result['provider_link']}")
        print(f"Warnings: {result['warnings']}")
        
        # Validate results
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
        
        assert result['coupon_code'] != "NO_CODE", f"Failed to extract coupon code. Warnings: {result['warnings']}"
        assert result['coupon_code'] != "html", "Extracted 'html' instead of actual coupon code"
        assert len(result['coupon_code']) >= 3, f"Coupon code too short: {result['coupon_code']}"
        
        print(f"\n✅ SUCCESS: Extracted coupon code '{result['coupon_code']}' successfully!")
        
        # Test meta tag extraction specifically
        print("\n=== TESTING META TAG EXTRACTION ===")
        meta_result = coupon_page._extract_coupon_code_from_meta()
        print(f"Meta extraction result: {meta_result}")
        
        if meta_result and meta_result != "NO_CODE":
            print(f"✅ Meta tag extraction successful: {meta_result}")
        else:
            print("⚠️ Meta tag extraction did not find coupon code")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = test_coupon_extraction_fix()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1) 