import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseConnection
from services.user_service import UserService
from services.post_service import PostService
from services.data_import_service import DataImportService

def initialize_app():
    # Initialize database connection
    db_connection = DatabaseConnection()
    db_connection.initialize(
        connection_string="mongodb://<username>:<password>@<remote_host>:<port>/<database_name>",
        db_name="my_database"
    )

def import_and_check_data(json_file_path: str, collection_name: str, field_to_check: str):
    # Initialize data import service
    data_service = DataImportService()
    
    # Load JSON data
    json_data = data_service.load_json_file(json_file_path)
    if not json_data:
        print("Failed to load JSON data")
        return
    
    # Insert documents
    success = data_service.insert_documents(collection_name, json_data)
    if not success:
        print("Failed to insert documents")
        return
    
    # Check field value
    field_value = data_service.get_field_value(collection_name, field_to_check)
    if field_value is None:
        print(f"Failed to retrieve value for field '{field_to_check}'")

if __name__ == "__main__":
    # Initialize the application
    initialize_app()
    
    # Configuration (using the same values from original MongoSetup.py)
    JSON_FILE_PATH = "OfferList.json"
    COLLECTION_NAME = "my_collection"
    TARGET_FIELD = "date_expires"
    
    import_and_check_data(JSON_FILE_PATH, COLLECTION_NAME, TARGET_FIELD)
    
    DatabaseConnection().close()