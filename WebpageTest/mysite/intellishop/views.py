# View functions that handle HTTP requests and return responses
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models.mongodb_models import User, Coupon
import json
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
import csv
import os
from datetime import datetime
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from intellishop.models.constants import FILTER_CONFIG
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'intellishop/index.html')

def index_home(request):
    # Get user details from session
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    # Get user from MongoDB
    user = User.find_one({'_id': ObjectId(user_id)})
    if not user:
        return redirect('login')

    # Build filters based on user preferences
    filters = {}
    
    # Add user statuses to filters
    user_statuses = user.get('status', [])
    if user_statuses:
        filters['statuses'] = user_statuses
    
    # Add user hobbies/interests to filters
    user_hobbies = user.get('hobbies', [])
    if user_hobbies:
        filters['interests'] = user_hobbies
    
    # Get filtered coupons from MongoDB
    filtered_coupons = []
    try:
        if filters:
            # Use the existing filtering system
            all_filtered_coupons = Coupon.get_filtered_coupons(filters)
            
            # Convert to list and randomize
            all_filtered_coupons = list(all_filtered_coupons)
            
            # Randomly select up to 5 coupons
            import random
            if len(all_filtered_coupons) > 5:
                filtered_coupons = random.sample(all_filtered_coupons, 5)
            else:
                filtered_coupons = all_filtered_coupons
        else:
            # If no filters, get random coupons from all available
            all_coupons = list(Coupon.get_all())
            import random
            if len(all_coupons) > 5:
                filtered_coupons = random.sample(all_coupons, 5)
            else:
                filtered_coupons = all_coupons
                
    except Exception as e:
        logger.error(f"Error getting filtered coupons: {str(e)}")
        # Fallback to empty list if there's an error
        filtered_coupons = []

    # Format coupons for display
    formatted_coupons = []
    for coupon in filtered_coupons:
        try:
            # Format the amount based on discount_type
            if coupon.get('discount_type') == 'percentage':
                amount = f"{coupon.get('price', 0)}%"
            else:
                amount = f"${coupon.get('price', 0)}"
            
            # Get store name from club_name array
            club_names = coupon.get('club_name', [])
            store_name = club_names[0] if club_names else "Unknown Store"
            
            formatted_coupon = {
                'store_name': store_name,
                'store_logo': coupon.get('image_link', ''),
                'code': coupon.get('coupon_code', ''),
                'amount': amount,
                'name': coupon.get('title', 'Special Offer'),
                'description': coupon.get('description', ''),
                'date_expires': coupon.get('valid_until', ''),
                'store_url': coupon.get('discount_link', ''),
                'discount_link': coupon.get('discount_link', ''),
                'minimum_amount': 0,  # Default value
                'discount_id': coupon.get('discount_id', ''),
                'terms_and_conditions': coupon.get('terms_and_conditions', ''),
                'usage_limit': coupon.get('usage_limit', None),
                'price': coupon.get('price', 0),  # Ensure price is passed
                'discount_type': coupon.get('discount_type', ''),  # Ensure discount_type is passed
            }
            formatted_coupons.append(formatted_coupon)
        except Exception as e:
            logger.error(f"Error formatting coupon: {str(e)}")
            continue

    context = {
        'user': {
            'email': user.get('email'),
            'status': user.get('status', []),
            'hobbies': user.get('hobbies', [])
        },
        'filtered_coupons': formatted_coupons
    }
    
    return render(request, 'intellishop/index_home_original.html', context)

