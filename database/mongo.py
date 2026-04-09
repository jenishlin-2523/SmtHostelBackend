# database/mongo.py
from pymongo import MongoClient
from config import MONGO_URI  # Import URI from config

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["smart_hostel"]
users_collection = db["users"]
