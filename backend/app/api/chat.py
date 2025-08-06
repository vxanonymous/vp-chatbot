"""
Chat API endpoints for the vacation planning chatbot.

This module handles all chat-related API endpoints including message sending,
streaming responses, conversation analysis, and user feedback.
"""
import logging
import asyncio
import re
import json
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.models.chat import ChatRequest, ChatResponse, Message, MessageRole
from app.auth.dependencies import get_current_user
from app.models.user import TokenData
from app.core.container import get_container, ServiceContainer
from app.services.conversation_service import ConversationService
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])

# Configuration constants for vacation planning chat
CHAT_TIMEOUT = 45.0  # seconds - allows time for AI to generate detailed travel advice
FALLBACK_RESPONSE = "I'm having trouble processing your request right now. Please try again in a moment."
ERROR_RESPONSE = "I apologize, but I encountered an error. Please try again."

# Service dependency functions for backward compatibility
def get_conversation_service() -> ConversationService:
    """Get conversation service from container."""
    return get_container().conversation_service

def get_openai_service() -> OpenAIService:
    """Get OpenAI service from container."""
    return get_container().openai_service

def _extract_budget_info(text: str) -> Optional[Dict]:
    """
    Extract budget information from user text for vacation planning.
    
    Looks for dollar amounts, budget level indicators, and spending preferences
    to help provide appropriate travel recommendations. Returns structured 
    budget data or None if no budget info found.
    """
    if text is None:
        return None
    
    text_lower = text.lower()
    budget_info = {}
    
    # Look for specific dollar amounts first (common in travel planning)
    dollar_patterns = [
        r'\$(\d+(?:,\d{3})*)',  # $1000, $1,500, $1,500.00
        r'(\d+(?:,\d{3})*)\s*dollars?',  # 1000 dollars, 1,500 dollars
        r'(\d+(?:,\d{3})*)\s*usd',  # 1000 USD, 1,500 USD
    ]
    
    for pattern in dollar_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            # Convert to integer (remove commas and decimals)
            amount = int(float(matches[0].replace(',', '')))
            budget_info["budget_amount"] = {"max": amount, "currency": "USD"}
            break
    
    # Pattern 2: Budget level indicators for travel planning
    budget_levels = {
        "ultra_budget": ["backpack", "hostel", "cheapest", "shoestring", "broke", "no money"],
        "budget": ["budget", "cheap", "affordable", "economical", "save money", "cost conscious"],
        "moderate": ["moderate", "comfortable", "reasonable", "mid-range", "decent"],
        "luxury": ["luxury", "premium", "exclusive", "splurge", "best", "five star", "no budget"]
    }
    
    for level, keywords in budget_levels.items():
        if any(keyword in text_lower for keyword in keywords):
            budget_info["budget_range"] = level
            break
    
    return budget_info if budget_info else None