def login_view(request):
    # If user is already logged in, redirect to home
    if request.session.get('user_id'):
        return redirect('index_home')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("\n=== FULL DEBUG ===")
            print("Attempting login with:", data)
            
            # Find user and print raw result
            collection = User.get_collection()
            raw_user = collection.find_one({'email': data['email']})
            print("Raw MongoDB result:", raw_user)
            
            user = User.find_one({'email': data['email']})
            print("User object:", user)
            
            print("=== Login Debug ===")
            print("1. Login attempt with email:", data['email'])
            print("2. Provided password:", data['password'])
            
            # Find user by email only first
            if user:
                print("4. User details:", {
                    'username': user.get('username'),
                    'email': user.get('email'),
                    'password': user.get('password'),
                    'status': user.get('status')
                })
                
                stored_password = user.get('password', '')
                input_password = data.get('password', '')
                print("5. Password comparison:")
                print(f"   - Stored password: '{stored_password}'")
                print(f"   - Input password: '{input_password}'")
                print(f"   - Length of stored password: {len(stored_password)}")
                print(f"   - Length of input password: {len(input_password)}")
                print(f"   - Are passwords equal? {stored_password == input_password}")
                
                if stored_password == input_password:
                    request.session['user_id'] = str(user['_id'])
                    request.session['username'] = user['username']
                    
                    # Debug session data
                    print("=== SESSION DEBUG ===")
                    print("Session ID:", request.session.session_key)
                    print("All session data:", dict(request.session))
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': f"Welcome back {user['username']}",
                        'redirect': '/home/',
                        'user_id': str(user['_id'])
                    })
                else:
                    print("6. Password mismatch")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Wrong Email/Password'
                    }, status=400)
            else:
                print("3. No user found with this email")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Wrong Email/Password'
                }, status=400)
                
        except Exception as e:
            print("Login error:", str(e))
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
            
    return render(request, 'intellishop/login.html')

def register(request):
    # If user is already logged in, redirect to home
    if request.session.get('user_id'):
        return redirect('index_home')
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Registration data:", data)  # Debug log
            
            # Check if user already exists
            existing_user = User.get_by_username(data['username'])
            if existing_user is not None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username already exists'
                }, status=400)
            
            existing_email = User.get_by_email(data['email'])
            if existing_email is not None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already exists'
                }, status=400)
            
            # Create new user in MongoDB
            user_id = User.create_user(
                username=data['username'],
                password=data['password'],
                email=data['email'],
                status=data['status'],
                age=data['age'],
                location=data['location'],
                hobbies=data['hobbies']
            )
            print("Created user with ID:", user_id)  # Debug log
            
            return JsonResponse({
                'status': 'success', 
                'message': 'User registered successfully',
                'user_id': str(user_id)
            })
            
        except Exception as e:
            print("Registration error:", str(e))  # Debug log
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    
    return render(request, 'intellishop/register.html')

def dashboard(request):
    try:
        # Get all users from MongoDB without any sorting
        users = list(User.find())  # Convert cursor to list immediately
        
        # Process the users
        users_list = []
        for user in users:
            if user is not None:
                # Convert ObjectId to string and ensure all fields exist
                user_data = {
                    'username': user.get('username', ''),
                    'email': user.get('email', ''),
                    'password': user.get('password', ''),
                    'status': user.get('status', ''),
                    'age': user.get('age', ''),
                    'location': user.get('location', ''),
                    'hobbies': user.get('hobbies', []),
                    '_id': str(user.get('_id', '')),
                    'date_created': user.get('created_at', '')
                }
                users_list.append(user_data)
        
        # Debug: Print hobby values for each user
        for user_data in users_list:
            print(f"User {user_data.get('username')}: Hobbies = {user_data.get('hobbies')}")

        return render(request, 'intellishop/dashboard.html', {'users': users_list})
        
    except Exception as e:
        # Handle any errors and return an error message
        return render(request, 'intellishop/dashboard.html', {
            'users': [],
            'error': f"Error loading users: {str(e)}"
        })

def template(request):
    return render(request, 'intellishop/Site_template.html')

def aliexpress_coupons(request):
    code = request.GET.get('code')
    if code:
        # Get the specific coupon details from your JSON file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, 'intellishop', 'data', 'coupon_samples.json')
        
        # Add fallback path if the primary one doesn't exist
        if not os.path.exists(json_path):
            alt_json_path = os.path.join(base_dir, 'data', 'coupon_samples.json')
            if os.path.exists(alt_json_path):
                json_path = alt_json_path
        
        try:
            with open(json_path, 'r') as f:
                coupons = json.load(f)
                coupon = next((c for c in coupons if c['code'] == code), None)
                if coupon:
                    return render(request, 'intellishop/coupon_for_aliexpress.html', {'coupon': coupon})
        except Exception as e:
            print(f"Error loading coupon: {e}")
    
    return render(request, 'intellishop/coupon_for_aliexpress.html', {'error': 'Coupon not found'})

