import pymongo
import json

# Step 1: Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27018/")

# Step 2: Create or access a database
db = client["my_database"]

# Step 3: Create a new collection
collection = db["my_collection"]

# Step 4: Load JSON data from a file
with open("OfferList.json", "r") as file:
    json_data = json.load(file)

# Step 5: Insert the JSON data into the collection
result = collection.insert_many(json_data)

print(f"Inserted {len(result.inserted_ids)} documents")

# Step 6: Read a JSON field into a variable
document = collection.find_one()
if document:
    field_value = document.get("date_expires")
    print(f"Value of 'date_expires': {field_value}")
else:
    print("No documents found in the collection")

# Step 7: Close the connection
client.close()
