#!/usr/bin/env python
"""
Groq Enhancement Script for IntelliShop

This script enhances discount data using Groq API with improved rate limiting
and duplicate tracking to avoid processing the same discount multiple times.

Usage:
    python groq_enhancement.py [--data-dir PATH] [--reset-tracking] [--log-level LEVEL]
"""

import os
import sys
import logging
from pathlib import Path

# Add the project directory to the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

# Import the groq_chat module
try:
    from groq_chat import process_json_files, reset_global_tracking, RATE_LIMIT_CONFIG
except ImportError as e:
    print(f"Error importing groq_chat module: {e}")
    print("Make sure groq_chat.py is in the same directory")
    sys.exit(1)

def main():
    """Main function for Groq enhancement process"""
    print("🚀 Starting Groq Enhancement Process")
    print(f"Rate limit configuration: {RATE_LIMIT_CONFIG}")
    
    # Check for required environment variables
    if not os.environ.get("GROQ_API_KEY"):
        print("❌ Error: GROQ_API_KEY environment variable not set")
        print("Please set your Groq API key before running this script")
        sys.exit(1)
    
    # Check for data directory
    data_dir = os.environ.get('DISCOUNT_DATA_DIR')
    if not data_dir:
        # Try to find data directory automatically
        possible_paths = [
            os.path.join(SCRIPT_DIR, 'intellishop', 'data'),
            os.path.join(SCRIPT_DIR, 'data'),
            os.path.join(os.path.dirname(SCRIPT_DIR), 'data')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                data_dir = path
                print(f"📁 Found data directory: {data_dir}")
                break
    
    if not data_dir or not os.path.exists(data_dir):
        print("❌ Error: Could not find data directory")
        print("Please set DISCOUNT_DATA_DIR environment variable or ensure data directory exists")
        sys.exit(1)
    
    # Check for reset tracking flag
    reset_tracking = os.environ.get('RESET_GROQ_TRACKING', 'false').lower() == 'true'
    if reset_tracking:
        reset_global_tracking()
        print("🔄 Tracking state reset - starting fresh")
    
    try:
        # Process the files
        process_json_files(data_dir)
        print("✅ Groq enhancement process completed successfully!")
        return True
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error during Groq enhancement: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 