def get_club_names(request):
    """Get all unique club names from the database for the Stores dropdown"""
    try:
        # Get all unique club names from the coupons collection
        collection = Coupon.get_collection()
        if collection is None:
            return JsonResponse({'clubs': []})
        
        # Use aggregation to get unique club names
        pipeline = [
            {'$unwind': '$club_name'},  # Unwind the array
            {'$group': {'_id': '$club_name'}},  # Group by club name
            {'$sort': {'_id': 1}}  # Sort alphabetically
        ]
        
        unique_clubs = list(collection.aggregate(pipeline))
        clubs = [club['_id'] for club in unique_clubs if club['_id']]
        
        return JsonResponse({'clubs': clubs})
    except Exception as e:
        logger.error(f"Error getting club names: {str(e)}")
        return JsonResponse({'clubs': []})

def coupon_detail(request, club_name):
    """Display coupons for a specific club/provider"""
    try:
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')
        
        # Get user from MongoDB
        user = User.find_one({'_id': ObjectId(user_id)})
        if not user:
            return redirect('login')
        
        # Get coupons for this specific club - search within the club_name array
        club_coupons_raw = Coupon.find({'club_name': {'$in': [club_name]}})
        
        # Convert ObjectId to string for JSON serialization
        club_coupons = []
        for coupon in club_coupons_raw:
            if '_id' in coupon:
                coupon['_id'] = str(coupon['_id'])
            if coupon.get('discount_type') == 'percentage':
                amount = f"{coupon.get('price', 0)}%"
            else:
                amount = f"${coupon.get('price', 0)}"
            club_names = coupon.get('club_name', [])
            store_name = club_names[0] if club_names else "Unknown Store"
            formatted_coupon = {
                'store_name': store_name,
                'store_logo': coupon.get('image_link', ''),
                'code': coupon.get('coupon_code', ''),
                'amount': amount,
                'name': coupon.get('title', 'Special Offer'),
                'description': coupon.get('description', ''),
                'date_expires': coupon.get('valid_until', ''),
                'store_url': coupon.get('discount_link', ''),
                'discount_link': coupon.get('discount_link', ''),
                'minimum_amount': 0,
                'discount_id': coupon.get('discount_id', ''),
                'terms_and_conditions': coupon.get('terms_and_conditions', ''),
                'usage_limit': coupon.get('usage_limit', None),
                'price': coupon.get('price', 0),
                'discount_type': coupon.get('discount_type', ''),
            }
            club_coupons.append(formatted_coupon)
        
        # Format club name for display (capitalize first letter)
        display_name = club_name.title()
        
        context = {
            'user': user,
            'club_name': display_name,
            'club_coupons': club_coupons,
            'coupon_count': len(club_coupons)
        }
        
        return render(request, 'intellishop/club_coupons.html', context)
        
    except Exception as e:
        logger.error(f"Error in coupon_detail for club {club_name}: {str(e)}")
        return render(request, 'intellishop/club_coupons.html', {
            'club_name': club_name.title(),
            'club_coupons': [],
            'coupon_count': 0,
            'error': 'Error loading coupons'
        })

# FILTER PAGE
def filter_search(request):
    # Check if the user is logged in using custom session variable
    if not request.session.get('user_id'):
        return redirect('login')
    
    # Get filter statistics using the new method
    stats = Coupon.get_filter_statistics()
    
    context = {
        'min_price': int(stats['price_range']['min']),
        'max_price': int(stats['price_range']['max']),
        'percentage_counts': stats['percentage_counts'],
    }
    
    return render(request, 'intellishop/filter_search.html', context)

def profile_view(request):
    
    # Get user from session
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    user = User.find_one({'_id': ObjectId(user_id)})
    if not user:
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_username':
            new_username = request.POST.get('username')
            User.update_one(
                {'_id': ObjectId(user_id)}, 
                {'username': new_username}
            )
            
        elif action == 'update_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if user.get('password') == current_password and new_password == confirm_password:
                User.update_one(
                    {'_id': ObjectId(user_id)}, 
                    {'password': new_password}
                )
            
        elif action == 'delete_account':
            # Add email verification here
            User.delete_one({'_id': ObjectId(user_id)})
            return redirect('logout')

    context = {
        'username': user.get('username'),
        'email': user.get('email')
    }
    return render(request, 'intellishop/profile.html', context)

def logout_view(request):
    # Clear the session
    request.session.flush()
    # Redirect to home page or login page
    return redirect('login')

