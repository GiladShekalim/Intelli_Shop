from bson import ObjectId
import datetime
import logging
import re
from jsonschema import validate, ValidationError
import json
import csv
import os
from .constants import CATEGORIES, CONSUMER_STATUS, DISCOUNT_TYPE, FILTER_CONFIG

logger = logging.getLogger(__name__)

class MongoDBModel:
    """Base class for MongoDB models"""
    collection_name = None
    
    @classmethod
    def get_collection(cls):
        """Get the MongoDB collection for this model"""
        from intellishop.utils.mongodb_utils import get_collection_handle
        return get_collection_handle(cls.collection_name)
    
    @classmethod
    def find_one(cls, query):
        """Find a single document"""
        collection = cls.get_collection()
        if collection is not None:  # Add explicit None check
            return collection.find_one(query)
        return None
    
    @classmethod
    def find(cls, query=None, sort=None, limit=None):
        """Find multiple documents"""
        collection = cls.get_collection()
        if collection is not None:  # Add explicit None check
            cursor = collection.find(query or {})
            
            if sort:
                cursor = cursor.sort(sort)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        return []  # Return empty list instead of None for consistency
    
    @classmethod
    def insert_one(cls, document):
        """Insert a document into the collection"""
        collection = cls.get_collection()
        if collection is not None:  # Add explicit None check
            result = collection.insert_one(document)
            return result.inserted_id
        return None
    
    @classmethod
    def update_one(cls, filter_dict, update_data, upsert=False):
        """
        Update a single document in the collection.
        
        Args:
            filter_dict: Dictionary to filter documents
            update_data: Dictionary with update data
            upsert: If True, insert a new document if no document matches the filter
        
        Returns:
            Result of the update operation
        """
        collection = cls.get_collection()
        
        # If update_data doesn't have $ operators, use $set
        if not any(key.startswith('$') for key in update_data.keys()):
            update_data = {'$set': update_data}
        
        return collection.update_one(filter_dict, update_data, upsert=upsert)
    
    @classmethod
    def delete_one(cls, query):
        """Delete a document from the collection"""
        collection = cls.get_collection()
        if collection is not None:  # Add explicit None check
            return collection.delete_one(query)
        return None

