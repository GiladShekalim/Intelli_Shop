# CategoryPage.py
# define a base class for all category pages

# Example usage for the Fashion category 
#from Scraper.pages.jemix.CategoryPage import CategoryPage
#fashion_page = CategoryPage(driver, "https://www.jemix.co.il/tag/fashion/")
#fashion_page.navigate_to_category()
#coupons = fashion_page.get_item_list("coupon-class")  # Replace with actual class name
#fashion_page.click_item("Specific Coupon Text")

# Example usage for the Shopping category
#shopping_page = CategoryPage(driver, "https://www.jemix.co.il/tag/shopping/")
#shopping_page.navigate_to_category()
#products = shopping_page.get_item_list("product-class")  # Replace with actual class name
#shopping_page.click_item("Specific Product Name")

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from Scraper.pages.base.BasePage import BasePage

class CategoryPage(BasePage):
    # Element locators
    PROVIDER_ARTICLE = (By.CSS_SELECTOR, "article.elementor-post")
    PROVIDER_LINK = (By.CSS_SELECTOR, "a.elementor-post__thumbnail__link")
    PROVIDER_THUMBNAIL = (By.CSS_SELECTOR, "div.elementor-post__thumbnail img")

    def __init__(self, driver, category_url, category_name=""):
        super().__init__(driver)
        self.category_url = category_url
        self.category_name = category_name

    def navigate_to_category(self):
        """Navigate to the category page"""
        self.driver.get(self.category_url)

    def get_provider_links(self):
        """Get all provider links in the category page with enhanced data
        
        Returns:
            list: List of provider data dictionaries
        """
        providers = []
        articles = self.get_provider_articles()
        
        for article in articles:
            try:
                link_element = article.find_element(*self.PROVIDER_LINK)
                provider_url = link_element.get_attribute('href')
                
                # Extract provider name from URL
                provider_name = self._extract_provider_name_from_url(provider_url)
                
                # Extract thumbnail if available
                try:
                    thumbnail_element = article.find_element(*self.PROVIDER_THUMBNAIL)
                    thumbnail_src = thumbnail_element.get_attribute('src')
                except NoSuchElementException:
                    thumbnail_src = ""
                
                providers.append({
                    'url': provider_url,
                    'name': provider_name,
                    'title': provider_name.replace('-', ' ').replace('_', ' ').title(),
                    'thumbnail': thumbnail_src,
                    'category': self.category_name
                })
            except NoSuchElementException:
                # Article without link is valid, continue to next
                continue
        
        return providers

    def _extract_provider_name_from_url(self, url):
        """Extract provider name from URL"""
        if not url:
            return ""
        
        # Extract from URLs like "https://www.jemix.co.il/addict-coupon/"
        if "jemix.co.il" in url:
            parts = url.rstrip('/').split('/')
            if len(parts) > 0:
                last_part = parts[-1]
                # Remove "-coupon" suffix if present
                if last_part.endswith('-coupon'):
                    return last_part[:-8]  # Remove "-coupon"
                return last_part
        
        return ""

    def get_item_list(self, item_class_name):
        # Retrieve a list of items (e.g., coupons, products) by class name
        item_locator = (By.CLASS_NAME, item_class_name)
        return self.driver.find_elements(*item_locator)

    def click_item(self, item_text):
        # Click a specific item by its text
        item_locator = (By.LINK_TEXT, item_text)
        self.click(item_locator)

    def get_provider_articles(self):
        """Get all provider articles in the category page
        
        Returns:
            list: List of article elements
        """
        return self.driver.find_elements(*self.PROVIDER_ARTICLE)

    def verify_provider_thumbnails(self):
        """Verify that provider articles with links have thumbnails
        
        Returns:
            bool: True if all linked articles have thumbnails
        """
        articles = self.get_provider_articles()
        for article in articles:
            try:
                link = article.find_element(*self.PROVIDER_LINK)
                # If there's a link, there should be a thumbnail
                thumbnail = article.find_element(*self.PROVIDER_THUMBNAIL)
                if not thumbnail.get_attribute('src'):
                    return False
            except:
                # Articles without links can skip thumbnail check
                continue
        return True

    def has_provider_content(self):
        """Check if the category page has any provider content
        
        Returns:
            bool: True if at least one provider article exists
        """
        return len(self.get_provider_articles()) > 0