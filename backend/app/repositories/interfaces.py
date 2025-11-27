from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.user import UserInDB, UserCreate
from app.models.conversation_db import ConversationInDB, ConversationSummary
from app.models.chat import Message

class IUserRepository(ABC):
    # @abstractmethod
    # async def create(self, user_data: UserCreate, hashed_password: str) -> UserInDB:
    #     pass
    # @abstractmethod
    # async def find_by_email(self, email: str) -> Optional[UserInDB]:
    #     pass
    # @abstractmethod
    # async def find_by_id(self, user_id: str) -> Optional[UserInDB]:
    #     pass
    # @abstractmethod
    # async def update(self, user_id: str, update_data: Dict[str, Any]) -> Optional[UserInDB]:
    #     pass
    # @abstractmethod
    # async def delete(self, user_id: str) -> bool:
    #     pass
    pass

class IConversationRepository(ABC):
    # Interface for conversation data access operations.
    
    @abstractmethod

    async def create(self, conversation_data: Dict[str, Any]) -> ConversationInDB:
        pass
    
    @abstractmethod

    async def find_by_id(self, conversation_id: str, user_id: str) -> Optional[ConversationInDB]:
        pass
    
    @abstractmethod
    async def find_by_user_id(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ConversationSummary]:

        pass
    
    @abstractmethod
    async def add_message(
        self, 
        conversation_id: str, 
        user_id: str, 
        message: Message
    ) -> Optional[ConversationInDB]:

        pass
    
    @abstractmethod
    async def update(
        self, 
        conversation_id: str, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[ConversationInDB]:

        pass
    
    @abstractmethod
    # Soft deletes a conversation (marks as inactive).

    async def soft_delete(self, conversation_id: str, user_id: str) -> bool:
        pass

