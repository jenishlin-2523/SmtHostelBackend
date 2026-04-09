# database/mongo.py
from pymongo import MongoClient
from config import MONGO_URI

# Connect to MongoDB with connect=False for Gunicorn compatibility
client = MongoClient(MONGO_URI, connect=False)
db = client["smart_hostel"]

def get_users_collection():
    return db["users"]

# Keep this for backward compatibility if used directly
users_collection = db["users"]
