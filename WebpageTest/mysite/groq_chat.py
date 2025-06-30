from dotenv import load_dotenv
import os
from groq import Groq
import json
import logging
import time
from typing import Dict, List, Any, Tuple
import re
from intellishop.models.constants import (
    JSON_SCHEMA, 
    get_categories_string,
    get_consumer_status_string,
    get_discount_type_string,
    CATEGORIES,
    CONSUMER_STATUS,
    DISCOUNT_TYPE
)
import glob
import sys

# Use the imported constants and helper functions
CATEGORIES = get_categories_string()
CONSUMER_STATUS = get_consumer_status_string()
DISCOUNT_TYPE = get_discount_type_string()

MESSAGE_TEMPLATE = f"""You are a data processing API that enhances discount objects.
You must return a valid JSON object that follows this schema:
{JSON_SCHEMA}

The input data may contain Hebrew text. this is valubale information, focus only on extracting the required information.

Instructions for processing fields:
price: Extract the discount amount from the description field,title,terms_and_conditions, and this will be the value of the price filed.
  - fixed_amount: Must be > 0
  - percentage: Must be 1-100
  - buy_one_get_one: Must be 1
  - Cost: Must be > 0
- discount_type: Extract from the description field,title,terms_and_conditions. Assign one value only from: {DISCOUNT_TYPE}
- category: Analyze the title and description and select relevant categories from: {CATEGORIES}
- consumer_statuses: Analyze the title and description and select most reasanble possible realeted relevant statuses from the following list: {CONSUMER_STATUS}


**Ultra-Critical Mandate: Zero Tolerance for Field Alteration**
Copy every field listed below exactly as provided—character by character, word by word, letter by letter. Do not modify, abbreviate, summarize, or otherwise alter any content except as explicitly permitted below. Any unauthorized change will be treated as a severe violation.
Field-Specific Requirements:
discount_id:Do not change.If value is "N/A", replace with an empty string.
title:Do not change.If value is "N/A", replace with an empty string.
description:Do not change.If value is "N/A", replace with an empty string.
image_link:Do not change.If value is "N/A", replace with an empty string.
discount_link:Do not change.If value is "N/A", replace with an empty string.
terms_and_conditions:Do not change.If value is "N/A", replace with "See provider website for details".
club_name:Do not change.If value is "N/A", replace with an empty array.
valid_until:Do not change.If value is "N/A", replace with an empty string.
usage_limit:Do not change.If value is "N/A", replace with null.
coupon_code:Do not change.If value is "N/A", replace with an empty string.
provider_link:Do not change.If value is "N/A", replace with an empty string.
***Final Warning: Any operation that does not follow these instructions verbatim is unacceptable. There is no margin for error. All processing must be performed with absolute precision.***


**IMPORTANT:**
- Return ONLY a valid JSON object, with NO extra text, code fences, or comments.
- Every key and string value must be enclosed in double quotes (").
- All arrays and objects must have correct JSON syntax.
- Do not include trailing commas.
- If a field is missing or not applicable, use the default value as specified in the schema.
- Do not invent or guess field names. Only use those in the schema.
- Before returning, validate your output to ensure it is valid JSON and matches the schema exactly.
- Return ONLY a valid JSON object with all fields from the schema and NOTHING ELSE.
**CRITICAL:**
- if price is 0 search for the price in the description field,title,terms_and_conditions again!
price, discount_type, category, consumer_statuses - MUST MUST MUST CONTAIN A VALUE AS DEFINED, IF NOT, SEND OBJECT AGAIN.
- make sure Original discount titles are not being modified
- make sure Provider links are not changed
- make sure each ID has unique discount IDs
- make sure data is not lost during processing
- generated values are logically correct.
- generated fields are not empty.

Critical Example: Input and Expected Output
Input json:
{{
  "club_name": "hot",
  "category": "Consumerism",
  "discount_id": "6",
  "title": "מארזי נקיון ופארם",
  "price": "20% הנחה",
  "discount_type": "percentage",
  "description": "פרטי ההטבה: הנחה על כלל המגוון באתר s2h\n20% הנחת קופון + 10% הנחה בחיוב על היתרה\n\nאתר s2h -כל מותגי הניקיון לבית במקום אחד! מגוון עשיר של מותגים מובילים לניקיון הבית ובישום הבית: פיניש, ווניש, קולון, סיליט, איירוויק ועוד.\n\nמימוש ההטבה: באמצעות קוד H525 באתר הספק. יש לשלם בכרטיס אשראי המשויך למועדון הוט בלבד.\nההנחה בחיוב תינתן אוטומטית למשלמים בכרטיס אשראי הוט. הנחה זו ניתנת על הסכום המשולם בפועל בכרטיס האשראי.\nאת ההנחה ניתן יהיה לראות בפרטי חיוב כרטיס האשראי (סטייטמנט) שם יופיע הזיכוי בגובה ההנחה, ולא בקופה בעת התשלום.",
  "terms_and_conditions": "20% הנחה + 10% הנחה בחיוב על היתרה מהתשלום בפועל לאחר ההנחה. סה\"כ הנחה אפקטיבית: 28%\nמימוש ההטבה באתר הספק, באמצעות קוד קופון: H525 בין התאריכים: 14-31.5.25 או עד גמר המלאי – המוקדם מביניהם. יש לשלם בכרטיס אשראי המשויך למועדון הוט.\n\n- תקף בקניה מעל 20 ₪\n- כולל כפל מבצעים\n- עלות משלוח משתנה בהתאם למוצרים\n- לא כולל כפל קופונים או מועדונים.\n- מינימום 300 יח' למבצע - המלאי מוגבל. \n- הספק רשאי לסיים את המבצע בכל עת וללא הודעה מראש. \n- התמונות להמחשה בלבד. ט.ל.ח.",
  "discount_link": "https://www.hot.co.il/%D7%94%D7%98%D7%91%D7%94/56476/%D7%9E%D7%90%D7%A8%D7%96%D7%99-%D7%A0%D7%A7%D7%99%D7%95%D7%9F-%D7%95%D7%A4%D7%90%D7%A8%D7%9D",
  "image_link": "https://cdn.hot.co.il/media/b487107d-aa98-4a4f-911f-8d7b5d5f208c.jpg",
  "provider_link": "https://s2h.co.il/",
  "coupon_code": "H525",
  "valid_until": "31.5.25",
  "usage_limit": 1,
  "location": "Israel"
}}
Expected Output (Strictly According to Your Critical Demand)
Only the fields explicitly listed in your original demand, copied exactly, except for the "N/A" replacements.
No new fields, no changes to field types unless "N/A" is present.

Expected Output json:
{{
  "discount_id": "6",
  "title": "מארזי נקיון ופארם",
  "description": "פרטי ההטבה: הנחה על כלל המגוון באתר s2h\n20% הנחת קופון + 10% הנחה בחיוב על היתרה\n\nאתר s2h -כל מותגי הניקיון לבית במקום אחד! מגוון עשיר של מותגים מובילים לניקיון הבית ובישום הבית: פיניש, ווניש, קולון, סיליט, איירוויק ועוד.\n\nמימוש ההטבה: באמצעות קוד H525 באתר הספק. יש לשלם בכרטיס אשראי המשויך למועדון הוט בלבד.\nההנחה בחיוב תינתן אוטומטית למשלמים בכרטיס אשראי הוט. הנחה זו ניתנת על הסכום המשולם בפועל בכרטיס האשראי.\nאת ההנחה ניתן יהיה לראות בפרטי חיוב כרטיס האשראי (סטייטמנט) שם יופיע הזיכוי בגובה ההנחה, ולא בקופה בעת התשלום.",
  "image_link": "https://cdn.hot.co.il/media/b487107d-aa98-4a4f-911f-8d7b5d5f208c.jpg",
  "discount_link": "https://www.hot.co.il/%D7%94%D7%98%D7%91%D7%94/56476/%D7%9E%D7%90%D7%A8%D7%96%D7%99-%D7%A0%D7%A7%D7%99%D7%95%D7%9F-%D7%95%D7%A4%D7%90%D7%A8%D7%9D",
  "terms_and_conditions": "20% הנחה + 10% הנחה בחיוב על היתרה מהתשלום בפועל לאחר ההנחה. סה\"כ הנחה אפקטיבית: 28%\nמימוש ההטבה באתר הספק, באמצעות קוד קופון: H525 בין התאריכים: 14-31.5.25 או עד גמר המלאי – המוקדם מביניהם. יש לשלם בכרטיס אשראי המשויך למועדון הוט.\n\n- תקף בקניה מעל 20 ₪\n- כולל כפל מבצעים\n- עלות משלוח משתנה בהתאם למוצרים\n- לא כולל כפל קופונים או מועדונים.\n- מינימום 300 יח' למבצע - המלאי מוגבל. \n- הספק רשאי לסיים את המבצע בכל עת וללא הודעה מראש. \n- התמונות להמחשה בלבד. ט.ל.ח.",
  "club_name": "hot",
  "valid_until": "31.5.25",
  "usage_limit": 1,
  "coupon_code": "H525",
  "provider_link": "https://s2h.co.il/"
}}
Important Notes
No new fields are added.
Fields are copied exactly, no changes except for "N/A" replacements (not present in this example).
If you want club_name as an array, you must specify this in your demand, but your original instruction only says to set to an empty array if "N/A".
If you want to add consumer_statuses or process price, you must explicitly state this in your requirements."""

