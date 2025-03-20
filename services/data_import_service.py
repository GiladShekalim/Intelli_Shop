import json
from typing import Optional, List, Dict, Any
from config.database import DatabaseConnection

class DataImportService:
    def __init__(self):
        self.db = DatabaseConnection().db

    def load_json_file(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Load data from JSON file"""
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return None

    def insert_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> bool:
        """Insert multiple documents into specified collection"""
        if not documents:
            return False

        try:
            collection = self.db[collection_name]
            result = collection.insert_many(documents)
            print(f"Successfully inserted {len(result.inserted_ids)} documents into {collection_name}")
            return True
        except Exception as e:
            print(f"Error inserting documents: {e}")
            return False

    def get_field_value(self, collection_name: str, field_name: str) -> Optional[Any]:
        """Get value of specified field from first document in collection"""
        try:
            collection = self.db[collection_name]
            document = collection.find_one()
            if document:
                value = document.get(field_name)
                print(f"Value of '{field_name}': {value}")
                return value
            print("No documents found in the collection")
            return None
        except Exception as e:
            print(f"Error retrieving field value: {e}")
            return None 