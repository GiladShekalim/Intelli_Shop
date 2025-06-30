import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from Scraper.pages.jemix.ProviderPage import ProviderPage
from Scraper.pages.jemix.CategoryPage import CategoryPage
from Scraper.config.settings import *

class ComprehensiveCouponExtractionTest:
    """Comprehensive test for extracting all coupon data from Jemix"""
    
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = None
        self.provider_page = None
        self.category_page = None
        self.extracted_data = []
        self.test_results = {
            "total_providers_tested": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "missing_fields_summary": {},
            "extraction_warnings": [],
            "test_duration": 0
        }
    
    def setup_driver(self):
        """Initialize the web driver"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.provider_page = ProviderPage(self.driver)
            self.category_page = CategoryPage(self.driver)
            print("✅ Driver setup successful")
            return True
        except Exception as e:
            print(f"❌ Driver setup failed: {str(e)}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive coupon extraction test"""
        start_time = time.time()
        
        if not self.setup_driver():
            return False
        
        try:
            print("🚀 Starting comprehensive coupon extraction test...")
            
            # Test all categories
            categories = [
                "fashion", "food", "electronics", "home", "beauty", "sports"
            ]
            
            for category in categories:
                print(f"\n📂 Testing category: {category}")
                self.test_category_extraction(category)
            
            # Generate comprehensive report
            self.generate_extraction_report()
            
            self.test_results["test_duration"] = time.time() - start_time
            print(f"\n⏱️  Test completed in {self.test_results['test_duration']:.2f} seconds")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def test_category_extraction(self, category_name):
        """Test extraction for a specific category"""
        try:
            category_url = f"https://www.jemix.co.il/tag/{category_name}/"
            self.driver.get(category_url)
            
            # Get all provider links in this category
            provider_links = self.category_page.get_provider_links()
            
            print(f"   Found {len(provider_links)} providers in {category_name}")
            
            for i, provider_url in enumerate(provider_links[:5]):  # Test first 5 providers per category
                print(f"   Testing provider {i+1}/{min(5, len(provider_links))}: {provider_url}")
                
                try:
                    coupon_data = self.provider_page.extract_coupon_data(provider_url, category_name)
                    
                    if coupon_data:
                        self.extracted_data.append(coupon_data)
                        self.test_results["successful_extractions"] += 1
                        print(f"   ✅ Successfully extracted data")
                    else:
                        self.test_results["failed_extractions"] += 1
                        print(f"   ❌ Failed to extract data")
                        
                except Exception as e:
                    self.test_results["failed_extractions"] += 1
                    self.test_results["extraction_warnings"].append(f"Error with {provider_url}: {str(e)}")
                    print(f"   ❌ Error: {str(e)}")
                
                self.test_results["total_providers_tested"] += 1
                
                # Small delay to be respectful to the server
                time.sleep(1)
                
        except Exception as e:
            print(f"   ❌ Category {category_name} failed: {str(e)}")
    
    def generate_extraction_report(self):
        """Generate comprehensive extraction report"""
        print("\n📊 Generating comprehensive extraction report...")
        
        # Get extraction warnings and missing fields
        extraction_report = self.provider_page.get_extraction_report()
        
        # Analyze missing fields
        missing_fields_count = {}
        for missing_instance in extraction_report["missing_fields"]:
            for field in missing_instance["missing_fields"]:
                missing_fields_count[field] = missing_fields_count.get(field, 0) + 1
        
        self.test_results["missing_fields_summary"] = missing_fields_count
        self.test_results["extraction_warnings"].extend(extraction_report["warnings"])
        
        # Print summary
        print(f"\n EXTRACTION SUMMARY:")
        print(f"   Total providers tested: {self.test_results['total_providers_tested']}")
        print(f"   Successful extractions: {self.test_results['successful_extractions']}")
        print(f"   Failed extractions: {self.test_results['failed_extractions']}")
        print(f"   Success rate: {(self.test_results['successful_extractions']/self.test_results['total_providers_tested']*100):.1f}%")
        
        print(f"\n⚠️  MISSING FIELDS SUMMARY:")
        for field, count in missing_fields_count.items():
            percentage = (count / self.test_results['total_providers_tested']) * 100
            print(f"   {field}: {count} times ({percentage:.1f}%)")
        
        print(f"\n🚨 EXTRACTION WARNINGS ({len(self.test_results['extraction_warnings'])} total):")
        for warning in self.test_results['extraction_warnings'][:10]:  # Show first 10 warnings
            print(f"   - {warning}")
        
        if len(self.test_results['extraction_warnings']) > 10:
            print(f"   ... and {len(self.test_results['extraction_warnings']) - 10} more warnings")
        
        # Save detailed results
        self.save_test_results()
    
    def save_test_results(self):
        """Save test results to file"""
        results = {
            "test_results": self.test_results,
            "extracted_data": self.extracted_data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        filename = f"comprehensive_coupon_extraction_results_{int(time.time())}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"\n❌ Failed to save results: {str(e)}")

def main():
    """Main test execution"""
    test = ComprehensiveCouponExtractionTest()
    success = test.run_comprehensive_test()
    
    if success:
        print("\n🎉 Comprehensive coupon extraction test completed successfully!")
    else:
        print("\n💥 Comprehensive coupon extraction test failed!")
    
    return success

if __name__ == "__main__":
    main() 