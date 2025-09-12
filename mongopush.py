import json
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Replace with your connection URI
db = client["Rainwater_Data"]
collection = db["Ingres_Data"]

# Load JSON file
with open("allyears_data.json", "r") as f:
    data = json.load(f)

# Insert records
# data is like: { "2012-2013": [ {...}, {...} ] }
# So we iterate over years and insert entries
for year, records in data.items():
    for record in records:
        record["year"] = year  # Optional: include year in document
        collection.insert_one(record)

print("Data inserted successfully!")
print("Available databases:", client.list_database_names())
print("Collections in Rainwater_Data:", db.list_collection_names())
print("Documents in Ingres_Data:", collection.count_documents({}))
