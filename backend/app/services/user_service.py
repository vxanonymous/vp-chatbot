from typing import List, Optional

try:
    from bson import ObjectId
except ImportError:
    # Fallback for environments without pymongo
    class ObjectId:
        def __init__(self, oid=None):
            self.oid = oid or "test_id"
            # Internal helper:  init  .
        def __str__(self):
            return str(self.oid)
            # Internal helper:  str  .
import logging

from app.auth.password import get_password_hash, verify_password
from app.models.user import UserCreate, UserInDB

try:
    from motor.motor_asyncio import AsyncIOMotorCollection
except ImportError:
    from typing import Any
    AsyncIOMotorCollection = Any


logger = logging.getLogger(__name__)


class UserService:

    def __init__(self, collection: AsyncIOMotorCollection):
        # Initialize user service with database collection
        self.collection = collection
    

    async def create_user(self, user_data: UserCreate) -> UserInDB:
        try:
            existing_user = await self.collection.find_one({"email": user_data.email})
            if existing_user:
                raise ValueError("This email is already registered. Please try logging in instead.")
            
            hashed_password = get_password_hash(user_data.password)
            from datetime import datetime
            
            user_doc = {
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.collection.insert_one(user_doc)
            
            return UserInDB(
                id=result.inserted_id,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                is_active=True,
                created_at=user_doc["created_at"],
                updated_at=user_doc["updated_at"]
            )
        except Exception as e:
            logger.error(f"Couldn't create the new user account: {e}")
            raise
    
    # Authenticates a user by checking email and password.

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        try:
            user_doc = await self.collection.find_one({"email": email})
            if not user_doc:
                return None
            
            if not user_doc.get("is_active", True):
                return None
            
            if not verify_password(password, user_doc["hashed_password"]):
                return None
            
            from datetime import datetime
            
            return UserInDB(
                id=user_doc["_id"],
                email=user_doc["email"],
                full_name=user_doc["full_name"],
                hashed_password=user_doc["hashed_password"],
                is_active=user_doc.get("is_active", True),
                created_at=user_doc.get("created_at", datetime.utcnow()),
                updated_at=user_doc.get("updated_at", datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Had trouble checking the user's login credentials: {e}")
            return None
    

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        try:
            user_doc = await self.collection.find_one({"_id": ObjectId(user_id)})
            if not user_doc:
                return None
            
            from datetime import datetime
            
            return UserInDB(
                id=user_doc["_id"],
                email=user_doc["email"],
                full_name=user_doc["full_name"],
                hashed_password=user_doc["hashed_password"],
                is_active=user_doc.get("is_active", True),
                created_at=user_doc.get("created_at", datetime.utcnow()),
                updated_at=user_doc.get("updated_at", datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Couldn't find the user by their ID: {e}")
            return None
    

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        try:
            user_doc = await self.collection.find_one({"email": email})
            if not user_doc:
                return None
            
            from datetime import datetime
            
            return UserInDB(
                id=user_doc["_id"],
                email=user_doc["email"],
                full_name=user_doc["full_name"],
                hashed_password=user_doc["hashed_password"],
                is_active=user_doc.get("is_active", True),
                created_at=user_doc.get("created_at", datetime.utcnow()),
                updated_at=user_doc.get("updated_at", datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Couldn't find the user by their email: {e}")
            return None
    

    async def update_user(self, user_id: str, update_data: dict) -> Optional[UserInDB]:
        try:
            update_data.pop("hashed_password", None)
            update_data.pop("email", None)
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Couldn't update the user's information: {e}")
            return None
    

    async def delete_user(self, user_id: str) -> bool:
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Couldn't delete the user account: {e}")
            return False
    

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        try:
            from datetime import datetime
            
            cursor = self.collection.find().skip(skip).limit(limit)
            users = []
            async for user_doc in cursor:
                users.append(UserInDB(
                    id=user_doc["_id"],
                    email=user_doc["email"],
                    full_name=user_doc["full_name"],
                    hashed_password=user_doc["hashed_password"],
                    is_active=user_doc.get("is_active", True),
                    created_at=user_doc.get("created_at", datetime.utcnow()),
                    updated_at=user_doc.get("updated_at", datetime.utcnow())
                ))
            return users
        except Exception as e:
            logger.error(f"Had trouble getting the list of users: {e}")
            return []