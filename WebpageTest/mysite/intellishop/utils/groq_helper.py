"""
AI Filter Helper Utility
This module provides functionality to use Groq API for extracting filter parameters from user text input.
It reuses the Groq API infrastructure from groq_chat.py but with a specific prompt for filter extraction.
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional
from groq import Groq
from dotenv import load_dotenv
from intellishop.models.constants import (
    CATEGORIES, 
    CONSUMER_STATUS, 
    FILTER_CONFIG,
    get_categories_string,
    get_consumer_status_string
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Get formatted strings for the prompt
CATEGORIES_STRING = get_categories_string()
CONSUMER_STATUS_STRING = get_consumer_status_string()

# Define the filter extraction prompt
FILTER_EXTRACTION_PROMPT = f"""You are an AI assistant that helps users set filters for a discount search system.

Given a user's text query, analyze it and return a JSON object with relevant filter parameters.
Only include fields that are relevant to the user's query. If no relevant filters are found, return an empty object {{}}.

Available filter fields and their possible values:

1. statuses (array): Consumer statuses that match the user's description
   Possible values: {CONSUMER_STATUS_STRING}
   
2. interests (array): Categories/interests that match the user's description  
   Possible values: {CATEGORIES_STRING}
   
3. price_range (object): For fixed amount discounts, if user mentions price ranges
   Format: {{"enabled": true, "max_value": number}}
   
4. percentage_range (object): For percentage discounts, if user mentions percentage ranges
   Format: {{"enabled": true, "bucket": "bucket_name"}}
   Available buckets: {list(FILTER_CONFIG['PERCENTAGE_BUCKETS'].keys())}

**IMPORTANT RULES:**
- Return ONLY a valid JSON object, no extra text or explanations
- Use exact field names and values as specified above
- Only include fields that are clearly relevant to the user's query
- For price_range, extract the maximum amount mentioned
- For percentage_range, choose the most appropriate bucket based on percentages mentioned
- If user mentions "young people" or "students", include relevant statuses
- If user mentions "electronics" or "travel", include relevant interests
- If user mentions specific amounts like "under 100" or "up to 50%", set appropriate ranges

**EXAMPLE RESPONSES:**
User: "I want electronics discounts for students under 200 shekels"
Response: {{"statuses": ["Student"], "interests": ["electronics"], "price_range": {{"enabled": true, "max_value": 200}}}}

User: "Show me travel discounts with 30% or more off"
Response: {{"interests": ["Travel and Vacation"], "percentage_range": {{"enabled": true, "bucket": "between_30_40"}}}}

User: "Just show me all discounts"
Response: {{}}

User query: """

def extract_filters_from_text(user_text: str, max_retries: int = 2) -> Dict[str, Any]:
    """
    Extract filter parameters from user text using Groq API.
    
    Args:
        user_text (str): The user's text input
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        Dict[str, Any]: Filter parameters in the expected format
    """
    if not user_text or not user_text.strip():
        logger.warning("Empty user text provided")
        return {}
    
    # Disable Groq client's internal logging
    logging.getLogger("groq").setLevel(logging.WARNING)
    logging.getLogger("groq._base_client").setLevel(logging.WARNING)
    
    # Available models (same as in groq_chat.py)
    models = ["llama3-70b-8192", "llama3-8b-8192", "llama-3.1-8b-instant", 
              "llama-3.3-70b-versatile", "gemma2-9b-it"]
    
    current_model_index = 0
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            current_model = models[current_model_index]
            
            logger.info(f"Extracting filters from text using model: {current_model}")
            
            # Create the complete prompt
            system_message = FILTER_EXTRACTION_PROMPT
            user_message = user_text.strip()
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                model=current_model,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            response_content = chat_completion.choices[0].message.content
            extracted_filters = json.loads(response_content)
            
            # Validate the extracted filters
            validated_filters = validate_extracted_filters(extracted_filters)
            
            logger.info(f"Successfully extracted filters: {validated_filters}")
            return validated_filters
                
        except Exception as e:
            error_message = f"Error extracting filters from text: {str(e)}"
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str:
                # Move to the next model in the list
                prev_model = models[current_model_index]
                current_model_index = (current_model_index + 1) % len(models)
                new_model = models[current_model_index]
                logger.info(f"429 Too Many Requests: Switching model from {prev_model} to {new_model}")
                time.sleep(1)  # Brief pause before trying the next model
                continue
            
            if retry_count < max_retries:
                retry_count += 1
                logger.warning(f"{error_message}\nRetrying attempt {retry_count} of {max_retries}...")
                time.sleep(2)  # Add a slightly longer delay before retrying
            else:
                logger.error(f"{error_message}\nMax retries exceeded. Returning empty filters.")
                return {}
    
    return {}

def validate_extracted_filters(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize the extracted filters to ensure they match expected format.
    
    Args:
        filters (Dict[str, Any]): Raw filters from Groq API
        
    Returns:
        Dict[str, Any]: Validated and sanitized filters
    """
    validated = {}
    
    # Validate statuses
    if 'statuses' in filters and isinstance(filters['statuses'], list):
        statuses = [s for s in filters['statuses'] if s in CONSUMER_STATUS]
        if statuses:
            validated['statuses'] = statuses
    
    # Validate interests/categories
    if 'interests' in filters and isinstance(filters['interests'], list):
        interests = [i for i in filters['interests'] if i in CATEGORIES]
        if interests:
            validated['interests'] = interests
    
    # Validate price_range
    if 'price_range' in filters and isinstance(filters['price_range'], dict):
        price_range = filters['price_range']
        if price_range.get('enabled') and 'max_value' in price_range:
            try:
                max_value = float(price_range['max_value'])
                if max_value >= 0:
                    validated['price_range'] = {
                        'enabled': True,
                        'max_value': max_value
                    }
            except (ValueError, TypeError):
                pass
    
    # Validate percentage_range
    if 'percentage_range' in filters and isinstance(filters['percentage_range'], dict):
        percentage_range = filters['percentage_range']
        if percentage_range.get('enabled'):
            validated_percentage = {'enabled': True}
            
            # Validate bucket
            bucket = percentage_range.get('bucket')
            if bucket and bucket in FILTER_CONFIG['PERCENTAGE_BUCKETS']:
                validated_percentage['bucket'] = bucket
            
            # Validate max_value if present
            if 'max_value' in percentage_range:
                try:
                    max_value = float(percentage_range['max_value'])
                    if 0 <= max_value <= 100:
                        validated_percentage['max_value'] = max_value
                except (ValueError, TypeError):
                    pass
            
            if len(validated_percentage) > 1:  # More than just 'enabled'
                validated['percentage_range'] = validated_percentage
    
    return validated

def get_filter_schema() -> Dict[str, Any]:
    """
    Get the filter schema for frontend validation and documentation.
    
    Returns:
        Dict[str, Any]: Filter schema with available options
    """
    return {
        'statuses': CONSUMER_STATUS,
        'interests': CATEGORIES,
        'price_range': {
            'enabled': True,
            'max_value': 'number'
        },
        'percentage_range': {
            'enabled': True,
            'bucket': list(FILTER_CONFIG['PERCENTAGE_BUCKETS'].keys()),
            'max_value': 'number (0-100)'
        }
    } 