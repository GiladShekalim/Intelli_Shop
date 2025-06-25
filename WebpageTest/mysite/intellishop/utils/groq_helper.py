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
Be comprehensive and include ALL relevant filters that could match the user's intent.
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

**CRITICAL RULES FOR COMPREHENSIVE FILTERING:**
- Return ONLY a valid JSON object, no extra text or explanations
- Use exact field names and values as specified above
- Be INCLUSIVE: Include ALL relevant statuses and interests that could apply
- For statuses: If user mentions any demographic (young, student, family, etc.), include ALL relevant statuses
- For interests: If user mentions any category (electronics, travel, etc.), include ALL related interests
- For percentage_range: ANY mention of percentages, discounts, or "off" should trigger percentage_range
- For price_range: ANY mention of amounts, prices, or costs should trigger price_range

**PERCENTAGE DETECTION RULES - CRITICAL:**
- If user mentions ANY percentage (e.g., "20% off", "discount", "sale", "reduced price"), set percentage_range
- Choose the most appropriate bucket based on the percentage mentioned
- If no specific percentage is mentioned but discount is implied, use "up_to_20" as default
- Keywords that should trigger percentage_range: "discount", "off", "sale", "reduced", "percentage", "%", "save"
- ALWAYS include a valid bucket name from the available buckets list
- If unsure about percentage, default to "up_to_20" bucket

**COMPREHENSIVE CATEGORY MATCHING:**
- "electronics" → include ["electronics", "Consumerism", "Tech"]
- "travel" → include ["Travel and Vacation", "Culture and Leisure"]
- "home" → include ["home", "lifestyle", "Consumerism"]
- "fitness" → include ["Fitness", "lifestyle", "Consumerism"]
- "student" → include ["Student", "Young", "Family"]
- "family" → include ["Family", "Parent", "Homeowner"]
- "young" → include ["Young", "Student", "Single"]
- "senior" → include ["Senior", "Retiree", "Homeowner"]

**EXAMPLE RESPONSES:**
User: "I want electronics discounts for students under 200 shekels"
Response: {{"statuses": ["Student", "Young", "Tech"], "interests": ["electronics", "Consumerism", "Tech"], "price_range": {{"enabled": true, "max_value": 200}}, "percentage_range": {{"enabled": true, "bucket": "up_to_20"}}}}

User: "Show me travel discounts with 30% or more off"
Response: {{"interests": ["Travel and Vacation", "Culture and Leisure"], "percentage_range": {{"enabled": true, "bucket": "between_30_40"}}}}

User: "Family discounts for home and garden"
Response: {{"statuses": ["Family", "Parent", "Homeowner"], "interests": ["home", "lifestyle", "Consumerism"], "percentage_range": {{"enabled": true, "bucket": "up_to_20"}}}}

User: "Student discounts on books"
Response: {{"statuses": ["Student", "Young"], "interests": ["books", "Consumerism"], "percentage_range": {{"enabled": true, "bucket": "up_to_20"}}}}

User: "Senior discounts with 50% off"
Response: {{"statuses": ["Senior", "Retiree"], "percentage_range": {{"enabled": true, "bucket": "between_50_60"}}}}

User: "Just show me all discounts"
Response: {{}}

