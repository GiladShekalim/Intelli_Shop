#!/usr/bin/env python3
"""
Test script for AI Filter Helper functionality
This script tests the improved AI Filter Helper with various text inputs
"""

import os
import sys
import django
from dotenv import load_dotenv

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from intellishop.utils.groq_helper import extract_filters_from_text, select_percentage_bucket

def test_percentage_bucket_selection():
    """Test the percentage bucket selection function"""
    print("=== Testing Percentage Bucket Selection ===")
    
    test_cases = [
        ("I want 50% off electronics", "between_50_60"),
        ("Show me discounts with 30% or more", "between_30_40"),
        ("Looking for 20% discounts", "between_20_30"),
        ("Any discount will do", "up_to_20"),
        ("I need 60% off", "more_than_60"),
        ("Save 15% on travel", "up_to_20"),
        ("No specific percentage mentioned", ""),
    ]
    
    for text, expected in test_cases:
        result = select_percentage_bucket(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected: {expected})")

def test_ai_filter_extraction():
    """Test the AI filter extraction with various inputs"""
    print("\n=== Testing AI Filter Extraction ===")
    
    test_cases = [
        "I want electronics discounts for students under 200 shekels",
        "Show me travel discounts with 30% or more off",
        "Family discounts for home and garden",
        "Student discounts on books",
        "Senior discounts with 50% off",
        "Just show me all discounts",
        "Young people electronics with discount",
        "Fitness discounts for remote workers",
    ]
    
    for text in test_cases:
        print(f"\nTesting: '{text}'")
        try:
            filters = extract_filters_from_text(text)
            print(f"Result: {filters}")
            
            # Check if percentage_range is properly set
            if filters.get('percentage_range'):
                print(f"  ✓ Percentage range: {filters['percentage_range']}")
            else:
                # Check if it should have percentage_range
                discount_terms = ['discount', 'off', 'sale', 'reduced', 'save', 'deal', '%', 'percent']
                if any(term in text.lower() for term in discount_terms):
                    print(f"  ⚠ Should have percentage_range but doesn't")
                else:
                    print(f"  ✓ No percentage_range (expected)")
            
            # Check if we have comprehensive statuses and interests
            if filters.get('statuses'):
                print(f"  ✓ Statuses: {filters['statuses']}")
            if filters.get('interests'):
                print(f"  ✓ Interests: {filters['interests']}")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")

if __name__ == "__main__":
    print("AI Filter Helper Test Suite")
    print("=" * 50)
    
    # Check if GROQ_API_KEY is set
    if not os.environ.get("GROQ_API_KEY"):
        print("⚠️  GROQ_API_KEY not set. Some tests may fail.")
        print("Set your GROQ_API_KEY environment variable to test AI functionality.")
    
    test_percentage_bucket_selection()
    test_ai_filter_extraction()
    
    print("\n" + "=" * 50)
    print("Test completed!") 