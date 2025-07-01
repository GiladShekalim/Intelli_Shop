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
import uuid
import re
from datetime import datetime
import json

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
        "//div[contains(@class, 'elementor-widget-container') and contains(., 'כיצד להשתמש')]",
        "//div[contains(@class, 'elementor-widget-text-editor') and contains(., 'שימוש')]",
        "//p[contains(text(), 'שימוש')]",
        "//div[contains(text(), 'תנאים')]"
    ]
    
    def __init__(self, driver, provider_url=None, category_name=None, provider_name=None):
        super().__init__(driver)
        self.provider_url = provider_url
        self.category_name = category_name
        self.provider_name = provider_name
        self.missing_fields = []
        self.extraction_warnings = []
    
    def extract_coupon_data(self, provider_url=None, category_name=None):
        """Extract comprehensive coupon data from provider page"""
        # Use instance variables if not provided as parameters
        provider_url = provider_url or self.provider_url
        category_name = category_name or self.category_name
        
        if not provider_url:
            raise ValueError("Provider URL is required")
        
        try:
            self.driver.get(provider_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract discount type from page content
            discount_type = self._extract_discount_type()
            
            coupon_data = {
                "discount_id": str(uuid.uuid4()),
                "title": self._extract_title(),
                "price": self._extract_price(),
                "discount_type": discount_type,
                "description": self._extract_description(),
                "image_link": self._extract_image(),
                "discount_link": self._extract_discount_link(),
                "terms_and_conditions": self._extract_terms(),
                "club_name": ["Jemix"],
                "coupon_code": None,  # Will be filled after redirect
                "provider_link": None,  # Will be filled after redirect
                "valid_until": self._extract_expiry_date(),
                "usage_limit": self._extract_usage_limit()
            }
            
            # Handle discount link redirect to get coupon code
            if coupon_data["discount_link"]:
                coupon_data.update(self._extract_coupon_code_data(coupon_data["discount_link"]))
            
            # Report missing fields
            self._report_missing_fields(coupon_data)
            
            return coupon_data
            
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting data from {provider_url}: {str(e)}")
            return None
    
    def _extract_title(self):
        """Extract coupon title with multiple fallback strategies"""
        for locator in self.TITLE_LOCATORS:
            try:
                element = self.driver.find_element(By.XPATH, locator)
                title = element.text.strip()
                if title and len(title) > 3:
                    return title
            except NoSuchElementException:
                continue
        
        # Fallback: extract from page title
        try:
            return self.driver.title.split('|')[0].strip()
        except:
            return "קופון"
    
    def _extract_price(self):
        """Extract price with number parsing - returns integer"""
        for locator in self.PRICE_LOCATORS:
            try:
                element = self.driver.find_element(By.XPATH, locator)
                price_text = element.text.strip()
                # Extract numeric value from price text
                price_match = re.search(r'(\d+(?:\.\d+)?)', price_text)
                if price_match:
                    return int(float(price_match.group(1)))
            except NoSuchElementException:
                continue
        return 0  # Return 0 instead of None to match schema requirements
    
    def _extract_description(self):
        """Extract description with content cleaning"""
        for locator in self.DESCRIPTION_LOCATORS:
            try:
                elements = self.driver.find_elements(By.XPATH, locator)
                descriptions = []
                for element in elements[:3]:  # Take first 3 paragraphs
                    text = element.text.strip()
                    if text and len(text) > 10:
                        descriptions.append(text)
                if descriptions:
                    return " ".join(descriptions)
            except NoSuchElementException:
                continue
        return "תיאור הקופון"  # Default description
    
    def _extract_image(self):
        """Extract image URL with fallbacks"""
        for locator in self.IMAGE_LOCATORS:
            try:
                element = self.driver.find_element(By.XPATH, locator)
                src = element.get_attribute('src')
                if src and 'wp-content/uploads' in src:
                    return src
            except NoSuchElementException:
                continue
        return "https://www.jemix.co.il/wp-content/uploads/2020/01/Logo-Jemix.jpg"  # Default image
    
    def _extract_discount_link(self):
        """Extract discount link with onclick handling"""
        for locator in self.DISCOUNT_LINK_LOCATORS:
            try:
                element = self.driver.find_element(By.XPATH, locator)
                href = element.get_attribute('href')
                onclick = element.get_attribute('onclick')
                
                if href:
                    return href
                elif onclick:
                    # Extract URL from onclick JavaScript
                    url_match = re.search(r"window\.open\('([^']+)'", onclick)
                    if url_match:
                        return url_match.group(1)
            except NoSuchElementException:
                continue
        return "https://www.jemix.co.il/"  # Default link
    
    def _extract_terms(self):
        """Extract terms and conditions"""
        for locator in self.TERMS_LOCATORS:
            try:
                element = self.driver.find_element(By.XPATH, locator)
                return element.text.strip()
            except NoSuchElementException:
                continue
        return "תנאים ותנאים חלים על הקופון"  # Default terms
    
    def _extract_provider_name(self):
        """Extract provider name from URL or page content"""
        if self.provider_name:
            return self.provider_name
            
        try:
            # Extract from URL
            url_parts = self.driver.current_url.split('/')
            for part in url_parts:
                if part and part != 'www.jemix.co.il' and part != 'tag':
                    return part.replace('-', ' ').title()
        except:
            pass
        return "Unknown Provider"
    
    def _extract_expiry_date(self):
        """Extract expiry date and convert to ISO format string"""
        try:
            # Look for date patterns in Hebrew
            date_patterns = [
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}-\d{1,2}-\d{4})',
                r'תוקף עד:?\s*(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            page_text = self.driver.page_source
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    date_str = match.group(1)
                    # Convert DD/MM/YYYY to ISO format YYYY-MM-DD
                    if '/' in date_str:
                        day, month, year = date_str.split('/')
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif '-' in date_str:
                        day, month, year = date_str.split('-')
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        return "2030-01-01"  # Default expiry date as per specification
    
    def _extract_usage_limit(self):
        """Extract usage limit information. Returns integer or 1 as default."""
        try:
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'שימוש') or contains(text(), 'usage')]")
            for element in elements:
                text = element.text
                if 'פעם' in text or 'times' in text:
                    # Extract number from text
                    number_match = re.search(r'(\d+)', text)
                    if number_match:
                        return int(number_match.group(1))
        except Exception:
            pass
        return 1  # Return 1 as default if not found
    
    def _extract_coupon_code_data(self, discount_link):
        """Follow discount link to extract coupon code and provider link"""
        try:
            # Store current window handle
            original_window = self.driver.current_window_handle
            
            # Open new tab/window
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Navigate to discount link
            self.driver.get(discount_link)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract coupon code and provider link
            coupon_code = self._find_coupon_code()
            provider_link = self.driver.current_url
            
            # Close tab and return to original window
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            return {
                "coupon_code": coupon_code or "NO_CODE",
                "provider_link": provider_link
            }
            
        except Exception as e:
            self.extraction_warnings.append(f"Error extracting coupon code: {str(e)}")
            # Make sure we return to original window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return {"coupon_code": "NO_CODE", "provider_link": discount_link}
    
    def _find_coupon_code(self):
        """Find coupon code on the redirected page"""
        try:
            # Look for common coupon code patterns
            page_text = self.driver.page_source
            
            # Pattern for coupon codes (alphanumeric, typically 4-20 characters)
            code_patterns = [
                r'קוד קופון[:\s]*([A-Z0-9]{4,20})',
                r'קופון[:\s]*([A-Z0-9]{4,20})',
                r'קוד[:\s]*([A-Z0-9]{4,20})',
                r'([A-Z0-9]{4,20})',  # Generic alphanumeric code
            ]
            
            for pattern in code_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Look for elements with specific classes or IDs
            code_elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'coupon') or contains(@class, 'code') or contains(@id, 'coupon') or contains(@id, 'code')]")
            
            for element in code_elements:
                text = element.text.strip()
                if text and len(text) >= 4 and len(text) <= 20:
                    return text
                    
        except Exception as e:
            self.extraction_warnings.append(f"Error finding coupon code: {str(e)}")
        
        return None
    
    def _report_missing_fields(self, coupon_data):
        """Report which fields failed to be collected"""
        missing = []
        for field, value in coupon_data.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field)
        
        if missing:
            self.missing_fields.append({
                "url": coupon_data.get("source_url", "Unknown"),
                "missing_fields": missing,
                "timestamp": datetime.now().isoformat()
            })
            
            print(f"⚠️  WARNING: Missing fields for {coupon_data.get('source_url', 'Unknown')}: {', '.join(missing)}")
    
    def get_extraction_report(self):
        """Get comprehensive extraction report"""
        return {
            "missing_fields": self.missing_fields,
            "warnings": self.extraction_warnings,
            "total_warnings": len(self.extraction_warnings),
            "total_missing_field_instances": len(self.missing_fields)
        }

    def navigate_to_provider(self):
        """Navigate to the provider page"""
        self.driver.get(self.provider_url)

    def get_coupon_list(self, coupon_class_name):
        # Retrieve a list of coupon elements by class name
        coupon_locator = (By.CLASS_NAME, coupon_class_name)
        return self.driver.find_elements(*coupon_locator)

    def click_coupon(self, coupon_text):
        # Click a specific coupon by its text
        coupon_locator = (By.LINK_TEXT, coupon_text)
        self.click(coupon_locator)

    def get_coupon_details(self, detail_class_name):
        # Retrieve details of a coupon, such as description or discount
        detail_locator = (By.CLASS_NAME, detail_class_name)
        return [element.text for element in self.driver.find_elements(*detail_locator)]

    def apply_coupon(self, coupon_code):
        # Example method to apply a coupon code, assuming there's an input field
        coupon_input_locator = (By.ID, "coupon-code-input")  # Replace with actual ID
        self.enter_text(coupon_input_locator, coupon_code)
        apply_button_locator = (By.ID, "apply-coupon-button")  # Replace with actual ID
        self.click(apply_button_locator)

    def _extract_discount_type(self):
        """Extract discount type from page content"""
        try:
            page_text = self.driver.page_source.lower()
            
            # Check for percentage discounts
            if '%' in page_text or 'אחוז' in page_text or 'percent' in page_text:
                return "percentage"
            
            # Check for fixed amount discounts
            if '₪' in page_text or 'shekel' in page_text or 'nis' in page_text:
                return "fixed_amount"
            
            # Check for buy one get one
            if 'קנה' in page_text and 'קבל' in page_text or 'buy' in page_text and 'get' in page_text:
                return "buy_one_get_one"
            
            # Check for cost discounts
            if 'עלות' in page_text or 'cost' in page_text:
                return "cost"
            
        except Exception:
            pass
        
        return "fixed_amount"  # Default to fixed_amount

    def _extract_consumer_statuses(self):
        """Extract consumer statuses from page content"""
        try:
            page_text = self.driver.page_source.lower()
            statuses = []
            
            # Check for new customer indicators
            if 'לקוח חדש' in page_text or 'new customer' in page_text:
                statuses.append("new_customer")
            
            # Check for returning customer indicators
            if 'לקוח חוזר' in page_text or 'returning customer' in page_text:
                statuses.append("returning_customer")
            
            # Check for VIP customer indicators
            if 'vip' in page_text or 'premium' in page_text:
                statuses.append("vip_customer")
            
            # If no specific status found, default to all
            if not statuses:
                statuses.append("all")
                
            return statuses
            
        except Exception:
            return ["all"]  # Default to all if extraction fails
