import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.interfaces import (IConversationService, IOpenAIService,
                                 IVacationIntelligenceService)
from app.models.chat import Message, MessageRole
from app.models.conversation_db import ConversationInDB
from app.services.conversation_memory import ConversationMemory
from app.services.conversation_service import ConversationService
from app.services.openai_service import OpenAIService
from app.services.vacation_intelligence_service import \
    VacationIntelligenceService
from app.services.request_deduplicator import RequestDeduplicator

logger = logging.getLogger(__name__)

class ConversationHandler:
    
    CHAT_TIMEOUT = 180.0
    FALLBACK_RESPONSE = "I'm having trouble processing your request right now. Please try again in a moment."
    ERROR_RESPONSE = "I apologize, but I encountered an error. Please try again."
    
    def __init__(
        self,
        conversation_service: IConversationService,
        openai_service: IOpenAIService,
        intelligence_service: Optional[IVacationIntelligenceService] = None,
        memory_service: Optional[ConversationMemory] = None,
        request_deduplicator: Optional[RequestDeduplicator] = None
    ):

        self.conversation_service = conversation_service
        self.openai_service = openai_service
        self.intelligence_service = intelligence_service
        self.memory_service = memory_service
        self.request_deduplicator = request_deduplicator or RequestDeduplicator()
    
    async def ensure_conversation_exists(
        self,
        conversation_id: Optional[str],
        user_id: str,
        initial_message: str
    ) -> ConversationInDB:

        if not conversation_id:
            if hasattr(self.conversation_service, 'create_conversation_with_auto_title'):
                conversation = await self.conversation_service.create_conversation_with_auto_title(
                    user_id=user_id,
                    initial_message=initial_message,
                    openai_service=self.openai_service if isinstance(self.openai_service, OpenAIService) else None
                )
            else:
                conversation = await self.conversation_service.create_conversation(
                    user_id=user_id,
                    title="New Vacation Planning Chat"
                )
            return conversation
        else:
            conversation = await self.conversation_service.get_conversation(
                conversation_id=conversation_id,
                user_id=user_id
            )
            if not conversation:
                raise ValueError("Conversation not found")
            return conversation
    
    async def add_user_message(
        self,
        conversation_id: str,
        user_id: str,
        message_content: str
    ) -> ConversationInDB:

        user_message = Message(
            role=MessageRole.USER,
            content=message_content
        )
        
        updated_conversation = await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            message=user_message
        )
        
        if not updated_conversation:
            raise ValueError("Failed to save message")
        
        return updated_conversation
    
    async def extract_user_preferences(
        self,
        conversation: ConversationInDB
    ) -> Optional[Dict[str, Any]]:

        user_preferences = None

        if len(conversation.messages) > 0:
            for msg in reversed(conversation.messages):
                # Handle both dict (from DB) and Message object formats
                if isinstance(msg, dict):
                    role = msg.get("role")
                else:
                    # Message object - handle enum role
                    role = getattr(msg, "role", None)
                    role = role.value if hasattr(role, "value") else str(role) if role else None
                
                if role == "assistant":
                    # Handle both dict (from DB) and Message object formats
                    if isinstance(msg, dict):
                        metadata = msg.get("metadata", {})
                    else:
                        metadata = getattr(msg, "metadata", {})
                    if isinstance(metadata, dict) and metadata.get("extracted_preferences"):
                        user_preferences = metadata["extracted_preferences"]
                        # If preferences exist but don't have destinations, still run extraction
                        if user_preferences and not user_preferences.get("destinations"):
                            user_preferences = None  # Force re-extraction
                        break

        if self.intelligence_service:
            try:
                user_messages = []
                for msg in conversation.messages:
                    # Handle both dict (from DB) and Message object formats
                    if isinstance(msg, dict):
                        role = msg.get("role")
                        content = msg.get("content", "")
                    else:
                        # Message object - handle enum role
                        role = getattr(msg, "role", None)
                        role = role.value if hasattr(role, "value") else str(role) if role else None
                        content = getattr(msg, "content", "")
                    
                    if role == "user":
                        user_messages.append({
                            "role": "user", 
                            "content": content
                        })
                
                if not user_messages:
                    logger.warning(f"No user messages found in conversation {conversation.id}. Total messages: {len(conversation.messages)}")
                else:
                    logger.debug(f"Extracting preferences from {len(user_messages)} user messages")
                
                insights = await self.intelligence_service.analyze_preferences(
                    user_messages, 
                    user_preferences
                )
                
                extracted_preferences = {}
                
                if insights.get("mentioned_destinations"):
                    extracted_preferences["destinations"] = insights["mentioned_destinations"]
                    logger.info(f"Extracted destinations from intelligence service: {insights['mentioned_destinations']}")
                
                # Fallback: check memory service for destinations if intelligence service didn't find any
                if not extracted_preferences.get("destinations") and self.memory_service:
                    try:
                        memory_context = self.memory_service.get_context(str(conversation.id))
                        if memory_context and memory_context.get("destinations"):
                            dest_value = memory_context["destinations"].get("value", [])
                            if dest_value:
                                extracted_preferences["destinations"] = dest_value if isinstance(dest_value, list) else [dest_value]
                                logger.info(f"Found destinations from memory service: {extracted_preferences['destinations']}")
                    except Exception as e:
                        logger.warning(f"Error checking memory service for destinations: {e}")
                if insights.get("budget_indicators"):
                    budget_level = insights["budget_indicators"][0] if insights["budget_indicators"] else "moderate"
                    extracted_preferences["budget_range"] = budget_level
                if insights.get("budget_amount"):
                    extracted_preferences["budget_amount"] = insights["budget_amount"]
                if insights.get("detected_interests"):
                    extracted_preferences["travel_style"] = insights["detected_interests"]
                if insights.get("decision_stage"):
                    extracted_preferences["decision_stage"] = insights["decision_stage"]
                
                if extracted_preferences:
                    if user_preferences:
                        user_preferences.update(extracted_preferences)
                    else:
                        user_preferences = extracted_preferences
                    logger.info(f"Extracted preferences: {extracted_preferences}")
            except Exception as e:
                logger.warning(f"Could not extract preferences using intelligence service: {e}")
        
        return user_preferences
    
    def build_conversation_metadata(
        self,
        conversation_id: str,
        user_id: str,
        message_count: int
    ) -> Dict[str, Any]:

        return {
            "conversation_id": conversation_id,
            "message_count": message_count,
            "user_id": user_id
        }
    
    def prepare_messages_for_ai(
        self,
        conversation: ConversationInDB
    ) -> List[Dict[str, str]]:

        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation.messages
        ]
    
    async def generate_ai_response(
        self,
        messages: List[Dict[str, str]],
        user_preferences: Optional[Dict[str, Any]],
        conversation_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:

        try:
            ai_response = await asyncio.wait_for(
                self.openai_service.generate_response_async(
                    messages,
                    user_preferences=user_preferences,
                    conversation_metadata=conversation_metadata
                ),
                timeout=self.CHAT_TIMEOUT
            )
            return ai_response
        except asyncio.TimeoutError:
            logger.warning("AI response generation timed out")
            return {"content": self.FALLBACK_RESPONSE}
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {"content": self.ERROR_RESPONSE}
    
    async def save_assistant_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        extracted_preferences: Optional[Dict[str, Any]] = None,
        confidence_score: float = 0.0
    ) -> ConversationInDB:

        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=content
        )

        if extracted_preferences:
            assistant_message.metadata = {
                "extracted_preferences": extracted_preferences,
                "confidence_score": confidence_score
            }
        
        final_conversation = await self.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            message=assistant_message
        )
        
        if not final_conversation:
            raise ValueError("Failed to save AI response")
        
        return final_conversation
    
    async def process_message(
        self,
        message_content: str,
        conversation_id: Optional[str],
        user_id: str
    ) -> Dict[str, Any]:

        conversation = await self.ensure_conversation_exists(
            conversation_id=conversation_id,
            user_id=user_id,
            initial_message=message_content
        )
        conversation_id = str(conversation.id)
        
        updated_conversation = await self.add_user_message(
            conversation_id=conversation_id,
            user_id=user_id,
            message_content=message_content
        )
        
        if self.memory_service:
            messages_dict = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in updated_conversation.messages
            ]
            key_points = self.memory_service.extract_key_points(messages_dict)
            
            context_to_store = {
                "last_message": message_content,
                "message_count": len(updated_conversation.messages)
            }
            if key_points.get("destinations"):
                context_to_store["destinations"] = key_points["destinations"]
            if key_points.get("preferences"):
                context_to_store["preferences"] = key_points["preferences"]
            
            self.memory_service.store_context(conversation_id, context_to_store, key_points)
        
        messages = self.prepare_messages_for_ai(updated_conversation)
        user_preferences = await self.extract_user_preferences(updated_conversation)
        
        if self.memory_service:
            memory_context = self.memory_service.get_context(conversation_id)
            if memory_context and user_preferences:
                for key, data in memory_context.items():
                    if key not in user_preferences and isinstance(data.get("value"), (str, list)):
                        user_preferences[f"memory_{key}"] = data["value"]
        
        conversation_metadata = self.build_conversation_metadata(
            conversation_id=conversation_id,
            user_id=user_id,
            message_count=len(updated_conversation.messages)
        )
        
        # Use request deduplication to cache identical AI responses
        async def _generate_ai_response():
            return await self.generate_ai_response(
                messages=messages,
                user_preferences=user_preferences,
                conversation_metadata=conversation_metadata
            )
        
        ai_response, is_cached = await self.request_deduplicator.get_or_execute(
            user_id=user_id,
            message=message_content,
            conversation_id=conversation_id,
            coro=_generate_ai_response
        )
        
        if is_cached:
            logger.info(f"Returned cached AI response for user {user_id}, conversation {conversation_id}")
        
        # Use extracted preferences from intelligence service, not from AI response
        # (OpenRouter doesn't support function calling, so ai_response won't have extracted_preferences)
        extracted_prefs_to_save = user_preferences if user_preferences else ai_response.get("extracted_preferences")
        
        await self.save_assistant_message(
            conversation_id=conversation_id,
            user_id=user_id,
            content=ai_response.get("content", self.ERROR_RESPONSE),
            extracted_preferences=extracted_prefs_to_save,
            confidence_score=ai_response.get("confidence_score", 0.0)
        )
        
        return {
            "response": ai_response.get("content", self.ERROR_RESPONSE),
            "conversation_id": conversation_id
        }

