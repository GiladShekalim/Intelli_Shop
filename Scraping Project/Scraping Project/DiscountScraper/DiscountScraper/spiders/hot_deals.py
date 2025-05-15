import scrapy

class HotDealsSpider(scrapy.Spider):
    name = "hot_deals"
    allowed_domains = ["hot.co.il"]
    start_urls = ["https://www.hot.co.il/%D7%9B%D7%9C_%D7%94%D7%94%D7%98%D7%91%D7%95%D7%AA"]  # Update to the actual URL with deals

    def parse(self, response):
        # Select the first 5 discount elements
        for discount in response.css('div.content-container div.benefits-results-container div.benefits-grid benefits-grid_regular')[:5]:
            title = discount.css('div.bottom div.title::text').get()

            yield {
                "title": title.strip() if title else "No Title Found"
            }


