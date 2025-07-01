import time
import re
import json
import uuid
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from ..base.BasePage import BasePage

class CouponPage(BasePage):
    """Dedicated page for extracting coupon codes and provider links from various page structures"""
    
    # Copy button locators for different page structures
    COPY_BUTTON_LOCATORS = [
        # Option 1: Copy button with onclick="copyEvent('copy')"
        {"xpath": "//button[@onclick=\"copyEvent('copy')\"]", "description": "Copy button with copyEvent function"},
        {"xpath": "//button[contains(@onclick, 'copyEvent')]", "description": "Copy button with copyEvent"},
        {"xpath": "//button[contains(text(), 'העתיקו קוד')]", "description": "Copy button with Hebrew text"},
        {"xpath": "//button[contains(text(), 'Copy')]", "description": "Copy button with English text"},
        
        # Option 2: Specific XPath for the provided example
        {"xpath": "//*[@id=\"content\"]/div/div[1]/section[1]/div/div/div/div[2]/div/button", "description": "Specific content button"},
        {"xpath": "/html/body/div[3]/main/div/div[1]/section[1]/div/div/div/div[2]/div/button", "description": "Specific main button"},
        
        # Option 3: Generic copy buttons
        {"xpath": "//button[contains(@class, 'copy')]", "description": "Button with copy class"},
        {"xpath": "//button[contains(@id, 'copy')]", "description": "Button with copy ID"},
        {"xpath": "//button[contains(@onclick, 'copy')]", "description": "Button with copy in onclick"},
    ]
    
    # Fallback coupon code locators (if copy button doesn't work)
    COUPON_CODE_LOCATORS = [
        # Option 1: Direct coupon code in paragraph
        {"xpath": "//p[@id='copy']", "description": "Direct coupon code in copy paragraph"},
        {"css": "#copy", "description": "Direct coupon code with copy ID"},
        {"xpath": "//p[contains(@id, 'copy')]", "description": "Copy paragraph with ID containing 'copy'"},
        
        # Option 2: Coupon code in various elements
        {"xpath": "//div[contains(@class, 'coupon-code')]//p", "description": "Coupon code in coupon-code class div"},
        {"xpath": "//span[contains(@class, 'coupon-code')]", "description": "Coupon code in coupon-code class span"},
        {"xpath": "//div[contains(@class, 'code')]//p", "description": "Coupon code in code class div"},
        {"xpath": "//span[contains(@class, 'code')]", "description": "Coupon code in code class span"},
        
        # Option 3: Generic coupon code patterns
        {"xpath": "//p[contains(text(), 'קוד')]", "description": "Paragraph containing 'קוד'"},
        {"xpath": "//div[contains(text(), 'קוד')]", "description": "Div containing 'קוד'"},
        {"xpath": "//span[contains(text(), 'קוד')]", "description": "Span containing 'קוד'"},
        
        # Option 4: Text-based patterns
        {"xpath": "//*[contains(text(), 'קופון')]", "description": "Element containing 'קופון'"},
        {"xpath": "//*[contains(text(), 'COUPON')]", "description": "Element containing 'COUPON'"},
        {"xpath": "//*[contains(text(), 'CODE')]", "description": "Element containing 'CODE'"},
    ]
    
    # Provider link locators for different page structures
    PROVIDER_LINK_LOCATORS = [
        # Option 1: Specific provider link button
        {"xpath": "//a[contains(text(), 'למעבר לאתר')]", "description": "Provider link with Hebrew text"},
        {"xpath": "//a[contains(text(), 'Go to site')]", "description": "Provider link with English text"},
        {"xpath": "//a[contains(@class, 'provider-link')]", "description": "Provider link with specific class"},
        
        # Option 2: Generic link patterns
        {"xpath": "//a[contains(@href, 'http') and not(contains(@href, 'jemix.co.il'))]", "description": "External links"},
        {"xpath": "//a[contains(@class, 'button')]", "description": "Button-style links"},
        {"xpath": "//a[contains(@class, 'btn')]", "description": "Button links"},
    ]
    
    # Meta tag and hidden source locators for anti-bot measures
    META_COUPON_LOCATORS = [
        {"xpath": "//meta[@property='og:description']", "description": "Open Graph description"},
        {"xpath": "//meta[@name='description']", "description": "Meta description"},
        {"xpath": "//meta[@property='twitter:description']", "description": "Twitter description"},
        {"xpath": "//script[@type='application/ld+json']", "description": "JSON-LD structured data"},
        {"xpath": "//script[contains(text(), 'coupon')]", "description": "Script with coupon data"},
        {"xpath": "//script[contains(text(), 'code')]", "description": "Script with code data"},
    ]
    
    def __init__(self, driver, coupon_url=None):
        super().__init__(driver)
        self.coupon_url = coupon_url
        self.extraction_warnings = []
    
    def extract_coupon_data(self, coupon_url=None):
        """Extract coupon code and provider link from the coupon page"""
        if coupon_url:
            self.coupon_url = coupon_url
            self.driver.get(coupon_url)
            time.sleep(2)  # Wait for page to load
            
        try:
            # Extract coupon code using multiple strategies
            coupon_code = self._extract_coupon_code()
            
            # Extract provider link
            provider_link = self._extract_provider_link()
            
            return {
                "discount_id": str(uuid.uuid4()),
                'coupon_code': coupon_code,
                'provider_link': provider_link,
                'warnings': self.extraction_warnings
            }
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in coupon extraction: {str(e)}")
            return {
                "discount_id": str(uuid.uuid4()),
                'coupon_code': 'NO_CODE',
                'provider_link': 'NO_LINK',
                'warnings': self.extraction_warnings
            }
    
    def _extract_coupon_code(self):
        """Extract coupon code using multiple strategies including anti-bot measures"""
        try:
            # Strategy 1: Try to click copy button and get from clipboard
            coupon_code = self._extract_coupon_code_via_copy_button()
            if coupon_code and coupon_code != "NO_CODE":
                return coupon_code
            
            # Strategy 2: Extract from meta tags and hidden sources (anti-bot measure)
            coupon_code = self._extract_coupon_code_from_meta()
            if coupon_code and coupon_code != "NO_CODE":
                print(f"Found coupon code '{coupon_code}' using meta tag extraction")
                return coupon_code
            
            # Strategy 3: Search for coupon code patterns in page text
            page_text = self.driver.page_source
            coupon_code = self._find_coupon_code_in_text(page_text)
            if coupon_code:
                print(f"Found coupon code '{coupon_code}' using text pattern matching")
                return coupon_code
            
            # Strategy 4: Look for elements with specific text patterns
            coupon_code = self._find_coupon_code_in_elements()
            if coupon_code:
                print(f"Found coupon code '{coupon_code}' using element text search")
                return coupon_code
            
            return "NO_CODE"
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in text extraction: {str(e)}")
            return "NO_CODE"
    
    def _extract_coupon_code_from_meta(self):
        """Extract coupon code from meta tags and hidden sources (anti-bot measure)"""
        try:
            # Check meta tags for coupon codes
            for locator_info in self.META_COUPON_LOCATORS:
                try:
                    if "xpath" in locator_info:
                        elements = self.driver.find_elements(By.XPATH, locator_info["xpath"])
                    else:
                        continue
                    
                    for element in elements:
                        content = element.get_attribute('content') or element.text
                        if content:
                            # Look for coupon code patterns in meta content
                            coupon_code = self._extract_coupon_from_text(content)
                            if coupon_code:
                                print(f"Found coupon code '{coupon_code}' in {locator_info['description']}")
                                return coupon_code
                                
                except Exception as e:
                    continue
            
            # Check JSON-LD structured data
            json_ld_scripts = self.driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
            for script in json_ld_scripts:
                try:
                    script_content = script.get_attribute('innerHTML')
                    if script_content:
                        # Parse JSON-LD and look for coupon data
                        json_data = json.loads(script_content)
                        coupon_code = self._extract_coupon_from_json(json_data)
                        if coupon_code:
                            print(f"Found coupon code '{coupon_code}' in JSON-LD data")
                            return coupon_code
                except:
                    continue
            
            return "NO_CODE"
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in meta extraction: {str(e)}")
            return "NO_CODE"
    
    def _extract_coupon_from_text(self, text):
        """Extract coupon code from text using various patterns"""
        if not text:
            return None
            
        # Pattern 1: Look for "קוד הקופון: CODE" pattern (Hebrew)
        hebrew_pattern = r'קוד\s*הקופון\s*:\s*([A-Z0-9]+)'
        match = re.search(hebrew_pattern, text)
        if match:
            return match.group(1)
        
        # Pattern 2: Look for "CODE" pattern in Hebrew text
        hebrew_code_pattern = r'([A-Z0-9]{3,10})\s*העתיקו\s*קוד'
        match = re.search(hebrew_code_pattern, text)
        if match:
            return match.group(1)
        
        # Pattern 3: Look for uppercase alphanumeric codes (3-10 characters)
        code_pattern = r'\b([A-Z0-9]{3,10})\b'
        matches = re.findall(code_pattern, text)
        for match in matches:
            if self._is_valid_coupon_code(match):
                return match
        
        # Pattern 4: Look for "COUPON CODE: XXX" pattern
        english_pattern = r'[Cc]oupon\s*[Cc]ode\s*:?\s*([A-Z0-9]+)'
        match = re.search(english_pattern, text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_coupon_from_json(self, json_data):
        """Extract coupon code from JSON-LD structured data"""
        try:
            # Recursively search through JSON structure
            if isinstance(json_data, dict):
                for key, value in json_data.items():
                    if isinstance(value, str):
                        coupon_code = self._extract_coupon_from_text(value)
                        if coupon_code:
                            return coupon_code
                    elif isinstance(value, (dict, list)):
                        coupon_code = self._extract_coupon_from_json(value)
                        if coupon_code:
                            return coupon_code
            elif isinstance(json_data, list):
                for item in json_data:
                    coupon_code = self._extract_coupon_from_json(item)
                    if coupon_code:
                        return coupon_code
        except:
            pass
        return None
    
    def _extract_coupon_code_via_copy_button(self):
        """Extract coupon code by clicking copy button and reading clipboard"""
        try:
            # Try to find and click copy button
            for locator_info in self.COPY_BUTTON_LOCATORS:
                try:
                    if "xpath" in locator_info:
                        elements = self.driver.find_elements(By.XPATH, locator_info["xpath"])
                    elif "css" in locator_info:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, locator_info["css"])
                    else:
                        continue
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Click the copy button
                            element.click()
                            time.sleep(1)
                            
                            # Try to get the copied text from clipboard or button text
                            copied_text = self._get_copied_text()
                            if copied_text and self._is_valid_coupon_code(copied_text):
                                print(f"Found coupon code '{copied_text}' via copy button")
                                return copied_text
                            
                            # If clipboard doesn't work, try to get from button's onclick attribute
                            onclick = element.get_attribute('onclick')
                            if onclick:
                                coupon_code = self._extract_coupon_from_text(onclick)
                                if coupon_code:
                                    print(f"Found coupon code '{coupon_code}' from button onclick")
                                    return coupon_code
                                    
                except Exception as e:
                    continue
            
            return "NO_CODE"
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in copy button extraction: {str(e)}")
            return "NO_CODE"
    
    def _get_copied_text(self):
        """Try to get text from clipboard (may not work in all browsers)"""
        try:
            # Try to get from clipboard using JavaScript
            clipboard_text = self.driver.execute_script("""
                return navigator.clipboard.readText().catch(() => {
                    // Fallback: try to get from a temporary textarea
                    const textarea = document.createElement('textarea');
                    document.body.appendChild(textarea);
                    textarea.focus();
                    document.execCommand('paste');
                    const text = textarea.value;
                    document.body.removeChild(textarea);
                    return text;
                });
            """)
            return clipboard_text if clipboard_text else None
        except:
            return None
    
    def _extract_coupon_code_via_text(self):
        """Extract coupon code by searching for text patterns in DOM elements"""
        try:
            for locator_info in self.COUPON_CODE_LOCATORS:
                try:
                    if "xpath" in locator_info:
                        elements = self.driver.find_elements(By.XPATH, locator_info["xpath"])
                    elif "css" in locator_info:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, locator_info["css"])
                    else:
                        continue
                    
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            coupon_code = self._extract_coupon_from_text(text)
                            if coupon_code:
                                print(f"Found coupon code '{coupon_code}' using {locator_info['description']}")
                                return coupon_code
                                
                except NoSuchElementException:
                    continue
            
            return "NO_CODE"
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in text extraction: {str(e)}")
            return "NO_CODE"
    
    def _extract_provider_link(self):
        """Extract provider link using multiple strategies"""
        try:
            # Strategy 1: Use specific locators
            for locator_info in self.PROVIDER_LINK_LOCATORS:
                try:
                    if "xpath" in locator_info:
                        elements = self.driver.find_elements(By.XPATH, locator_info["xpath"])
                    elif "css" in locator_info:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, locator_info["css"])
                    else:
                        continue
                    
                    for element in elements:
                        href = element.get_attribute('href')
                        if self._is_valid_provider_link(href):
                            print(f"Found provider link '{href}' using {locator_info['description']}")
                            return href
                            
                except NoSuchElementException:
                    continue
            
            # Strategy 2: Look for external links in meta tags
            meta_links = self.driver.find_elements(By.XPATH, "//meta[@property='og:url' or @name='canonical']")
            for meta in meta_links:
                content = meta.get_attribute('content')
                if content and 'jemix.co.il' not in content:
                    print(f"Found provider link '{content}' in meta tag")
                    return content
            
            return "NO_LINK"
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in provider link extraction: {str(e)}")
            return "NO_LINK"
    
    def _is_valid_coupon_code(self, text):
        """Validate if text looks like a valid coupon code"""
        if not text or len(text) < 3 or len(text) > 20:
            return False
        
        # Check if it contains HTML tags (invalid)
        if '<' in text or '>' in text:
            return False
        
        # Check if it's just whitespace or common invalid values
        invalid_values = ['NO_CODE', 'html', 'body', 'head', 'script', 'style', 'div', 'span', 'p']
        if text.strip().lower() in invalid_values:
            return False
        
        # Check if it contains only alphanumeric characters and common symbols
        if re.match(r'^[A-Z0-9\-_]+$', text.strip()):
            return True
        
        return False
    
    def _is_valid_provider_link(self, url):
        """Validate if URL looks like a valid provider link"""
        if not url or url == "NO_LINK":
            return False
        
        # Check if it's a valid URL format
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check if it's not the same domain as Jemix
        if 'jemix.co.il' in url:
            return False
        
        return True
    
    def _find_coupon_code_in_text(self, page_text):
        """Search for coupon code patterns in the entire page text"""
        if not page_text:
            return None
        
        # Extract coupon code from page text
        coupon_code = self._extract_coupon_from_text(page_text)
        return coupon_code if coupon_code else None
    
    def _find_coupon_code_in_elements(self):
        """Search for coupon codes in all visible text elements"""
        try:
            # Get all text elements
            text_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            
            for element in text_elements:
                try:
                    text = element.text.strip()
                    if text:
                        coupon_code = self._extract_coupon_from_text(text)
                        if coupon_code:
                            return coupon_code
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.extraction_warnings.append(f"Error in element search: {str(e)}")
            return None
    
    def get_extraction_warnings(self):
        """Get list of warnings from extraction process"""
        return self.extraction_warnings 