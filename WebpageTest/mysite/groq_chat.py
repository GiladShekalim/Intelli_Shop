from dotenv import load_dotenv
import os
from groq import Groq
import json
import logging
import time
from typing import Dict, List, Any
import re
from intellishop.models.constants import (
    JSON_SCHEMA, 
    get_categories_string,
    get_consumer_status_string,
    get_discount_type_string
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
- discount_id: No change required. If "N/A", set to empty string.
- title: No change required. If "N/A", set to empty string.
- price: Extract the discount amount from the description field as an integer value.
  - fixed_amount: Must be > 0
  - percentage: Must be 1-100
  - buy_one_get_one: Must be 1
  - Cost: Must be > 0
- discount_type: Extract from the description field. Assign one value only from: {DISCOUNT_TYPE}
- description: No change required. If "N/A", set to empty string.
- image_link: No change required. If "N/A", set to empty string.
- discount_link: No change required. If "N/A", set to empty string.
- terms_and_conditions: No change required. If "N/A", set to "See provider website for details".
- club_name: No change required. If "N/A", set to an empty array.
- category: Analyze the title and description and select relevant categories from: {CATEGORIES}
- consumer_statuses: Analyze the title and description and select relevant statuses from: {CONSUMER_STATUS}
- valid_until: No change required. If "N/A", set to empty string.
- usage_limit: No change required. If "N/A", set to null.
- coupon_code: No change required. If "N/A", set to empty string.
- provider_link: No change required. If "N/A", set to empty string.

**IMPORTANT:**
- Return ONLY a valid JSON object, with NO extra text, code fences, or comments.
- Every key and string value must be enclosed in double quotes (").
- All arrays and objects must have correct JSON syntax.
- Do not include trailing commas.
- If a field is missing or not applicable, use the default value as specified in the schema.
- Do not invent or guess field names. Only use those in the schema.
- Before returning, validate your output to ensure it is valid JSON and matches the schema exactly.
- Return ONLY a valid JSON object with all fields from the schema and NOTHING ELSE."""

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

def process_discount_with_groq(discount: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
    """
    Send a discount object to Groq API using JSON Mode and get back an edited version.
    
    Args:
        discount: A discount object from the JSON file
        max_retries: Maximum number of retry attempts (default: 2)
        
    Returns:
        The edited discount object from Groq
    """
    global current_model_index  # Use the global variable
    
    # Force disable Groq client's internal logging right before we use it
    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("groq._base_client").setLevel(logging.WARNING)
    
    models = ["llama3-70b-8192", "llama3-8b-8192", "llama-3.1-8b-instant", 
              "llama-3.3-70b-versatile", "gemma2-9b-it"]
    
    system_message = MESSAGE_TEMPLATE
    
    discount_id = discount.get('discount_id', 'unknown')
    user_message = f"Please enhance this discount object according to the instructions:\n{json.dumps(discount, indent=2, ensure_ascii=False)}"
    
    retry_count = 0
    while retry_count <= max_retries:
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            current_model = models[current_model_index]
            
            # Log when sending a new object to the API with discount ID
            logger.info(f"Sending discount ID: {discount_id} to Groq API using model: {current_model}")
            
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
            return json.loads(response_content)
                
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
                # Log specifically when making the second retry attempt
                if retry_count == 2:
                    logger.info(f"Making final retry (attempt {retry_count} of {max_retries}) for discount ID: {discount_id}")
                else:
                    logger.warning(f"{error_message}\nRetrying attempt {retry_count} of {max_retries}...")
                time.sleep(2)  # Add a slightly longer delay before retrying
            else:
                logger.error(f"{error_message}\nMax retries exceeded. Using original discount.")
                return discount
    
    return discount

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
        
        # Process with Groq with retry mechanism
        edited_discount = process_discount_with_groq(discount, max_retries=2)
        
        # Check if the discount is the original one (indicating failed processing)
        if edited_discount is discount:
            logger.warning(f"Failed to enhance discount ID: {discount_id}")
            deprecated_discount_ids.append(discount_id)
            continue
        
        # successfully processed, add it to our list
        enhanced_discounts.append(edited_discount)
        
        # Add a small delay to avoid rate limits
        time.sleep(1)
    
    # Save successfull enhanced discounts
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
    """Find all JSON files in the data directory and its subdirectories"""
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
            if file.lower().endswith('.json'):
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    
    log_checkpoint(f"Found {len(json_files)} JSON files")
    
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