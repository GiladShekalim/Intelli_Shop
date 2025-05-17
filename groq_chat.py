from dotenv import load_dotenv
import os
from groq import Groq
import json
import logging

TITLE = """FLASH50: Half-Price Frenzy!"""
DESCRIPTION = """Grab your favorite items at unbeatable prices! For the next 24 hours, enjoy a whopping 50% off on all products storewide. Whether you're eyeing that stylish jacket or the latest tech gadget, now's your chance to snag it for half the price. But hurry, this offer vanishes at midnight! Use code FLASH50 at checkout to unlock your savings. Don't miss out on this lightning-fast deal – shop now before time runs out!"""    
CATEGORIES = """["Home & Furniture","Electronics & Gadgets","Fashion & Apparel","Beauty & Personal Care","Groceries & Food","Health & Wellness","Sports & Outdoors","Toys & Games","Books & Media","Automotive & Tools","Pet Supplies","Office & School Supplies","Jewelry & Accessories","Baby & Kids","Garden & Outdoor Living"]"""
CONSUMER_STATUS = """["Student","Parent","Retiree","Professional","Homeowner","Renter","Newlywed","Single","Military/Veteran","Entrepreneur","Unemployed","Caregiver","Digital Nomad","First-time Buyer","Empty Nester"]"""
MESSAGE_TO_SEND = f"""Instructions: You are an AI tool connected via API to my project. Your task is to process the attached coupon JSON object according to the following precise requirements. For each field, handle, organize, and validate as instructed below. Return the edited coupon object in JSON format, perfectly adhering to the schema and requirements. All data must be either as requested or set to the specified default value for each field-no omissions or errors are allowed, as this data will go directly into validation and a database.
Field-by-Field Instructions
discount_id:
No change required.
If value is "N\A", set to empty string.
title:
No change required.
If value is "N\A", set to empty string.
price:
Extract the discount amount from the description field.
Assign an integer value according to the discount type:
fixed_amount: Must be > 0
percentage: Must be 1–100
buy_one_get_one: Must be 1
Cost: Must be > 0
discount_type:
Extract from the description field.
Assign one value only from: {fixed_amount, percentage, buy_one_get_one, Cost}
description:
No change required.
If value is "N\A", set to empty string.
image_link:
No change required.
If value is "N\A", set to empty string.
discount_link:
No change required.
If value is "N\A", set to empty string.
terms_and_conditions:
No change required.
If value is "N\A", set to "See provider website for details".
club_name:
No change required.
If value is "N\A", set to an empty array.
category:
Analyze the title and description.
Select all relevant categories from:
{Consumerism, Travel and Vacation, Culture and Leisure, Cars, Insurance, Finance and Banking}
Use exact names, and include as many relevant categories as possible.
consumer_statuses:
Analyze the title and description.
Select all applicable statuses from:
{Young, Senior, Homeowner, Traveler, Tech, Pets, Fitness, Student, Remote, Family}
Use exact names, and include all that apply.
valid_until:
No change required.
If value is "N\A", set to empty string.
usage_limit:
No change required.
If value is "N\A", set to null.
coupon_code:
No change required.
If value is "N\A", set to empty string.
provider_link:
No change required.
If value is "N\A", set to empty string.

Output Requirements
Return the edited coupon object in valid JSON format.
Ensure all fields are present and correctly set as per above.
The "category" and "consumer_statuses" fields must use only values from their respective lists, and include all that apply.
The "price" field must be an integer, and "discount_type" must be a single value from the enum.
Unchanged fields must retain their original values unless "N\A", in which case use the specified default.

Coupon Object JSON Schema
{
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
}

Please process the following coupon object according to the instructions above and return the validated, edited JSON object:
{json.dumps(discount, ensure_ascii=False, indent=2)}
"""





# Load environment variables
load_dotenv()


def send_chat_message(message: str) -> dict | None:
    """
    Send a message to Groq API and receive JSON response.

    Args:
        message (str): The message to send to the AI

    Returns:
        dict | None: Parsed JSON response from the API, or None if error occurs
    """
    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
        completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": message
            }],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        return json.loads(completion.choices[0].message.content)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    # Load the discounts data
    with open('hot_discounts.json', 'r', encoding='utf-8') as f:
        discount_objects = json.load(f)

    results = []

    # Process each discount object
    for discount in discount_objects:
        # Replace the hardcoded message with the current discount object
        message_to_send = f"""Please process the following coupon object according to the instructions above and return the validated, edited JSON object:
        {json.dumps(discount, ensure_ascii=False, indent=2)}"""

        # The rest of your code to send the request to Groq API
        response = send_chat_message(message_to_send)
        if response:
            print("\nAI's API Response:")
            print(json.dumps(response, indent=2))
            results.append(response)

    # Save all results to a single file
    with open('processed_discounts.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main() 