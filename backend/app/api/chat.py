# Chat API endpoints for the vacation planning system.
# streaming responses, conversation analysis, and user feedback.
import asyncio
import json
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.responses import StreamingResponse

from app.api.error_handlers import handle_app_exception
from app.auth.dependencies import get_current_user
from app.core.container import ServiceContainer, get_container
from app.core.exceptions import AppException
from app.middleware.rate_limiter import chat_rate_limiter
from app.models.chat import ChatRequest, ChatResponse, Message, MessageRole
from app.models.user import TokenData

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

CHAT_TIMEOUT = 180.0
FALLBACK_RESPONSE = "I'm having trouble processing your request right now. Please try again in a moment."
ERROR_RESPONSE = "I apologize, but I encountered an error. Please try again."



@router.post("/", response_model=ChatResponse)
# send message.

async def send_message(
    request: ChatRequest,
    conversation_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):

    # Rate limiting check
    is_allowed, remaining = await chat_rate_limiter.is_allowed(current_user.user_id)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait before sending another message. Limit: {chat_rate_limiter.max_requests} requests per {chat_rate_limiter.window_seconds} seconds."
        )

    try:
        # Get existing conversation messages for validation if conversation_id exists
        messages_for_validation = []
        if conversation_id:
            existing_conversation = await container.conversation_service.get_conversation(
                conversation_id=conversation_id,
                user_id=current_user.user_id
            )
            if existing_conversation:
                messages_for_validation = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in existing_conversation.messages
                ]
        
        validation = container.error_recovery.validate_conversation_flow(
            messages=messages_for_validation,
            new_message=request.message
        )
        
        if not validation["is_valid"]:
            recovery_response = container.error_recovery.get_recovery_response(
                error_type="off_topic" if "possibly_off_topic" in validation["issues"] else "unclear_input"
            )
            return ChatResponse(
                response=recovery_response,
                conversation_id=conversation_id or "",
                suggestions=None,
                vacation_summary=None
            )
        
        result = await container.conversation_handler.process_message(
            message_content=request.message,
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        
        conversation_id = result["conversation_id"]
        
        conversation = await container.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        
        user_preferences = await container.conversation_handler.extract_user_preferences(
            conversation
        ) if conversation else None
        
        suggestions = None
        vacation_summary = None
        
        if conversation:
            stage = user_preferences.get("decision_stage", "exploring") if user_preferences else "exploring"
            context = {"stage": stage}
            
            suggestions_list = container.proactive_assistant.get_proactive_suggestions(
                context=context,
                preferences=user_preferences or {},
                message_count=len(conversation.messages)
            )
            suggestions = [s["content"] for s in suggestions_list] if suggestions_list else None
            
            if user_preferences and user_preferences.get("destinations"):
                logger.info(f"Creating vacation_summary for conversation {conversation_id} with destinations: {user_preferences.get('destinations')}")
                vacation_summary = container.vacation_planner.create_vacation_summary(
                    preferences=user_preferences
                )
                logger.info(f"Created vacation_summary: {vacation_summary}")
            else:
                logger.info(f"No vacation_summary created - user_preferences: {user_preferences}, destinations: {user_preferences.get('destinations') if user_preferences else None}")
        
        return ChatResponse(
            response=result["response"],
            conversation_id=conversation_id,
            suggestions=suggestions,
            vacation_summary=vacation_summary
        )
        
    except ValueError as e:
        if "Conversation not found" in str(e):
            recovery_response = container.error_recovery.get_recovery_response(
                error_type="no_context",
                context={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=recovery_response
            )
        elif "Failed to save" in str(e):
            recovery_response = container.error_recovery.get_recovery_response(
                error_type="api_error",
                context={"error": str(e)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=recovery_response
            )
        recovery_response = container.error_recovery.get_recovery_response(
            error_type="general_error",
            context={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=recovery_response
        )
    except HTTPException:
        raise
    except AppException as e:
        recovery_response = container.error_recovery.get_recovery_response(
            error_type="api_error",
            context={"error": str(e)}
        )
        raise handle_app_exception(e)
    except Exception as e:
        logger.error(f"Something went wrong in the chat endpoint: {e}")
        recovery_response = container.error_recovery.get_recovery_response(
            error_type="api_error",
            context={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=recovery_response
        )

@router.post("/stream")
# stream message.

async def stream_message(
    request: ChatRequest,
    conversation_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):

    try:
        if not conversation_id:
            conversation = await container.conversation_service.create_conversation_with_auto_title(
                user_id=current_user.user_id,
                initial_message=request.message,
                openai_service=container.openai_service
            )
            conversation_id = str(conversation.id)
        else:
            conversation = await container.conversation_service.get_conversation(
                conversation_id=conversation_id,
                user_id=current_user.user_id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        user_message = Message(
            role=MessageRole.USER,
            content=request.message
        )
        
        try:
            updated_conversation = await container.conversation_service.add_message(
                conversation_id=conversation_id,
                user_id=current_user.user_id,
                message=user_message
            )
            
            if not updated_conversation:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save message"
                )
        except AppException as e:
            raise handle_app_exception(e)
        
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in updated_conversation.messages
        ]
        
        async def generate_stream():
            try:

                user_preferences = await container.conversation_handler.extract_user_preferences(
                    updated_conversation
                )
                
                conversation_context = container.conversation_handler.build_conversation_metadata(
                    conversation_id=conversation_id,
                    user_id=current_user.user_id,
                    message_count=len(updated_conversation.messages)
                )
                
                ai_response = await asyncio.wait_for(
                    container.openai_service.generate_response_async(
                        messages,
                        user_preferences=user_preferences,
                        conversation_metadata=conversation_context
                    ),
                    timeout=CHAT_TIMEOUT
                )
                
                response_content = ai_response["content"]
                for chunk in response_content.split():
                    yield f"data: {json.dumps({'content': f'{chunk} '})}\n\n"
                    await asyncio.sleep(0.1)
                
                assistant_message = Message(
                    role=MessageRole.ASSISTANT,
                    content=response_content
                )
                
                if ai_response.get("extracted_preferences"):
                    assistant_message.metadata = {
                        "extracted_preferences": ai_response["extracted_preferences"],
                        "confidence_score": ai_response.get("confidence_score", 0.0)
                    }
                
                await container.conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=current_user.user_id,
                    message=assistant_message
                )
                
                final_conversation = await container.conversation_service.get_conversation(
                    conversation_id=conversation_id,
                    user_id=current_user.user_id
                )
                
                if final_conversation:
                    final_user_preferences = await container.conversation_handler.extract_user_preferences(
                        final_conversation
                    )
                    
                    stage = final_user_preferences.get("decision_stage", "exploring") if final_user_preferences else "exploring"
                    context = {"stage": stage}
                    
                    suggestions_list = container.proactive_assistant.get_proactive_suggestions(
                        context=context,
                        preferences=final_user_preferences or {},
                        message_count=len(final_conversation.messages)
                    )
                    suggestions = [s["content"] for s in suggestions_list] if suggestions_list else None
                    
                    if suggestions:
                        yield f"data: {json.dumps({'suggestions': suggestions})}\n\n"
                    
                    if final_user_preferences and final_user_preferences.get("destinations"):
                        vacation_summary = container.vacation_planner.create_vacation_summary(
                            preferences=final_user_preferences
                        )
                        if vacation_summary:
                            yield f"data: {json.dumps({'vacation_summary': vacation_summary})}\n\n"
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except asyncio.TimeoutError:
                logger.warning(f"The streaming response took too long for conversation {conversation_id}")
                recovery_response = container.error_recovery.get_recovery_response(
                    error_type="api_error",
                    context={"error": "timeout"}
                )
                yield f"data: {json.dumps({'content': recovery_response})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except AppException as e:
                logger.error(f"Application error in chat stream: {e.message}")
                recovery_response = container.error_recovery.get_recovery_response(
                    error_type="api_error",
                    context={"error": str(e)}
                )
                yield f"data: {json.dumps({'content': recovery_response})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                logger.error(f"Something went wrong in the chat stream: {e}")
                recovery_response = container.error_recovery.get_recovery_response(
                    error_type="api_error",
                    context={"error": str(e)}
                )
                yield f"data: {json.dumps({'content': recovery_response})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except HTTPException:
        raise
    except AppException as e:
        raise handle_app_exception(e)
    except Exception as e:
        logger.error(f"Something went wrong in the chat stream endpoint: {e}")
        recovery_response = container.error_recovery.get_recovery_response(
            error_type="api_error",
            context={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=recovery_response
        )

@router.get("/conversations/{conversation_id}/analysis")
# get conversation analysis.

async def get_conversation_analysis(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):

    try:
        conversation = await container.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        analysis = await container.conversation_service.analyze_conversation(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except AppException as e:
        raise handle_app_exception(e)
    except Exception as e:
        logger.error(f"Couldn't analyze the conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze conversation"
        )

@router.post("/feedback")
# submit feedback.

async def submit_feedback(
    conversation_id: str,
    feedback: str,
    rating: int,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):

    try:
        conversation = await container.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        success = await container.conversation_service.add_feedback(
            conversation_id=conversation_id,
            feedback=feedback,
            rating=rating
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save feedback"
            )
        
        return {"message": "Feedback submitted successfully"}
        
    except HTTPException:
        raise
    except AppException as e:
        raise handle_app_exception(e)
    except Exception as e:
        logger.error(f"Couldn't submit the user's feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )