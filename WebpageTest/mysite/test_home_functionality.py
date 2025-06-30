#!/usr/bin/env python
"""
Test script to verify the home page random filtering functionality
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from intellishop.models.mongodb_models import User, Coupon
from bson import ObjectId
import random

def test_home_functionality():
    """Test the home page filtering and randomization functionality"""
    print("Testing Home Page Functionality...")
    
    # Check if there are any users in the database
    users = list(User.find())
    print(f"Found {len(users)} users in database")
    
    if not users:
        print("No users found. Creating a test user...")
        # Create a test user
        user_id = User.create_user(
            username="testuser",
            password="testpass",
            email="test@example.com",
            status=["Student", "Tech"],
            age=25,
            location="Tel Aviv",
            hobbies=["electronics", "lifestyle"]
        )
        print(f"Created test user with ID: {user_id}")
        user = User.find_one({'_id': ObjectId(user_id)})
    else:
        user = users[0]
        print(f"Using existing user: {user.get('username')}")
    
    # Check if there are any coupons in the database
    all_coupons = list(Coupon.get_all())
    print(f"Found {len(all_coupons)} coupons in database")
    
    if not all_coupons:
        print("No coupons found in database. Please run the database initialization first.")
        return
    
    # Test the filtering logic
    print("\nTesting filtering logic...")
    
    # Build filters based on user preferences
    filters = {}
    
    # Add user statuses to filters
    user_statuses = user.get('status', [])
    if user_statuses:
        filters['statuses'] = user_statuses
        print(f"User statuses: {user_statuses}")
    
    # Add user hobbies/interests to filters
    user_hobbies = user.get('hobbies', [])
    if user_hobbies:
        filters['interests'] = user_hobbies
        print(f"User hobbies: {user_hobbies}")
    
    # Get filtered coupons
    if filters:
        print("Getting filtered coupons...")
        all_filtered_coupons = Coupon.get_filtered_coupons(filters)
        all_filtered_coupons = list(all_filtered_coupons)
        print(f"Found {len(all_filtered_coupons)} filtered coupons")
        
        # Test randomization
        if len(all_filtered_coupons) > 5:
            filtered_coupons = random.sample(all_filtered_coupons, 5)
            print(f"Randomly selected 5 coupons from {len(all_filtered_coupons)} available")
        else:
            filtered_coupons = all_filtered_coupons
            print(f"Using all {len(filtered_coupons)} available coupons")
    else:
        print("No filters applied, getting random coupons from all available")
        all_coupons = list(Coupon.get_all())
        if len(all_coupons) > 5:
            filtered_coupons = random.sample(all_coupons, 5)
            print(f"Randomly selected 5 coupons from {len(all_coupons)} available")
        else:
            filtered_coupons = all_coupons
            print(f"Using all {len(filtered_coupons)} available coupons")
    
    # Display sample of filtered coupons
    print(f"\nSample of {len(filtered_coupons)} filtered coupons:")
    for i, coupon in enumerate(filtered_coupons[:3]):  # Show first 3
        print(f"{i+1}. {coupon.get('title', 'No title')} - {coupon.get('price', 'No price')}")
        print(f"   Store: {coupon.get('club_name', ['Unknown'])[0] if coupon.get('club_name') else 'Unknown'}")
        print(f"   Categories: {coupon.get('category', [])}")
        print()
    
    print("Home page functionality test completed successfully!")
    print("You can now visit http://localhost:8000/home/ to see the filtered offers.")

if __name__ == "__main__":
    test_home_functionality() 