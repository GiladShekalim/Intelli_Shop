import os
import pymongo
import json
import jsonschema
from scheme_definitions import coupon_schema

def connect_to_mongodb(uri):
    """Establish connection to MongoDB server"""
    try:
        client = pymongo.MongoClient(uri)
        return client
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None

def get_collection(client, database_name, collection_name):
    """Get or create a collection in specified database"""
    if not client:
        return None
    db = client[database_name]
    return db[collection_name]

def load_json_file(file_path):
    """Load data from JSON file"""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def insert_documents(collection, documents):
    """Insert multiple documents into collection"""
    if not documents:
        return None
    try:
        result = collection.insert_many(documents)
        print(f"Inserted {len(result.inserted_ids)} documents")
        return result
    except Exception as e:
        print(f"Error inserting documents: {e}")
        return None

def get_field_value(collection, field_name):
    """Get value of specified field from first document"""
    document = collection.find_one()
    if document:
        value = document.get(field_name)
        print(f"Value of '{field_name}': {value}")
        return value
    print("No documents found in the collection")
    return None

def close_connection(client):
    """Close MongoDB connection"""
    if client:
        client.close()

def validate_coupon_data(json_data):
    """Validate coupon data against schema"""
    try:
        for coupon in json_data:
            jsonschema.validate(instance=coupon, schema=coupon_schema)
        print("JSON data validation successful")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"JSON validation error: {e.message}")
        return False
    except jsonschema.exceptions.SchemaError as e:
        print(f"Schema error: {e.message}")
        return False

# Example usage
if __name__ == "__main__":
    # Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://<username>:<password>@localhost:27017/<database_name>")
    DATABASE_NAME = "my_database"
    COLLECTION_NAME = "my_collection"
    JSON_FILE_PATH = "OfferList.json"
    TARGET_FIELD = "date_expires"

    # Execute workflow
    client = connect_to_mongodb(MONGO_URI)
    if client:
        collection = get_collection(client, DATABASE_NAME, COLLECTION_NAME)

        json_data = load_json_file(JSON_FILE_PATH)
        if json_data:
            if validate_coupon_data(json_data):
                insert_documents(collection, json_data)
            get_field_value(collection, TARGET_FIELD)
        close_connection(client)
