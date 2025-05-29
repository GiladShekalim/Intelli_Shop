"""
Shared constants and schemas used throughout the application.
This module serves as the single source of truth for data structures and enumerations.
"""

# JSON schema for discount objects
JSON_SCHEMA = """{{
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
  "consumer_statuses": ["string"]
}}"""

# Available categories for discounts
CATEGORIES = [
    "Consumerism",
    "Travel and Vacation",
    "Culture and Leisure",
    "Cars",
    "Insurance",
    "Finance and Banking"
]

# Consumer status classifications
CONSUMER_STATUS = [
    "Young",
    "Senior",
    "Homeowner",
    "Traveler",
    "Tech",
    "Pets",
    "Fitness",
    "Student",
    "Remote",
    "Family"
]

# Types of discounts
DISCOUNT_TYPE = [
    "fixed_amount",
    "percentage",
    "buy_one_get_one",
    "Cost"
]

# Helper function to get formatted strings for prompt templates
def get_categories_string():
    return "{" + ", ".join(CATEGORIES) + "}"

def get_consumer_status_string():
    return "{" + ", ".join(CONSUMER_STATUS) + "}"

def get_discount_type_string():
    return "{" + ", ".join(DISCOUNT_TYPE) + "}" 