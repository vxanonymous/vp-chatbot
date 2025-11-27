from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.user import UserCreate, UserInDB
from app.models.chat import Message
from app.models.conversation_db import ConversationInDB


class IUserService(ABC):
    # Interface for user service operations.
    
    @abstractmethod
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        # Create a new user.
        pass
    
    @abstractmethod
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        # Authenticate a user.
        pass
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        # Get user by ID.
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        # Get user by email.
        pass


class IConversationService(ABC):
    # Interface for conversation service operations.
    
    @abstractmethod
    async def create_conversation(self, user_id: str, title: str) -> ConversationInDB:
        # Create a new conversation.
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[ConversationInDB]:
        # Get conversation by ID.
        pass
    
    @abstractmethod
    async def add_message(self, conversation_id: str, user_id: str, message: Message) -> Optional[ConversationInDB]:
        # Add a message to a conversation.
        pass
    
    @abstractmethod
    async def update_conversation(self, conversation_id: str, user_id: str, **kwargs) -> Optional[ConversationInDB]:
        # Update a conversation.
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        # Delete a conversation.
        pass


class IOpenAIService(ABC):
    # Interface for OpenAI service operations.
    
    @abstractmethod
    async def generate_response_async(self, messages: List[Message]) -> Dict[str, Any]:
        # Generate response asynchronously.
        pass
    
    @abstractmethod
    def generate_response(self, messages: List[Message]) -> Dict[str, Any]:
        # Generate response synchronously.
        pass


class IVacationIntelligenceService(ABC):
    # Interface for vacation intelligence operations.
    
    @abstractmethod
    async def analyze_preferences(self, messages: List[Dict], current_preferences: Optional[Dict]) -> Dict[str, Any]:
        # Analyze user preferences from conversation.
        pass


class IConversationMemory(ABC):
    # Interface for conversation memory operations.
    
    @abstractmethod
    def store_context(self, conversation_id: str, context: Dict[str, Any]) -> bool:
        # Store conversation context.
        pass
    
    @abstractmethod
    def get_context(self, conversation_id: str) -> Dict[str, Any]:
        # Get conversation context.
        pass
    
    @abstractmethod
    def extract_key_points(self, messages: List[Dict]) -> Dict[str, Any]:
        # Extract key points from messages.
        pass


class IProactiveAssistant(ABC):
    # Interface for proactive assistance.
    
    @abstractmethod
    def anticipate_next_questions(self, stage: str, preferences: Dict[str, Any], recent_topics: List[str]) -> List[str]:
        # Anticipate next user questions.
        pass


class IErrorRecoveryService(ABC):
    # Interface for error recovery operations.
    
    @abstractmethod
    def get_recovery_response(self, error_type: str, context: Optional[Dict[str, Any]] = None) -> str:
        # Get recovery response for error type.
        pass


class IVacationPlannerService(ABC):
    # Interface for vacation planning operations.
    
    @abstractmethod
    def generate_suggestions(self, requirements: Dict[str, Any]) -> List[str]:
        # Generate vacation suggestions.
        pass
    
    @abstractmethod
    def create_vacation_summary(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        # Create vacation summary.
        pass 