def _extract_date_info(text: str) -> Optional[Dict]:
    """
    Extract date and time information from user text for vacation planning.
    
    Identifies specific months, seasons, and relative time references to help
    suggest optimal travel timing and seasonal recommendations. Returns structured 
    date data or None if no date info found.
    """
    if text is None:
        return None
    
    text_lower = text.lower()
    date_info = {}
    
    # Check for specific month mentions (important for travel planning)
    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12"
    }
    
    current_year = datetime.now().year
    
    for month_name, month_num in months.items():
        if month_name in text_lower:
            # Calculate start and end of month
            start_date = f"{current_year}-{month_num}-01"
            
            # Handle different month lengths
            if month_num in ["04", "06", "09", "11"]:
                end_day = "30"
            elif month_num == "02":
                # Simple leap year check (not perfect but good enough)
                end_day = "29" if current_year % 4 == 0 else "28"
            else:
                end_day = "31"
            
            end_date = f"{current_year}-{month_num}-{end_day}"
            date_info["travel_dates"] = {"start": start_date, "end": end_date}
            break
    
    # Pattern 2: Seasons
    seasons = {
        "spring": {"start": f"{current_year}-03-20", "end": f"{current_year}-06-20"},
        "summer": {"start": f"{current_year}-06-21", "end": f"{current_year}-09-22"},
        "fall": {"start": f"{current_year}-09-23", "end": f"{current_year}-12-20"},
        "autumn": {"start": f"{current_year}-09-23", "end": f"{current_year}-12-20"},
        "winter": {"start": f"{current_year}-12-21", "end": f"{current_year+1}-03-19"}
    }
    
    for season_name, dates in seasons.items():
        if season_name in text_lower and "travel_dates" not in date_info:
            date_info["travel_dates"] = dates
            break
    
    # Pattern 3: Specific date ranges (e.g., "next week", "in 2 months")
    if "next week" in text_lower:
        # Calculate next week's dates
        today = datetime.now()
        next_week_start = today + timedelta(days=(7 - today.weekday()))
        next_week_end = next_week_start + timedelta(days=6)
        date_info["travel_dates"] = {
            "start": next_week_start.strftime("%Y-%m-%d"),
            "end": next_week_end.strftime("%Y-%m-%d")
        }
    
    return date_info if date_info else None

