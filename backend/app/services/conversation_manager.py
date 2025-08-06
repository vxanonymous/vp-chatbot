try:
    import redis
except ImportError:
    # Fallback for environments without redis
    class redis:
        @staticmethod
        def from_url(url):
            return type('obj', (object,), {
                'setex': lambda key, ttl, data: None,
                'get': lambda key: None,
                'delete': lambda key: 0
            })
import json
import uuid
from typing import Optional, Dict
from datetime import datetime, timezone
import logging
from app.config import settings
from app.models.chat import Message, ConversationHistory, MessageRole
from app.models.conversation_db import ConversationInDB

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages active vacation planning conversations in Redis for fast access."""
    
    def __init__(self):
        # Set up Redis to keep track of all the vacation planning conversations
        # This helps us remember what people are talking about without having to hit the database every time
        self.redis_client = redis.from_url(settings.redis_url)
        
        # How long we keep vacation chats in memory (people sometimes come back to finish planning)
        self.ttl = settings.conversation_ttl
        
        # Maximum number of messages in a conversation (most vacation planning chats don't need hundreds of messages)
        self.max_length = settings.max_conversation_length
    
    def create_conversation(self) -> str:
        """Create a new vacation planning conversation."""
        # Generate a more human-readable ID with timestamp and random suffix
        current_time = datetime.now(timezone.utc)
        
        # Use a more natural timestamp format - like how humans think about time
        if current_time.hour < 12:
            time_label = "morning"
        elif current_time.hour < 17:
            time_label = "afternoon"
        else:
            time_label = "evening"
            
        date_part = current_time.strftime("%m%d")
        random_suffix = str(uuid.uuid4())[:6]  # Shorter, more readable
        conversation_id = f"vacation_{date_part}_{time_label}_{random_suffix}"
        
        # Initialize with vacation-specific structure and some default preferences
        # These defaults reflect common vacation planning scenarios
        conversation_data = {
            "id": conversation_id,
            "messages": [],
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
            "user_preferences": {
                "budget_range": "not_set",
                "travel_style": "not_set",
                "group_size": 1,
                "preferred_destinations": [],
                "accessibility_needs": False,
                "has_pets": False,  # Some people travel with pets
                "preferred_weather": "not_set"
            },
            "vacation_session": {
                "when_started": current_time.isoformat(),
                "how_many_messages": 0,
                "last_heard_from": None,
                "what_we_are_doing": "planning_a_vacation",
                "how_long_this_takes": None,
                "time_of_day": time_label,
                "day_of_week": current_time.strftime("%A").lower(),
                "is_weekend": current_time.weekday() >= 5,
                "planning_mood": "just_started",
                "what_we_know": {
                    "destinations": [],
                    "budget_range": "not_sure_yet",
                    "travel_style": "still_figuring_out",
                    "group_size": 1,
                    "has_pets": False,
                    "weather_preference": "not_decided"
                },
                "conversation_flow": {
                    "questions_asked": 0,
                    "excitement_level": 0,
                    "destinations_mentioned": 0,
                    "budget_talked_about": 0,
                    "planning_stage": "initial_chat"
                }
            }
        }
        
        # Store with vacation-specific key pattern and add some metadata
        redis_key = f"vacation_chat:{conversation_id}"
        self.redis_client.setex(
            redis_key,
            self.ttl,
            json.dumps(conversation_data)
        )
        
        logger.info(f"Started a new vacation planning chat session - ID: {conversation_id} at {current_time.strftime('%H:%M:%S')}")
        return conversation_id
    
    def create_conversation_with_id(self, conversation_id: str) -> str:
        """Create a vacation planning conversation with a specific ID."""
        # Make sure we have a valid conversation ID to work with
        if not conversation_id or conversation_id.strip() == "":
            raise ValueError("Hey, we need a conversation ID - can't create a vacation chat without one")
        
        # Check for reasonable ID length (not too short, not too long)
        # Most conversation IDs should be meaningful but not ridiculously long
        if len(conversation_id) < 5 or len(conversation_id) > 100:
            raise ValueError("The conversation ID needs to be between 5 and 100 characters - that one's too short or too long")
            
        current_time = datetime.now(timezone.utc)
        
        # Figure out what time of day this is for vacation planning context
        if current_time.hour < 12:
            time_context = "morning_planning"
        elif current_time.hour < 17:
            time_context = "afternoon_planning"
        else:
            time_context = "evening_planning"
            
        conversation_data = {
            "id": conversation_id,
            "messages": [],
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
            "user_preferences": {
                "budget_range": "not_set",
                "travel_style": "not_set",
                "group_size": 1,
                "preferred_destinations": [],
                "accessibility_needs": False,
                "has_pets": False,  # Some people travel with pets
                "preferred_weather": "not_set",
                "accommodation_type": "not_set"
            },
            "vacation_session": {
                "when_started": current_time.isoformat(),
                "how_many_messages": 0,
                "last_heard_from": None,
                "what_we_are_doing": "planning_a_vacation",
                "how_long_this_takes": None,
                "custom_id": True,
                "time_context": time_context,
                "day_of_week": current_time.strftime("%A").lower(),
                "is_weekend": current_time.weekday() >= 5,  # Saturday = 5, Sunday = 6
                "planning_mood": "just_started",
                "what_we_know": {
                    "destinations": [],
                    "budget_range": "not_sure_yet",
                    "travel_style": "still_figuring_out",
                    "group_size": 1,
                    "has_pets": False,
                    "weather_preference": "not_decided",
                    "accommodation_type": "not_decided"
                },
                "conversation_flow": {
                    "questions_asked": 0,
                    "excitement_level": 0,
                    "destinations_mentioned": 0,
                    "budget_talked_about": 0,
                    "planning_stage": "initial_chat"
                }
            }
        }
        
        # Use vacation-specific key pattern for consistency
        redis_key = f"vacation_chat:{conversation_id}"
        self.redis_client.setex(
            redis_key,
            self.ttl,
            json.dumps(conversation_data)
        )
        
        logger.info(f"Set up a vacation planning session with the custom ID: {conversation_id} at {current_time.strftime('%H:%M')}")
        return conversation_id
    
    def load_from_mongodb(self, db_conversation: ConversationInDB):
        """Load a vacation planning conversation from MongoDB into Redis for fast access."""
        # Process and validate messages from the database
        messages = []
        valid_message_count = 0
        total_content_length = 0
        questions_count = 0
        exclamations_count = 0
        
        for msg in db_conversation.messages:
            # Skip completely empty or invalid messages
            if not msg.get("content") or msg.get("content", "").strip() == "":
                continue
                
            # Skip messages that are just punctuation or whitespace
            content = msg.get("content", "").strip()
            if len(content) < 2:  # At least 2 characters to be meaningful
                continue
                
            # Add some validation and metadata
            has_question = "?" in content
            has_exclamation = "!" in content
            
            if has_question:
                questions_count += 1
            if has_exclamation:
                exclamations_count += 1
                
            message_data = {
                "role": msg.get("role", "user"),
                "content": content,
                "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "loaded_from_db": True,
                "message_index": valid_message_count,
                "content_length": len(content),
                "has_question": has_question,
                "has_exclamation": has_exclamation,
                "mentions_destination": any(dest in content.lower() for dest in ["paris", "london", "tokyo", "beach", "mountains", "city", "resort", "hotel"]),
                "mentions_budget": any(word in content.lower() for word in ["$", "dollar", "budget", "cheap", "expensive", "cost", "price"])
            }
            messages.append(message_data)
            valid_message_count += 1
            total_content_length += len(content)
        
        # Create enhanced session metadata with vacation planning context
        current_time = datetime.now(timezone.utc)
        
        # Calculate some interesting stats about this vacation planning conversation
        destinations_discussed = sum(1 for msg in messages if msg.get("mentions_destination", False))
        budget_discussed = sum(1 for msg in messages if msg.get("mentions_budget", False))
        
        # Figure out the planning mood based on conversation content
        if questions_count > exclamations_count:
            planning_mood = "curious_and_asking"
        elif exclamations_count > questions_count:
            planning_mood = "excited_and_enthusiastic"
        else:
            planning_mood = "balanced_and_thoughtful"
            
        # Determine planning stage based on content
        if destinations_discussed > 0 and budget_discussed > 0:
            planning_stage = "detailed_planning"
        elif destinations_discussed > 0:
            planning_stage = "destination_exploration"
        elif budget_discussed > 0:
            planning_stage = "budget_consideration"
        else:
            planning_stage = "initial_chat"
            
        vacation_session = {
            "when_started": db_conversation.created_at.isoformat(),
            "how_many_messages": len(messages),
            "last_heard_from": db_conversation.updated_at.isoformat(),
            "what_we_are_doing": "planning_a_vacation",
            "how_long_this_takes": None,
            "loaded_from_database": True,
            "when_we_loaded_it": current_time.isoformat(),
            "valid_messages": valid_message_count,
            "total_words_written": total_content_length,
            "average_message_length": total_content_length // max(1, valid_message_count),
            "planning_mood": planning_mood,
            "what_we_know": {
                "destinations": [],
                "budget_range": "not_sure_yet",
                "travel_style": "still_figuring_out",
                "group_size": 1,
                "has_pets": False,
                "weather_preference": "not_decided"
            },
            "conversation_flow": {
                "questions_asked": questions_count,
                "excitement_level": exclamations_count,
                "destinations_mentioned": destinations_discussed,
                "budget_talked_about": budget_discussed,
                "planning_stage": planning_stage,
                "conversation_style": "lots_of_questions" if questions_count > exclamations_count else "very_excited" if exclamations_count > questions_count else "balanced_discussion"
            }
        }
        
        # Merge existing preferences with defaults for vacation planning
        # These defaults reflect common vacation planning scenarios
        default_prefs = {
            "budget_range": "not_set",
            "travel_style": "not_set", 
            "group_size": 1,
            "preferred_destinations": [],
            "accessibility_needs": False,
            "has_pets": False,
            "preferred_weather": "not_set",
            "accommodation_type": "not_set",
            "transportation": "not_set"
        }
        
        existing_prefs = db_conversation.vacation_preferences or {}
        merged_prefs = {**default_prefs, **existing_prefs}
        
        # Add some vacation planning context based on the conversation content
        if destinations_discussed > 0:
            merged_prefs["destinations_discussed"] = True
        if budget_discussed > 0:
            merged_prefs["budget_mentioned"] = True
        
        conversation_data = {
            "id": db_conversation.id,
            "messages": messages,
            "created_at": db_conversation.created_at.isoformat(),
            "updated_at": db_conversation.updated_at.isoformat(),
            "user_preferences": merged_prefs,
            "vacation_session": vacation_session
        }
        
        # Cache with vacation-specific key pattern
        redis_key = f"vacation_chat:{db_conversation.id}"
        self.redis_client.setex(  # 
            redis_key,
            self.ttl,
            json.dumps(conversation_data)
        )
        
        # Log some interesting details about what we loaded
        logger.info(f"Pulled vacation chat history from the database - conversation {db_conversation.id} has {len(messages)} messages")
        if destinations_discussed > 0:
            logger.info(f"  - {destinations_discussed} messages mentioned destinations")
        if budget_discussed > 0:
            logger.info(f"  - {budget_discussed} messages discussed budget")
        if questions_count > 0:
            logger.info(f"  - {questions_count} questions were asked")
        if exclamations_count > 0:
            logger.info(f"  - {exclamations_count} exclamations detected")
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get a vacation planning conversation from Redis cache."""
        # Try vacation-specific key pattern first, then fallback to legacy patterns
        redis_key = f"vacation_chat:{conversation_id}"
        data = self.redis_client.get(redis_key)  # 
        
        if not data:
            # Fallback to other key patterns for backward compatibility
            fallback_keys = [
                f"vacation_session:{conversation_id}",
                f"conversation:{conversation_id}"
            ]
            
            for key in fallback_keys:
                data = self.redis_client.get(key)  # 
                if data:
                    logger.info(f"Found the vacation chat using the backup key pattern: {key} for conversation {conversation_id}")
                    break
            
        if not data:
            logger.warning(f"Couldn't find that vacation chat in the cache - conversation ID: {conversation_id}")
            return None
        
        try:
            conversation_data = json.loads(data)
            messages = []
            
            # Convert stored messages back to Message objects for vacation planning context
            for msg_data in conversation_data["messages"]:
                # Skip messages without content or with invalid content
                if not msg_data.get("content") or len(msg_data.get("content", "").strip()) == 0:
                    continue
                    
                role_str = msg_data.get("role", "user")
                if role_str == "user":
                    role = MessageRole.USER
                elif role_str == "assistant":
                    role = MessageRole.ASSISTANT
                else:
                    role = MessageRole.SYSTEM
                
                # Preserve and enhance metadata
                metadata = msg_data.get("metadata") or {}
                if msg_data.get("loaded_from_db"):
                    metadata["loaded_from_db"] = True
                if msg_data.get("message_index") is not None:
                    metadata["message_index"] = msg_data["message_index"]
                if msg_data.get("content_length") is not None:
                    metadata["content_length"] = msg_data["content_length"]
                
                message = Message(
                    role=role,
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]) if "timestamp" in msg_data else datetime.now(timezone.utc),
                    metadata=metadata
                )
                messages.append(message)
            
            return ConversationHistory(
                conversation_id=conversation_id,
                messages=messages,
                created_at=datetime.fromisoformat(conversation_data["created_at"]),
                updated_at=datetime.fromisoformat(conversation_data["updated_at"]),
                user_preferences=conversation_data.get("user_preferences")
            )
        except Exception as e:
            logger.error(f"Something went wrong while reading the vacation chat data for {conversation_id}: {str(e)}")
            return None
    
    def add_message(self, conversation_id: str, message: Message) -> bool:
        """Add a vacation planning message to a conversation."""
        # First, let's see if this conversation actually exists
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Tried to add a message to a vacation chat that doesn't exist - conversation ID: {conversation_id}")
            return False
        
        # Clean up the message content - people sometimes send weird stuff
        if not message.content or not message.content.strip():
            logger.warning(f"Got an empty message for conversation {conversation_id} - skipping it")
            return False
        
        # Vacation planning messages shouldn't be novels - trim if too long
        # Most people don't write 10k character messages about travel
        if len(message.content) > 10000:
            logger.warning(f"Message was way too long for conversation {conversation_id} - had to cut it down")
            message.content = message.content[:10000] + "..."
        
        # Check for weird patterns that might be spam or bots
        if len(message.content) > 100:
            # Look for suspicious repeated characters (like "aaaaaaaaaa")
            repeated_chars = any(message.content.count(char) > len(message.content) * 0.3 for char in set(message.content))
            if repeated_chars:
                logger.warning(f"Message has suspicious repeated characters for conversation {conversation_id}")
                # Don't block it, but log it for monitoring
        
        current_time = datetime.now(timezone.utc)
        
        # Build the message data with some vacation-specific metadata
        message_dict = {
            "role": message.role.value,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
            "added_at": current_time.isoformat(),
            "content_length": len(message.content),
            "message_index": None,  # Will be set below
            "has_question": "?" in message.content,
            "has_exclamation": "!" in message.content,
            "mentions_destination": any(dest in message.content.lower() for dest in ["paris", "london", "tokyo", "beach", "mountains", "city"]),
            "mentions_budget": any(word in message.content.lower() for word in ["$", "dollar", "budget", "cheap", "expensive", "cost"])
        }
        
        # Try to find the conversation data - we've used different key formats over time
        redis_key = f"vacation_chat:{conversation_id}"
        data = self.redis_client.get(redis_key)  # 
        
        if not data:
            # If not found, try the old key patterns we used before
            fallback_keys = [
                f"vacation_session:{conversation_id}",
                f"conversation:{conversation_id}",
                f"chat:{conversation_id}"  # Some really old sessions
            ]
            
            for key in fallback_keys:
                data = self.redis_client.get(key)  # 
                if data:
                    redis_key = key
                    logger.info(f"Found conversation using old key format: {key}")
                    break
            
        if not data:
            logger.error(f"Couldn't find the conversation data in Redis for {conversation_id} - something's missing")
            return False
            
        conv_dict = json.loads(data)
        
        # Figure out where this message should go in the conversation
        message_dict["message_index"] = len(conv_dict["messages"])
        conv_dict["messages"].append(message_dict)
        
        # Keep the conversation from getting too long - most vacation planning chats don't need 100+ messages
        if len(conv_dict["messages"]) > self.max_length:
            # Keep the most recent messages but make sure we don't lose important context
            recent_messages = conv_dict["messages"][-self.max_length:]
            conv_dict["messages"] = recent_messages
            
            # Fix the message indexes since we trimmed the conversation
            for i, msg in enumerate(conv_dict["messages"]):
                msg["message_index"] = i
        
        conv_dict["updated_at"] = current_time.isoformat()
        
        # Update the vacation session info to track how the planning is going
        if "vacation_session" not in conv_dict:
            conv_dict["vacation_session"] = {
                "what_we_are_doing": "planning_a_vacation",
                "when_started": current_time.isoformat(),
                "planning_mood": "just_started",
                "what_we_know": {
                    "destinations": [],
                    "budget_range": "not_sure_yet",
                    "travel_style": "still_figuring_out",
                    "group_size": 1,
                    "has_pets": False,
                    "weather_preference": "not_decided"
                },
                "conversation_flow": {
                    "questions_asked": 0,
                    "excitement_level": 0,
                    "destinations_mentioned": 0,
                    "budget_talked_about": 0,
                    "planning_stage": "initial_chat"
                }
            }
        
        conv_dict["vacation_session"]["how_many_messages"] = len(conv_dict["messages"])
        conv_dict["vacation_session"]["last_heard_from"] = current_time.isoformat()
        
        # Track some vacation-specific analytics
        if message_dict.get("mentions_destination"):
            conv_dict["vacation_session"]["conversation_flow"]["destinations_mentioned"] = conv_dict["vacation_session"]["conversation_flow"].get("destinations_mentioned", 0) + 1
        if message_dict.get("mentions_budget"):
            conv_dict["vacation_session"]["conversation_flow"]["budget_talked_about"] = conv_dict["vacation_session"]["conversation_flow"].get("budget_talked_about", 0) + 1
        
        # Update questions and excitement tracking
        if message_dict.get("has_question"):
            conv_dict["vacation_session"]["conversation_flow"]["questions_asked"] = conv_dict["vacation_session"]["conversation_flow"].get("questions_asked", 0) + 1
        if message_dict.get("has_exclamation"):
            conv_dict["vacation_session"]["conversation_flow"]["excitement_level"] = conv_dict["vacation_session"]["conversation_flow"].get("excitement_level", 0) + 1
        
        # Figure out how long this vacation planning session has been going
        if conv_dict["vacation_session"].get("when_started"):
            start_time = datetime.fromisoformat(conv_dict["vacation_session"]["when_started"])
            duration = current_time - start_time
            
            # Make the duration human-readable - people don't think in seconds
            if duration.total_seconds() < 60:
                duration_str = f"{int(duration.total_seconds())} seconds"
            elif duration.total_seconds() < 3600:
                minutes = int(duration.total_seconds() // 60)
                duration_str = f"{minutes} minutes"
            else:
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                duration_str = f"{hours} hours, {minutes} minutes"
                
            conv_dict["vacation_session"]["how_long_this_takes"] = duration_str
            conv_dict["vacation_session"]["duration_seconds"] = int(duration.total_seconds())
            
            # Track if this is a long planning session (some people really plan their vacations!)
            if duration.total_seconds() > 1800:  # 30 minutes
                conv_dict["vacation_session"]["long_planning_session"] = True
        
        # Save the updated conversation back to Redis
        self.redis_client.setex(  # 
            redis_key,
            self.ttl,
            json.dumps(conv_dict)
        )
        
        logger.info(f"Added a {message.role.value} message to the vacation chat {conversation_id} - now has {len(conv_dict['messages'])} messages total")
        return True
    
    def update_user_preferences(self, conversation_id: str, preferences: Dict) -> bool:
        """Update user vacation preferences in a conversation."""
        # Look for the conversation data using our various key formats
        redis_key = f"vacation_chat:{conversation_id}"
        data = self.redis_client.get(redis_key)  # 
        
        if not data:
            # Try the older key formats we used before - we've changed our naming a few times
            fallback_keys = [
                f"vacation_session:{conversation_id}",
                f"conversation:{conversation_id}",
                f"chat:{conversation_id}",  # Really old format from early development
                f"vacation:{conversation_id}"  # Another variation we tried
            ]
            
            for key in fallback_keys:
                data = self.redis_client.get(key)  # 
                if data:
                    redis_key = key
                    logger.info(f"Found the vacation chat using an old key format: {key}")
                    break
            
        if not data:
            logger.warning(f"Tried to update preferences for a vacation chat that doesn't exist: {conversation_id}")
            return False
        
        # Load up the conversation data so we can update their travel preferences
        conv_dict = json.loads(data)
        current_time = datetime.now(timezone.utc)
        
        # Check and update the user's vacation preferences
        # These are the kinds of things people actually think about when planning trips
        # We want to capture what makes their vacation unique and special
        valid_preferences = {
            "budget_range": ["low", "medium", "high", "luxury", "not_set", "budget", "affordable", "expensive", "cheap", "splurge", "whatever_it_takes"],
            "travel_style": ["adventure", "relaxation", "culture", "family", "romantic", "business", "not_set", "backpacking", "luxury", "road_trip", "cruise", "all_inclusive", "digital_nomad", "foodie_tour"],
            "group_size": range(1, 21),  # 1-20 people (covers most travel groups - from solo to big family trips)
            "preferred_destinations": [],
            "accessibility_needs": [True, False],
            "has_pets": [True, False],
            "preferred_weather": ["warm", "cold", "tropical", "mountain", "beach", "city", "not_set", "sunny", "snowy", "mild", "extreme"],
            "travel_season": ["spring", "summer", "fall", "winter", "not_set", "peak", "off_peak", "shoulder_season"],
            "accommodation_type": ["hotel", "resort", "airbnb", "hostel", "camping", "not_set", "boutique_hotel", "luxury_resort", "treehouse", "houseboat"],
            "transportation": ["plane", "car", "train", "bus", "cruise", "not_set", "motorcycle", "bicycle", "walking", "private_transfer"]
        }
        
        updated_count = 0
        for key, value in preferences.items():
            if value is not None and value != "":
                # Make sure the preference value makes sense for vacation planning
                # People have all sorts of unique travel preferences - we want to capture that
                if key in valid_preferences:
                    if isinstance(valid_preferences[key], list):
                        if value in valid_preferences[key]:
                            conv_dict["user_preferences"][key] = value
                            updated_count += 1
                            logger.debug(f"Updated {key} to {value} for vacation planning")
                    elif isinstance(valid_preferences[key], range):
                        if isinstance(value, int) and value in valid_preferences[key]:
                            conv_dict["user_preferences"][key] = value
                            updated_count += 1
                            logger.debug(f"Updated {key} to {value} for vacation planning")
                    elif isinstance(valid_preferences[key], list) and key == "preferred_destinations":
                        # Handle destination list - people often have multiple places they want to visit
                        # Some people have bucket lists, others just want to explore
                        if isinstance(value, list):
                            conv_dict["user_preferences"][key] = value
                            updated_count += 1
                            logger.debug(f"Updated destinations list with {len(value)} places")
                else:
                    # Allow custom preferences - some people have unique travel needs
                    # Maybe they want to visit every coffee shop in Paris, or only stay in treehouses
                    conv_dict["user_preferences"][key] = value
                    updated_count += 1
                    logger.debug(f"Added custom preference {key}: {value}")
                
        conv_dict["updated_at"] = current_time.isoformat()
        
        # Update the vacation session info to track preference changes
        # People often change their minds as they learn more about their options
        if "vacation_session" not in conv_dict:
            conv_dict["vacation_session"] = {
                "what_we_are_doing": "planning_a_vacation",
                "when_started": current_time.isoformat(),
                "planning_mood": "just_started",
                "what_we_know": {
                    "destinations": [],
                    "budget_range": "not_sure_yet",
                    "travel_style": "still_figuring_out",
                    "group_size": 1,
                    "has_pets": False,
                    "weather_preference": "not_decided"
                },
                "conversation_flow": {
                    "questions_asked": 0,
                    "excitement_level": 0,
                    "destinations_mentioned": 0,
                    "budget_talked_about": 0,
                    "planning_stage": "initial_chat"
                }
            }
        
        conv_dict["vacation_session"]["last_heard_from"] = current_time.isoformat()
        conv_dict["vacation_session"]["preferences_updated"] = True
        conv_dict["vacation_session"]["preferences_updated_at"] = current_time.isoformat()
        
        # Track how many times preferences have been updated (some people change their minds a lot!)
        # This helps us understand how indecisive or decisive they are about their travel plans
        conv_dict["vacation_session"]["preference_update_count"] = conv_dict["vacation_session"].get("preference_update_count", 0) + 1
        
        # Save the updated preferences back to Redis so we remember them
        # This way we don't lose track of what they want for their perfect vacation
        self.redis_client.setex(  # 
            redis_key,
            self.ttl,
            json.dumps(conv_dict)
        )
        
        # Log what we learned about their travel preferences
        if updated_count > 0:
            logger.info(f"Updated {updated_count} vacation preferences for chat {conversation_id} - user's travel plans are getting more specific")
            if "budget_range" in preferences:
                logger.info(f"  - They're thinking about {preferences['budget_range']} budget")
            if "travel_style" in preferences:
                logger.info(f"  - They want a {preferences['travel_style']} kind of trip")
            if "group_size" in preferences:
                logger.info(f"  - Traveling with {preferences['group_size']} people")
        else:
            logger.info(f"No vacation preferences were updated for chat {conversation_id} - maybe they're still figuring things out")
            
        return True
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a vacation planning conversation from Redis cache."""
        # Try all possible key patterns to ensure complete cleanup
        # We've used different key formats over time, so check them all
        possible_keys = [
            f"vacation_chat:{conversation_id}",
            f"vacation_session:{conversation_id}",
            f"conversation:{conversation_id}",
            f"chat:{conversation_id}",  # Some old sessions might use this
            f"vacation:{conversation_id}"  # Another possible format
        ]
        
        total_deleted = 0
        deleted_keys = []
        
        for key in possible_keys:
            result = self.redis_client.delete(key)  # 
            if result > 0:
                total_deleted += result
                deleted_keys.append(key)
        
        if total_deleted > 0:
            logger.info(f"Cleaned up the vacation chat {conversation_id} from the cache - removed keys: {', '.join(deleted_keys)}")
        else:
            logger.warning(f"Nothing to clean up - couldn't find any vacation chat with ID: {conversation_id}")
        
        return total_deleted > 0