# Add this User model for MongoDB
class User(MongoDBModel):
    collection_name = 'users'
    
    @classmethod
    def create_user(cls, username, password, email, status, age, location, hobbies):
        """Create a new user in MongoDB"""
        user_data = {
            'username': username,
            'password': password,  # In production, hash this
            'email': email,
            'status': status,
            'age': age,
            'location': location,
            'hobbies': hobbies,
            'created_at': datetime.datetime.now()
        }
        return cls.insert_one(user_data)
    
    @classmethod
    def get_by_username(cls, username):
        """Get a user by username"""
        return cls.find_one({'username': username})
    
    @classmethod
    def get_by_email(cls, email):
        """Get a user by email"""
        return cls.find_one({'email': email})
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by ID"""
        return cls.find_one({'_id': ObjectId(user_id)})

# Updated Coupon model with new schema
class Coupon(MongoDBModel):
    collection_name = 'coupons'
    
    # Define the updated coupon schema using imported constants
    schema = {
        "type": "object",
        "properties": {
            "discount_id": {
                "type": ["string", "null"],
                "description": "Unique automatic identifier of the coupon by MongoDB."
            },
            "title": {
                "type": "string",
                "description": "Title of the coupon."
            },
            "price": {
                "type": "integer",
                "minimum": 0,
                "description": "Price or discount amount."
            },
            "discount_type": {
                "type": "string",
                "enum": DISCOUNT_TYPE,
                "description": "Type of discount (fixed_amount, percentage, buy_one_get_one, Cost)."
            },
            "description": {
                "type": "string",
                "description": "Detailed description of the coupon."
            },
            "image_link": {
                "type": "string",
                "description": "URL to an image representing the coupon."
            },
            "discount_link": {
                "type": "string",
                "description": "URL to the discount page."
            },
            "terms_and_conditions": {
                "type": "string",
                "description": "Terms and conditions for using the coupon."
            },
            "club_name": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of club names associated with the coupon."
            },
            "category": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": CATEGORIES
                },
                "description": "Categories the coupon belongs to."
            },
            "valid_until": {
                "type": "string",
                "description": "Expiry date of the coupon in ISO format."
            },
            "usage_limit": {
                "type": ["integer", "null"],
                "minimum": 1,
                "description": "Total number of times the coupon can be used."
            },
            "coupon_code": {
                "type": "string",
                "description": "Code to be used when redeeming the coupon."
            },
            "provider_link": {
                "type": "string",
                "description": "URL to the provider's website."
            },
            "consumer_statuses": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": CONSUMER_STATUS
                },
                "description": "Consumer statuses this coupon targets."
            }
        },
        "required": ["title", "price", "discount_link"],
        "additionalProperties": True
    }
    
    @classmethod
    def get_all(cls):
        """Get all coupons in the collection"""
        return list(cls.find({}))
    
    @classmethod
    def get_by_code(cls, code):
        """Get a coupon by its code"""
        return cls.find_one({'coupon_code': code})
    
    @classmethod
    def get_active_coupons(cls):
        """Get all active coupons (not expired)"""
        current_date = datetime.datetime.utcnow().isoformat()
        return cls.find({
            '$or': [
                {'valid_until': {'$exists': False}},
                {'valid_until': None},
                {'valid_until': ''},
                {'valid_until': {'$gt': current_date}}
            ]
        })
    
    @classmethod
    def get_filtered_coupons(cls, filters=None):
        """
        Get coupons based on applied filters with three search scenarios:
        1. Text-only: Find discounts where each word appears in text fields
        2. Parameters-only: Filter by categories, statuses, price, percentage (AND logic)
        3. Combined: Apply parameter filters first, then text search on filtered results
        
        Args:
            filters (dict): Dictionary containing filter criteria
            
        Returns:
            list: Filtered coupons
        """
        if not filters:
            return cls.get_all()
        
        # Determine search scenario
        has_text = bool(filters.get('text_search'))
        has_parameters = bool(
            filters.get('statuses') or 
            filters.get('interests') or 
            filters.get('price_range') or 
            filters.get('percentage_range')
        )
        
        if has_text and has_parameters:
            # Scenario 3: Combined search - parameters first, then text
            return cls._combined_search(filters)
        elif has_text and not has_parameters:
            # Scenario 1: Text-only search
            return cls._text_only_search(filters['text_search'])
        elif not has_text and has_parameters:
            # Scenario 2: Parameters-only search
            return cls._parameters_only_search(filters)
        else:
            # No filters - return all
            return cls.get_all()

    @classmethod
    def _text_only_search(cls, search_text):
        """
        Scenario 1: Text-only search
        Find discounts where each individual word is found in text fields
        
        Args:
            search_text (str): Text to search for
            
        Returns:
            list: Matching coupons
        """
        if not search_text or len(search_text.strip()) < FILTER_CONFIG['TEXT_SEARCH']['MIN_WORD_LENGTH']:
            return cls.get_all()
        
        # Clean and prepare search text
        search_text = search_text.strip()
        
        # Split into words
        search_words = [word.strip() for word in search_text.split() if len(word.strip()) >= FILTER_CONFIG['TEXT_SEARCH']['MIN_WORD_LENGTH']]
        
        if not search_words:
            return cls.get_all()
        
        # Build query where each word must be found in at least one text field
        word_conditions = []
        searchable_fields = FILTER_CONFIG['SEARCHABLE_FIELDS']
        
        for word in search_words:
            # For each word, it must appear in at least one of the searchable fields
            field_conditions = []
            for field in searchable_fields:
                regex_pattern = f'.*{re.escape(word)}.*'
                field_conditions.append({field: {'$regex': regex_pattern, '$options': 'i'}})
            
            # Word must be found in at least one field (OR logic for fields)
            word_conditions.append({'$or': field_conditions})
        
        # All words must be found (AND logic for words)
        if word_conditions:
            query = {'$and': word_conditions}
            return cls.find(query, limit=FILTER_CONFIG['TEXT_SEARCH']['MAX_RESULTS'])
        
        return []

    @classmethod
    def _parameters_only_search(cls, filters):
        """
        Scenario 2: Parameters-only search
        Filter by categories, statuses, price, percentage with AND logic
        
        Args:
            filters (dict): Parameter filters
            
        Returns:
            list: Matching coupons
        """
        query = cls._build_parameter_query(filters)
        return cls.find(query)

    @classmethod
    def _combined_search(cls, filters):
        """
        Scenario 3: Combined search
        Apply parameter filters first, then text search on filtered results
        
        Args:
            filters (dict): Combined filters
            
        Returns:
            list: Matching coupons
        """
        # Step 1: Apply parameter filters
        parameter_query = cls._build_parameter_query(filters)
        parameter_results = cls.find(parameter_query)
        
        if not parameter_results:
            return []
        
        # Step 2: Apply text search on parameter-filtered results
        search_text = filters['text_search']
        if not search_text or len(search_text.strip()) < FILTER_CONFIG['TEXT_SEARCH']['MIN_WORD_LENGTH']:
            return parameter_results
        
        # Clean and prepare search text
        search_text = search_text.strip()
        search_words = [word.strip() for word in search_text.split() if len(word.strip()) >= FILTER_CONFIG['TEXT_SEARCH']['MIN_WORD_LENGTH']]
        
        if not search_words:
            return parameter_results
        
        # Filter parameter results by text search
        searchable_fields = FILTER_CONFIG['SEARCHABLE_FIELDS']
        filtered_results = []
        
        for coupon in parameter_results:
            # Check if all words are found in the coupon
            all_words_found = True
            
            for word in search_words:
                word_found = False
                
                # Check each searchable field for the word
                for field in searchable_fields:
                    field_value = coupon.get(field, '')
                    if isinstance(field_value, list):
                        # Handle array fields like club_name
                        field_value = ' '.join(field_value)
                    
                    if field_value and word.lower() in str(field_value).lower():
                        word_found = True
                        break
                
                if not word_found:
                    all_words_found = False
                    break
            
            if all_words_found:
                filtered_results.append(coupon)
        
        return filtered_results

    @classmethod
    def _build_parameter_query(cls, filters):
        """
        Build MongoDB query for parameter-only filters
        
        Args:
            filters (dict): Parameter filters
            
        Returns:
            dict: MongoDB query
        """
        query = {}
        
        # Status filters
        if filters.get('statuses'):
            query['consumer_statuses'] = {'$in': filters['statuses']}
        
        # Interest/Category filters
        if filters.get('interests'):
            query['category'] = {'$in': filters['interests']}
        
        # Price range filters (for fixed_amount type)
        if filters.get('price_range'):
            price_range = filters['price_range']
            if price_range.get('enabled') and price_range.get('max_value') is not None:
                query['$and'] = query.get('$and', [])
                query['$and'].extend([
                    {'discount_type': 'fixed_amount'},
                    {'price': {'$lte': price_range['max_value']}}
                ])
        
        # Percentage range filters (bucket only)
        if filters.get('percentage_range'):
            percentage_range = filters['percentage_range']
            if percentage_range.get('enabled'):
                # Always filter by discount_type: 'percentage'
                and_clauses = query.get('$and', [])
                and_clauses.append({'discount_type': 'percentage'})

                # If a bucket is selected, use its min/max
                if percentage_range.get('bucket'):
                    bucket_config = FILTER_CONFIG['PERCENTAGE_BUCKETS'].get(percentage_range['bucket'])
                    if bucket_config:
                        and_clauses.append({'price': {'$gte': bucket_config['min'], '$lte': bucket_config['max']}})

                query['$and'] = and_clauses
        
        return query

    @classmethod
    def search_coupons_by_text(cls, search_text, limit=None):
        """
        Search coupons by text across multiple fields (updated to use new logic)
        
        Args:
            search_text (str): Text to search for
            limit (int): Maximum number of results
            
        Returns:
            list: Matching coupons
        """
        if not search_text:
            return cls.get_all()
        
        return cls._text_only_search(search_text)

    @classmethod
    def get_filter_statistics(cls):
        """
        Get statistics for filter options (counts, ranges, etc.)
        
        Returns:
            dict: Statistics for filter configuration
        """
        stats = {
            'price_range': {'min': 0, 'max': 0},
            'percentage_counts': {}
        }
        
        # Get price range for fixed_amount discounts
        fixed_amount_coupons = cls.find({'discount_type': 'fixed_amount'})
        if fixed_amount_coupons:
            prices = [float(c.get('price', 0)) for c in fixed_amount_coupons if c.get('price') is not None]
            if prices:
                stats['price_range']['min'] = min(prices)
                stats['price_range']['max'] = max(prices)
        
        # Get percentage counts
        percentage_coupons = cls.find({'discount_type': 'percentage'})
        for bucket_name, bucket_config in FILTER_CONFIG['PERCENTAGE_BUCKETS'].items():
            count = len(cls.find({
                'discount_type': 'percentage',
                'price': {'$gte': bucket_config['min'], '$lte': bucket_config['max']}
            }))
            stats['percentage_counts'][bucket_name] = count
        
        return stats
    
    @classmethod
    def import_from_json(cls, json_data):
        """Import coupons from JSON data"""
        results = {
            'success': 0,
            'errors': [],
            'warnings': [],
            'details': []
        }
        
        try:
            if isinstance(json_data, str):
                try:
                    json_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    results['errors'].append(f"Invalid JSON format: {str(e)}")
                    return results
            
            if not isinstance(json_data, list):
                json_data = [json_data]
            
            for idx, coupon_data in enumerate(json_data):
                try:
                    # Validate required fields
                    required_fields = ['title', 'price', 'discount_link']
                    missing_fields = [field for field in required_fields if field not in coupon_data or 
                                     (coupon_data[field] is None or (field != 'price' and not coupon_data[field]))]
                    
                    if missing_fields:
                        error_msg = f"Entry #{idx+1}: Missing required fields: {', '.join(missing_fields)}"
                        results['errors'].append(error_msg)
                        results['details'].append({
                            'entry': idx+1,
                            'title': coupon_data.get('title', 'Unknown'),
                            'error': f"Missing required fields: {', '.join(missing_fields)}"
                        })
                        continue
                    
                    # Handle price validation separately
                    if 'price' in coupon_data:
                        price = coupon_data['price']
                        if isinstance(price, dict):
                            if 'amount' not in price:
                                error_msg = f"Entry #{idx+1}: Price dictionary missing 'amount' field"
                                results['errors'].append(error_msg)
                                results['details'].append({
                                    'entry': idx+1,
                                    'title': coupon_data.get('title', 'Unknown'),
                                    'error': f"Price dictionary missing 'amount' field"
                                })
                                continue
                    
                    # Normalize coupon data
                    normalized_data = cls._normalize_coupon_data(coupon_data)
                    
                    # Insert or update coupon
                    if 'discount_id' in normalized_data and normalized_data['discount_id']:
                        # Update by discount_id
                        filter_dict = {'discount_id': normalized_data['discount_id']}
                        cls.update_one(filter_dict, normalized_data, upsert=True)
                    elif 'coupon_code' in normalized_data and normalized_data['coupon_code']:
                        # Update by coupon_code
                        filter_dict = {'coupon_code': normalized_data['coupon_code']}
                        cls.update_one(filter_dict, normalized_data, upsert=True)
                    else:
                        # Insert as new
                        cls.insert_one(normalized_data)
                    
                    results['success'] += 1
                
                except Exception as e:
                    error_msg = f"Entry #{idx+1}: Error processing coupon '{coupon_data.get('title', 'Unknown')}': {str(e)}"
                    results['errors'].append(error_msg)
                    results['details'].append({
                        'entry': idx+1,
                        'title': coupon_data.get('title', 'Unknown'),
                        'error': str(e)
                    })
            
        except Exception as e:
            results['errors'].append(f"Error during JSON import: {str(e)}")
        
        return results

    @classmethod
    def _validate_coupon_data_types(cls, coupon_data, entry_idx, results):
        """Validate data types of coupon fields"""
        is_valid = True
        
        # Check price data type
        if 'price' in coupon_data:
            price = coupon_data['price']
            if isinstance(price, str) and price.endswith('%'):
                try:
                    float(price.rstrip('%'))
                except ValueError:
                    results['errors'].append(f"Entry #{entry_idx}: Invalid price format '{price}'")
                    results['details'].append({
                        'entry': entry_idx,
                        'title': coupon_data.get('title', 'Unknown'),
                        'error': f"Invalid price format: '{price}'"
                    })
                    is_valid = False
            elif not isinstance(price, (int, float, str)):
                results['errors'].append(f"Entry #{entry_idx}: Price must be a number or string, got {type(price).__name__}")
                results['details'].append({
                    'entry': entry_idx,
                    'title': coupon_data.get('title', 'Unknown'),
                    'error': f"Price must be a number or string, got {type(price).__name__}"
                })
                is_valid = False
        
        # Check discount_type
        if 'discount_type' in coupon_data:
            discount_type = coupon_data['discount_type']
            valid_types = ['percentage', 'fixed_amount', 'buy_one_get_one', 'free_shipping', '']
            if discount_type not in valid_types:
                results['warnings'].append(f"Entry #{entry_idx}: Unknown discount_type '{discount_type}'")
                results['details'].append({
                    'entry': entry_idx,
                    'title': coupon_data.get('title', 'Unknown'),
                    'warning': f"Unknown discount_type: '{discount_type}'"
                })
        
        # Check date format for valid_until
        if 'valid_until' in coupon_data and coupon_data['valid_until']:
            date_str = coupon_data['valid_until']
            
            # Try to parse in known formats
            parsed = False
            for date_format in ['%d.%m.%y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    datetime.datetime.strptime(date_str, date_format)
                    parsed = True
                    break
                except ValueError:
                    continue
            
            if not parsed:
                results['warnings'].append(f"Entry #{entry_idx}: Potentially invalid date format '{date_str}'")
                results['details'].append({
                    'entry': entry_idx,
                    'title': coupon_data.get('title', 'Unknown'),
                    'warning': f"Potentially invalid date format: '{date_str}'"
                })
        
        return is_valid

    @classmethod
    def _normalize_coupon_data(cls, coupon_data):
        """Normalize coupon data to ensure consistent schema"""
        normalized = dict(coupon_data)
        
        # Set default values for missing fields
        if 'discount_id' not in normalized or not normalized['discount_id']:
            normalized['discount_id'] = str(ObjectId())
            
        if 'date_created' not in normalized:
            normalized['date_created'] = datetime.datetime.now().isoformat()
            
        # Normalize price - handle dictionary price format
        if 'price' in normalized:
            price = normalized['price']
            # Handle price as dictionary (from enhanced_hot_discounts.json)
            if isinstance(price, dict) and 'amount' in price:
                normalized['price'] = price['amount']
                if 'type' in price and not normalized.get('discount_type'):
                    normalized['discount_type'] = price['type']
            elif isinstance(price, str):
                if price.endswith('%'):
                    # It's a percentage discount
                    try:
                        normalized['price'] = float(price.rstrip('%'))
                        if 'discount_type' not in normalized or not normalized['discount_type']:
                            normalized['discount_type'] = 'percentage'
                    except ValueError:
                        # Keep as is if conversion fails
                        pass
                elif price.lower() in ['free_shipping', 'buy_one_get_one']:
                    # Special discount types
                    normalized['discount_type'] = price.lower()
                    normalized['price'] = 0
        
        # Normalize arrays
        for field in ['club_name', 'category', 'consumer_statuses']:
            if field in normalized:
                if not isinstance(normalized[field], list):
                    if normalized[field]:  # Only convert non-empty values to list
                        normalized[field] = [normalized[field]]
                    else:
                        normalized[field] = []
        
        # Normalize date format
        if 'valid_until' in normalized and normalized['valid_until']:
            date_str = normalized['valid_until']
            # Try common date formats
            for date_format in ['%d.%m.%y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                try:
                    date_obj = datetime.datetime.strptime(date_str, date_format)
                    normalized['valid_until'] = date_obj.strftime('%Y-%m-%d')  # ISO format
                    break
                except ValueError:
                    continue
        
        # Ensure numeric price value
        if 'price' in normalized and normalized['price'] is not None:
            try:
                normalized['price'] = float(normalized['price'])
            except (ValueError, TypeError):
                # If conversion fails, set a default price
                normalized['price'] = 0
        
        return normalized

    @classmethod
    def import_from_csv(cls, csv_file):
        """Import coupons from a CSV file or file object"""
        results = {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'updated': 0,
            'new': 0,
            'errors': []
        }
        
        close_after = False
        
        try:
            # If a string path is provided, open the file
            if isinstance(csv_file, str):
                file_obj = open(csv_file, 'r', encoding='utf-8')
                close_after = True
            else:
                file_obj = csv_file
                
            try:
                # Read the CSV file
                reader = csv.DictReader(file_obj)
                if not reader.fieldnames:
                    results['errors'].append("CSV file has no headers")
                    return results
                    
                # Map CSV fields to model fields (case insensitive)
                field_mapping = {
                    'id': 'discount_id',
                    'discount_id': 'discount_id',
                    'title': 'title',
                    'name': 'title',
                    'price': 'price',
                    'amount': 'price',
                    'discount': 'price',
                    'discount_type': 'discount_type',
                    'price_type': 'discount_type',
                    'type': 'discount_type',
                    'description': 'description',
                    'desc': 'description',
                    'image': 'image_link',
                    'image_link': 'image_link',
                    'image_url': 'image_link',
                    'link': 'discount_link',
                    'discount_link': 'discount_link',
                    'url': 'discount_link',
                    'terms': 'terms_and_conditions',
                    'terms_and_conditions': 'terms_and_conditions',
                    'tc': 'terms_and_conditions',
                    'club': 'club_name',
                    'club_name': 'club_name',
                    'category': 'category',
                    'categories': 'category',
                    'valid_until': 'valid_until',
                    'expiry': 'valid_until',
                    'expiry_date': 'valid_until',
                    'expires': 'valid_until',
                    'usage_limit': 'usage_limit',
                    'limit': 'usage_limit',
                    'code': 'coupon_code',
                    'coupon_code': 'coupon_code',
                    'provider': 'provider_link',
                    'provider_link': 'provider_link',
                    'provider_url': 'provider_link',
                    'consumer_status': 'consumer_statuses',
                    'consumer_statuses': 'consumer_statuses',
                    'status': 'consumer_statuses'
                }
                
                for row in reader:
                    results['total'] += 1
                    
                    try:
                        # Map CSV fields to model fields
                        coupon = {}
                        for csv_field, value in row.items():
                            if csv_field.lower() in field_mapping:
                                model_field = field_mapping[csv_field.lower()]
                                
                                # Handle array fields
                                if model_field in ['category', 'club_name', 'consumer_statuses']:
                                    if value:
                                        coupon[model_field] = [v.strip() for v in value.split(',')]
                                else:
                                    coupon[model_field] = value
                        
                        # Normalize and set defaults
                        coupon = cls._normalize_coupon_data(coupon)
                        
                        # Validate against schema
                        try:
                            validate(instance=coupon, schema=cls.schema)
                        except ValidationError as e:
                            results['invalid'] += 1
                            results['errors'].append(f"Row {results['total']}: {str(e)}")
                            continue
                        
                        # Check if we want to update by coupon_code (if it exists)
                        if 'coupon_code' in coupon and coupon['coupon_code']:
                            existing = cls.find_one({'coupon_code': coupon['coupon_code']})
                            
                            if existing:
                                # Update existing coupon
                                cls.update_one({'_id': existing['_id']}, coupon)
                                results['updated'] += 1
                            else:
                                # Insert new coupon
                                cls.insert_one(coupon)
                                results['new'] += 1
                        else:
                            # Insert as new coupon
                            cls.insert_one(coupon)
                            results['new'] += 1
                            
                        results['valid'] += 1
                        
                    except Exception as e:
                        results['invalid'] += 1
                        results['errors'].append(f"Row {results['total']}: {str(e)}")
                        
            finally:
                if close_after:
                    file_obj.close()
                    
        except Exception as e:
            results['errors'].append(f"CSV processing error: {str(e)}")
            
        return results

def find_json_and_csv_files(data_dir_path=None):
    # ... existing code ...
    
    # Filter to only include enhanced files
    json_files = [f for f in json_files if os.path.basename(f).lower().startswith('enhanced_')]
    csv_files = [f for f in csv_files if os.path.basename(f).lower().startswith('enhanced_')]
    
    logger.info(f"Found {len(json_files)} enhanced JSON files and {len(csv_files)} enhanced CSV files")
    
    return json_files, csv_files