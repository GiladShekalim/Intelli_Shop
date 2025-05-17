from dotenv import load_dotenv
import os
from groq import Groq
import json
import logging

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

Coupon Object JSON Schema
{{
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
}}

Please process the following coupon object according to the instructions above and return the validated, edited JSON object:
{json_object}
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
        # Format the message with the current discount object
        message_to_send = MESSAGE_TEMPLATE.format(
            json_object=json.dumps(discount, ensure_ascii=False, indent=2),
            DISCOUNT_TYPE=DISCOUNT_TYPE,
            CATEGORIES=CATEGORIES,
            CONSUMER_STATUS=CONSUMER_STATUS
        )

        # Send the request to Groq API
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