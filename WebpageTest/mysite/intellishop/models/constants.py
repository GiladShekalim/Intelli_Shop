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
    "Finance and Banking",
    "lifestyle",
    "home",
    "electronics",
    "books"
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
    "Family",
    "Parent",
    "Military/Veteran",
    "Digital Nomad",
    "First-time Buyer",
    "Retiree",
    "Single",
    "Renter"
]

# Types of discounts
DISCOUNT_TYPE = [
    "fixed_amount",
    "percentage",
    "buy_one_get_one",
    "Cost"
]

# Text search configuration
TEXT_SEARCH_FIELDS = [
    'title',
    'description', 
    'terms_and_conditions',
    'coupon_code',
    'club_name'
]

# Text search options
TEXT_SEARCH_CONFIG = {
    'CASE_SENSITIVE': False,
    'MIN_WORD_LENGTH': 10,
    'MAX_RESULTS': 1000,
    'SEARCH_OPERATOR': 'AND'  # 'AND' or 'OR' - using AND for individual words
}

# Update FILTER_CONFIG to include text search
FILTER_CONFIG = {
    'PERCENTAGE_BUCKETS': {
        'more_than_60': {'min': 60, 'max': 100},
        'between_50_60': {'min': 50, 'max': 59.99},
        'between_40_50': {'min': 40, 'max': 49.99},
        'between_30_40': {'min': 30, 'max': 39.99},
        'between_20_30': {'min': 20, 'max': 29.99},
        'up_to_20': {'min': 0, 'max': 19.99}
    },
    'DEFAULT_PRICE_RANGE': {
        'min': 0,
        'max': 1000
    },
    'DEFAULT_PERCENTAGE_RANGE': {
        'min': 0,
        'max': 100
    },
    'TEXT_SEARCH': TEXT_SEARCH_CONFIG,
    'SEARCHABLE_FIELDS': TEXT_SEARCH_FIELDS
}

# Helper function to get formatted strings for prompt templates
def get_categories_string():
    return "{" + ", ".join(CATEGORIES) + "}"

def get_consumer_status_string():
    return "{" + ", ".join(CONSUMER_STATUS) + "}"

def get_discount_type_string():
    return "{" + ", ".join(DISCOUNT_TYPE) + "}"

def get_filter_config():
    """Get filter configuration for consistent usage across the application"""
    return FILTER_CONFIG 