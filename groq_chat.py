from dotenv import load_dotenv
import os
from groq import Groq
import json
import logging
import time
from typing import Dict, List, Any
import re
from constants import (
    JSON_SCHEMA, 
    get_categories_string,
    get_consumer_status_string,
    get_discount_type_string
)

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

current_model_index = 0

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
    
    # List of available models to cycle through when hitting rate limits
    models = ["llama3-70b-8192", "llama3-8b-8192", "llama-3.1-8b-instant", 
              "llama-3.3-70b-versatile", "gemma2-9b-it"]
    # current_model_index now defined globally instead of here
    
    # System message with schema description and instructions
    system_message = MESSAGE_TEMPLATE

    # User message with the discount object
    user_message = f"Please enhance this discount object according to the instructions:\n{json.dumps(discount, indent=2, ensure_ascii=False)}"
    
    retry_count = 0
    while retry_count <= max_retries:
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            current_model = models[current_model_index]
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                model=current_model,
                max_tokens=2048,
                # Enable JSON Mode by setting the response format
                response_format={"type": "json_object"}
            )
            
            # With JSON Mode, we can directly parse the response content
            response_content = chat_completion.choices[0].message.content
            return json.loads(response_content)
                
        except Exception as e:
            error_message = f"Error processing discount with ID {discount.get('discount_id')}: {str(e)}"
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str and "rate_limit_exceeded" in error_str:
                # Move to the next model in the list
                current_model_index = (current_model_index + 1) % len(models)
                print(f"{error_message}\nSwitching to model: {models[current_model_index]}")
                time.sleep(1)  # Brief pause before trying the next model
                continue
            
            if retry_count < max_retries:
                retry_count += 1
                print(f"{error_message}\nRetrying attempt {retry_count} of {max_retries}...")
                time.sleep(2)  # Add a slightly longer delay before retrying
            else:
                print(f"{error_message}\nMax retries exceeded. Using original discount.")
                # If all retries fail, return the original discount
                return discount
    
    # This line should never be reached, but included for completeness
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
    print(f"Processing {total_discounts} discounts...")
    
    # Process each discount one by one
    for i, discount in enumerate(discounts):
        discount_id = discount.get('discount_id', 'unknown')
        print(f"Processing discount {i+1}/{total_discounts} (ID: {discount_id})...")
        
        # Process with Groq with retry mechanism
        edited_discount = process_discount_with_groq(discount, max_retries=2)
        
        # Check if the discount is the original one (indicating failed processing)
        if edited_discount is discount:
            print(f"Skipping discount {discount_id} due to processing failure.")
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
    
    print(f"\nSummary:")
    print(f"Total discounts parsed: {total_discounts}")
    print(f"Total discounts deprecated: {deprecated_count}")
    
    if deprecated_count > 0:
        print(f"Deprecated discount IDs: {', '.join(deprecated_discount_ids)}")
    
    print(f"Processing complete: {successful_count} discounts saved to {output_file_path}.")

if __name__ == "__main__":
    # Set the paths to your input and output files
    input_file_path = "hot_discounts.json"
    output_file_path = "enhanced_discounts.json"
    
    # Process and create the enhanced file
    update_discounts_file(input_file_path, output_file_path) 