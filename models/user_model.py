from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, db):
        self.collection = db["users"]

    def create_user(self, username, password, role):
        if role not in ["student", "warden", "security"]:
            raise ValueError("Invalid role")
        hashed_password = generate_password_hash(password)
        user = {
            "username": username,
            "password": hashed_password,
            "role": role
        }
        return self.collection.insert_one(user).inserted_id

    def find_by_username(self, username):
        return self.collection.find_one({"username": username})

    def verify_password(self, username, password):
        user = self.find_by_username(username)
        if not user:
            return False
        return check_password_hash(user["password"], password)
