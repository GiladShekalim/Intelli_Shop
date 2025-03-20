from typing import Optional, Dict, List
from bson import ObjectId
from datetime import datetime
from config.database import DatabaseConnection

class PostService:
    def __init__(self):
        self.db = DatabaseConnection().db
        self.collection = self.db.posts

    def create_post(self, user_id: ObjectId, content: str) -> Optional[Dict]:
        """Create a new post"""
        post = {
            "user_id": user_id,
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = self.collection.insert_one(post)
        return self.get_post_by_id(result.inserted_id)

    def get_post_by_id(self, post_id: ObjectId) -> Optional[Dict]:
        """Get post by ID"""
        return self.collection.find_one({"_id": post_id})

    def get_user_posts(self, user_id: ObjectId) -> List[Dict]:
        """Get all posts by a user"""
        return list(self.collection.find({"user_id": user_id})) 