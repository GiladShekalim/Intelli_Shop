from pymongo import MongoClient
from pymongo.database import Database
from typing import Optional

class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def initialize(self, connection_string: str, db_name: str) -> None:
        """Initialize database connection"""
        if self._client is None:
            self._client = MongoClient(connection_string)
            self._db = self._client[db_name]

    @property
    def db(self) -> Database:
        """Get database instance"""
        if self._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._db

    def close(self) -> None:
        """Close database connection"""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None 