User query: """

def select_percentage_bucket(text: str) -> str:
    """
    Intelligently select a percentage bucket based on text analysis.
    
    Args:
        text (str): User text input
        
    Returns:
        str: Selected bucket name or empty string if no match
    """
    text_lower = text.lower()
    
    # Keywords that indicate percentage ranges
    percentage_keywords = {
        'more_than_60': ['60%', '60 percent', '60% or more', 'over 60', 'above 60', '60+', 'sixty percent'],
        'between_50_60': ['50%', '50 percent', '50-60', '50 to 60', 'fifty percent', '55%', '55 percent'],
        'between_40_50': ['40%', '40 percent', '40-50', '40 to 50', 'forty percent', '45%', '45 percent'],
        'between_30_40': ['30%', '30 percent', '30-40', '30 to 40', 'thirty percent', '35%', '35 percent'],
        'between_20_30': ['20%', '20 percent', '20-30', '20 to 30', 'twenty percent', '25%', '25 percent'],
        'up_to_20': ['10%', '10 percent', '15%', '15 percent', '20%', '20 percent', 'up to 20', 'under 20', 'less than 20']
    }
    
    # Check for specific percentage mentions
    for bucket, keywords in percentage_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                logger.info(f"Found percentage keyword '{keyword}' in text, selecting bucket: {bucket}")
                return bucket
    
    # Check for general discount terms that should default to a lower percentage
    general_discount_terms = ['discount', 'off', 'sale', 'reduced', 'save', 'deal']
    for term in general_discount_terms:
        if term in text_lower:
            logger.info(f"Found general discount term '{term}' in text, defaulting to up_to_20 bucket")
            return 'up_to_20'
    
    return ''

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
            
            # If percentage_range is missing but should be included based on text analysis
            if not validated_filters.get('percentage_range') and any(term in user_text.lower() for term in ['discount', 'off', 'sale', 'reduced', 'save', 'deal', '%', 'percent']):
                selected_bucket = select_percentage_bucket(user_text)
                if selected_bucket:
                    validated_filters['percentage_range'] = {
                        'enabled': True,
                        'bucket': selected_bucket
                    }
                    logger.info(f"✓ Added missing percentage_range with bucket: {selected_bucket}")
                else:
                    # Default to up_to_20 if no specific bucket can be determined
                    validated_filters['percentage_range'] = {
                        'enabled': True,
                        'bucket': 'up_to_20'
                    }
                    logger.info("✓ Added default percentage_range with 'up_to_20' bucket")
            
            # Additional check: if percentage_range exists but has no bucket, add one
            if validated_filters.get('percentage_range') and validated_filters['percentage_range'].get('enabled') and not validated_filters['percentage_range'].get('bucket'):
                selected_bucket = select_percentage_bucket(user_text)
                if selected_bucket:
                    validated_filters['percentage_range']['bucket'] = selected_bucket
                    logger.info(f"✓ Added missing bucket to existing percentage_range: {selected_bucket}")
                else:
                    validated_filters['percentage_range']['bucket'] = 'up_to_20'
                    logger.info("✓ Added default bucket 'up_to_20' to existing percentage_range")
            
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
            logger.info(f"Validated statuses: {statuses}")
    
    # Validate interests/categories
    if 'interests' in filters and isinstance(filters['interests'], list):
        interests = [i for i in filters['interests'] if i in CATEGORIES]
        if interests:
            validated['interests'] = interests
            logger.info(f"Validated interests: {interests}")
    
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
                    logger.info(f"Validated price_range: {validated['price_range']}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid price_range max_value: {price_range.get('max_value')}")
    
    # Validate percentage_range - improved validation with better logging
    if 'percentage_range' in filters and isinstance(filters['percentage_range'], dict):
        percentage_range = filters['percentage_range']
        logger.info(f"Processing percentage_range: {percentage_range}")
        
        if percentage_range.get('enabled'):
            validated_percentage = {'enabled': True}
            
            # Validate bucket - this is the most important part
            bucket = percentage_range.get('bucket')
            if bucket and bucket in FILTER_CONFIG['PERCENTAGE_BUCKETS']:
                validated_percentage['bucket'] = bucket
                logger.info(f"✓ Validated percentage bucket: {bucket}")
            else:
                # If no valid bucket but percentage_range is enabled, try to infer one
                logger.warning(f"Invalid or missing percentage bucket: {bucket}. Available buckets: {list(FILTER_CONFIG['PERCENTAGE_BUCKETS'].keys())}")
                
                # Try to infer a bucket from max_value if present
                if 'max_value' in percentage_range:
                    try:
                        max_value = float(percentage_range['max_value'])
                        if 0 <= max_value <= 100:
                            # Map max_value to appropriate bucket
                            if max_value >= 60:
                                inferred_bucket = 'more_than_60'
                            elif max_value >= 50:
                                inferred_bucket = 'between_50_60'
                            elif max_value >= 40:
                                inferred_bucket = 'between_40_50'
                            elif max_value >= 30:
                                inferred_bucket = 'between_30_40'
                            elif max_value >= 20:
                                inferred_bucket = 'between_20_30'
                            else:
                                inferred_bucket = 'up_to_20'
                            
                            validated_percentage['bucket'] = inferred_bucket
                            logger.info(f"✓ Inferred percentage bucket from max_value {max_value}: {inferred_bucket}")
                        else:
                            logger.warning(f"Invalid max_value for percentage: {max_value}")
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid max_value format: {percentage_range.get('max_value')}")
                else:
                    # Default to up_to_20 if no bucket and no max_value
                    validated_percentage['bucket'] = 'up_to_20'
                    logger.info("✓ Defaulting to 'up_to_20' bucket for percentage_range")
            
            # Validate max_value if present
            if 'max_value' in percentage_range:
                try:
                    max_value = float(percentage_range['max_value'])
                    if 0 <= max_value <= 100:
                        validated_percentage['max_value'] = max_value
                        logger.info(f"✓ Validated percentage max_value: {max_value}")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid percentage max_value: {percentage_range.get('max_value')}")
            
            # Only include if we have a valid bucket
            if 'bucket' in validated_percentage:
                validated['percentage_range'] = validated_percentage
                logger.info(f"✓ Final validated percentage_range: {validated_percentage}")
            else:
                logger.warning("✗ Percentage range enabled but no valid bucket found")
    
    logger.info(f"Final validated filters: {validated}")
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