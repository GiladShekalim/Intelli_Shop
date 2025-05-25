# config.py
MAX_DISCOUNTS = 10
AMOUNT = 1
LOCATION = "Israel"
HEADLESS = True
SCRAPE_TARGET = "adif"
BASE_URL_HOT = "https://www.hot.co.il"
BASE_URL_ADIF = "https://adif.org.il"

CATEGORIES_ADIF = [
    {"name": "Consumerism", "url": f"{BASE_URL_ADIF}/category/328"},
    {"name": "Travel and Vacation", "url": f"{BASE_URL_ADIF}/category/637"},
    {"name": "Culture and Leisure", "url": f"{BASE_URL_ADIF}/category/444"},
    {"name": "Lifestyle", "url": f"{BASE_URL_ADIF}/category/172"},
    {"name": "Electronics", "url": f"{BASE_URL_ADIF}/category/145"},
    {"name": "Fashion", "url": f"{BASE_URL_ADIF}/category/457"},
]

CATEGORIES_HOT = [
    {"name": "Consumerism", "url": f"{BASE_URL_HOT}/קטגוריה/688/צרכנות"},
    {"name": "Travel and Vacation", "url": f"{BASE_URL_HOT}/קטגוריה/96/תיירות_ונופש"},
    {"name": "Culture and Leisure", "url": f"{BASE_URL_HOT}/קטגוריה/817/תרבות_ופנאי"},
    {"name": "Cars", "url": f"{BASE_URL_HOT}/קטגוריה/877/רכב"},
    {"name": "Insurance", "url": f"{BASE_URL_HOT}/קטגוריה/818/ביטוח"},
    {"name": "Finance and Banking", "url": f"{BASE_URL_HOT}/קטגוריה/777/פיננסים_ובנקאות"},
]
