# define a base class for all provider pages

#from Scraper.pages.jemix.ProviderPage import ProviderPage

# Example usage for a specific provider
#provider_page = ProviderPage(driver, "https://www.jemix.co.il/feetfun-coupon/")
#provider_page.navigate_to_provider()
#coupons = provider_page.get_coupon_list("coupon-class")  # Replace with actual class name
#provider_page.click_coupon("Specific Coupon Text")
#details = provider_page.get_coupon_details("detail-class")  # Replace with actual class name
#provider_page.apply_coupon("COUPON2025")




from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from Scraper.pages.base.BasePage import BasePage
from Scraper.pages.jemix.CouponPage import CouponPage
import uuid
import re
from datetime import datetime
import json
import time

class ProviderPage(BasePage):
    """Enhanced provider page with comprehensive coupon data extraction"""
    
    # Updated locators based on actual Jemix structure
    TITLE_LOCATORS = [
        "//h1[contains(@class, 'elementor-heading-title')]",
        "//h2[contains(@class, 'elementor-heading-title')]",
        "//h1",
        "//h2"
    ]
    
    PRICE_LOCATORS = [
        "//p[contains(@class, 'elementor-heading-title') and contains(text(), '₪')]",
        "//p[contains(text(), '₪')]",
        "//span[contains(text(), '₪')]",
        "//div[contains(text(), '₪')]"
    ]
    
    DESCRIPTION_LOCATORS = [
        "//div[contains(@class, 'elementor-widget-text-editor')]//p",
        "//div[contains(@class, 'elementor-widget-container')]//p",
        "//section[contains(@class, 'elementor-section')]//p"
    ]
    
    IMAGE_LOCATORS = [
        "//img[contains(@class, 'attachment-large')]",
        "//img[contains(@src, 'wp-content/uploads')]",
        "//img[contains(@alt, 'logo')]",
        "//img[contains(@class, 'wp-image-')]"
    ]
    
    DISCOUNT_LINK_LOCATORS = [
        "//a[contains(text(), 'קבלו קוד')]",
        "//a[contains(text(), 'עברו להטבה')]",
        "//a[contains(@class, 'elementor-button')]",
        "//div[@id='coupon']//a"
    ]
    
    TERMS_LOCATORS = [
        "//div[contains(@class, 'elementor-widget-text-editor')]//p[contains(text(), 'תנאים')]",
        "//p[contains(text(), 'תנאים')]",
        "//div[contains(text(), 'תנאים')]"
    ]
    
    def __init__(self, driver, provider_url=None, category_name=None, provider_name=None):
        super().__init__(driver)
        self.provider_url = provider_url
        self.category_name = category_name
        self.provider_name = provider_name
        self.extraction_warnings = []
    
    def extract_coupon_data(self, provider_url=None, category_name=None):
        """Extract comprehensive coupon data from provider page"""
        if provider_url:
            self.provider_url = provider_url
            self.driver.get(provider_url)
            time.sleep(2)  # Wait for page to load
            
        if category_name:
            self.category_name = category_name
            
        try:
            # Extract basic information
            title = self._extract_title()
            price = self._extract_price()
            description = self._extract_description()
            image = self._extract_image()
            discount_link = self._extract_discount_link()
            terms = self._extract_terms()
            provider_name = self._extract_provider_name()
            expiry_date = self._extract_expiry_date()
            usage_limit = self._extract_usage_limit()
            discount_type = self._extract_discount_type()
            consumer_statuses = self._extract_consumer_statuses()
            
            # Extract coupon code data if discount link is available
            coupon_code_data = None
            if discount_link and discount_link != "NO_LINK":
                coupon_code_data = self._extract_coupon_code_data(discount_link)
            
            return {
                'discount_id': str(uuid.uuid4()),
                'title': title,
                'price': int(price.replace('₪', '').replace(',', '')) if isinstance(price, str) and price != 'NO_PRICE' else 0,
                'discount_type': discount_type,
                'description': description,
                'image_link': image,
                'discount_link': discount_link,
                'terms_and_conditions': terms,
                'club_name': ['Jemix'],
                'category': [self.category_name] if self.category_name else ['Unknown'],
                'coupon_code': coupon_code_data.get('coupon_code', 'NO_CODE') if coupon_code_data else 'NO_CODE',
                'provider_link': coupon_code_data.get('provider_link', 'NO_LINK') if coupon_code_data else 'NO_LINK',
                'valid_until': expiry_date,
                'usage_limit': int(usage_limit) if isinstance(usage_limit, str) and usage_limit != 'NO_LIMIT' else 1,
                'source_url': self.provider_url or 'NO_URL',
                'consumer_statuses': consumer_statuses,
                'warnings': self.extraction_warnings
            }
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in provider extraction: {str(e)}")
            return {
                'discount_id': str(uuid.uuid4()),
                'title': 'NO_TITLE',
                'price': 0,
                'discount_type': 'NO_TYPE',
                'description': 'NO_DESCRIPTION',
                'image_link': 'NO_IMAGE',
                'discount_link': 'NO_LINK',
                'terms_and_conditions': 'NO_TERMS',
                'club_name': ['Jemix'],
                'category': [self.category_name] if self.category_name else ['Unknown'],
                'coupon_code': 'NO_CODE',
                'provider_link': 'NO_LINK',
                'valid_until': 'NO_EXPIRY',
                'usage_limit': 1,
                'source_url': self.provider_url or 'NO_URL',
                'consumer_statuses': [],
                'warnings': self.extraction_warnings
            }
    
    def _extract_title(self):
        """Extract title from the page"""
        try:
            for xpath in self.TITLE_LOCATORS:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    title = element.text.strip()
                    if title and title != "NO_TITLE":
                        return title
                except NoSuchElementException:
                    continue
            return "NO_TITLE"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting title: {str(e)}")
            return "NO_TITLE"
    
    def _extract_price(self):
        """Extract price information"""
        try:
            for xpath in self.PRICE_LOCATORS:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    price = element.text.strip()
                    if price and '₪' in price:
                        return price
                except NoSuchElementException:
                    continue
            return "NO_PRICE"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting price: {str(e)}")
            return "NO_PRICE"
    
    def _extract_description(self):
        """Extract description from the page"""
        try:
            for xpath in self.DESCRIPTION_LOCATORS:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        desc = element.text.strip()
                        if desc and len(desc) > 10:
                            return desc
                except NoSuchElementException:
                    continue
            return "NO_DESCRIPTION"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting description: {str(e)}")
            return "NO_DESCRIPTION"
    
    def _extract_image(self):
        """Extract image URL"""
        try:
            for xpath in self.IMAGE_LOCATORS:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    src = element.get_attribute('src')
                    if src and 'wp-content/uploads' in src:
                        return src
                except NoSuchElementException:
                    continue
            return "NO_IMAGE"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting image: {str(e)}")
            return "NO_IMAGE"
    
    def _extract_discount_link(self):
        """Extract discount link"""
        try:
            for xpath in self.DISCOUNT_LINK_LOCATORS:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    href = element.get_attribute('href')
                    if href and href.startswith('http'):
                        return href
                except NoSuchElementException:
                    continue
            return "NO_LINK"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting discount link: {str(e)}")
            return "NO_LINK"
    
    def _extract_terms(self):
        """Extract terms and conditions"""
        try:
            for xpath in self.TERMS_LOCATORS:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    terms = element.text.strip()
                    if terms and 'תנאים' in terms:
                        return terms
                except NoSuchElementException:
                    continue
            return "NO_TERMS"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting terms: {str(e)}")
            return "NO_TERMS"
    
    def _extract_provider_name(self):
        """Extract provider name"""
        try:
            # Try to extract from title
            title = self._extract_title()
            if title and title != "NO_TITLE":
                # Extract provider name from title (usually before the first separator)
                provider_name = title.split('|')[0].split('-')[0].strip()
                if provider_name:
                    return provider_name
            
            # Try to extract from URL
            if self.provider_url:
                url_parts = self.provider_url.split('/')
                for part in url_parts:
                    if part and part != 'www.jemix.co.il' and part != 'jemix.co.il':
                        return part.replace('-', ' ').title()
            
            return "NO_PROVIDER"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting provider name: {str(e)}")
            return "NO_PROVIDER"
    
    def _extract_expiry_date(self):
        """Extract expiry date"""
        try:
            # Look for date patterns in the page
            page_text = self.driver.page_source
            date_patterns = [
                r'(\d{1,2}/\d{1,2}/\d{4})',  # DD/MM/YYYY
                r'(\d{1,2}-\d{1,2}-\d{4})',  # DD-MM-YYYY
                r'(\d{4}-\d{1,2}-\d{1,2})',  # YYYY-MM-DD
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    return matches[0]
            
            return "NO_EXPIRY"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting expiry date: {str(e)}")
            return "NO_EXPIRY"
    
    def _extract_usage_limit(self):
        """Extract usage limit information"""
        try:
            page_text = self.driver.page_source
            limit_patterns = [
                r'(\d+)\s*פעמים',  # Hebrew: X times
                r'(\d+)\s*times',   # English: X times
                r'(\d+)\s*שימושים', # Hebrew: X uses
            ]
            
            for pattern in limit_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    return matches[0]
            
            return "NO_LIMIT"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting usage limit: {str(e)}")
            return "NO_LIMIT"
    
    def _extract_coupon_code_data(self, discount_link):
        """Extract coupon code data from the discount link page"""
        try:
            # Navigate to the discount link page
            self.driver.get(discount_link)
            time.sleep(2)
            
            # Use the enhanced CouponPage to extract coupon data
            from .CouponPage import CouponPage
            coupon_page = CouponPage(self.driver)
            coupon_data = coupon_page.extract_coupon_data()
            
            return {
                'coupon_code': coupon_data.get('coupon_code', 'NO_CODE'),
                'provider_link': coupon_data.get('provider_link', 'NO_LINK')
            }
            
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting coupon code data: {str(e)}")
            return {
                'coupon_code': 'NO_CODE',
                'provider_link': 'NO_LINK'
            }
    
    def _report_missing_fields(self, coupon_data):
        """Report which fields are missing from the extraction"""
        missing_fields = []
        for field, value in coupon_data.items():
            if value in ['NO_TITLE', 'NO_PRICE', 'NO_DESCRIPTION', 'NO_IMAGE', 'NO_LINK', 'NO_TERMS', 'NO_PROVIDER', 'NO_EXPIRY', 'NO_LIMIT', 'NO_TYPE', 'NO_CODE']:
                missing_fields.append(field)
        
        if missing_fields:
            self.extraction_warnings.append(f"Missing fields: {', '.join(missing_fields)}")
        
        return missing_fields
    
    def get_extraction_report(self):
        """Get a comprehensive extraction report"""
        return {
            'warnings': self.extraction_warnings,
            'provider_url': self.provider_url,
            'category_name': self.category_name
        }
    
    def navigate_to_provider(self):
        """Navigate to the provider's website"""
        try:
            if self.provider_url:
                self.driver.get(self.provider_url)
                return True
        except Exception as e:
            self.extraction_warnings.append(f"Error navigating to provider: {str(e)}")
            return False
    
    def get_coupon_list(self, coupon_class_name):
        """Retrieve a list of coupon elements by class name"""
        try:
            elements = self.driver.find_elements(By.CLASS_NAME, coupon_class_name)
            return elements
        except Exception as e:
            self.extraction_warnings.append(f"Error getting coupon list: {str(e)}")
            return []
    
    def click_coupon(self, coupon_text):
        """Click a specific coupon by its text"""
        try:
            element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{coupon_text}')]")
            element.click()
            return True
        except Exception as e:
            self.extraction_warnings.append(f"Error clicking coupon: {str(e)}")
            return False
    
    def get_coupon_details(self, detail_class_name):
        """Retrieve details of a coupon, such as description or discount"""
        try:
            element = self.driver.find_element(By.CLASS_NAME, detail_class_name)
            return element.text
        except Exception as e:
            self.extraction_warnings.append(f"Error getting coupon details: {str(e)}")
            return None
    
    def apply_coupon(self, coupon_code):
        """Example method to apply a coupon code, assuming there's an input field"""
        try:
            # Find coupon input field
            input_field = self.driver.find_element(By.XPATH, "//input[@placeholder='קוד קופון' or @placeholder='Coupon Code']")
            input_field.clear()
            input_field.send_keys(coupon_code)
            
            # Find apply button
            apply_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'החל') or contains(text(), 'Apply')]")
            apply_button.click()
            
            return True
        except Exception as e:
            self.extraction_warnings.append(f"Error applying coupon: {str(e)}")
            return False
    
    def _extract_discount_type(self):
        """Extract discount type (percentage, fixed amount, etc.)"""
        try:
            page_text = self.driver.page_source
            
            # Look for percentage patterns
            percentage_patterns = [
                r'(\d+)%\s*הנחה',  # Hebrew: X% discount
                r'(\d+)%\s*discount',  # English: X% discount
                r'(\d+)%\s*off',  # English: X% off
            ]
            
            for pattern in percentage_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    return f"{matches[0]}% discount"
            
            # Look for fixed amount patterns
            amount_patterns = [
                r'(\d+)\s*₪\s*הנחה',  # Hebrew: X₪ discount
                r'(\d+)\s*₪\s*off',  # Hebrew: X₪ off
                r'(\d+)\s*shekel',  # English: X shekel
            ]
            
            for pattern in amount_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    return f"{matches[0]}₪ discount"
            
            return "NO_TYPE"
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting discount type: {str(e)}")
            return "NO_TYPE"
    
    def _extract_consumer_statuses(self):
        """Extract consumer statuses (new customers, existing customers, etc.)"""
        try:
            page_text = self.driver.page_source
            statuses = []
            
            # Look for customer status patterns
            status_patterns = [
                'לקוחות חדשים',  # New customers
                'לקוחות קיימים',  # Existing customers
                'new customers',
                'existing customers',
                'first time',
                'returning customers'
            ]
            
            for pattern in status_patterns:
                if pattern.lower() in page_text.lower():
                    statuses.append(pattern)
            
            return statuses
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting consumer statuses: {str(e)}")
            return []
