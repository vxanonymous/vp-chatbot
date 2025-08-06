"""
Dependency Injection Container for the application.
This provides a centralized way to manage service dependencies and improve modularity.
"""
from typing import Optional
from functools import lru_cache
from app.database import get_database
from app.services.user_service import UserService
from app.services.conversation_service import ConversationService
from app.services.openai_service import OpenAIService
from app.services.vacation_intelligence_service import VacationIntelligenceService
from app.services.conversation_memory import ConversationMemory
from app.services.proactive_assistant import ProactiveAssistant
from app.services.error_recovery import ErrorRecoveryService
from app.services.vacation_planner import VacationPlanner


class ServiceContainer:
    """Container for managing service dependencies."""
    
    def __init__(self):
        self._user_service: Optional[UserService] = None
        self._conversation_service: Optional[ConversationService] = None
        self._openai_service: Optional[OpenAIService] = None
        self._intelligence_service: Optional[VacationIntelligenceService] = None
        self._memory: Optional[ConversationMemory] = None
        self._proactive_assistant: Optional[ProactiveAssistant] = None
        self._error_recovery: Optional[ErrorRecoveryService] = None
        self._vacation_planner: Optional[VacationPlanner] = None
    
    @property
    def user_service(self) -> UserService:
        """Get or create UserService instance."""
        if self._user_service is None:
            db = get_database()
            if db is None:
                raise RuntimeError("Database is not available")
            self._user_service = UserService(db.users)
        return self._user_service
    
    @property
    def conversation_service(self) -> ConversationService:
        """Get or create ConversationService instance."""
        if self._conversation_service is None:
            db = get_database()
            if db is None:
                raise RuntimeError("Database is not available")
            self._conversation_service = ConversationService(db.conversations)
        return self._conversation_service
    
    @property
    def openai_service(self) -> OpenAIService:
        """Get or create OpenAIService instance."""
        if self._openai_service is None:
            self._openai_service = OpenAIService()
        return self._openai_service
    
    @property
    def intelligence_service(self) -> VacationIntelligenceService:
        """Get or create VacationIntelligenceService instance."""
        if self._intelligence_service is None:
            self._intelligence_service = VacationIntelligenceService()
        return self._intelligence_service
    
    @property
    def memory(self) -> ConversationMemory:
        """Get or create ConversationMemory instance."""
        if self._memory is None:
            self._memory = ConversationMemory()
        return self._memory
    
    @property
    def proactive_assistant(self) -> ProactiveAssistant:
        """Get or create ProactiveAssistant instance."""
        if self._proactive_assistant is None:
            self._proactive_assistant = ProactiveAssistant()
        return self._proactive_assistant
    
    @property
    def error_recovery(self) -> ErrorRecoveryService:
        """Get or create ErrorRecoveryService instance."""
        if self._error_recovery is None:
            self._error_recovery = ErrorRecoveryService()
        return self._error_recovery
    
    @property
    def vacation_planner(self) -> VacationPlanner:
        """Get or create VacationPlanner instance."""
        if self._vacation_planner is None:
            self._vacation_planner = VacationPlanner()
        return self._vacation_planner
    
    def reset(self):
        """Reset all service instances (useful for testing)."""
        self._user_service = None
        self._conversation_service = None
        self._openai_service = None
        self._intelligence_service = None
        self._memory = None
        self._proactive_assistant = None
        self._error_recovery = None
        self._vacation_planner = None


# Global container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container."""
    return _container


# Convenience functions for common services
@lru_cache()
def get_user_service() -> UserService:
    """Get UserService instance."""
    return get_container().user_service


@lru_cache()
def get_conversation_service() -> ConversationService:
    """Get ConversationService instance."""
    return get_container().conversation_service


@lru_cache()
def get_openai_service() -> OpenAIService:
    """Get OpenAIService instance."""
    return get_container().openai_service


@lru_cache()
def get_intelligence_service() -> VacationIntelligenceService:
    """Get VacationIntelligenceService instance."""
    return get_container().intelligence_service


@lru_cache()
def get_memory() -> ConversationMemory:
    """Get ConversationMemory instance."""
    return get_container().memory


@lru_cache()
def get_proactive_assistant() -> ProactiveAssistant:
    """Get ProactiveAssistant instance."""
    return get_container().proactive_assistant


@lru_cache()
def get_error_recovery() -> ErrorRecoveryService:
    """Get ErrorRecoveryService instance."""
    return get_container().error_recovery


@lru_cache()
def get_vacation_planner() -> VacationPlanner:
    """Get VacationPlanner instance."""
    return get_container().vacation_planner 