def coupon_code_view(request, code):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'intellishop', 'data', 'coupon_samples.json')
    
    # Add fallback path if the primary one doesn't exist
    if not os.path.exists(json_path):
        alt_json_path = os.path.join(base_dir, 'data', 'coupon_samples.json')
        if os.path.exists(alt_json_path):
            json_path = alt_json_path
    
    try:
        with open(json_path, 'r') as f:
            coupons = json.load(f)
            # Case-insensitive comparison
            coupon = next((c for c in coupons if c['code'].upper() == code.upper()), None)
            
            if coupon:
                formatted_coupon = {
                    'code': coupon['code'],
                    'amount': f"{coupon['amount']}%" if coupon['discount_type'] == 'percent' else f"${coupon['amount']}",
                    'minimum_amount': coupon['minimum_amount'],
                }
                return render(request, 'intellishop/coupon_code.html', {'coupon': formatted_coupon})
            
    except Exception as e:
        print(f"Error loading coupon: {e}")
    
    # If we get here, redirect to home instead of showing error
    return redirect('index_home')



# Favorites Page
def favorites_view(request):
    """Display user's favorite coupons"""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    user = User.find_one({'_id': ObjectId(user_id)})
    if not user:
        return redirect('login')
    favorite_ids = user.get('favorites', [])
    favorite_coupons = []
    if favorite_ids:
        raw_coupons = Coupon.find({'discount_id': {'$in': favorite_ids}})
        for coupon in raw_coupons:
            if coupon.get('discount_type') == 'percentage':
                amount = f"{coupon.get('price', 0)}%"
            else:
                amount = f"${coupon.get('price', 0)}"
            club_names = coupon.get('club_name', [])
            store_name = club_names[0] if club_names else "Unknown Store"
            formatted_coupon = {
                'store_name': store_name,
                'store_logo': coupon.get('image_link', ''),
                'code': coupon.get('coupon_code', ''),
                'amount': amount,
                'name': coupon.get('title', 'Special Offer'),
                'description': coupon.get('description', ''),
                'date_expires': coupon.get('valid_until', ''),
                'store_url': coupon.get('discount_link', ''),
                'discount_link': coupon.get('discount_link', ''),
                'minimum_amount': 0,
                'discount_id': coupon.get('discount_id', ''),
                'terms_and_conditions': coupon.get('terms_and_conditions', ''),
                'usage_limit': coupon.get('usage_limit', None),
                'price': coupon.get('price', 0),
                'discount_type': coupon.get('discount_type', ''),
            }
            favorite_coupons.append(formatted_coupon)
    context = {
        'user': user,
        'favorite_coupons': favorite_coupons,
        'favorite_count': len(favorite_coupons)
    }
    return render(request, 'intellishop/favorites.html', context)

@csrf_exempt
def show_all_discounts(request):
    # Fetch all coupons from MongoDB
    discounts = Coupon.get_all()
    # Convert ObjectId to string for JSON serialization
    for discount in discounts:
        if '_id' in discount:
            discount['_id'] = str(discount['_id'])
    return JsonResponse({'discounts': discounts})

