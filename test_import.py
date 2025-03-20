import os

# Print the content of database.py to verify it exists and has content
db_file_path = os.path.join('config', 'database.py')
print(f"Checking if file exists: {os.path.exists(db_file_path)}")

with open(db_file_path, 'r') as f:
    print("Content of database.py:")
    print(f.read())

# Now try to import
from config.database import DatabaseConnection
print("Successfully imported DatabaseConnection") 