@router.post("/", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    conversation_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Send a message and get a response."""
    try:
        # If no conversation_id provided, create a new conversation with auto title
        if not conversation_id:
            conversation = await container.conversation_service.create_conversation_with_auto_title(
                user_id=current_user.user_id,
                initial_message=request.message,
                openai_service=container.openai_service
            )
            conversation_id = str(conversation.id)
        else:
            # Validate conversation exists
            conversation = await container.conversation_service.get_conversation(
                conversation_id=conversation_id,
                user_id=current_user.user_id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        
        # Create user message
        user_message = Message(
            role=MessageRole.USER,
            content=request.message
        )
        
        # Add user message to conversation
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
        
        # Prepare messages for AI
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in updated_conversation.messages
        ]
        
        # Log what we're working on
        logger.info(f"Processing a new message for conversation {conversation_id}")
        logger.info(f"This conversation now has {len(updated_conversation.messages)} messages total")
        logger.info(f"The user just said: {request.message}")
        if len(updated_conversation.messages) > 1:
            logger.info(f"Previous messages: {[msg.get('content', '')[:50] + '...' for msg in updated_conversation.messages[:-1]]}")
        
        # Get conversation context and preferences
        conversation_context = None
        user_preferences = None
        
        # Try to get conversation context from previous messages
        if len(updated_conversation.messages) > 1:
            # Look for the most recent AI response that has extracted preferences
            for msg in reversed(updated_conversation.messages[:-1]):  # Exclude the current user message
                if getattr(msg, "role", None) == "assistant" and getattr(msg, "metadata", {}).get("extracted_preferences"):
                    user_preferences = getattr(msg, "metadata", {}).get("extracted_preferences")
                    break
        
        # If no preferences found, try to extract from conversation messages using intelligent analysis
        if not user_preferences:
            try:
                # Use vacation intelligence service for comprehensive preference extraction
                vacation_service = container.intelligence_service
                
                # Convert conversation messages to the format expected by the intelligence service
                user_messages = [
                    {"role": "user", "content": getattr(msg, "content", "")} 
                    for msg in updated_conversation.messages 
                    if getattr(msg, "role", None) == "user"
                ]
                
                # Use the intelligence service to analyze the entire conversation
                insights = await vacation_service.analyze_preferences(user_messages, None)
                
                # Build comprehensive preferences from insights
                extracted_preferences = {}
                
                # Extract destinations from intelligence service
                if insights.get("mentioned_destinations"):
                    extracted_preferences["destinations"] = insights["mentioned_destinations"]
                
                # Extract budget information
                if insights.get("budget_indicators"):
                    budget_level = insights["budget_indicators"][0] if insights["budget_indicators"] else "moderate"
                    extracted_preferences["budget_range"] = budget_level
                
                # Extract travel interests and style
                if insights.get("detected_interests"):
                    extracted_preferences["travel_style"] = insights["detected_interests"]
                
                # Extract decision stage for better context
                if insights.get("decision_stage"):
                    extracted_preferences["decision_stage"] = insights["decision_stage"]
                
                # Set preferences if we found any meaningful data
                if extracted_preferences:
                    user_preferences = extracted_preferences
                    logger.info(f"Found some useful preferences from the conversation: {extracted_preferences}")
                
            except Exception as e:
                logger.warning(f"Couldn't extract preferences using the intelligence service: {e}")
                # Minimal fallback: let the AI service handle preference extraction
                # This is better than hardcoded destinations as it allows the AI to extract any destination
        
        # Always extract basic context from conversation if no preferences found
        if not user_preferences:
            conversation_text = " ".join([getattr(msg, "content", "") for msg in updated_conversation.messages])
            
            # Enhanced budget extraction with multiple patterns
            budget_info = _extract_budget_info(conversation_text)
            if budget_info:
                user_preferences = user_preferences or {}
                user_preferences.update(budget_info)
            
            # Enhanced date extraction with multiple patterns
            date_info = _extract_date_info(conversation_text)
            if date_info:
                user_preferences = user_preferences or {}
                user_preferences.update(date_info)
        
        # Build conversation metadata
        conversation_context = {
            "conversation_id": conversation_id,
            "message_count": len(updated_conversation.messages),
            "user_id": current_user.user_id
        }
        
        # Generate AI response with timeout
        try:
            ai_response = await asyncio.wait_for(
                container.openai_service.generate_response_async(
                    messages,
                    user_preferences=user_preferences,
                    conversation_metadata=conversation_context
                ),
                timeout=CHAT_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"The AI took too long to respond for conversation {conversation_id}")
            ai_response = {"content": FALLBACK_RESPONSE}
        except Exception as e:
            logger.error(f"Something went wrong while generating the AI response: {e}")
            ai_response = {"content": ERROR_RESPONSE}
        
        # Create assistant message with metadata
        assistant_message = Message(
            role=MessageRole.ASSISTANT,
            content=ai_response["content"]
        )
        
        # Add metadata if preferences were extracted
        if ai_response.get("extracted_preferences"):
            assistant_message.metadata = {
                "extracted_preferences": ai_response["extracted_preferences"],
                "confidence_score": ai_response.get("confidence_score", 0.0)
            }
        
        # Add assistant message to conversation
        final_conversation = await container.conversation_service.add_message(
            conversation_id=conversation_id,
            user_id=current_user.user_id,
            message=assistant_message
        )
        
        if not final_conversation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save AI response"
            )
        
        return ChatResponse(
            response=assistant_message.content,
            conversation_id=conversation_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Something went wrong in the chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    conversation_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Stream a message response."""
    try:
        # If no conversation_id provided, create a new conversation with auto title
        if not conversation_id:
            conversation = await container.conversation_service.create_conversation_with_auto_title(
                user_id=current_user.user_id,
                initial_message=request.message,
                openai_service=container.openai_service
            )
            conversation_id = str(conversation.id)
        else:
            # Validate conversation exists
            conversation = await container.conversation_service.get_conversation(
                conversation_id=conversation_id,
                user_id=current_user.user_id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        
        # Create user message
        user_message = Message(
            role=MessageRole.USER,
            content=request.message
        )
        
        # Add user message to conversation
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
        
        # Prepare messages for AI
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in updated_conversation.messages
        ]
        
        async def generate_stream():
            try:
                # Get conversation context and preferences
                conversation_context = None
                user_preferences = None
                
                # Try to get conversation context from previous messages
                if len(updated_conversation.messages) > 1:
                    # Look for the most recent AI response that has extracted preferences
                    for msg in reversed(updated_conversation.messages[:-1]):  # Exclude the current user message
                        if getattr(msg, "role", None) == "assistant" and getattr(msg, "metadata", {}).get("extracted_preferences"):
                            user_preferences = getattr(msg, "metadata", {}).get("extracted_preferences")
                            break
                
                # If no preferences found, try to extract from conversation messages
                if not user_preferences:
                    # Extract basic preferences from conversation content
                    conversation_text = " ".join([getattr(msg, "content", "") for msg in updated_conversation.messages])
                    if "mongolia" in conversation_text.lower():
                        user_preferences = {"destinations": ["Mongolia"]}
                    elif "japan" in conversation_text.lower():
                        user_preferences = {"destinations": ["Japan"]}
                    elif "bali" in conversation_text.lower():
                        user_preferences = {"destinations": ["Bali"]}
                    elif "paris" in conversation_text.lower():
                        user_preferences = {"destinations": ["Paris"]}
                
                # Always extract basic context from conversation if no preferences found
                if not user_preferences:
                    conversation_text = " ".join([getattr(msg, "content", "") for msg in updated_conversation.messages])
                    # Look for budget mentions
                    if "budget" in conversation_text.lower() or "$" in conversation_text:
                        budget_match = re.search(r'\$(\d+)', conversation_text)
                        if budget_match:
                            budget_amount = int(budget_match.group(1))
                            user_preferences = {"budget_amount": {"max": budget_amount}}
                    
                    # Look for date mentions
                    if "june" in conversation_text.lower():
                        user_preferences = user_preferences or {}
                        user_preferences["travel_dates"] = {"start": "2023-06-01", "end": "2023-06-30"}
                
                # Build conversation metadata
                conversation_context = {
                    "conversation_id": conversation_id,
                    "message_count": len(updated_conversation.messages),
                    "user_id": current_user.user_id
                }
                
                # Generate AI response with timeout
                ai_response = await asyncio.wait_for(
                    container.openai_service.generate_response_async(
                        messages,
                        user_preferences=user_preferences,
                        conversation_metadata=conversation_context
                    ),
                    timeout=CHAT_TIMEOUT
                )
                
                # Stream the response
                response_content = ai_response["content"]
                for chunk in response_content.split():
                    yield f"data: {json.dumps({'content': chunk + ' '})}\n\n"
                    await asyncio.sleep(0.1)  # Small delay for streaming effect
                
                # Create assistant message with metadata
                assistant_message = Message(
                    role=MessageRole.ASSISTANT,
                    content=response_content
                )
                
                # Add metadata if preferences were extracted
                if ai_response.get("extracted_preferences"):
                    assistant_message.metadata = {
                        "extracted_preferences": ai_response["extracted_preferences"],
                        "confidence_score": ai_response.get("confidence_score", 0.0)
                    }
                
                # Add assistant message to conversation
                await container.conversation_service.add_message(
                    conversation_id=conversation_id,
                    user_id=current_user.user_id,
                    message=assistant_message
                )
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except asyncio.TimeoutError:
                logger.warning(f"The streaming response took too long for conversation {conversation_id}")
                yield f"data: {json.dumps({'content': FALLBACK_RESPONSE})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                logger.error(f"Something went wrong in the chat stream: {e}")
                yield f"data: {json.dumps({'content': ERROR_RESPONSE})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Something went wrong in the chat stream endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat stream request"
        )


@router.get("/conversations/{conversation_id}/analysis")
async def get_conversation_analysis(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Get analysis of a conversation."""
    try:
        # Validate conversation exists
        conversation = await container.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Analyze conversation
        analysis = await container.conversation_service.analyze_conversation(conversation_id)
        
        return {
            "conversation_id": conversation_id,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Couldn't analyze the conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze conversation"
        )


@router.post("/feedback")
async def submit_feedback(
    conversation_id: str,
    feedback: str,
    rating: int,
    current_user: TokenData = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container)
):
    """Submit feedback for a conversation."""
    try:
        # Validate conversation exists
        conversation = await container.conversation_service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Store feedback
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
    except Exception as e:
        logger.error(f"Couldn't submit the user's feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )