# The following imports may trigger linter errors in some environments due to missing type stubs.
# They are required for runtime and are present in requirements.txt.
import asyncio
import logging
import re
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument, DESCENDING

from app.models.conversation_db import ConversationInDB, ConversationSummary, ConversationUpdate
from app.models.chat import Message
from app.models.object_id import PyObjectId

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Handles vacation conversation management - creating new chats, adding messages,
    tracking user preferences and all that good stuff.
    
    I built this to handle the vacation planning chat system. It's got caching
    to avoid hitting the DB too much and some decent error handling.
    """
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        # Simple cache to avoid unnecessary DB hits
        self._cache = {}
        # 30 seconds seems reasonable for cache TTL
        self._cache_ttl = 30
        
    async def _ensure_indexes(self):
        """Make sure we have the right indexes for decent performance."""
        try:
            # These indexes should help with the common queries
            index_tasks = [
                self.collection.create_index([("user_id", 1), ("is_active", 1), ("updated_at", -1)]),
                self.collection.create_index([("_id", 1), ("user_id", 1)]),
                self.collection.create_index("updated_at"),
            ]
            await asyncio.gather(*index_tasks, return_exceptions=True)
        except Exception as e:
            logger.warning(f"Had some trouble setting up the database indexes: {e}")
    
    async def create_conversation(self, user_id: str, title: str = "New Vacation Planning Chat") -> ConversationInDB:
        """Creates a fresh conversation for vacation planning."""
        try:
            now = datetime.now(timezone.utc)
            
            # Set up some reasonable defaults for vacation planning
            vacation_prefs = {
                "budget_range": "not_set",
                "travel_style": "not_set", 
                "group_size": 1,
                "preferred_destinations": [],
                "accessibility_needs": False,
                "has_pets": False,
                "preferred_weather": "not_set"
            }
            
            conversation_doc = {
                "user_id": user_id,
                "title": title,
                "messages": [],
                "vacation_preferences": vacation_prefs,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }
            
            # Save to database with timeout
            result = await asyncio.wait_for(
                self.collection.insert_one(conversation_doc),
                timeout=10.0
            )
            
            conv_id = result.inserted_id
            if isinstance(conv_id, ObjectId):
                conv_id = PyObjectId(conv_id)
            
            return ConversationInDB(
                id=conv_id,
                user_id=user_id,
                title=title,
                messages=[],
                vacation_preferences=vacation_prefs,
                is_active=True,
                created_at=now,
                updated_at=now
            )
        except asyncio.TimeoutError:
            logger.error("Database took too long to create the conversation")
            raise Exception("Having trouble creating your chat right now. Try again?")
        except Exception as e:
            logger.error(f"Something went wrong while creating the conversation: {e}")
            raise

    async def create_conversation_with_auto_title(self, user_id: str, initial_message: str, openai_service=None) -> ConversationInDB:
        """Creates conversation with a smart title based on what the user said."""
        
        # Step 1: Generate a basic title first (our fallback)
        basic_title = self._generate_simple_title(initial_message)
        
        # Step 2: Try to get a better title from AI if we can
        final_title = basic_title
        if openai_service:
            ai_title = await self._try_get_ai_title(openai_service, initial_message)
            if ai_title:
                final_title = ai_title
        
        # Step 3: Create a conversation with the chosen title
        try:
            return await self.create_conversation(user_id, final_title)
        except Exception as e:
            logger.error(f"Cannot create the conversation with the smart title: {e}")
            # Last resort - use the most basic title
            return await self.create_conversation(user_id, "Vacation Planning Chat")
    
    async def _try_get_ai_title(self, openai_service, initial_message: str) -> Optional[str]:
        """Attempts to get a title from AI, returns None if it fails."""
        try:
            ai_title = await openai_service.generate_conversation_title(initial_message)
            if ai_title and len(ai_title.strip()) > 5:
                logger.info(f"AI came up with a good title: {ai_title}")
                return ai_title
            else:
                logger.info("AI's title suggestion was too short, so we'll skip it")
                return None
        except Exception as e:
            logger.warning(f"AI couldn't generate a title this time: {e}")
            return None



    def _generate_simple_title(self, message: str) -> str:
        """Generates a decent title when AI isn't available."""
        
        clean_msg = self._clean_message_content(message)
        if not clean_msg.strip():
            clean_msg = "I'd like to plan a vacation"
        
        msg_lower = clean_msg.lower()
        
        # Check for space-related content (redirect to Earth travel)
        space_title = self._detect_space_content(msg_lower)
        if space_title:
            return space_title
        
        # Look for specific destinations
        dest_title = self._detect_destinations(msg_lower)
        if dest_title:
            return dest_title
        
        # Check vacation types
        type_title = self._detect_vacation_types(msg_lower)
        if type_title:
            return type_title
        
        return "Vacation Planning"
    
    def _clean_message_content(self, message: str) -> str:
        """Removes any sketchy content from messages."""
        # Patterns that might be injection attempts
        suspicious_patterns = [
            r"system\s*override\s*:.*?(?=\n|$)",
            r"ignore\s+previous\s+instructions.*?(?=\n|$)",
            r"you\s+are\s+now.*?(?=\n|$)",
            r"pretend\s+to\s+be.*?(?=\n|$)",
            r"act\s+as\s+if.*?(?=\n|$)",
            r"new\s+instructions.*?(?=\n|$)",
            r"forget\s+everything.*?(?=\n|$)",
            r'\b(system|assistant|user|role|instruction|prompt|command|directive|override)\s*:.*?(?=\n|$)'
        ]
        
        cleaned = message
        for pattern in suspicious_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned
    
    def _detect_space_content(self, msg_lower: str) -> Optional[str]:
        """Checks if someone's asking about space travel (redirect to Earth)."""
        space_keywords = [
            r"\bmoon\b", r"\bmars\b", r"\bjupiter\b", r"\bsaturn\b", r"\bvenus\b", r"\bmercury\b", 
            r"\bneptune\b", r"\buranus\b", r"\bpluto\b", r"\bgalaxy\b", r"\bgalaxies\b", r"\buniverse\b", 
            r"\bplanet\b", r"\bplanets\b", r"\basteroid\b", r"\basteroids\b", r"\bcomet\b", r"\bcomets\b",
            r"\bmilky\s+way\b", r"\bmilkyway\b", r"\bandromeda\b", r"\bnebula\b", r"\bnebulas\b", 
            r"\bconstellation\b", r"\bconstellations\b", r"\bblack\s+hole\b", r"\bblackhole\b", 
            r"\bwormhole\b", r"\bworm\s+hole\b", r"\bsupernova\b", r"\bsupernovas\b", r"\bsolar\s+system\b", 
            r"\bsolarsystem\b", r"\borbit\b", r"\borbital\b", r"\bcosmic\b", r"\bcosmos\b", r"\binterstellar\b",
            r"\bextraterrestrial\b", r"\balien\b", r"\baliens\b", r"\bufo\b", r"\bufos\b", r"\bspaceship\b", 
            r"\bspaceships\b", r"\brocket\b", r"\brockets\b", r"\bsatellite\b", r"\bsatellites\b", 
            r"\bspace\s+station\b", r"\bspacestation\b", r"\bspace\s+travel\b", r"\bspacetravel\b", 
            r"\bspace\s+tourism\b", r"\bspacetourism\b", r"\bspace\s+vacation\b", r"\bspacevacation\b"
        ]
        
        for keyword in space_keywords:
            if re.search(keyword, msg_lower, re.IGNORECASE):
                return "Earth Travel Planning"
        
        return None
    
    def _detect_destinations(self, msg_lower: str) -> Optional[str]:
        """Looks for specific destination mentions."""
        destinations = [
            r"\bmongolia\b", r"\bparis\b", r"\bbali\b", r"\bjapan\b", r"\bthailand\b", r"\bvietnam\b", 
            r"\bitaly\b", r"\bspain\b", r"\bgreece\b", r"\bturkey\b", r"\bmorocco\b", r"\begypt\b", 
            r"\bindia\b", r"\bchina\b", r"\baustralia\b", r"\bnew\s+zealand\b", r"\bcanada\b", 
            r"\bmexico\b", r"\bbrazil\b", r"\bargentina\b", r"\bperu\b", r"\bchile\b"
        ]
        
        for dest_pattern in destinations:
            match = re.search(dest_pattern, msg_lower, re.IGNORECASE)
            if match:
                place = match.group(0).title()
                return f"{place} Trip Planning"
        
        return None
    
    def _detect_vacation_types(self, msg_lower: str) -> Optional[str]:
        """Detects what kind of vacation they're interested in."""
        vacation_types = [
            (r"\bbudget\b", "Budget Travel Planning"),
            (r"\bluxury\b", "Luxury Vacation Planning"),
            (r"\badventure\b", "Adventure Planning"),
            (r"\bbeach\b", "Beach Vacation Planning"),
            (r"\bculture\b|\bcultural\b", "Cultural Trip Planning")
        ]
        
        for pattern, title in vacation_types:
            if re.search(pattern, msg_lower, re.IGNORECASE):
                return title
        
        return None
    
    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[ConversationInDB]:
        """Gets a conversation by ID."""
        
        # Try to get it from the database
        conv_data = await self._get_conversation_from_db(conversation_id, user_id)
        if not conv_data:
            return None
        
        # Convert to the object format
        return self._convert_to_conversation_object(conv_data)
    
    async def _get_conversation_from_db(self, conversation_id: str, user_id: str) -> Optional[Dict]:
        """Actually fetches the data from MongoDB."""
        try:
            return await asyncio.wait_for(
                self.collection.find_one({
                    "_id": ObjectId(conversation_id),
                    "user_id": user_id
                }),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.error("Database took too long to find the conversation")
            return None
        except Exception as e:
            logger.error(f"Had trouble getting the conversation from the database: {e}")
            return None
    
    def _convert_to_conversation_object(self, conv_data: Dict) -> ConversationInDB:
        """Converts DB document to the ConversationInDB object."""
        now = datetime.now(timezone.utc)
        
        # Handle ObjectId conversion
        conv_id = conv_data["_id"]
        if isinstance(conv_id, ObjectId):
            conv_id = PyObjectId(conv_id)
        
        # Validate required fields
        if "user_id" not in conv_data:
            raise ValueError("Missing required field: user_id")
        if "title" not in conv_data:
            raise ValueError("Missing required field: title")
        
        # Build the object with defaults for missing fields
        return ConversationInDB(
            id=conv_id,
            user_id=conv_data["user_id"],
            title=conv_data["title"],
            messages=conv_data.get("messages", []),
            vacation_preferences=conv_data.get("vacation_preferences", {}),
            is_active=conv_data.get("is_active", True),
            created_at=conv_data.get("created_at", now),
            updated_at=conv_data.get("updated_at", now)
        )
    
    async def add_message(self, conversation_id: str, user_id: str, message: Message) -> Optional[ConversationInDB]:
        """Adds a message to the conversation."""
        try:
            # Push the message and update timestamp
            update_result = await asyncio.wait_for(
                self.collection.update_one(
                    {
                        "_id": ObjectId(conversation_id),
                        "user_id": user_id
                    },
                    {
                        "$push": {"messages": message.model_dump()},
                        "$set": {"updated_at": datetime.now(timezone.utc)}
                    }
                ),
                timeout=10.0
            )
            
            # Check if anything was actually updated
            if update_result.modified_count == 0:
                return None
            
            # Return the updated conversation
            return await self.get_conversation(conversation_id, user_id)
        except asyncio.TimeoutError:
            logger.error("Database took too long to save the message")
            return None
        except Exception as e:
            logger.error(f"Something went wrong while adding the message: {e}")
            return None
    
    async def update_conversation(self, conversation_id: str, user_id: str, update: ConversationUpdate) -> Optional[ConversationInDB]:
        """Updates conversation details like title."""
        try:
            # Figure out what to update
            update_fields = {}
            if update.title is not None:
                update_fields["title"] = update.title
            
            # Nothing to update? Just return current state
            if not update_fields:
                return await self.get_conversation(conversation_id, user_id)
            
            # Do the update
            result = await asyncio.wait_for(
                self.collection.update_one(
                    {
                        "_id": ObjectId(conversation_id),
                        "user_id": user_id
                    },
                    {
                        "$set": update_fields,
                        "$currentDate": {"updated_at": True}
                    }
                ),
                timeout=10.0
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_conversation(conversation_id, user_id)
        except asyncio.TimeoutError:
            logger.error("Database took too long to update the conversation")
            return None
        except Exception as e:
            logger.error(f"Something went wrong while updating the conversation: {e}")
            return None
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Soft deletes a conversation (sets is_active to False)."""
        try:
            # Soft delete by marking inactive
            result = await asyncio.wait_for(
                self.collection.update_one(
                    {"_id": ObjectId(conversation_id), "user_id": user_id},
                    {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
                ),
                timeout=10.0
            )
            
            return result.modified_count > 0
        except asyncio.TimeoutError:
            logger.error("Database took too long to delete the conversation")
            return False
        except Exception as e:
            logger.error(f"Something went wrong while deleting the conversation: {e}")
            return False
    
    async def list_conversations(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ConversationInDB]:
        """Lists user's conversations with pagination."""
        try:
            cursor = self.collection.find(
                {"user_id": user_id, "is_active": True}
            ).skip(skip).limit(limit).sort("updated_at", -1)
            
            conversations = []
            
            async for doc in cursor:
                now = datetime.now(timezone.utc)
                conv_id = doc["_id"]
                if isinstance(conv_id, ObjectId):
                    conv_id = PyObjectId(conv_id)
                
                conversations.append(ConversationInDB(
                    id=conv_id,
                    user_id=doc["user_id"],
                    title=doc["title"],
                    messages=doc.get("messages", []),
                    vacation_preferences=doc.get("vacation_preferences", {}),
                    is_active=doc.get("is_active", True),
                    created_at=doc.get("created_at", now),
                    updated_at=doc.get("updated_at", now)
                ))
            return conversations
        except Exception as e:
            logger.error(f"Had trouble getting the list of conversations: {e}")
            return []
    
    async def get_conversation_summary(self, conversation_id: str, user_id: str) -> Optional[ConversationSummary]:
        """Gets a summary view of a conversation."""
        try:
            full_conv = await self.get_conversation(conversation_id, user_id)
            if not full_conv:
                return None
            
            return ConversationSummary(
                id=str(full_conv.id),
                title=full_conv.title,
                created_at=full_conv.created_at,
                updated_at=full_conv.updated_at,
                message_count=len(full_conv.messages)
            )
        except Exception as e:
            logger.error(f"Couldn't get the conversation summary: {e}")
            return None
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50,
        skip: int = 0
    ) -> List[ConversationSummary]:
        """Gets user's conversation summaries with caching."""
        # Create cache key
        cache_key = f"user_convs_{user_id}_{limit}_{skip}"
        
        # Check cache first
        if cache_key in self._cache:
            cached_time, data = self._cache[cache_key]
            if (datetime.now(timezone.utc) - cached_time).seconds < self._cache_ttl:
                return data
        
        try:
            # Use aggregation for efficiency
            pipeline = [
                {"$match": {"user_id": user_id, "is_active": True}},
                {"$sort": {"updated_at": DESCENDING}},
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "id": {"$toString": "$_id"},
                        "title": 1,
                        "created_at": 1,
                        "updated_at": 1,
                        "message_count": {"$size": "$messages"}
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            conversations = []
            
            async for doc in cursor:
                now = datetime.now(timezone.utc)
                summary_data = {
                    "id": doc.get("id", doc.get("_id", "")),
                    "title": doc.get("title", "New Conversation"),
                    "created_at": doc.get("created_at", now),
                    "updated_at": doc.get("updated_at", now),
                    "message_count": doc.get("message_count", 0)
                }
                conversations.append(ConversationSummary(**summary_data))
            
            # Cache the results
            self._cache[cache_key] = (datetime.now(timezone.utc), conversations)
            
            logger.info(f"Found {len(conversations)} conversations for user {user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Had trouble getting the user's conversations: {e}")
            return []
    
    async def batch_get_conversations(
        self, 
        conversation_ids: List[str], 
        user_id: str
    ) -> Dict[str, ConversationInDB]:
        """Gets multiple conversations at once."""
        # Filter out invalid IDs
        valid_ids = [cid for cid in conversation_ids if self._is_valid_object_id(cid)]
        
        if not valid_ids:
            return {}
        
        try:
            cursor = self.collection.find({
                "_id": {"$in": [ObjectId(cid) for cid in valid_ids]},
                "user_id": user_id
            })
            
            results = {}
            async for doc in cursor:
                now = datetime.now(timezone.utc)
                conv_id = doc["_id"]
                if isinstance(conv_id, ObjectId):
                    conv_id = PyObjectId(conv_id)
                
                conversation = ConversationInDB(
                    id=conv_id,
                    user_id=doc["user_id"],
                    title=doc["title"],
                    messages=doc.get("messages", []),
                    vacation_preferences=doc.get("vacation_preferences", {}),
                    is_active=doc.get("is_active", True),
                    created_at=doc.get("created_at", now),
                    updated_at=doc.get("updated_at", now)
                )
                results[str(doc["_id"])] = conversation
            
            return results
            
        except Exception as e:
            logger.error(f"Something went wrong while getting multiple conversations: {e}")
            return {}
    
    async def update_preferences(
        self,
        conversation_id: str,
        user_id: str,
        preferences: Dict
    ) -> Optional[ConversationInDB]:
        """Updates vacation preferences for a conversation."""
        if not self._is_valid_object_id(conversation_id):
            return None
        
        try:
            updated_doc = await self.collection.find_one_and_update(
                {"_id": ObjectId(conversation_id), "user_id": user_id},
                {
                    "$set": {
                        "vacation_preferences": preferences,
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                return_document=ReturnDocument.AFTER
            )
            
            if updated_doc:
                self._clear_user_cache(user_id)
                conv_id = updated_doc["_id"]
                if isinstance(conv_id, ObjectId):
                    conv_id = PyObjectId(conv_id)
                
                return ConversationInDB(
                    id=conv_id,
                    user_id=updated_doc["user_id"],
                    title=updated_doc["title"],
                    messages=updated_doc.get("messages", []),
                    vacation_preferences=updated_doc.get("vacation_preferences", {}),
                    is_active=updated_doc.get("is_active", True),
                    created_at=updated_doc.get("created_at", datetime.now(timezone.utc)),
                    updated_at=updated_doc.get("updated_at", datetime.now(timezone.utc))
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Couldn't update the vacation preferences: {e}")
            return None
    
    async def cleanup_old_conversations(
        self, 
        days_old: int = 30
    ) -> Tuple[int, int]:
        """Cleans up old conversations in batches."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        try:
            # Count what we need to clean up
            total_count = await self.collection.count_documents({
                "updated_at": {"$lt": cutoff_date},
                "is_active": True
            })
            
            if total_count == 0:
                return 0, 0
            
            # Process in chunks
            batch_size = 100
            cleanup_tasks = []
            
            for offset in range(0, total_count, batch_size):
                task = self._process_cleanup_batch(cutoff_date, offset, batch_size)
                cleanup_tasks.append(task)
            
            # Run all the cleanup batches and see what happened
            batch_results = await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            # Count up how many conversations we successfully cleaned up
            successful_cleanups = sum(result for result in batch_results if isinstance(result, int))
            
            # Count how many batches had problems
            failed_batches = sum(1 for result in batch_results if isinstance(result, Exception))
            
            return successful_cleanups, failed_batches
            
        except Exception as e:
            logger.error(f"Something went wrong during the cleanup process: {e}")
            return 0, 1
    
    async def _process_cleanup_batch(
        self, 
        cutoff_date: datetime, 
        offset: int, 
        batch_size: int
    ) -> int:
        """Processes one batch of cleanup."""
        try:
            result = await self.collection.update_many(
                {
                    "updated_at": {"$lt": cutoff_date},
                    "is_active": True
                },
                {"$set": {"is_active": False}},
                limit=batch_size
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Had trouble cleaning up this batch: {e}")
            return 0
    
    def _is_valid_object_id(self, id_string: str) -> bool:
        """Checks if a string is a valid ObjectId."""
        try:
            return ObjectId.is_valid(id_string)
        except Exception:
            return False
    
    def _clear_user_cache(self, user_id: str):
        """Clears cache entries for a specific user."""
        cache_keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"user_{user_id}")]
        for key in cache_keys_to_remove:
            del self._cache[key]
    
    async def analyze_conversation(self, conversation_id: str) -> Dict:
        """Analyzes a conversation and returns some insights."""
        try:
            # Get the conversation data
            conv = await self.get_conversation(conversation_id, "")
            if not conv:
                return {"error": "Conversation not found"}
            
            # Do some basic analysis
            analysis_data = {
                "message_count": len(conv.messages),
                "user_messages": len([m for m in conv.messages if m.get("role") == "user"]),
                "assistant_messages": len([m for m in conv.messages if m.get("role") == "assistant"]),
                "conversation_length": len(conv.messages),
                "has_preferences": bool(conv.vacation_preferences),
                "preferences_count": len(conv.vacation_preferences) if conv.vacation_preferences else 0
            }
            
            # Extract topics from user messages
            detected_topics = []
            for msg in conv.messages:
                if msg.get("role") == "user":
                    content = msg.get("content", "").lower()
                    # Check for various topic keywords
                    if any(keyword in content for keyword in ["destination", "place", "city", "country"]):
                        detected_topics.append("destinations")
                    if any(keyword in content for keyword in ["budget", "cost", "price", "expensive", "cheap"]):
                        detected_topics.append("budget")
                    if any(keyword in content for keyword in ["date", "time", "when", "month", "season"]):
                        detected_topics.append("timing")
                    if any(keyword in content for keyword in ["hotel", "accommodation", "stay", "room"]):
                        detected_topics.append("accommodation")
                    if any(keyword in content for keyword in ["food", "restaurant", "cuisine", "dining"]):
                        detected_topics.append("food")
            
            analysis_data["topics"] = list(set(detected_topics))
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Couldn't analyze the conversation: {e}")
            return {"error": "Failed to analyze conversation"}
    
    async def add_feedback(self, conversation_id: str, feedback: str, rating: int) -> bool:
        """Adds user feedback to a conversation."""
        try:
            result = await asyncio.wait_for(
                self.collection.update_one(
                    {"_id": ObjectId(conversation_id)},
                    {
                        "$push": {
                            "feedback": {
                                "feedback": feedback,
                                "rating": rating,
                                "timestamp": datetime.now(timezone.utc)
                            }
                        }
                    }
                ),
                timeout=10.0
            )
            
            return result.modified_count > 0
            
        except asyncio.TimeoutError:
            logger.error("Database took too long to save the feedback")
            return False
        except Exception as e:
            logger.error(f"Something went wrong while adding the feedback: {e}")
            return False