# Load environment variables
load_dotenv()

# Near the top of the file, after loading environment variables
DEFAULT_DATA_DIR = os.environ.get('DISCOUNT_DATA_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))

current_model_index = 0

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)
logger = logging.getLogger("GroqEnhancer")
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()  # Default to INFO instead of WARNING
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Add configuration for httpx logger to suppress successful requests
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)  # Only show warnings and errors by default

# Silence the Groq client's internal retry logs
groq_logger = logging.getLogger("groq._base_client")
groq_logger.setLevel(logging.WARNING)  # Only show warnings and errors

def log_checkpoint(message):
    """Log important checkpoints at INFO level regardless of current log level"""
    current_level = logger.level
    logger.setLevel(logging.INFO)
    logger.info(message)
    logger.setLevel(current_level)

# Ensure constants.py exists in the same directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONSTANTS_PATH = os.path.join(SCRIPT_DIR, 'intellishop', 'models', 'constants.py')

if not os.path.exists(CONSTANTS_PATH):
    logger.error(f"constants.py not found at {CONSTANTS_PATH}. Please ensure this file exists.")
    sys.exit(1)

def validate_discount_data(discount: Dict[str, Any], original_discount: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the generated discount data against schema constraints and business rules.
    
    Args:
        discount: The generated discount object to validate
        original_discount: The original discount object for comparison
        
    Returns:
        Tuple of (is_valid, list_of_validation_errors)
    """
    errors = []
    
    # Required fields that must be present
    required_fields = [
        'discount_id', 'title', 'price', 'discount_type', 'description',
        'image_link', 'discount_link', 'terms_and_conditions', 'club_name',
        'category', 'valid_until', 'usage_limit', 'coupon_code', 
        'provider_link', 'consumer_statuses', 'favorites'
    ]
    
    # Check all required fields are present
    for field in required_fields:
        if field not in discount:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate price constraints based on discount_type
    price = discount.get('price', 0)
    discount_type = discount.get('discount_type', '')
    
    if discount_type == 'fixed_amount' and price <= 0:
        errors.append(f"fixed_amount discount type requires price > 0, got: {price}")
    elif discount_type == 'percentage' and (price < 1 or price > 100):
        errors.append(f"percentage discount type requires price between 1-100, got: {price}")
    elif discount_type == 'buy_one_get_one' and price != 1:
        errors.append(f"buy_one_get_one discount type requires price = 1, got: {price}")
    elif discount_type == 'Cost' and price <= 0:
        errors.append(f"Cost discount type requires price > 0, got: {price}")
    
    # Validate discount_type is from allowed values
    if discount_type not in DISCOUNT_TYPE:
        errors.append(f"Invalid discount_type: {discount_type}. Must be one of: {DISCOUNT_TYPE}")
    
    # Validate category is from allowed values and not empty
    category = discount.get('category', [])
    if not isinstance(category, list) or len(category) == 0:
        errors.append(f"category must be a non-empty array, got: {category}")
    else:
        invalid_categories = [cat for cat in category if cat not in CATEGORIES]
        if invalid_categories:
            errors.append(f"Invalid categories: {invalid_categories}. Must be from: {CATEGORIES}")
    
    # Validate consumer_statuses is from allowed values and not empty
    consumer_statuses = discount.get('consumer_statuses', [])
    if not isinstance(consumer_statuses, list) or len(consumer_statuses) == 0:
        errors.append(f"consumer_statuses must be a non-empty array, got: {consumer_statuses}")
    else:
        invalid_statuses = [status for status in consumer_statuses if status not in CONSUMER_STATUS]
        if invalid_statuses:
            errors.append(f"Invalid consumer_statuses: {invalid_statuses}. Must be from: {CONSUMER_STATUS}")
    
    # Validate club_name is an array
    club_name = discount.get('club_name', [])
    if not isinstance(club_name, list):
        errors.append(f"club_name must be an array, got: {type(club_name)}")
    
    # Validate favorites is an array
    favorites = discount.get('favorites', [])
    if not isinstance(favorites, list):
        errors.append(f"favorites must be an array, got: {type(favorites)}")
    
    # Validate string fields are not None
    string_fields = ['title', 'description', 'image_link', 'discount_link', 
                    'terms_and_conditions', 'coupon_code', 'provider_link']
    for field in string_fields:
        value = discount.get(field)
        if value is None:
            errors.append(f"{field} cannot be None, must be a string")
    
    # Validate usage_limit is integer or null
    usage_limit = discount.get('usage_limit')
    if usage_limit is not None and not isinstance(usage_limit, int):
        errors.append(f"usage_limit must be an integer or null, got: {type(usage_limit)}")
    
    # Business rule: Original title should not be modified
    original_title = original_discount.get('title', '')
    current_title = discount.get('title', '')
    if original_title and current_title != original_title:
        errors.append(f"Original title should not be modified. Original: '{original_title}', Current: '{current_title}'")
    
    # Business rule: Provider link should not be changed
    original_provider_link = original_discount.get('provider_link', '')
    current_provider_link = discount.get('provider_link', '')
    if original_provider_link and current_provider_link != original_provider_link:
        errors.append(f"Provider link should not be changed. Original: '{original_provider_link}', Current: '{current_provider_link}'")
    
    # Business rule: If price is 0, it's likely a failure in extraction
    if price == 0:
        errors.append("Price is 0, likely failed to extract price from description/title/terms")
    
    # Business rule: discount_id should not be empty
    if not discount.get('discount_id'):
        errors.append("discount_id cannot be empty")
    
    return len(errors) == 0, errors

def process_discount_with_groq(discount: Dict[str, Any], max_retries: int = 10) -> Dict[str, Any]:
    """
    Send a discount object to Groq API using JSON Mode and get back an edited version.
    Includes comprehensive validation with up to 10 retries.
    Changes model after 3 consecutive validation failures for the same object.
    
    Args:
        discount: A discount object from the JSON file
        max_retries: Maximum number of retry attempts (default: 10)
        
    Returns:
        The edited discount object from Groq, or original if all retries fail
    """
    global current_model_index  # Use the global variable
    
    # disable Groq client's internal logging
    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("groq._base_client").setLevel(logging.WARNING)
    
    models = ["llama3-70b-8192", "llama3-8b-8192", "llama-3.1-8b-instant", 
              "llama-3.3-70b-versatile", "gemma2-9b-it"]
    
    system_message = MESSAGE_TEMPLATE
    
    discount_id = discount.get('discount_id', 'unknown')
    user_message = f"Please edit each indvidual field for the following discount object as described in the instructions:\n{json.dumps(discount, indent=2, ensure_ascii=False)}"
    
    retry_count = 0
    validation_failures_count = 0  # Track consecutive validation failures
    
    while retry_count <= max_retries:
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            current_model = models[current_model_index]
            
            # Log when sending a new object to the API with discount ID
            logger.info(f"Sending discount ID: {discount_id} to Groq API using model: {current_model} (attempt {retry_count + 1}/{max_retries + 1})")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                model=current_model,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            
            # With JSON Mode, we can directly parse the response content
            response_content = chat_completion.choices[0].message.content
            edited_discount = json.loads(response_content)
            
            # Validate the response
            is_valid, validation_errors = validate_discount_data(edited_discount, discount)
            
            if is_valid:
                logger.info(f"✅ Discount ID {discount_id} successfully processed and validated")
                return edited_discount
            else:
                validation_failures_count += 1
                logger.warning(f"❌ Validation failed for discount ID {discount_id} (attempt {retry_count + 1}, validation failure #{validation_failures_count}):")
                for error in validation_errors:
                    logger.warning(f"  - {error}")
                
                # Change model after 3 consecutive validation failures
                if validation_failures_count >= 3:
                    prev_model = models[current_model_index]
                    current_model_index = (current_model_index + 1) % len(models)
                    new_model = models[current_model_index]
                    logger.info(f"🔄 3 consecutive validation failures: Switching model from {prev_model} to {new_model} for discount ID: {discount_id}")
                    validation_failures_count = 0  # Reset counter for new model
                    time.sleep(1)  # Brief pause before trying the new model
                
                if retry_count < max_retries:
                    retry_count += 1
                    logger.info(f"Retrying discount ID {discount_id} (attempt {retry_count + 1}/{max_retries + 1})")
                    time.sleep(2)  # Add delay before retry
                    continue
                else:
                    logger.error(f"❌ All {max_retries + 1} attempts failed for discount ID {discount_id}. Using original discount.")
                    return discount
                
        except json.JSONDecodeError as e:
            error_message = f"JSON decode error for discount ID {discount_id}: {str(e)}"
            logger.warning(f"❌ {error_message}")
            
            if retry_count < max_retries:
                retry_count += 1
                logger.info(f"Retrying discount ID {discount_id} due to JSON error (attempt {retry_count + 1}/{max_retries + 1})")
                time.sleep(2)
                continue
            else:
                logger.error(f"❌ All {max_retries + 1} attempts failed for discount ID {discount_id}. Using original discount.")
                return discount
                
        except Exception as e:
            error_message = f"Error processing discount with ID {discount_id}: {str(e)}"
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str:
                # Move to the next model in the list
                prev_model = models[current_model_index]
                current_model_index = (current_model_index + 1) % len(models)
                new_model = models[current_model_index]
                # Always log model changes at INFO level
                logger.info(f"429 Too Many Requests: Switching model from {prev_model} to {new_model} for discount ID: {discount_id}")
                time.sleep(1)  # Brief pause before trying the next model
                continue
            
            if retry_count < max_retries:
                retry_count += 1
                logger.warning(f"{error_message}\nRetrying attempt {retry_count} of {max_retries}...")
                time.sleep(2)  # Add a slightly longer delay before retrying
            else:
                logger.error(f"{error_message}\nMax retries exceeded. Using original discount.")
                return discount
    
    return discount

# TODO: 
# create a copy file of the original coupons list.
# the copy file will contain the list of objects with a change - ID is generated.
# After groq return response with the json format. - containing only the required fields for edits. 
# 1 get the relevent fields from the response.
# 2 change the copy file with the new values for the specific object. - using the discount_id as the key.
# 3 save the copy file as a new file
#

def update_discounts_file(input_file_path: str, output_file_path: str) -> None:
    """
    Process each discount in the JSON file with Groq and create a new file with only successfully processed discounts.
    
    Args:
        input_file_path: Path to the original hot_discounts.json file
        output_file_path: Path to the new Inhanced_discounts.json file
    """
    # Load the original JSON file
    with open(input_file_path, 'r', encoding='utf-8') as f:
        discounts = json.load(f)
    
    # Create an empty list to hold only successfully processed discounts
    enhanced_discounts = []
    # Track IDs of deprecated/skipped discounts
    deprecated_discount_ids = []
    
    total_discounts = len(discounts)
    log_checkpoint(f"Processing file: {os.path.basename(input_file_path)} with {total_discounts} discounts")
    
    # Process each discount one by one
    for i, discount in enumerate(discounts):
        discount_id = discount.get('discount_id', 'unknown')
        # Reduce frequency of progress logs - only log at DEBUG level
        if (i+1) % 10 == 0 or i+1 == total_discounts:
            logger.debug(f"Progress: {i+1}/{total_discounts} discounts processed")
        
        # Process with Groq with retry mechanism (up to 10 attempts)
        edited_discount = process_discount_with_groq(discount, max_retries=10)
        
        # Check if the discount is the original one (indicating failed processing after all retries)
        if edited_discount is discount:
            logger.warning(f"❌ Failed to enhance discount ID: {discount_id} after all retry attempts")
            deprecated_discount_ids.append(discount_id)
            continue
        
        # Validate the final result one more time before adding to enhanced list
        is_valid, validation_errors = validate_discount_data(edited_discount, discount)
        if not is_valid:
            logger.error(f"❌ Final validation failed for discount ID: {discount_id}")
            for error in validation_errors:
                logger.error(f"  - {error}")
            deprecated_discount_ids.append(discount_id)
            continue
        
        # Successfully processed and validated, add it to our list
        enhanced_discounts.append(edited_discount)
        logger.info(f"✅ Successfully enhanced discount ID: {discount_id}")
        
        # Add a small delay to avoid rate limits
        time.sleep(1)
    
    # Save successfully enhanced discounts
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_discounts, f, ensure_ascii=False, indent=2)
    
    successful_count = len(enhanced_discounts)
    deprecated_count = total_discounts - successful_count
    
    # Log summary in the same format as update_database.py
    log_checkpoint("\nFile Summary:")
    log_checkpoint(f"  - Total discounts processed: {total_discounts}")
    log_checkpoint(f"  - Successfully enhanced: {successful_count}")
    log_checkpoint(f"  - Failed/deprecated: {deprecated_count}")
    
    if deprecated_count > 0:
        if len(deprecated_discount_ids) <= 20:
            log_checkpoint(f"  - Deprecated discount IDs: {', '.join(deprecated_discount_ids)}")
        else:
            log_checkpoint(f"  - Deprecated discount IDs: {', '.join(deprecated_discount_ids[:20])}...")
            log_checkpoint(f"    ... and {len(deprecated_discount_ids) - 20} more")
    
    log_checkpoint(f"Output saved to: {output_file_path}")

def find_json_files(data_dir_path=None):
    """Find all JSON files in the data directory and its subdirectories, excluding files that start with 'enhanced_'"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up two levels now
    
    # Use provided path if available
    if data_dir_path and os.path.exists(data_dir_path):
        data_dir = data_dir_path
        logger.debug(f"Using provided data directory: {data_dir}")
    else:
        # Use the global default with fallbacks
        data_dir = DEFAULT_DATA_DIR
        
        # Add additional fallback paths if needed
        if not os.path.exists(data_dir):
            alternative_paths = [
                os.path.join(base_dir, '..', 'data'),
                os.path.join(base_dir, 'data'),
                os.path.join(base_dir, 'intellishop', 'data'),
                os.path.join(base_dir, 'mysite', 'intellishop', 'data')
            ]
            
            # Check if any alternative paths exist
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    data_dir = alt_path
                    logger.debug(f"Using alternative data directory: {data_dir}")
                    break
    
    log_checkpoint(f"Scanning for JSON files in {data_dir}")
    
    json_files = []
    # Walk through directory and its subdirectories
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            # Only include JSON files that don't start with "enhanced_"
            if file.lower().endswith('.json') and not file.startswith('enhanced_'):
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    
    log_checkpoint(f"Found {len(json_files)} JSON files to process (excluding enhanced files)")
    
    return json_files

def process_json_files(data_dir_path=None):
    """Process all JSON files found in the data directory
    
    Args:
        data_dir_path: Optional path to the data directory.
    """
    log_checkpoint("Starting Groq discount enhancement process")
    json_files = find_json_files(data_dir_path)
    
    if not json_files:
        logger.warning("No JSON files found to process.")
        return
    
    success_count = 0
    for input_file_path in json_files:
        # Create output file path based on input file name
        file_name = os.path.basename(input_file_path)
        file_dir = os.path.dirname(input_file_path)
        output_file_name = f"enhanced_{file_name}"
        output_file_path = os.path.join(file_dir, output_file_name)
        
        log_checkpoint(f"\nProcessing file: {file_name}")
        
        # Process the file
        update_discounts_file(input_file_path, output_file_path)
        success_count += 1
    
    # Final summary - always show at INFO level
    log_checkpoint("\nSummary:")
    log_checkpoint(f"  - Total files processed: {len(json_files)}")
    log_checkpoint(f"  - Successfully processed: {success_count}")
    
    if success_count == len(json_files):
        log_checkpoint("✅ Groq enhancement process completed successfully!")
    else:
        logger.warning("⚠️ Groq enhancement process completed with warnings.")

if __name__ == "__main__":
    # Check for environment variable to control log level
    if 'LOG_LEVEL' in os.environ:
        level_name = os.environ['LOG_LEVEL'].upper()
        level = getattr(logging, level_name, None)
        if level is not None:
            logger.setLevel(level)
            log_checkpoint(f"Log level set to {level_name}")
    else:
        # Set default to INFO if not specified
        logger.setLevel(logging.INFO)
        log_checkpoint("Log level defaulting to INFO")
    
    # You can set a custom data directory here or pass None to use defaults
    data_directory = None  # Replace with your variable path if needed
    process_json_files(data_directory)