@csrf_exempt
def filtered_discounts(request):
    """
    Get filtered discounts based on applied criteria with three search scenarios:
    1. Text-only: Find discounts where each word appears in text fields
    2. Parameters-only: Filter by categories, statuses, price, percentage (AND logic)
    3. Combined: Apply parameter filters first, then text search on filtered results
    
    Expected JSON payload:
    {
        "text_search": "electronics discount",  # Optional
        "statuses": ["Young", "Senior"],        # Optional
        "interests": ["Consumerism", "Travel and Vacation"],  # Optional
        "price_range": {                        # Optional
            "enabled": true,
            "max_value": 500
        },
        "percentage_range": {                   # Optional
            "enabled": true,
            "max_value": 50,
            "bucket": "between_30_40"
        }
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        filters = json.loads(request.body)
        
        # Validate filters
        validated_filters = _validate_filters(filters)
        
        # Determine search type for logging/debugging
        has_text = bool(validated_filters.get('text_search'))
        has_parameters = bool(
            validated_filters.get('statuses') or 
            validated_filters.get('interests') or 
            validated_filters.get('price_range') or 
            validated_filters.get('percentage_range')
        )
        
        if has_text and has_parameters:
            search_type = "Combined Search"
        elif has_text and not has_parameters:
            search_type = "Text-Only Search"
        elif not has_text and has_parameters:
            search_type = "Parameters-Only Search"
        else:
            search_type = "Show All"
        
        logger.info(f"Executing {search_type} with filters: {validated_filters}")
        
        # Get filtered coupons using the new logic
        discounts = Coupon.get_filtered_coupons(validated_filters)
        
        # Convert ObjectId to string for JSON serialization
        for discount in discounts:
            if '_id' in discount:
                discount['_id'] = str(discount['_id'])
        
        return JsonResponse({
            'discounts': discounts,
            'total_count': len(discounts),
            'applied_filters': validated_filters,
            'search_type': search_type
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in filtered_discounts: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

def _validate_filters(filters):
    """
    Validate and sanitize filter parameters
    
    Args:
        filters (dict): Raw filter data including text_search
        
    Returns:
        dict: Validated and sanitized filters
    """
    from intellishop.models.constants import CONSUMER_STATUS, CATEGORIES, FILTER_CONFIG
    
    validated = {}
    
    # Validate text search
    if filters.get('text_search'):
        text_search = filters['text_search'].strip()
        if text_search and len(text_search) >= FILTER_CONFIG['TEXT_SEARCH']['MIN_WORD_LENGTH']:
            validated['text_search'] = text_search
    
    # Validate statuses
    if filters.get('statuses'):
        statuses = [s for s in filters['statuses'] if s in CONSUMER_STATUS]
        if statuses:
            validated['statuses'] = statuses
    
    # Validate interests/categories
    if filters.get('interests'):
        interests = [i for i in filters['interests'] if i in CATEGORIES]
        if interests:
            validated['interests'] = interests
    
    # Validate price range
    if filters.get('price_range'):
        price_range = filters['price_range']
        if isinstance(price_range, dict) and price_range.get('enabled'):
            max_value = price_range.get('max_value')
            if max_value is not None:
                try:
                    max_value = float(max_value)
                    if max_value >= 0:
                        validated['price_range'] = {
                            'enabled': True,
                            'max_value': max_value
                        }
                except (ValueError, TypeError):
                    pass
    
    # Validate percentage range
    if filters.get('percentage_range'):
        percentage_range = filters['percentage_range']
        if isinstance(percentage_range, dict) and percentage_range.get('enabled'):
            validated_percentage = {'enabled': True}
            
            # Validate max_value
            max_value = percentage_range.get('max_value')
            if max_value is not None:
                try:
                    max_value = float(max_value)
                    if 0 <= max_value <= 100:
                        validated_percentage['max_value'] = max_value
                except (ValueError, TypeError):
                    pass
            
            # Validate bucket
            bucket = percentage_range.get('bucket')
            if bucket and bucket in FILTER_CONFIG['PERCENTAGE_BUCKETS']:
                validated_percentage['bucket'] = bucket
            
            if len(validated_percentage) > 1:  # More than just 'enabled'
                validated['percentage_range'] = validated_percentage
    
    return validated

# Add new view for text-only search (optional)
@csrf_exempt
def search_discounts_by_text(request):
    """
    Search discounts by text only (for future use)
    
    Expected JSON payload:
    {
        "search_text": "electronics discount"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        search_text = data.get('search_text', '').strip()
        
        if not search_text:
            return JsonResponse({'error': 'Search text is required'}, status=400)
        
        # Use the new search method
        discounts = Coupon.search_coupons_by_text(search_text)
        
        # Convert ObjectId to string for JSON serialization
        for discount in discounts:
            if '_id' in discount:
                discount['_id'] = str(discount['_id'])
        
        return JsonResponse({
            'discounts': discounts,
            'total_count': len(discounts),
            'search_text': search_text
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in search_discounts_by_text: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
def add_favorite_view(request):
    """Add a discount to user's favorites"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            logger.warning("add_favorite_view: User not authenticated")
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        
        data = json.loads(request.body)
        discount_id = data.get('discount_id')
        
        if not discount_id:
            logger.warning("add_favorite_view: discount_id is required")
            return JsonResponse({'error': 'discount_id is required'}, status=400)
        
        # Verify discount exists
        coupon = Coupon.find_one({'discount_id': discount_id})
        if not coupon:
            logger.warning(f"add_favorite_view: Discount not found - {discount_id}")
            return JsonResponse({'error': 'Discount not found'}, status=404)
        
        # Add to favorites
        result = User.add_favorite(user_id, discount_id)
        
        # Check if the update was successful (MongoDB UpdateResult has modified_count)
        if result and hasattr(result, 'modified_count') and result.modified_count >= 0:
            logger.info(f"add_favorite_view: Successfully added {discount_id} to favorites for user {user_id}")
            return JsonResponse({
                'status': 'success',
                'message': 'Added to favorites',
                'discount_id': discount_id
            })
        else:
            logger.error(f"add_favorite_view: Failed to add {discount_id} to favorites for user {user_id}")
            return JsonResponse({'error': 'Failed to add to favorites'}, status=500)
            
    except json.JSONDecodeError as e:
        logger.error(f"add_favorite_view: JSON decode error - {str(e)}")
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in add_favorite_view: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
def remove_favorite_view(request):
    """Remove a discount from user's favorites"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            logger.warning("remove_favorite_view: User not authenticated")
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        
        data = json.loads(request.body)
        discount_id = data.get('discount_id')
        
        if not discount_id:
            logger.warning("remove_favorite_view: discount_id is required")
            return JsonResponse({'error': 'discount_id is required'}, status=400)
        
        # Remove from favorites
        result = User.remove_favorite(user_id, discount_id)
        
        # Check if the update was successful (MongoDB UpdateResult has modified_count)
        if result and hasattr(result, 'modified_count') and result.modified_count >= 0:
            logger.info(f"remove_favorite_view: Successfully removed {discount_id} from favorites for user {user_id}")
            return JsonResponse({
                'status': 'success',
                'message': 'Removed from favorites',
                'discount_id': discount_id
            })
        else:
            logger.error(f"remove_favorite_view: Failed to remove {discount_id} from favorites for user {user_id}")
            return JsonResponse({'error': 'Failed to remove from favorites'}, status=500)
            
    except json.JSONDecodeError as e:
        logger.error(f"remove_favorite_view: JSON decode error - {str(e)}")
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in remove_favorite_view: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
def check_favorite_view(request, discount_id):
    """Check if a discount is in user's favorites"""
    try:
        # Check if user is logged in
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'is_favorite': False})
        
        is_favorite = User.is_favorite(user_id, discount_id)
        return JsonResponse({'is_favorite': is_favorite})
        
    except Exception as e:
        logger.error(f"Error in check_favorite_view: {str(e)}")
        return JsonResponse({'is_favorite': False})

@csrf_exempt
def ai_filter_helper(request):
    """
    AI Filter Helper endpoint that uses Groq API to extract filter parameters from user text.
    
    Expected JSON payload:
    {
        "user_text": "I want electronics discounts for students under 200 shekels"
    }
    
    Returns:
    {
        "filters": {
            "statuses": ["Student"],
            "interests": ["electronics"],
            "price_range": {"enabled": true, "max_value": 200}
        },
        "success": true
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_text = data.get('user_text', '').strip()
        
        if not user_text:
            return JsonResponse({'error': 'User text is required'}, status=400)
        
        # Import the AI filter helper utility
        from intellishop.utils.groq_helper import extract_filters_from_text
        
        logger.info(f"AI Filter Helper request received for text: {user_text[:100]}...")
        
        # Extract filters using Groq API
        extracted_filters = extract_filters_from_text(user_text)
        
        logger.info(f"AI Filter Helper extracted filters: {extracted_filters}")
        
        return JsonResponse({
            'filters': extracted_filters,
            'success': True,
            'user_text': user_text
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error in ai_filter_helper: {str(e)}")
        return JsonResponse({
            'error': 'Failed to process AI filter request',
            'success': False
        }, status=500)

@csrf_exempt
def debug_favorites(request):
    """Debug endpoint to check session and CSRF token"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        user_id = request.session.get('user_id')
        csrf_token = request.META.get('CSRF_COOKIE')
        
        debug_info = {
            'user_id': user_id,
            'csrf_token': csrf_token,
            'session_keys': list(request.session.keys()),
            'method': request.method,
            'headers': dict(request.headers),
            'cookies': dict(request.COOKIES)
        }
        
        return JsonResponse(debug_info)
        
    except Exception as e:
        logger.error(f"Error in debug_favorites: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
def debug_favorites_page(request):
    """Debug page for testing favorites functionality"""
    return render(request, 'intellishop/debug_favorites.html')

