from dotenv import load_dotenv
import os
from groq import Groq
import json
import logging
import time
from typing import Dict, List, Any

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

CATEGORIES = """{Consumerism, Travel and Vacation, Culture and Leisure, Cars, Insurance, Finance and Banking}"""
CONSUMER_STATUS = """{Young, Senior, Homeowner, Traveler, Tech, Pets, Fitness, Student, Remote, Family}"""
DISCOUNT_TYPE = """{fixed_amount, percentage, buy_one_get_one, Cost}"""

MESSAGE_TEMPLATE = """Instructions: You are an AI tool connected via API to my project. Your task is to process the attached coupon JSON object according to the following precise requirements. For each field, handle, organize, and validate as instructed below. Return the edited coupon object in JSON format, perfectly adhering to the schema and requirements. All data must be either as requested or set to the specified default value for each field-no omissions or errors are allowed, as this data will go directly into validation and a database.
Field-by-Field Instructions
discount_id:
No change required.
If value is "N/A", set to empty string.
title:
No change required.
If value is "N/A", set to empty string.
price:
Extract the discount amount from the description field.
Assign an integer value according to the discount type:
fixed_amount: Must be > 0
percentage: Must be 1–100
buy_one_get_one: Must be 1
Cost: Must be > 0
discount_type:
Extract from the description field.
Assign one value only from: {DISCOUNT_TYPE}
description:
No change required.
If value is "N/A", set to empty string.
image_link:
No change required.
If value is "N/A", set to empty string.
discount_link:
No change required.
If value is "N/A", set to empty string.
terms_and_conditions:
No change required.
If value is "N/A", set to "See provider website for details".
club_name:
No change required.
If value is "N/A", set to an empty array.
category:
Analyze the title and description.
Select all relevant categories from: {CATEGORIES}
Use exact names, and include as many relevant categories as possible.
consumer_statuses:
Analyze the title and description.
Select all applicable statuses from: {CONSUMER_STATUS}
Use exact names, and include all that apply.
valid_until:
No change required.
If value is "N/A", set to empty string.
usage_limit:
No change required.
If value is "N/A", set to null.
coupon_code:
No change required.
If value is "N/A", set to empty string.
provider_link:
No change required.
If value is "N/A", set to empty string.

Output Requirements
Return the edited coupon object in valid JSON format.
Ensure all fields are present and correctly set as per above.
The "category" and "consumer_statuses" fields must use only values from their respective lists, and include all that apply.
The "price" field must be an integer, and "discount_type" must be a single value from the enum.
Unchanged fields must retain their original values unless "N/A", in which case use the specified default.

Coupon Object:
{JSON_SCHEMA}


Please process the following coupon object according to the instructions above and return the validated, edited JSON object:
{json_object}
"""

# Load environment variables
load_dotenv()

def process_discount_with_groq(discount: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a discount object to Groq API and get back an edited version.
    
    Args:
        discount: A discount object from the JSON file
        
    Returns:
        The edited discount object from Groq
    """
    # Format the message template with the JSON object and required schema/categories
    formatted_message = MESSAGE_TEMPLATE.format(
        JSON_SCHEMA=JSON_SCHEMA,
        CATEGORIES=CATEGORIES,
        CONSUMER_STATUS=CONSUMER_STATUS,
        DISCOUNT_TYPE=DISCOUNT_TYPE,
        json_object=json.dumps(discount, indent=2, ensure_ascii=False)
    )
    
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": formatted_message
                }
            ],
            model="llama3-70b-8192",
            max_tokens=2048,
        )
        
        # Extract the response content
        response_content = chat_completion.choices[0].message.content
        
        # Handle potential JSON formatting issues by extracting only the JSON part
        try:
            # Try to parse directly first
            edited_discount = json.loads(response_content)
            return edited_discount
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from potential code blocks or explanations
            if "```json" in response_content:
                json_content = response_content.split("```json")[1].split("```")[0].strip()
            elif "```" in response_content:
                json_content = response_content.split("```")[1].split("```")[0].strip()
            else:
                # Try to find JSON object between curly braces
                start_idx = response_content.find('{')
                end_idx = response_content.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_content = response_content[start_idx:end_idx]
                else:
                    print(f"Could not find valid JSON in response for discount ID {discount.get('discount_id')}")
                    return discount
                    
            try:
                edited_discount = json.loads(json_content)
                return edited_discount
            except json.JSONDecodeError as e:
                print(f"Warrning: extracted JSON: {e}")
                return discount
            
    except Exception as e:
        print(f"Error processing discount with ID {discount.get('discount_id')}: {e}")
        return discount  # Return the original discount if processing fails

def update_discounts_file(input_file_path: str, output_file_path: str) -> None:
    """
    Process each discount in the JSON file with Groq and create a new file with updated discounts.
    
    Args:
        input_file_path: Path to the original hot_discounts.json file
        output_file_path: Path to the new Inhanced_discounts.json file
    """
    # Load the original JSON file
    with open(input_file_path, 'r', encoding='utf-8') as f:
        discounts = json.load(f)
    
    # Create a deep copy of the discounts for our enhanced version
    enhanced_discounts = json.loads(json.dumps(discounts))
    
    total_discounts = len(discounts)
    print(f"Processing {total_discounts} discounts...")
    
    # Process each discount one by one
    for i, discount in enumerate(enhanced_discounts):
        discount_id = discount.get('discount_id', 'unknown')
        print(f"Processing discount {i+1}/{total_discounts} (ID: {discount_id})...")
        
        # Process with Groq
        edited_discount = process_discount_with_groq(discount)
        
        # Update only specific fields in the discount
        fields_to_update = [
            'price', 
            'discount_type', 
            'category', 
            'consumer_statuses'
        ]
        
        for field in fields_to_update:
            if field in edited_discount:
                discount[field] = edited_discount[field]
        
        # Add a small delay to avoid rate limits
        time.sleep(1)
    
    # Save the enhanced discounts to the new file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_discounts, f, ensure_ascii=False, indent=2)
    
    print(f"All {total_discounts} discounts have been processed and saved to {output_file_path}!")

if __name__ == "__main__":
    # Set the paths to your input and output files
    input_file_path = "hot_discounts.json"
    output_file_path = "Inhanced_discounts.json"
    
    # Process and create the enhanced file
    update_discounts_file(input_file_path, output_file_path) 