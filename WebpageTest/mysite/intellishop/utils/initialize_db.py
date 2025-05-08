from intellishop.utils.mongodb_utils import get_collection_handle
from intellishop.models.mongodb_models import Coupon
import logging
import os
import csv
import json

logger = logging.getLogger(__name__)

def create_indexes():
    """Create MongoDB indexes for performance and constraints"""
    # Users collection
    users_collection = get_collection_handle('users')
    
    # Add None check before trying to create indexes
    if users_collection is not None:
        try:
            # Create unique indexes
            users_collection.create_index('username', unique=True)
            users_collection.create_index('email', unique=True)
            logger.info("Created user collection indexes")
        except Exception as e:
            logger.error(f"Error creating user indexes: {str(e)}")
    else:
        logger.error("Could not get users collection handle")
    
    # Products collection
    products_collection = get_collection_handle('products')
    
    # Add None check before trying to create indexes
    if products_collection is not None:
        try:
            products_collection.create_index('category')
            logger.info("Created product collection indexes")
        except Exception as e:
            logger.error(f"Error creating product indexes: {str(e)}")
    else:
        logger.error("Could not get products collection handle")
        
    # Coupons collection
    coupons_collection = get_collection_handle('coupons')
    
    # Add None check before trying to create indexes
    if coupons_collection is not None:
        try:
            # Create unique index on coupon code
            coupons_collection.create_index('code', unique=True)
            # Create index for finding active coupons
            coupons_collection.create_index('date_expires')
            logger.info("Created coupon collection indexes")
        except Exception as e:
            logger.error(f"Error creating coupon indexes: {str(e)}")
    else:
        logger.error("Could not get coupons collection handle")

def import_sample_coupon_data():
    """Import sample coupon data from the app data directory"""
    try:
        from intellishop.models.mongodb_models import Coupon
        
        # Get the base directory path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data')
        
        # Check if the data directory exists
        if not os.path.exists(data_dir):
            logger.warning(f"Coupon data directory not found: {data_dir}")
            return
        
        # Look for JSON files
        json_path = os.path.join(data_dir, 'coupon_samples.json')
        if os.path.exists(json_path):
            logger.info(f"Importing coupon data from {json_path}")
            with open(json_path, 'r') as f:
                data = json.load(f)
                results = Coupon.import_from_json(data)
                logger.info(f"Coupon import results: {results['valid']} valid, {results['invalid']} invalid")
        
        # Look for CSV files
        csv_path = os.path.join(data_dir, 'sample_offers.csv')
        if os.path.exists(csv_path):
            logger.info(f"Importing coupon data from {csv_path}")
            with open(csv_path, 'r') as f:
                results = Coupon.import_from_csv(f)
                logger.info(f"Coupon import results: {results['valid']} valid, {results['invalid']} invalid")
                
    except Exception as e:
        logger.error(f"Error during coupon data import: {str(e)}")

def initialize_database():
    """Initialize MongoDB database with required setup"""
    try:
        create_indexes()
        import_sample_coupon_data()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
    # Add any other initialization tasks here 