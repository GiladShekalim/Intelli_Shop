# utils/helpers.py
import re
import random
from datetime import datetime, timedelta
from urllib.parse import urlparse

def extract_valid_until(text):
    """
    Extracts the valid-until date from a block of text.
    Supports formats like:
    - עד תאריך 31.12.2026
    - תוקף ההטבה בין התאריכים: 01.01.2024-31.12.2024
    """
    patterns = [
        r'בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'תוקף ההטבה בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'תקף בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'מימוש ההטבה בין התאריכים:\s*\d{1,2}-([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'עד לתאריך\s*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})',
        r'עד תאריך\s*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    # fallback: add random days
    fallback = (datetime.now() + timedelta(days=random.randint(10, 40))).strftime("%d.%m.%y")
    return fallback

def classify_price_type(price_text):
    if not price_text or price_text.strip() == "":
        return "N/A"

    price_text = price_text.strip()

    # Percentage match: 10%, 15 אחוז
    if re.search(r'\d{1,3}\s*[%אחוז]', price_text):
        return "percentage"

    # Price match: matches both '199 ₪' and '₪199', also ש"ח before/after
    if re.search(r'(₪|\$|€|ש\"ח|שח)?\s*\d{1,4}|\d{1,4}\s*(₪|\$|€|ש\"ח|שח)', price_text):
        return "price"

    return "N/A"

def extract_coupon_code(text):
    """
    Extracts a coupon code (קוד קופון / קוד הטבה / קוד המבצע / קוד) from text.
    Returns 'N/A' if not found or if the match is a known false positive.
    """
    pattern = r'(?:קוד קופון|קוד הטבה|קוד המבצע|קוד)\s*:?\s*([A-Za-z0-9]{4,})'
    match = re.search(pattern, text)
    if match:
        code = match.group(1)
        false_positives = {"באתר", "למוכרן", "בטרם", "קופה", "טרם", "בהצגה", "אפליקציית", "מועדון"}
        return code if code not in false_positives else "N/A"
    return "N/A"

def get_club_name_from_url(url):
    parts = urlparse(url).netloc.split('.')
    return parts[1] if parts[0] == "www" else parts[0]

def extract_price_fallback(description, terms):
    """
    Tries to extract a price or percentage from the description and terms text.
    Covers Hebrew formats like '10%', '10 אחוז', '10% הנחה', 'ב-199 ש"ח', etc.
    """
    combined_text = f"{description}\n{terms}"

    patterns = [
        r"\d{1,3}%\s*הנחה",                  # 10% הנחה
        r"הנחה\s*של\s*\d{1,3}%",             # הנחה של 10%
        r"\d{1,3}%",                          # 10%
        r"\d{1,3}\s*אחוז\s*הנחה",            # 10 אחוז הנחה
        r"הנחה\s*של\s*\d{1,3}\s*אחוז",       # הנחה של 10 אחוז
        r"\d{1,3}\s*אחוז",                   # 10 אחוז
        r"\d{1,4}\s*₪",                       # 199 ₪
        r"₪\s*\d{1,4}",                       # ₪199
        r"(?:ב-)?\d{1,4}(?:\s*ש\"ח|\s*שח)"    # ב-199 ש"ח
    ]

    for pattern in patterns:
        match = re.search(pattern, combined_text)
        if match:
            return match.group().strip()

    return "N/A"

# def extract_provider_link_from_text(text):
#     """
#     Extracts the first URL from the description or any raw text.
#     Returns 'N/A' if no URL is found.
#     """
#     pattern = r"(https?://[^\s]+|www\.[^\s]+)"
#     match = re.search(pattern, text)
#     if match:
#         return match.group(0).strip()
#     return "N/A"
