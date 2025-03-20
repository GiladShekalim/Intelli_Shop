from typing import Optional, Dict, List
from bson import ObjectId
from models.user import User
from config.database import DatabaseConnection
from utils.security import hash_password, verify_password

class UserService:
    def __init__(self):
        self.db = DatabaseConnection().db
        self.collection = self.db.users

    def create_user(self, username: str, email: str, password: str) -> Optional[Dict]:
        """Create a new user"""
        if self.get_user_by_email(email) or self.get_user_by_username(username):
            return None
        
        user = User(username, email, hash_password(password))
        result = self.collection.insert_one(user.to_dict())
        return self.get_user_by_id(result.inserted_id)

    def get_user_by_id(self, user_id: ObjectId) -> Optional[Dict]:
        """Get user by ID"""
        return self.collection.find_one({"_id": user_id})

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return self.collection.find_one({"email": email})

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        return self.collection.find_one({"username": username}) 