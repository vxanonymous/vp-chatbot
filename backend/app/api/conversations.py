"""
Conversations API endpoints.

Manages conversation CRUD operations for the vacation planning chatbot,
including creation, retrieval, updates, and deletion of user conversations.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.conversation_db import ConversationInDB, ConversationSummary, ConversationUpdate
from app.auth.dependencies import get_current_user
from app.models.user import TokenData
from app.core.container import get_container, ServiceContainer
from app.services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])

# Service dependency functions for backward compatibility
def get_conversation_service() -> ConversationService:
    """Get conversation service from dependency injection container."""
    return get_container().conversation_service


@router.get("/", response_model=List[ConversationSummary])
async def get_conversations(
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """
    Retrieve all conversations for the current user.
    
    Returns a list of conversation summaries with metadata.
    """
    try:
        conversations = await container.conversation_service.get_user_conversations(
            user_id=current_user.user_id
        )
        return conversations
    except Exception as e:
        logger.error(f"Had trouble getting the user's conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we're having trouble loading your conversations right now. Please try again."
        )


@router.post("/", response_model=ConversationInDB, status_code=201)
async def create_conversation(
    title: str = "New Conversation",
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """
    Create a new conversation for the current user.
    
    Initializes a new conversation with the specified title.
    """
    try:
        # Create new conversation
        conversation = await container.conversation_service.create_conversation(
            user_id=current_user.user_id,
            title=title
        )
        return conversation
    except Exception as e:
        logger.error(f"Couldn't create a new conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we couldn't create a new conversation right now. Please try again."
        )


@router.get("/{conversation_id}", response_model=ConversationInDB)
async def get_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """
    Retrieve a specific conversation by ID.
    
    Returns the full conversation with all messages and metadata.
    """
    try:
        conversation = await container.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="We couldn't find that conversation. It may have been deleted or you don't have access to it."
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Had trouble getting that specific conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we're having trouble loading that conversation right now. Please try again."
        )


@router.put("/{conversation_id}", response_model=ConversationInDB)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Update a conversation."""
    try:
        conversation = await container.conversation_service.update_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id,
            update=update_data
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="We couldn't find that conversation to update. It may have been deleted or you don't have access to it."
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Couldn't update the conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we couldn't update that conversation right now. Please try again."
        )


@router.patch("/{conversation_id}", response_model=ConversationInDB)
async def patch_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Update a conversation (PATCH method)."""
    try:
        conversation = await container.conversation_service.update_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id,
            update=update_data
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="We couldn't find that conversation to update. It may have been deleted or you don't have access to it."
            )
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Couldn't update the conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Delete a conversation."""
    try:
        success = await container.conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="We couldn't find that conversation to delete. It may have been already deleted or you don't have access to it."
            )
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Couldn't delete the conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we couldn't delete that conversation right now. Please try again."
        )