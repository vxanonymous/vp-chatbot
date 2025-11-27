from typing import List, Dict, Optional, Any
import logging
import re
import json
from app.domains.vacation.config_loader import vacation_config_loader

logger = logging.getLogger(__name__)


class VacationIntelligenceService:
    # Helps understand what users want for their vacation by reading between the lines.
    # are in planning their trip, and gives smart suggestions based on what we learn.
    
    def __init__(self, openai_service=None):
        logger.info("Started up the vacation intelligence service")
        self.stage_keywords = self._init_stage_keywords()
        self.openai_service = openai_service
        
    def _default_stage_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        return {
            "exploring": {
                "positive": [
                    "thinking about", "considering", "wondering", "ideas", "suggestions",
                    "inspire", "options", "possibilities", "what about", "how about",
                    "somewhere", "anywhere", "dream", "always wanted", "bucket list"
                ],
                "questions": [
                    "where should", "where can", "what destinations", "any recommendations",
                    "suggest some places", "what do you think"
                ]
            },
            "comparing": {
                "positive": [
                    "vs", "versus", "or", "between", "compare", "comparison",
                    "which is better", "difference between", "pros and cons",
                    "advantages", "disadvantages", "rather", "instead of"
                ],
                "questions": [
                    "which one", "what's better", "should i choose", "help me decide"
                ]
            },
            "planning": {
                "positive": [
                    "itinerary", "schedule", "plan", "days in", "nights in",
                    "what to do", "activities", "must see", "must do", "route",
                    "transportation", "getting around", "where to stay", "neighborhoods",
                    "july", "august", "september", "october", "november", "december",
                    "january", "february", "march", "april", "may", "june",
                    "days", "weeks", "months", "duration", "length", "time",
                    "budget", "cost", "price", "money", "dollars", "euros",
                    "specific", "detailed", "exact", "precise", "definite"
                ],
                "questions": [
                    "how many days", "what should i do", "where to stay", "how to get",
                    "how much will it cost", "what's the budget", "when should i go"
                ]
            },
            "finalizing": {
                "positive": [
                    "book", "booking", "reserve", "reservation", "when to book",
                    "best time to book", "finalize", "decided", "going to",
                    "will be traveling", "confirmed", "tickets", "visa"
                ],
                "questions": [
                    "how to book", "where to book", "when should i book", "what documents"
                ]
            }
        }
    
    def _init_stage_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        # Set up words that help us figure out where users are in planning their trip.
        default_keywords = self._default_stage_keywords()
        try:
            config = vacation_config_loader.load_keywords()
            stage_keywords = config.get("stage_keywords")
            if isinstance(stage_keywords, dict) and stage_keywords:
                return stage_keywords
        except Exception as exc:
            logger.warning("Falling back to default stage keywords: %s", exc)
        return default_keywords
    
    async def analyze_preferences(
        self, 
        messages: List[Dict], 
        current_preferences: Optional[Dict]
    ) -> Dict:
        # Look at what the user has been saying to understand what they want for their vacation.
        insights = {
            "detected_interests": [],
            "budget_indicators": [],
            "timeline_flexibility": None,
            "travel_experience_level": "unknown",
            "decision_stage": "exploring",
            "stage_confidence": 0.0,
            "stage_progression": [],
            "concerns": [],
            "excitement_factors": [],
            "mentioned_destinations": [],
            "decision_readiness": 0.0
        }
        
        # Look at all user messages to understand what they want
        user_messages = [m for m in messages if m["role"] == "user"]
        full_text = " ".join([m["content"].lower() for m in user_messages])
        
        # Figure out where they are in planning their trip
        stage_scores = self._calculate_stage_scores(user_messages, current_preferences)
        insights["decision_stage"] = stage_scores["stage"]
        insights["stage_confidence"] = stage_scores["confidence"]
        insights["stage_progression"] = stage_scores["progression"]
        
        # Find out what kind of vacation they're interested in
        insights["detected_interests"] = self._detect_interests(full_text)
        
        # Capture explicit budget amounts before classification
        budget_amount_info = self._extract_budget_amount(full_text)
        if budget_amount_info:
            insights["budget_amount"] = budget_amount_info["formatted"]
        
        # See what destinations they've mentioned
        # Try AI extraction first, fallback to known list
        ai_destinations = await self._extract_destinations_with_ai(user_messages) if self.openai_service else None
        
        # Post-process AI-extracted destinations through alias mapping and filter verbs
        common_verbs = {
            "visit", "go", "travel", "trip", "vacation", "holiday", "journey",
            "explore", "see", "tour", "tourist", "tourists", "traveling", "travelling",
            "plan", "planning", "want", "wants", "would", "like", "love", "dream",
            "thinking", "considering", "interested", "looking", "hoping", "wishing"
        }
        
        if ai_destinations:
            processed_destinations = []
            for dest in ai_destinations:
                dest_lower = dest.lower().strip()
                # Skip common verbs
                if dest_lower in common_verbs:
                    logger.debug(f"Filtered out verb '{dest}' from AI-extracted destinations")
                    continue
                
                processed_destinations.append(dest)
            
            insights["mentioned_destinations"] = processed_destinations if processed_destinations else self._extract_destinations(user_messages)
        else:
            insights["mentioned_destinations"] = self._extract_destinations(user_messages)
        
        # See how ready they are to make decisions
        insights["decision_readiness"] = self._calculate_decision_readiness(
            current_preferences, 
            len(user_messages),
            insights["mentioned_destinations"]
        )
        
        # Look for budget clues
        insights["budget_indicators"] = self._detect_budget_level(full_text, budget_amount_info)
        
        # Find any concerns they might have
        insights["concerns"] = self._detect_concerns(full_text)
        
        # See how experienced they are with travel
        insights["travel_experience_level"] = self._detect_experience_level(full_text)
        
        return insights
    
    def _calculate_stage_scores(
        self, 
        user_messages: List[Dict], 
        preferences: Optional[Dict]
    ) -> Dict:
        # Figure out where the user is in planning their trip.
        # Debug logging removed for production
        
        stage_scores = {
            "exploring": 0.0,
            "comparing": 0.0,
            "planning": 0.0,
            "finalizing": 0.0
        }
        
        # Pay more attention to recent messages
        recent_weight = 0.7
        older_weight = 0.3
        
        recent_messages = user_messages[-3:] if len(user_messages) > 3 else user_messages
        older_messages = user_messages[:-3] if len(user_messages) > 3 else []
        
        # Look at recent messages
        for i, msg in enumerate(recent_messages):
            text = msg["content"].lower()
            for stage, keywords in self.stage_keywords.items():
                score = 0
                # Check positive keywords
                for keyword in keywords["positive"]:
                    if keyword in text:
                        score += 1
                # Check questions
                for question in keywords["questions"]:
                    if question in text:
                        score += 1.5  # Questions are stronger indicators
                
                stage_scores[stage] += score * recent_weight
        
        # Look at older messages
        for i, msg in enumerate(older_messages):
            text = msg["content"].lower()
            for stage, keywords in self.stage_keywords.items():
                score = sum(1 for keyword in keywords["positive"] if keyword in text)
                stage_scores[stage] += score * older_weight
        
        # Adjust scores based on what we already know about them
        if preferences:
            if preferences.get("destinations"):
                stage_scores["exploring"] *= 0.5  # Less likely to be exploring
                stage_scores["comparing"] *= 1.2
                stage_scores["planning"] *= 1.3
            
            if preferences.get("travel_dates") and preferences.get("budget_range"):
                stage_scores["planning"] *= 1.5
                stage_scores["finalizing"] *= 1.2
        
        # Look for planning clues in the most recent message
        explicit_stage_override = None
        if user_messages:
            latest_message = user_messages[-1]["content"]
            latest_message_lower = latest_message.lower()
            
            # Check for specific planning indicators
            has_planning = any(word in latest_message_lower for word in ["july", "august", "september", "october", "november", "december", 
                                                       "january", "february", "march", "april", "may", "june"])
            has_duration = any(word in latest_message_lower for word in ["days", "weeks", "months", "duration", "length"])
            has_budget = any(word in latest_message_lower for word in ["budget", "cost", "price", "money", "dollars", "euros"])
            
            # Check if ANY message in the conversation mentions multiple destinations for comparison
            all_messages_text = " ".join([msg["content"].lower() for msg in user_messages])
            city_test_set = {"paris", "tokyo", "new york", "london", "rome", "barcelona", "amsterdam", "berlin", "prague", "vienna", "budapest", "copenhagen", "stockholm", "oslo", "helsinki", "reykjavik", "dublin", "edinburgh", "glasgow", "manchester", "birmingham", "liverpool", "leeds", "sheffield", "bristol", "cardiff", "belfast", "cork", "galway", "limerick", "waterford", "kilkenny", "drogheda", "wicklow", "wexford", "carlow", "laois", "offaly", "westmeath", "longford", "louth", "meath", "cavan", "monaghan", "fermanagh", "tyrone", "derry", "antrim", "down", "armagh"}
            
            # Check for comparison keywords in any message
            has_comparison_keywords = any(word in all_messages_text for word in ["between", "vs", "versus", "or", "compare", "comparison", "which", "rather", "instead"])
            
            # Count cities mentioned across all messages
            found_cities = set()
            for city in city_test_set:
                if city in all_messages_text:
                    found_cities.add(city)
            
            preference_words = [
                'want', 'prefer', 'looking for', 'interested in', 'options', 'ideas', 'experience', 'adventure', 'culture', 'food', 'local', 'not luxury', 'not expensive', 'not costly', 'not pricey', 'affordable', 'cheap', 'budget-friendly', 'save', 'explore', 'try', 'see', 'do', 'enjoy', 'fun', 'relax', 'discover', 'learn', 'meet', 'connect', 'enrich', 'grow', 'enjoyable', 'memorable', 'unique', 'special', 'different', 'variety', 'diverse', 'broad', 'wide', 'range', 'choice', 'select', 'pick', 'choose', 'decide', 'consider', 'think', 'plan', 'dream', 'wish', 'hope', 'aspire', 'goal', 'aim', 'objective', 'target', 'purpose', 'reason', 'motivation', 'drive', 'passion', 'interest', 'curious', 'curiosity']
            # Priority 1: If multiple destinations and comparison keywords, force comparing
            if len(found_cities) >= 2 and has_comparison_keywords:
                explicit_stage_override = "comparing"
            # Priority 2: If budget is mentioned but not strong planning/duration, and the latest message is about preferences/interests, set exploring as primary
            elif has_budget and not (has_planning or has_duration):
                if any(word in latest_message_lower for word in preference_words):
                    explicit_stage_override = "exploring"
            # Priority 3: If any message contains 'tight budget', 'limited budget', 'small budget', and latest message is about preferences/interests, set exploring
            elif any(phrase in all_messages_text for phrase in ["tight budget", "limited budget", "small budget", "low budget", "restricted budget"]) and any(word in latest_message_lower for word in preference_words):
                explicit_stage_override = "exploring"
        
        # Normalize scores and find the highest
        total_score = sum(stage_scores.values()) or 1
        normalized_scores = {k: v/total_score for k, v in stage_scores.items()}
        
        # Determine stage and confidence
        if explicit_stage_override:
            primary_stage = explicit_stage_override
            confidence = 1.0
        else:
            sorted_stages = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
            primary_stage = sorted_stages[0][0]
            confidence = sorted_stages[0][1]
        
        # Track progression
        progression = [stage for stage, score in normalized_scores.items() if score > 0.1]
        
        result = {
            "stage": primary_stage,
            "confidence": confidence,
            "progression": progression,
            "scores": normalized_scores
        }
        
        return result
        
        return result
    
    def _detect_interests(self, text: str) -> List[str]:
        # See what kind of vacation activities they're interested in.
        interest_patterns = {
            "adventure": {
                "keywords": ["hiking", "climbing", "diving", "extreme", "adventure", 
                           "trek", "explore", "outdoor", "adrenaline", "sports"],
                "weight": 1.0
            },
            "relaxation": {
                "keywords": ["relax", "spa", "beach", "resort", "peaceful", "quiet",
                           "unwind", "chill", "lazy", "slow pace", "rest"],
                "weight": 1.0
            },
            "cultural": {
                "keywords": ["culture", "history", "museum", "local", "authentic", 
                           "heritage", "tradition", "art", "architecture", "temple"],
                "weight": 1.0
            },
            "foodie": {
                "keywords": ["food", "restaurant", "cuisine", "eat", "culinary", 
                           "taste", "dining", "chef", "wine", "local dishes"],
                "weight": 1.0
            },
            "nature": {
                "keywords": ["nature", "wildlife", "national park", "mountains", 
                           "forest", "scenic", "landscape", "natural", "animals"],
                "weight": 1.0
            },
            "urban": {
                "keywords": ["city", "urban", "metropolitan", "shopping", "nightlife",
                           "modern", "cosmopolitan", "downtown", "skyline"],
                "weight": 0.8
            },
            "photography": {
                "keywords": ["photo", "photography", "instagram", "scenic", "views",
                           "sunrise", "sunset", "picturesque", "beautiful"],
                "weight": 0.7
            }
        }
        
        detected_interests = []
        interest_scores = {}
        
        for interest, data in interest_patterns.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword in text:
                    score += data["weight"]
            
            if score > 0:
                interest_scores[interest] = score
        
        # Add 'budget' if they mention money stuff
        budget_keywords = ["budget", "cheap", "affordable", "economical", "save", "cost", "price", "money"]
        if any(word in text for word in budget_keywords):
            detected_interests.append("budget")
        
        # Sort by score and return the top interests
        sorted_interests = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)
        detected_interests += [interest for interest, score in sorted_interests if score >= 1.0]
        return detected_interests
    
    def _extract_destinations(self, messages: List[Dict]) -> List[str]:
        # Find places they've mentioned in their messages.
        destinations = []
        
        # Try to match against known destinations list from config
        try:
            known_destinations = vacation_config_loader.load_destinations()
            if known_destinations:
                for msg in messages:
                    if msg.get("role") and msg["role"] != "user":
                        continue
                    text_lower = msg.get("content", "").lower()
                    original_text = msg.get("content", "")
                    
                    # Check each known destination
                    for known_dest in known_destinations:
                        if known_dest.lower() in text_lower:
                            start_idx = text_lower.find(known_dest.lower())
                            if start_idx != -1:
                                end_idx = start_idx + len(known_dest)
                                matched_text = original_text[start_idx:end_idx]
                                if matched_text and matched_text not in destinations:
                                    destinations.append(matched_text)
                                    logger.debug(f"Found destination '{matched_text}' from known list")
        except Exception as e:
            logger.warning(f"Error loading known destinations: {e}")
        
        if destinations:
            logger.info(f"Extracted {len(destinations)} destinations from known list/aliases: {destinations}")
        
        if not destinations:
            logger.debug("Attempting regex/geocode patterns to find additional destinations")
            destination_patterns = [
                r"(?:to|visit|go to|travel to|trip to|vacation in|holiday in|plan.*?trip to|want.*?go to)\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|!|\?|$|\s)",
                r"(?:^|[\s])([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*?)(?:\s+is\s+|\.|\?|!|$)",
                r"(?:considering|thinking about|interested in|planning)\s+([A-Z][a-zA-Z\s]+?)(?:\.|,|!|\?|$)"
            ]
            
            for msg in messages:
                if msg.get("role") and msg["role"] != "user":
                    continue
                text = msg.get("content", "")
                # Look for lists of cities
                city_list_matches = re.findall(r"([A-Z][a-zA-Z]+(?:,\s*[A-Z][a-zA-Z]+)+(?:,?\s*and\s*[A-Z][a-zA-Z]+)?)", text)
                for match in city_list_matches:
                    # Split by comma and 'and'
                    parts = re.split(r",\s*|\s+and\s+", match)
                    for part in parts:
                        city = part.strip()
                        if city and city not in destinations:
                            destinations.append(city)
                # Try the other patterns
                for pattern in destination_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        dest = match.strip() if isinstance(match, str) else match[0].strip() if match else ""
                        if (dest and len(dest) > 2 and 
                            dest not in ["I", "We", "The", "This", "That", "My", "Our", "Plan", "Want", "Trip"] and
                            not dest.startswith("I ") and
                            not any(word in dest.lower() for word in ["plan", "want", "trip", "vacation", "holiday"])):
                            if dest not in destinations:
                                destinations.append(dest)
                # Last resort: look for any capitalized words (probably city/country names)
                fallback_cities = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", text)
                for city in fallback_cities:
                    if (city not in destinations and 
                        city not in ["I", "We", "The", "This", "That", "My", "Our", "Plan", "Want", "Trip", "Vacation", "Holiday"] and
                        len(city) > 2):
                        destinations.append(city)
        
        # Filter out common verbs and non-destination words
        common_verbs = {
            "visit", "go", "travel", "trip", "vacation", "holiday", "journey",
            "explore", "see", "tour", "tourist", "tourists", "traveling", "travelling",
            "plan", "planning", "want", "wants", "would", "like", "love", "dream",
            "thinking", "considering", "interested", "looking", "hoping", "wishing"
        }
        
        # Get rid of duplicates and filter out verbs, but keep the order
        seen = set()
        unique_destinations = []
        for dest in destinations:
            dest_lower = dest.lower().strip()
            # Skip if it's a common verb or already seen
            if dest_lower in common_verbs or dest_lower in seen:
                continue
            seen.add(dest_lower)
            unique_destinations.append(dest)
        
        if unique_destinations:
            logger.info(f"Extracted {len(unique_destinations)} destinations via regex: {unique_destinations}")
        else:
            logger.warning(f"No destinations extracted from messages: {[m.get('content', '')[:50] for m in messages]}")
        
        return unique_destinations
    
    async def _extract_destinations_with_ai(self, messages: List[Dict]) -> Optional[List[str]]:
        # Use AI to extract destinations from user messages
        if not self.openai_service or not self.openai_service.client:
            logger.debug("OpenAI service not available, skipping AI extraction")
            return None
        
        try:
            # Combine user messages into a single text
            user_text = " ".join([msg.get("content", "") for msg in messages if msg.get("role") == "user"])
            if not user_text.strip():
                return None
            
            # Create a simple prompt for destination extraction
            extraction_prompt = f"""Extract all travel destinations (countries, cities, regions, landmarks) mentioned in the following user message. 
Important: 
- When extracting city names, also include the country name if you know it (e.g., "Danang" should include "Vietnam", "Paris" should include "France").
- For ambiguous region names (like "Victoria" which could be Australia, Canada, or other places), use context clues from the conversation to determine the most likely location, or include both the region and country if context is unclear.
- Return ONLY a JSON array of destination names, nothing else. Do NOT include verbs like "visit", "go", "travel", "trip", etc.

User message: "{user_text}"

Return format: ["destination1", "destination2", "country_name", ...]
If no destinations found, return: []

Examples:
- User: "I want to visit Danang" → ["Danang", "Vietnam"]
- User: "Paris sounds nice" → ["Paris", "France"]
- User: "Tokyo and Kyoto" → ["Tokyo", "Kyoto", "Japan"]
- User: "I'm going to Italy" → ["Italy"]
- User: "Thinking about Victoria" → ["Victoria, Australia"] (if context suggests Australia) or ["Victoria"] (if context is unclear)
- "I want to visit Bangladesh" → ["Bangladesh"]
- "Planning a trip to Paris and Tokyo" → ["Paris", "France", "Tokyo", "Japan"]
- "Thinking about Vietnam or Thailand" → ["Vietnam", "Thailand"]
- "I want to visit Taj Mahal" → ["Taj Mahal", "Agra", "India"]
- "No specific place yet" → []
"""
            
            # Make a quick API call for extraction
            response = self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "You are a travel destination extraction assistant. Extract destinations from user messages and return only a JSON array."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON from the response
            # Handle cases where response might have markdown code blocks
            if content.startswith("```"):
                # Extract JSON from code block
                lines = content.split("\n")
                json_start = next((i for i, line in enumerate(lines) if "[" in line), None)
                if json_start is not None:
                    json_end = next((i for i, line in enumerate(lines[json_start:], json_start) if "]" in line), None)
                    if json_end is not None:
                        content = "\n".join(lines[json_start:json_end+1])
            
            # Remove any markdown formatting
            content = content.replace("```json", "").replace("```", "").strip()
            
            destinations = json.loads(content)
            
            if isinstance(destinations, list) and destinations:
                logger.info(f"AI extracted destinations: {destinations}")
                return destinations
            else:
                logger.debug("AI found no destinations")
                return None
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI extraction response as JSON: {e}, content: {content[:100] if 'content' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.warning(f"AI destination extraction failed: {e}, falling back to regex")
            return None
    
    def _calculate_decision_readiness(
        self, 
        preferences: Optional[Dict],
        message_count: int,
        mentioned_destinations: List[str]
    ) -> float:
        # See how ready they are to make decisions about their trip.
        readiness_score = 0.0
        
        if not preferences:
            return 0.1
        
        # Things that show they're ready to decide
        factors = {
            "has_destination": (bool(preferences.get("destinations") or mentioned_destinations), 0.25),
            "has_dates": (bool(preferences.get("travel_dates")), 0.20),
            "has_budget": (bool(preferences.get("budget_range")), 0.15),
            "has_duration": (bool(preferences.get("trip_duration")), 0.10),
            "has_group_size": (bool(preferences.get("group_size")), 0.10),
            "has_interests": (bool(preferences.get("travel_style")), 0.10),
            "sufficient_messages": (message_count >= 4, 0.10)
        }
        
        for factor, (condition, weight) in factors.items():
            if condition:
                readiness_score += weight
        
        return min(readiness_score, 1.0)
    
    def _categorize_budget_amount(self, amount: int) -> str:
        if amount <= 1500:
            return "budget"
        if amount <= 5000:
            return "moderate"
        return "luxury"
    
    def _extract_budget_amount(self, text: str) -> Optional[Dict[str, Any]]:
        currency_patterns = [
            r'(?P<symbol>[$€£])\s*(?P<amount>[\d,]+)',
            r'(?P<currency>usd|eur|gbp|cad|aud|sgd|inr)\s*(?P<amount>[\d,]+)',
            r'(?P<amount>[\d,]+)\s*(?P<currency>usd|eur|gbp|cad|aud|sgd|inr|dollars|euros|pounds|bucks)'
        ]
        symbol_map = {
            "$": "$",
            "€": "€",
            "£": "£",
            "usd": "$",
            "dollars": "$",
            "bucks": "$",
            "eur": "€",
            "euros": "€",
            "gbp": "£",
            "pounds": "£",
            "cad": "$",
            "aud": "$",
            "sgd": "$",
            "inr": "₹"
        }
        for pattern in currency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group("amount")
                digits = re.sub(r"[^\d]", "", amount_str)
                if not digits:
                    continue
                amount_value = int(digits)
                raw_currency = match.groupdict().get("symbol") or match.groupdict().get("currency")
                currency_key = raw_currency.lower() if isinstance(raw_currency, str) else raw_currency
                symbol = symbol_map.get(currency_key, "$")
                formatted = f"{symbol}{amount_value:,.0f}"
                return {
                    "amount": amount_value,
                    "symbol": symbol,
                    "formatted": formatted
                }
        return None
    
    def _detect_budget_level(self, text: str, amount_info: Optional[Dict[str, Any]] = None) -> List[str]:
        # See what kind of budget they're thinking about.
        budget_indicators = []
        
        budget_patterns = {
            "ultra_budget": {
                "keywords": ["backpack", "hostel", "cheapest", "shoestring", "broke"],
                "phrases": ["as cheap as possible", "very tight budget", "no money"]
            },
            "budget": {
                "keywords": ["budget", "cheap", "affordable", "economical", "save"],
                "phrases": ["on a budget", "save money", "cost conscious", "good value"]
            },
            "moderate": {
                "keywords": ["moderate", "comfortable", "reasonable", "balanced"],
                "phrases": ["mid-range", "not too expensive", "decent hotels", "some nice meals"]
            },
            "luxury": {
                "keywords": ["luxury", "premium", "exclusive", "splurge", "best"],
                "phrases": ["five star", "no budget", "money no object", "treat ourselves"]
            }
        }
        
        if amount_info is None:
            amount_info = self._extract_budget_amount(text)
        
        if amount_info and amount_info.get("amount"):
            category = self._categorize_budget_amount(amount_info["amount"])
            if category:
                budget_indicators.append(category)
        
        for level, patterns in budget_patterns.items():
            # Check keywords
            if any(keyword in text for keyword in patterns["keywords"]):
                budget_indicators.append(level)
            # Check phrases
            if any(phrase in text for phrase in patterns["phrases"]):
                budget_indicators.append(level)
                break  # Phrases are more definitive
        
        # Don't count ultra_budget if they mention other budget levels too
        if len(budget_indicators) > 1 and "ultra_budget" in budget_indicators:
            budget_indicators = [b for b in budget_indicators if b != "ultra_budget"]
        
        unique_indicators: List[str] = []
        for indicator in budget_indicators:
            if indicator not in unique_indicators:
                unique_indicators.append(indicator)
        
        return unique_indicators
    
    def _detect_concerns(self, text: str) -> List[str]:
        # Find any worries or concerns they might have.
        concerns = []
        
        concern_patterns = {
            "safety": ["safe", "dangerous", "crime", "secure", "risk", "safety"],
            "health": ["health", "medical", "hospital", "vaccine", "illness", "doctor"],
            "weather": ["weather", "rain", "hot", "cold", "hurricane", "climate", "season"],
            "crowds": ["crowd", "busy", "tourist", "peaceful", "quiet", "packed", "overcrowded"],
            "language": ["language", "english", "speak", "communicate", "understand"],
            "cost": ["expensive", "cost", "price", "afford", "budget", "money"],
            "solo_travel": ["alone", "solo", "single", "by myself", "solo travel"],
            "accessibility": ["wheelchair", "accessible", "disability", "mobility"],
            "dietary": ["vegetarian", "vegan", "allergy", "dietary", "food restrictions"],
            "visa": ["visa", "passport", "documentation", "entry requirements"]
        }
        
        for concern_type, keywords in concern_patterns.items():
            if any(keyword in text for keyword in keywords):
                concerns.append(concern_type)
        
        return list(set(concerns))
    
    def _detect_experience_level(self, text: str) -> str:
        # See how experienced they are with travel.
        experience_indicators = {
            "beginner": [
                "first time", "never been", "new to travel", "nervous about",
                "worried about", "inexperienced", "first international"
            ],
            "intermediate": [
                "traveled before", "been to a few", "some experience",
                "comfortable with", "done this before"
            ],
            "experienced": [
                "traveled extensively", "been everywhere", "seasoned traveler",
                "always traveling", "travel frequently", "been to many"
            ]
        }
        
        for level, indicators in experience_indicators.items():
            if any(indicator in text for indicator in indicators):
                return level
        
        return "unknown"
    
    def generate_dynamic_suggestions(
        self,
        conversation_state: Dict,
        last_message: str
    ) -> List[str]:
        # Come up with helpful suggestions based on what the user is thinking about.
        suggestions = []
        stage = conversation_state.get("decision_stage", "exploring")
        confidence = conversation_state.get("stage_confidence", 0)
        interests = conversation_state.get("detected_interests", [])
        readiness = conversation_state.get("decision_readiness", 0)
        mentioned_destinations = conversation_state.get("mentioned_destinations", [])
        concerns = conversation_state.get("concerns", [])
        
        # See if they just mentioned a place
        last_lower = last_message.lower()
        just_mentioned_destination = any(dest.lower() in last_lower for dest in mentioned_destinations)
        
        # If they just mentioned a place, give them helpful follow-up questions
        if just_mentioned_destination and mentioned_destinations:
            dest = mentioned_destinations[0]
            suggestions = [
                f"Tell me more about {dest}",
                "When do you want to go?",
                "What's your budget like?",
                "What kind of activities do you enjoy?"
            ]
            return suggestions[:4]
        
        # If we're pretty sure about where they are, give them specific suggestions
        if confidence > 0.6:
            if stage == "exploring":
                if interests:
                    suggestions.append(f"Best places for {interests[0]}")
                    suggestions.append("Match my travel style")
                else:
                    suggestions.append("Help me find inspiration")
                    suggestions.append("What's popular right now")
                
                if not mentioned_destinations:
                    suggestions.append("I have a place in mind")
                    suggestions.append("Surprise me with ideas")
                else:
                    suggestions.append(f"Tell me about {mentioned_destinations[0]}")
                    suggestions.append("Compare with other places")
                    
            elif stage == "comparing":
                if mentioned_destinations and len(mentioned_destinations) >= 2:
                    suggestions.append(f"Compare {mentioned_destinations[0]} vs {mentioned_destinations[1]}")
                    suggestions.append("Which one is better for me?")
                suggestions.append("Compare costs")
                suggestions.append("Best time to visit")
                    
            elif stage == "planning":
                if mentioned_destinations:
                    dest = mentioned_destinations[0]
                    suggestions.append(f"Create {dest} itinerary")
                    suggestions.append(f"Where to stay in {dest}")
                    suggestions.append(f"Must-see in {dest}")
                else:
                    suggestions.append("Create an itinerary")
                    suggestions.append("Where to stay")
                    suggestions.append("Must-see attractions")
                suggestions.append("Getting around tips")
                    
            elif stage == "finalizing":
                suggestions.append("When should I book?")
                suggestions.append("What documents do I need?")
                suggestions.append("Travel insurance advice")
                suggestions.append("Final checklist")
        
        # If we're not sure where they are, help them figure it out
        else:
            if not mentioned_destinations:
                suggestions = [
                    "I need some ideas",
                    "Beach vacation ideas",
                    "Adventure travel ideas",
                    "City break ideas"
                ]
            elif readiness < 0.3:
                suggestions = [
                    f"Tell me about {mentioned_destinations[0]}" if mentioned_destinations else "I need inspiration",
                    "When should I travel?",
                    "What's my budget?",
                    "Who's coming with me?"
                ]
            elif readiness < 0.6:
                suggestions = [
                    "Help me plan activities",
                    "Where should I stay?",
                    "Compare with similar places",
                    "What's the weather like?"
                ]
            else:
                suggestions = [
                    "Review my travel plan",
                    "What am I forgetting?",
                    "Booking tips",
                    "Local customs to know"
                ]
        
        # Help with any worries they might have
        if concerns:
            if "safety" in concerns:
                suggestions.insert(0, "Is it safe to travel there?")
            elif "budget" in concerns:
                suggestions.insert(0, "How can I save money?")
            elif "weather" in concerns:
                suggestions.insert(0, "What's the weather like?")
        
        # If they asked a question, offer to help more
        if "?" in last_message:
            # They asked a question, so offer more help
            if "I need more information" not in suggestions:
                suggestions.append("I need more information")
        
        # Get rid of duplicates but keep the order
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)
        
        return unique_suggestions[:4]
    
    def get_smart_recommendations(
        self,
        preferences: Optional[Dict],
        insights: Dict,
        message_count: int
    ) -> List[Dict]:
        # Give them helpful recommendations based on what we know about them.
        recommendations = []
        
        stage = insights.get("decision_stage", "exploring")
        confidence = insights.get("stage_confidence", 0)
        interests = insights.get("detected_interests", [])
        concerns = insights.get("concerns", [])
        readiness = insights.get("decision_readiness", 0)
        mentioned_destinations = insights.get("mentioned_destinations", [])
        
        # Give them a friendly welcome if they're just starting
        if message_count <= 3:
            recommendations.append({
                "type": "welcome",
                "content": "👋 **Welcome to Vacation Planning!**\n\n" +
                          "I'm here to help you plan your perfect trip. " +
                          "Let's start by understanding what you're dreaming of for your vacation."
            })
        
        # Give them specific help based on where they are in planning
        if confidence > 0.6:
            if stage == "exploring" and interests:
                interest_text = interests[0]
                recommendations.append({
                    "type": "targeted_inspiration",
                    "content": f"🎯 **Perfect for {interest_text.title()} Lovers**\n\n" +
                              f"Since you're into {interest_text}, think about:\n" +
                              f"• **Tropical Paradise** - Beach resorts with {interest_text} activities\n" +
                              f"• **Mountain Escapes** - High-altitude {interest_text} experiences\n" +
                              f"• **Cultural Hubs** - Cities known for {interest_text}\n\n" +
                              f"What kind of setting sounds most appealing to you?"
                })
            
            elif stage == "comparing" and mentioned_destinations:
                destinations = mentioned_destinations[:2]
                recommendations.append({
                    "type": "comparison_framework",
                    "content": "📊 **Smart Comparison Framework**\n\n" +
                              "To help you decide, think about:\n" +
                              "• **Total Cost** (flights + accommodation + activities)\n" +
                              "• **Weather** during your travel period\n" +
                              "• **Activities** that match your interests\n" +
                              "• **Travel Time** and convenience\n" +
                              "• **Visa Requirements** and ease of entry\n\n" +
                              "Which factor matters most to you?"
                })
            
            elif stage == "planning":
                recommendations.append({
                    "type": "planning_structure",
                    "content": "📅 **Smart Planning Approach**\n\n" +
                              "Let's structure your trip:\n" +
                              "1. **Arrival & Settling** (Day 1)\n" +
                              "2. **Major Attractions** (Days 2-3)\n" +
                              "3. **Local Experiences** (Days 4-5)\n" +
                              "4. **Hidden Gems** (Day 6)\n" +
                              "5. **Departure Prep** (Last Day)\n\n" +
                              "How many days are you thinking of staying?"
                })
        
        # Give them specific help for places they mentioned
        if mentioned_destinations:
            dest = mentioned_destinations[0]
            recommendations.append({
                "type": "destination_focus",
                "content": f"🗺️ **{dest} Highlights**\n\n" +
                          f"I can help you discover the best of {dest}:\n" +
                          f"• **Must-See Attractions**\n" +
                          f"• **Local Cuisine & Dining**\n" +
                          f"• **Hidden Gems**\n" +
                          f"• **Best Neighborhoods**\n" +
                          f"• **Practical Tips**\n\n" +
                          f"What interests you most about {dest}?"
            })
        
        # Help with any worries they mentioned
        if concerns:
            primary_concern = concerns[0]
            concern_responses = {
                "safety": "🔒 **Safety First**: I'll focus on safe neighborhoods, reliable transportation, and current travel advisories.",
                "budget": "💰 **Budget-Conscious Planning**: Let's find great value options and money-saving tips.",
                "weather": "🌤️ **Weather Considerations**: I'll help you pick the best time and prepare for conditions.",
                "language": "🗣️ **Communication Tips**: I'll share key phrases and apps to help you communicate.",
                "health": "🏥 **Health Preparedness**: Let's cover vaccinations, insurance, and medical facilities."
            }
            
            if primary_concern in concern_responses:
                recommendations.append({
                    "type": "concern_addressed",
                    "content": concern_responses[primary_concern]
                })
        
        # If they're almost ready to decide, help them finish up
        if readiness > 0.7 and stage != "finalizing":
            missing_elements = []
            if not preferences or not preferences.get("destinations"):
                missing_elements.append("destination")
            if not preferences or not preferences.get("travel_dates"):
                missing_elements.append("travel dates")
            if not preferences or not preferences.get("budget_range"):
                missing_elements.append("budget")
            
            if missing_elements:
                recommendations.append({
                    "type": "readiness_prompt",
                    "content": f"✅ **Almost Ready!** Just need your {' and '.join(missing_elements)} to create a complete plan."
                })
        
        # Give them general help based on where they are
        if stage == "exploring":
            recommendations.append({
                "type": "exploration_guidance",
                "content": "🌟 **Let's Find Your Perfect Destination**\n\n" +
                          "I can help you discover:\n" +
                          "• **Beach Getaways** - Relaxation and water activities\n" +
                          "• **City Breaks** - Culture, food, and urban adventures\n" +
                          "• **Mountain Escapes** - Hiking and outdoor activities\n" +
                          "• **Cultural Journeys** - History, art, and local traditions\n\n" +
                          "What kind of experience are you dreaming of?"
            })
        elif stage == "planning":
            recommendations.append({
                "type": "planning_guidance",
                "content": "📋 **Let's Build Your Perfect Itinerary**\n\n" +
                          "I can help you plan:\n" +
                          "• **Daily Schedules** - Optimized for your interests\n" +
                          "• **Accommodation** - Best areas and options\n" +
                          "• **Transportation** - Getting around efficiently\n" +
                          "• **Local Tips** - Insider knowledge and advice\n\n" +
                          "What would you like to focus on first?"
            })
        
        # Ensure we provide helpful recommendations
        if not recommendations:
            recommendations.append({
                "type": "general_guidance",
                "content": "🎯 **Let's Plan Your Perfect Trip**\n\n" +
                          "I'm here to help you create an amazing vacation experience. " +
                          "Tell me about your travel dreams and I'll guide you every step of the way!"
            })
        
        return recommendations[:3]