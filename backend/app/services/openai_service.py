import json
import logging
import re
from typing import List, Dict, Optional, Any
from app.config import get_settings

settings = get_settings()
from app.models.chat import Message, MessageRole

"""
OpenAI Service for Vacation Planning System

This service handles all interactions with OpenRouter's API (using OpenAI-compatible client),
providing intelligent conversation generation, context analysis, and travel planning assistance.
"""

logger = logging.getLogger(__name__)

# Mock OpenAI client for when API key is not available (for testing)
class MockOpenAI:
    def __init__(self, api_key=None, base_url=None):
        pass
    
    class chat:
        class completions:
            @staticmethod
            def create(**kwargs):
                class MockResponse:
                    class MockChoice:
                        class MockMessage:
                            content = 'I apologize, but I\'m currently unable to access my travel database. Please check your API configuration.'
                            function_call = None
                        
                        message = MockMessage()
                    
                    choices = [MockChoice()]
                
                return MockResponse()

# Import the real OpenAI client (used for OpenRouter compatibility)
try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessageParam
except ImportError:
    OpenAI = MockOpenAI
    ChatCompletionMessageParam = Dict[str, Any]  # 

class OpenAIService:
    
    def __init__(self):
        if settings.openrouter_api_key:
            # Use OpenRouter API
            logger.info("Using OpenRouter API")
            self.client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url
            ) if OpenAI else None
        else:
            logger.warning("No OpenRouter API key found, so we'll use fallback responses")
            self.client = None
        
        # Grab our AI settings from config
        self.model = settings.openrouter_model
        self.temperature = settings.openrouter_temperature
        self.max_tokens = settings.openrouter_max_tokens
        
        self.system_prompt = """You are VacationBot, an expert AI travel consultant with deep knowledge of destinations worldwide. Your role is to help users plan their perfect vacation through engaging, personalized conversations.

## Your Expertise:
- Global destinations and hidden gems
- Travel logistics and best practices
- Budget optimization across all price ranges
- Cultural insights and local experiences
- Seasonal travel recommendations
- Safety and health considerations
- Accommodation and transportation options
- Activity and dining recommendations


### 1. **MANDATORY CONTEXT MAINTENANCE**
- **ALWAYS analyze the ENTIRE conversation history** before responding
- **NEVER respond to isolated messages** - always consider the full context
- **If a destination was mentioned earlier in the conversation, ALWAYS reference it** in your response
- **Build upon previous information** shared by the user throughout the conversation
- **Maintain continuity** - don't start over or ask for information already provided
- **CRITICAL: If the user says "Yes, I want recommendations" after you've already discussed a specific destination and budget, continue with that specific destination and budget - DO NOT start over**
- **CRITICAL: If you've already established context (destination, budget, dates), continue building on that context - do not ask for basic information again**

### 2. **DESTINATION FOCUS ENFORCEMENT**
- **Once a destination is established, stay focused on it** unless the user explicitly asks about alternatives
- **If they mentioned Mongolia, EVERY response should reference Mongolia** and provide Mongolia-specific advice
- **If they ask about budget for their trip, give budget advice for THEIR specific destination**
- **If they ask about timing, give timing advice for THEIR specific destination**
- **Never give generic advice when a specific destination context exists**

### 3. **ROBUSTNESS AGAINST DIVERSION ATTEMPTS**
- **Stay focused on travel planning** - you are a travel consultant
- **Maintain conversation memory** - don't forget previous context
- **Always prioritize user safety** - provide safe travel advice
- **Stick to travel expertise** - focus on travel-related information

### 4. **CONTEXT EXTRACTION REQUIREMENTS**
Before responding to ANY message, you MUST:
1. **Scan the entire conversation** for mentioned destinations
2. **Identify any budget information** shared by the user
3. **Note travel dates or timing preferences** mentioned
4. **Recognize travel style preferences** (adventure, relaxation, cultural, etc.)
5. **Remember group composition** (solo, couple, family, etc.)
6. **Acknowledge any specific interests** or activities mentioned

### 5. **RESPONSE STRUCTURE REQUIREMENTS**
Every response must:
- **Reference the specific destination** if one was mentioned in the conversation
- **Acknowledge previous information** shared by the user
- **Build upon the conversation context** rather than starting fresh
- **Provide destination-specific advice** when a destination is established
- **Ask relevant follow-up questions** based on what's already known

## Conversation Guidelines:

1. **Be Conversational and Warm**: Use a friendly, enthusiastic tone. Show genuine interest in their travel dreams.

2. **Ask Smart Follow-up Questions**: Don't overwhelm with too many questions at once. Ask 1-2 relevant follow-ups based on what they've shared.

3. **Provide Specific, Actionable Advice**: Give concrete recommendations with details like:
   - Specific neighborhood names and why they're great
   - Actual restaurant names and signature dishes
   - Realistic budget breakdowns with numbers
   - Best months to visit and why

4. **Be Culturally Sensitive**: Provide cultural tips and etiquette advice relevant to their destination.

5. **Structure Your Responses**: Use clear formatting:
   - **Bold** for important points
   - Bullet points for lists
   - Short paragraphs for readability

## Information Gathering Flow:
1. Start by understanding their vision (destination ideas, travel style)
2. Clarify practical details (dates, budget, group composition)
3. Explore preferences (activities, pace, must-haves/must-avoids)
4. Provide tailored recommendations
5. Refine based on feedback

## Itinerary Requests:
- **If the user asks for an itinerary, always generate a detailed, day-by-day plan with activities, restaurants, and attractions for each day, using whatever information is available.**
- If some details are missing, make reasonable assumptions and clearly note them in the itinerary.
- If the user hasn't provided enough details, use your travel expertise to fill in the gaps and explain your choices.

- You MUST always provide a helpful, contextual response in the content field
- Even when extracting preferences via function calls, you must still provide a conversational response
- Never return empty content - always give a helpful reply that addresses their question or concern
- If you're extracting preferences, acknowledge what you've learned and provide relevant advice

- **NEVER start over or ask for basic information that was already provided**
- **If the user says "Yes, I want recommendations" after you've discussed a destination and budget, provide specific recommendations for that destination and budget**
- **If the user asks for recommendations, give them recommendations based on the context already established**
- **Do NOT ask "What's your dream destination?" if a destination was already mentioned in the conversation**
- **Always build upon the existing conversation context, never ignore it**

## Example Response Patterns:

When they mention a destination:
"Paris sounds wonderful! The City of Light has so much to offer. To help me craft the perfect Parisian experience for you, I'm curious - are you drawn more to the classic attractions like the Eiffel Tower and Louvre, or would you prefer discovering hidden neighborhood gems in areas like Le Marais or Belleville?"

When discussing budget for a specific destination:
"For your Mongolia trip with a $2000 budget, here's a realistic breakdown:
- Accommodation (ger stays): $20-40/night = $280-560
- Food: $15-25/day = $210-350  
- Activities (horseback riding, tours): $300-500
- Transport: $200-300

When they say "Yes, I want recommendations" after you've already established context:
"Perfect! Based on your Paris trip in August with a $4000 budget, here are my top recommendations:

**Accommodation Recommendations:**
- Le Marais area: Hotel Caron de Beaumarchais ($180-220/night) - charming boutique hotel
- Saint-Germain-des-Prés: Hotel d'Aubusson ($200-250/night) - elegant 17th-century mansion
- Montmartre: Hotel Particulier Montmartre ($160-200/night) - unique artistic atmosphere

**Must-See Attractions:**
- Eiffel Tower (book skip-the-line tickets in advance)
- Louvre Museum (Wednesday/Friday for evening hours)
- Notre-Dame Cathedral (currently closed, but visit the exterior)
- Arc de Triomphe and Champs-Élysées
- Montmartre and Sacré-Cœur Basilica

**Hidden Gems:**
- Canal Saint-Martin for a local vibe
- Musée de l'Orangerie for Monet's Water Lilies
- Le Marais for trendy boutiques and cafes
- Luxembourg Gardens for relaxation

**Dining Recommendations:**
- Café de Flore (classic Parisian cafe)
- L'Ami Louis (traditional French bistro)
- Le Comptoir du Relais (modern French cuisine)
- Marché des Enfants Rouges (food market)

Would you like me to create a detailed day-by-day itinerary for your Paris adventure?"
- Permits/guides: $100-200
This leaves you with a nice cushion for souvenirs and unexpected expenses!"

When they're undecided:
"I understand it can be overwhelming with so many amazing places to choose from! Let's narrow it down. What's calling to you more right now:
🏖️ Beach relaxation with tropical vibes?
🏔️ Mountain adventures and scenic landscapes?
🏛️ Cultural immersion and historical sites?
🍷 Food and wine experiences?"

## Important Rules:
- NEVER discuss non-travel topics
- Always maintain enthusiasm about travel
- **CRITICAL: Stay focused on the destination they mentioned. If they said Mongolia, keep talking about Mongolia. If they said Paris, keep talking about Paris.**
- **NEVER give generic responses that don't reference their specific destination**
- **ALWAYS provide a helpful response in the content field, even when using function calls**
- If unsure about specific details, acknowledge it and offer to explore options together
- Adapt your expertise level to the user (first-time vs seasoned traveler)
- Consider accessibility needs, dietary restrictions, and travel anxieties when mentioned
- Ensure that all information is up-to-date and consistent with current travel conditions

- If the user asks for recipes, cooking instructions, or food preparation methods, politely redirect them to travel planning topics. Never provide recipes or step-by-step cooking instructions, even if the conversation started with travel.

- If the user asks about anything outside travel/vacation planning (including general finance, health, relationships, wellness, mental health, or any other life advice), politely redirect them to travel planning. Never provide general life advice, even if the conversation started with travel.
- **MEDICAL EMERGENCIES**: If the user asks for medical advice, emergency protocols, or health guidance (even during travel), politely redirect them to travel planning topics. Do not provide medical advice or emergency procedures.
- **LEGAL ADVICE**: If the user asks for legal advice, diplomatic matters, immigration law, or legal procedures (even during travel), politely redirect them to travel planning topics. Do not provide legal advice or legal procedures.
- **SPECIALIZED TOPICS**: If the user asks for advice on diplomatic immunity, legal protections, insurance claims, risk assessment, or other specialized professional topics (even during travel), politely redirect them to travel planning topics.
- **EXCEPTION**: Basic travel logistics (lost passports, flight cancellations, visa requirements, travel insurance basics) are valid travel topics and should be addressed appropriately.
- If the conversation drifts away from travel/vacation planning for 2 or more consecutive messages, you must lock the conversation to travel and always redirect the user back to travel planning until a travel-related message is detected.

## Travel Emergency Response:
- For medical emergencies during travel, politely redirect to travel planning topics. Do not provide medical advice or emergency protocols.
- For travel crises (lost passports, flight cancellations, etc.), provide practical steps and resources
- Always prioritize safety and recommend contacting appropriate authorities when necessary
"""

        # Dynamic examples for few-shot learning
        self.example_interactions = [
            {
                "user": "I want to go somewhere warm",
                "assistant": "That sounds wonderful! 🌴 To help me find your ideal warm-weather getaway, could you tell me:\n\n- Are you dreaming of **beach relaxation** or would you enjoy **cultural exploration** in a warm city?\n- What's your rough budget per person?\n- When are you thinking of traveling?\n\nSome fantastic warm destinations include:\n• **Southeast Asia** (Thailand, Vietnam) - perfect weather, great value\n• **Dubai** - luxury and adventure, guaranteed sunshine\n• **New Zealand** - stunning landscapes and outdoor adventures\n• **Morocco** - warm days, cool nights, incredible culture"
            }
        ]

        # Drift prevention state
        self._drift_counter = 0
        self._drift_lock = False
        self._drift_lock_threshold = 2  # Number of consecutive non-travel messages to trigger lock
        self._last_drift_state = True  # True = travel, False = non-travel

    def _sanitize_user_input(self, text: str) -> str:
        # Sanitize user input - simplified to avoid conflicts with LLM-based intent classification.
        # Basic sanitization without conflicting patterns
        if not text or not text.strip():
            return "I'd like to plan a vacation"
        
        # Simple cleanup of excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text

    def generate_response(
        self, 
        messages: List[Message], 
        user_preferences: Optional[Dict] = None,
        conversation_metadata: Optional[Dict] = None
    ) -> Dict:
        try:
            # Check if we can actually talk to OpenAI
            if not self.client:
                logger.warning("OpenAI client isn't available, so we'll use a fallback response")
                return self._generate_smart_fallback_response(messages)

            # If the user went off-topic before, gently guide them back
            if self._drift_lock:
                logger.info("User went off-topic, redirecting them back to travel planning")
                redirect_response = self._generate_topic_redirect_response(messages[-1].content if messages else "")
                return {
                    "content": redirect_response,
                    "extracted_preferences": None,
                    "confidence_score": 0.8,
                    "topic_drift_detected": True
                }

            # Check if the user is staying on topic about travel
            if messages and len(messages) > 0:
                latest_user_message = None
                for msg in reversed(messages):
                    if msg.role == MessageRole.USER:
                        latest_user_message = msg.content
                        break
                if latest_user_message:
                    is_travel_related = self._is_travel_related(latest_user_message, messages)
                    if not is_travel_related:
                        logger.info(f"User seems to be going off-topic: {latest_user_message[:50]}...")
                        redirect_response = self._generate_topic_redirect_response(latest_user_message)
                        return {
                            "content": redirect_response,
                            "extracted_preferences": None,
                            "confidence_score": 0.8,
                            "topic_drift_detected": True
                        }
            
            # Put together all the context and messages for the AI
            api_messages = self._build_messages(messages, user_preferences, conversation_metadata)
            
            # Ask OpenAI/OpenRouter to generate a helpful response
            # OpenRouter models may not support function calling, so we conditionally include it
            create_kwargs = {
                "model": self.model,
                "messages": api_messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # OpenRouter models don't support function calling, so we skip it
            
            response = self.client.chat.completions.create(**create_kwargs)
            
            # Get the AI's response and see what it found
            assistant_message = response.choices[0].message  # 
            extracted_preferences = None
            
            # Check if the AI found any useful preferences in what the user said
            # (Only available when using OpenAI with function calling, not OpenRouter)
            if hasattr(assistant_message, 'function_call') and assistant_message.function_call:
                try:
                    extracted_preferences = json.loads(
                        assistant_message.function_call.arguments
                    )
                    logger.info(f"Found some useful preferences: {extracted_preferences}")
                except json.JSONDecodeError as e:
                    logger.error(f"Couldn't understand the AI's response format: {e}")
                    logger.error(f"Raw arguments: {assistant_message.function_call.arguments}")
            
            # Get the actual response content
            content = assistant_message.content
            if not content:
                logger.warning("AI didn't give us any content, so we'll create a helpful fallback")
                content = self._generate_contextual_fallback_response(messages, user_preferences)
            
            return {
                "content": content,
                "extracted_preferences": extracted_preferences,
                "confidence_score": self._calculate_response_confidence(content, messages)
            }
        except Exception as e:
            logger.error(f"Something went wrong with the OpenAI API: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Messages count: {len(messages) if messages else 0}")
            logger.error(f"First message content: {messages[0].content if messages else 'No messages'}")
            
            # Give the user a friendly message based on what went wrong
            if "rate limit" in str(e).lower():
                fallback_msg = "I'm experiencing high traffic right now. Please try again in a moment while I process your request."
            elif "timeout" in str(e).lower():
                fallback_msg = "The request is taking longer than expected. Let me try a different approach to help you plan your trip."
            elif "authentication" in str(e).lower() or "api key" in str(e).lower() or "invalid_api_key" in str(e).lower():
                fallback_msg = "I'm having trouble connecting to the AI service. Please check your API configuration and try again."
            else:
                fallback_msg = self._generate_contextual_fallback_response(messages, user_preferences)
            
            return {
                "content": fallback_msg,
                "extracted_preferences": None,
                "confidence_score": 0.0
            }

    async def generate_response_async(self, messages, user_preferences=None, conversation_metadata=None):
        # Generate response using OpenAI API (async version).
        try:
            # Convert messages to the format expected by the sync method
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    # Handle both string roles and MessageRole enum
                    role = msg.get('role', 'user')
                    if isinstance(role, str):
                        # Convert string role to MessageRole enum
                        from app.models.chat import MessageRole
                        try:
                            role = MessageRole(role)
                        except ValueError:
                            role = MessageRole.USER
                    
                    formatted_messages.append(Message(
                        role=role,
                        content=msg.get('content', '')
                    ))
                else:
                    formatted_messages.append(msg)
            
            logger.info(f"Prepared {len(formatted_messages)} messages for the AI to process")
            logger.info(f"First message: {formatted_messages[0].content[:100] if formatted_messages else 'No messages'}")
            
            # Use the sync method for now (can be made truly async later)
            return self.generate_response(formatted_messages, user_preferences, conversation_metadata)
        except Exception as e:
            logger.error(f"Something went wrong with the OpenAI API in the async method: {str(e)}")
            last_content = ""
            if messages and len(messages) > 0:
                last_msg = messages[-1]
                if isinstance(last_msg, dict):
                    last_content = last_msg.get('content', '')
                elif hasattr(last_msg, 'content'):
                    last_content = last_msg.content
            return {
                "content": self._generate_contextual_fallback_response(messages, user_preferences),
                "extracted_preferences": None,
                "confidence_score": 0.0
            }

    async def generate_conversation_title(self, initial_message: str) -> str:
        # Generate a short, descriptive title for a new conversation.
        try:
            if not self.client:
                return self._generate_simple_title(initial_message)
            
            # Sanitize the initial message to prevent prompt injection
            sanitized_message = self._sanitize_user_input(initial_message)
            
            # Create a focused prompt for title generation
            title_prompt = f"""Generate a very short (3-6 words) descriptive title for a vacation planning conversation that starts with: "{sanitized_message}"

CRITICAL RULES:
1. This is a vacation planning bot for REALISTIC Earth destinations only
2. If the user mentions ANY space-related terms (moon, mars, milky way, galaxy, universe, cosmos, nebula, black hole, wormhole, solar system, etc.), you MUST return exactly: "Earth Travel Planning"
3. Do NOT be creative with space-related requests - always return "Earth Travel Planning"
4. For realistic Earth destinations, create appropriate titles
5. IMPORTANT: The word "space" alone is NOT space-related. Only flag it if it's clearly about outer space (like "space travel", "space station", "space vacation")
6. Common travel phrases with "space" should be treated normally: "spacious room", "need space to think", "space for family"

Examples:
- "I want to go to Paris" → "Paris Trip Planning"
- "Plan a trip to the Milky Way" → "Earth Travel Planning"
- "Visit Mars" → "Earth Travel Planning"
- "Go to Japan" → "Japan Trip Planning"
- "I need a spacious hotel room" → "Hotel Accommodation Planning"
- "I need space to think about my trip" → "Vacation Planning"
- "Space vacation" → "Earth Travel Planning"
- "Looking for space for my family" → "Family Travel Planning"

Return only the title, nothing else."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": title_prompt}],
                temperature=0.3,
                max_tokens=20
            )
            
            title = response.choices[0].message.content
            if title:
                title = title.strip()
                # Clean up the title
                title = title.replace('"', '').replace("'", "")
                
                # Additional safety check: if AI still generates space-themed titles, replace them
                title_lower = title.lower()
                # More precise space terms that are unlikely to appear in legitimate travel contexts
                space_terms = ["galactic", "cosmic", "cosmos", "nebula", "wormhole", "black hole", "solar system", "interstellar", "extraterrestrial", "alien", "ufo", "spaceship", "rocket", "satellite", "orbit", "constellation", "supernova", "andromeda", "mars", "jupiter", "saturn", "venus", "mercury", "neptune", "uranus", "pluto"]
                for term in space_terms:
                    if term in title_lower:
                        title = "Earth Travel Planning"
                        break
                
                if len(title) > 50:  # Fallback if too long
                    title = self._generate_simple_title(initial_message)
            else:
                title = self._generate_simple_title(initial_message)
            
            return title
            
        except Exception as e:
            logger.error(f"Couldn't generate a title for the conversation: {e}")
            return self._generate_simple_title(initial_message)

    def _generate_simple_title(self, message: str) -> str:
        # Generate a simple title when AI is not available.
        # Sanitize the message first
        sanitized_message = self._sanitize_user_input(message)
        message_lower = sanitized_message.lower()
        
        # Check for unrealistic destinations first - comprehensive space-related terms
        # Use word boundaries to avoid false positives (e.g., "spacious" hotel)
        unrealistic_destinations = [
            r"\bmoon\b", r"\bmars\b", r"\bjupiter\b", r"\bsaturn\b", r"\bvenus\b", r"\bmercury\b", r"\bneptune\b", r"\buranus\b", r"\bpluto\b",
            r"\bgalaxy\b", r"\bgalaxies\b", r"\buniverse\b", r"\bplanet\b", r"\bplanets\b", r"\basteroid\b", r"\basteroids\b", r"\bcomet\b", r"\bcomets\b",
            r"\bmilky\s+way\b", r"\bmilkyway\b", r"\bandromeda\b", r"\bnebula\b", r"\bnebulas\b", r"\bconstellation\b", r"\bconstellations\b",
            r"\bblack\s+hole\b", r"\bblackhole\b", r"\bwormhole\b", r"\bworm\s+hole\b", r"\bsupernova\b", r"\bsupernovas\b",
            r"\bsolar\s+system\b", r"\bsolarsystem\b", r"\borbit\b", r"\borbital\b", r"\bcosmic\b", r"\bcosmos\b", r"\binterstellar\b",
            r"\bextraterrestrial\b", r"\balien\b", r"\baliens\b", r"\bufo\b", r"\bufos\b", r"\bspaceship\b", r"\bspaceships\b",
            r"\brocket\b", r"\brockets\b", r"\bsatellite\b", r"\bsatellites\b", r"\bspace\s+station\b", r"\bspacestation\b",
            r"\bspace\s+travel\b", r"\bspacetravel\b", r"\bspace\s+tourism\b", r"\bspacetourism\b", r"\bspace\s+vacation\b", r"\bspacevacation\b"
        ]
        import re
        for dest in unrealistic_destinations:
            if re.search(dest, message_lower, re.IGNORECASE):
                return "Earth Travel Planning"
        
        # Extract destination keywords with word boundaries
        destinations = [
            r"\bmongolia\b", r"\bparis\b", r"\bbali\b", r"\bjapan\b", r"\bthailand\b", r"\bvietnam\b", 
            r"\bitaly\b", r"\bspain\b", r"\bgreece\b", r"\bturkey\b", r"\bmorocco\b", r"\begypt\b", 
            r"\bindia\b", r"\bchina\b", r"\baustralia\b", r"\bnew\s+zealand\b", r"\bcanada\b", 
            r"\bmexico\b", r"\bbrazil\b", r"\bargentina\b", r"\bperu\b", r"\bchile\b"
        ]
        
        for dest in destinations:
            if re.search(dest, message_lower, re.IGNORECASE):
                # Extract the actual destination name for title
                dest_name = re.search(dest, message_lower, re.IGNORECASE).group(0)
                return f"{dest_name.title()} Trip Planning"
        
        # Check for travel types with word boundaries
        if re.search(r"\bbudget\b", message_lower, re.IGNORECASE):
            return "Budget Travel Planning"
        elif re.search(r"\bluxury\b", message_lower, re.IGNORECASE):
            return "Luxury Vacation Planning"
        elif re.search(r"\badventure\b", message_lower, re.IGNORECASE):
            return "Adventure Trip Planning"
        elif re.search(r"\bbeach\b", message_lower, re.IGNORECASE):
            return "Beach Vacation Planning"
        elif re.search(r"\bculture\b|\bcultural\b", message_lower, re.IGNORECASE):
            return "Cultural Trip Planning"
        else:
            return "Vacation Planning"

    def _build_messages(
        self, 
        messages: List[Message], 
        user_preferences: Optional[Dict],
        conversation_metadata: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        # Put together all the context and messages we want to send to the AI.
        api_messages = [{"role": "system", "content": self.system_prompt}]
        
        # Figure out what we know about this conversation so far
        conversation_context = self._extract_conversation_context(messages)
        
        # Add what we know about the conversation so far
        if conversation_context:
            api_messages.append({
                "role": "system",
                "content": f"CONVERSATION CONTEXT SUMMARY:\n{conversation_context}\n\nCRITICAL: Use this context to maintain conversation continuity. Do NOT ask for information already provided in the conversation history."
            })
        
        # Add what we know about the user's preferences
        if user_preferences and any(user_preferences.values()):
            context = self._build_preference_context(user_preferences)
            api_messages.append({
                "role": "system", 
                "content": f"Current user preferences and context:\n{context}"
            })
        
        # Add any extra conversation info we have
        if conversation_metadata:
            api_messages.append({
                "role": "system",
                "content": f"Conversation metadata: {json.dumps(conversation_metadata)}"
            })
        
        # Add some example conversations to help the AI understand how to respond
        if len(messages) <= 2:  # Early in conversation
            for example in self.example_interactions[:1]:
                api_messages.extend([
                    {"role": "user", "content": example["user"]},
                    {"role": "assistant", "content": example["assistant"]}
                ])
        
        # Add the actual conversation messages (cleaned up for safety)
        for msg in messages:
            # Clean up user messages to prevent any funny business
            content = msg.content
            if msg.role.value == "user":
                content = self._sanitize_user_input(content)
            
            api_messages.append({
                "role": msg.role.value,
                "content": content
            })
        
        # Log what we're sending to the AI
        logger.info(f"Built {len(api_messages)} messages for the API")
        logger.info(f"Conversation context: {conversation_context[:200] if conversation_context else 'None'}...")
        logger.info(f"Last user message: {messages[-1].content if messages else 'None'}")
        
        return api_messages

    def _extract_conversation_context(self, messages: List[Message]) -> str:
        # Remember what we've been talking about in this conversation.
        if not messages:
            return ""
        
        # Just grab what the user said
        user_messages = [msg.content.lower() for msg in messages if msg.role.value == "user"]
        if not user_messages:
            return ""
        
        # Combine their messages to see what they want
        full_conversation_text = " ".join(user_messages)
        
        context_parts = []
        
        # What places did they mention?
        destinations = self._extract_destinations(full_conversation_text)
        if destinations:
            context_parts.append(f"Destinations mentioned: {', '.join(destinations)}")
        
        # Any budget talk?
        budget_info = self._extract_budget_info(full_conversation_text)
        if budget_info:
            context_parts.append(f"Budget information: {budget_info}")
        
        # When do they want to go?
        timing_info = self._extract_timing_info(full_conversation_text)
        if timing_info:
            context_parts.append(f"Timing information: {timing_info}")
        
        # What kind of trip are they looking for?
        travel_styles = self._extract_travel_styles(full_conversation_text)
        if travel_styles:
            context_parts.append(f"Travel style preferences: {', '.join(travel_styles)}")
        
        # Who's going with them?
        group_info = self._extract_group_info(full_conversation_text)
        if group_info:
            context_parts.append(f"Group composition: {group_info}")
        
        # What activities interest them?
        interests = self._extract_interests(full_conversation_text)
        if interests:
            context_parts.append(f"Specific interests: {', '.join(interests)}")
        
        # If we've been chatting for a while, add some context
        if len(messages) > 2:
            context_parts.append(f"Conversation length: {len(messages)} messages")
            # Show the last few messages to keep track
            recent_messages = messages[-6:]
            recent_context = []
            for msg in recent_messages:
                role = "User" if msg.role.value == "user" else "Assistant"
                content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                recent_context.append(f"{role}: {content_preview}")
            
            if recent_context:
                context_parts.append(f"Recent conversation flow:\n" + "\n".join(recent_context))
        
        return "\n".join(context_parts)

    def _extract_destinations(self, text: str) -> List[str]:
        # Look for places the user mentioned in their message.
        # Duplicate of the list in conversation_memory.py
        destinations = [
            "paris", "nice", "lyon", "marseille", "bordeaux", "toulouse", "cannes", 
            "versailles", "madrid", "barcelona", "seville", "valencia", "granada", 
            "bilbao", "malaga", "palma de mallorca", "rome", "milan", "florence", 
            "venice", "naples", "palermo", "catania", "amalfi coast", "london", 
            "edinburgh", "manchester", "bath", "oxford", "york", "cambridge", 
            "liverpool", "berlin", "munich", "frankfurt", "cologne", "hamburg", 
            "dresden", "dusseldorf", "amsterdam", "rotterdam", "utrecht", "hague", 
            "leiden", "vienna", "salzburg", "innsbruck", "graz", "prague", "brno", 
            "cesky krumlov", "budapest", "szeged", "debrecen", "athens", 
            "santorini", "mykonos", "thessaloniki", "crete", "rhodes", "corfu", 
            "istanbul", "cappadocia", "antalya", "izmir", "ankara", "pamukkale", 
            "moscow", "saint petersburg", "kazan", "yekaterinburg", "novosibirsk", 
            "new york", "los angeles", "chicago", "miami", "san francisco", "dallas", 
            "orlando", "washington dc", "toronto", "montreal", "vancouver", "calgary", 
            "ottawa", "quebec city", "mexico city", "cancun", "guadalajara", 
            "puerto vallarta", "merida", "san miguel de allende", "rio de janeiro", 
            "sao paulo", "salvador", "brasilia", "recife", "porto alegre", 
            "buenos aires", "cordoba", "mendoza", "bariloche", "rosario", "lima", 
            "cusco", "machu picchu", "arequipa", "trujillo", "santiago", 
            "valparaiso", "punta arenas", "easter island", "bogota", "medellin", 
            "cali", "cartagena", "santa marta", "cairo", "giza", "alexandria", 
            "luxor", "aswan", "sharm el sheikh", "dubai", "abu dhabi", 
            "ras al khaimah", "delhi", "mumbai", "bangalore", "chennai", "kolkata", 
            "hyderabad", "jaipur", "varanasi", "goa", "beijing", "shanghai", 
            "guangzhou", "shenzhen", "xian", "hong kong", "macau", "hangzhou", 
            "tokyo", "osaka", "kyoto", "yokohama", "sapporo", "fukuoka", "seoul", 
            "busan", "incheon", "daegu", "jeju island", "bangkok", "chiang mai", 
            "phuket", "pattaya", "krabi", "koh samui", "ho chi minh city", "hanoi", 
            "da nang", "hoi an", "nha trang", "hue", "jakarta", "bali", 
            "yogyakarta", "surabaya", "lombok", "bandung", "manila", "cebu", 
            "davao", "palawan", "boracay", "bohol", "kuala lumpur", "penang", 
            "malacca", "langkawi", "kota kinabalu", "sarawak", "sydney", 
            "melbourne", "brisbane", "perth", "adelaide", "gold coast", "auckland", 
            "wellington", "christchurch", "queenstown", "rotorua", "cape town", 
            "johannesburg", "durban", "pretoria", "marrakech", "fes", "casablanca", 
            "chefchaouen", "lisbon", "porto", "sintra", "coimbra", "faro", "riyadh", 
            "jeddah", "medina", "mecca", "afghanistan", "albania", "algeria", 
            "andorra", "angola", "antigua and barbuda", "argentina", "armenia", 
            "australia", "austria", "azerbaijan", "bahamas", "bahrain", 
            "bangladesh", "barbados", "belarus", "belgium", "belize", "benin", 
            "bhutan", "bolivia", "bosnia and herzegovina", "botswana", "brazil", 
            "brunei", "bulgaria", "burkina faso", "burundi", "cabo verde", 
            "cambodia", "cameroon", "canada", "central african republic", "chad", 
            "chile", "china", "colombia", "comoros", "congo", "costa rica", 
            "croatia", "cuba", "cyprus", "czech republic", "denmark", "djibouti", 
            "dominica", "dominican republic", "ecuador", "egypt", "el salvador", 
            "equatorial guinea", "eritrea", "estonia", "eswatini", "ethiopia", 
            "fiji", "finland", "france", "gabon", "gambia", "georgia", "germany", 
            "ghana", "greece", "grenada", "guatemala", "guinea", "guinea-bissau", 
            "guyana", "haiti", "honduras", "hungary", "iceland", "india", 
            "indonesia", "iran", "iraq", "ireland", "israel", "italy", "jamaica", 
            "japan", "jordan", "kazakhstan", "kenya", "kiribati", "kuwait", 
            "kyrgyzstan", "laos", "latvia", "lebanon", "lesotho", "liberia", 
            "libya", "liechtenstein", "lithuania", "luxembourg", "madagascar", 
            "malawi", "malaysia", "maldives", "mali", "malta", "marshall islands", 
            "mauritania", "mauritius", "mexico", "micronesia", "moldova", "monaco", 
            "mongolia", "montenegro", "morocco", "mozambique", "myanmar", "namibia", 
            "nauru", "nepal", "netherlands", "new zealand", "nicaragua", "niger", 
            "nigeria", "north korea", "north macedonia", "norway", "oman", 
            "pakistan", "palau", "panama", "papua new guinea", "paraguay", "peru", 
            "philippines", "poland", "portugal", "qatar", "romania", "russia", 
            "rwanda", "saint kitts and nevis", "saint lucia", 
            "saint vincent and the grenadines", "samoa", "san marino", 
            "sao tome and principe", "saudi arabia", "senegal", "serbia", 
            "seychelles", "sierra leone", "singapore", "slovakia", "slovenia", 
            "solomon islands", "somalia", "south africa", "south korea", 
            "south sudan", "spain", "sri lanka", "sudan", "suriname", "sweden", 
            "switzerland", "syria", "taiwan", "tajikistan", "tanzania", "thailand", 
            "timor-leste", "togo", "tonga", "trinidad and tobago", "tunisia", 
            "turkey", "turkmenistan", "tuvalu", "uganda", "ukraine", 
            "united arab emirates", "united kingdom", "united states", "uruguay", 
            "uzbekistan", "vanuatu", "venezuela", "vietnam", "yemen", "zambia", 
            "zimbabwe"
        ]
        
        found_destinations = []
        for dest in destinations:
            if dest in text:
                found_destinations.append(dest.title())
        
        return found_destinations

    def _extract_budget_info(self, text: str) -> str:
        # See if they mentioned anything about money.
        
        # Check for dollar amounts
        dollar_matches = re.findall(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        if dollar_matches:
            amounts = [f"${amount}" for amount in dollar_matches]
            return f"Budget amounts mentioned: {', '.join(amounts)}"
        
        # Look for budget words
        budget_words = ["budget", "cheap", "expensive", "luxury", "affordable", "cost", "price"]
        found_words = [word for word in budget_words if word in text]
        if found_words:
            return f"Budget preferences: {', '.join(found_words)}"
        
        return ""

    def _extract_timing_info(self, text: str) -> str:
        # See when they want to travel.
        
        # Check for months
        months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december"
        ]
        found_months = [month for month in months if month in text]
        if found_months:
            return f"Months mentioned: {', '.join(found_months)}"
        
        # Check for seasons
        seasons = ["spring", "summer", "fall", "autumn", "winter"]
        found_seasons = [season for season in seasons if season in text]
        if found_seasons:
            return f"Seasons mentioned: {', '.join(found_seasons)}"
        
        # Look for timing words
        timing_words = ["when", "time", "season", "weather", "best time"]
        found_words = [word for word in timing_words if word in text]
        if found_words:
            return f"Timing preferences: {', '.join(found_words)}"
        
        return ""

    def _extract_travel_styles(self, text: str) -> List[str]:
        # See what kind of travel experience the user is looking for.
        styles = [
            "adventure", "relaxation", "cultural", "family", "romantic", "business",
            "luxury", "backpacking", "foodie", "photography", "hiking", "beach",
            "city", "rural", "wildlife", "history", "art", "music", "sports",
            "shopping", "nightlife", "spiritual", "wellness", "educational"
        ]
        
        found_styles = [style for style in styles if style in text]
        return found_styles

    def _extract_group_info(self, text: str) -> str:
        # Figure out who the user is traveling with.
        group_keywords = {
            "solo": ["alone", "solo", "by myself", "single"],
            "couple": ["couple", "romantic", "honeymoon", "anniversary"],
            "family": ["family", "kids", "children", "parents"],
            "group": ["group", "friends", "team", "colleagues"]
        }
        
        for group_type, keywords in group_keywords.items():
            if any(keyword in text for keyword in keywords):
                return group_type
        
        return ""

    def _extract_interests(self, text: str) -> List[str]:
        # See what activities and interests the user mentioned.
        interests = [
            "hiking", "climbing", "diving", "snorkeling", "swimming", "surfing",
            "skiing", "snowboarding", "cycling", "running", "yoga", "meditation",
            "cooking", "wine", "beer", "coffee", "tea", "shopping", "markets",
            "museums", "galleries", "theaters", "concerts", "festivals", "parks",
            "gardens", "temples", "churches", "mosques", "castles", "palaces",
            "ruins", "archaeology", "architecture", "design", "fashion", "art",
            "music", "dance", "literature", "poetry", "photography", "filming",
            "writing", "painting", "sculpture", "crafts", "pottery", "weaving",
            "jewelry", "textiles", "woodwork", "metalwork", "glassblowing",
            "farming", "gardening", "fishing", "hunting", "birdwatching",
            "wildlife", "safari", "zoo", "aquarium", "botanical", "forest",
            "mountain", "desert", "ocean", "river", "lake", "waterfall",
            "cave", "volcano", "glacier", "island", "beach", "reef", "coral"
        ]
        
        found_interests = [interest for interest in interests if interest in text]
        return found_interests

    def _build_preference_context(self, preferences: Dict) -> str:
        # Put together what we know about what they want.
        context_parts = []
        
        if preferences.get("destinations"):
            context_parts.append(f"Interested in: {', '.join(preferences['destinations'])}")
        
        if preferences.get("travel_dates"):
            dates = preferences["travel_dates"]
            if dates.get("start") and dates.get("end"):
                context_parts.append(f"Travel dates: {dates['start']} to {dates['end']}")
        
        if preferences.get("budget_range"):
            context_parts.append(f"Budget level: {preferences['budget_range']}")
        
        if preferences.get("travel_style"):
            context_parts.append(f"Travel style: {', '.join(preferences['travel_style'])}")
        
        if preferences.get("group_size"):
            context_parts.append(f"Group size: {preferences['group_size']} people")
        
        if preferences.get("interests"):
            context_parts.append(f"Interests: {', '.join(preferences['interests'])}")
        
        return "\n".join(context_parts)

    def _get_preference_extraction_function(self):
        # Tell the AI how to extract useful information from what the user says.
        return {
            "name": "extract_vacation_preferences",
            "description": "Extract and update vacation planning preferences from user input",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific destinations, regions, or countries mentioned"
                    },
                    "travel_dates": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "string", "format": "date"},
                            "end": {"type": "string", "format": "date"},
                            "flexible": {"type": "boolean"},
                            "duration_days": {"type": "integer"}
                        }
                    },
                    "budget_range": {
                        "type": "string",
                        "enum": ["budget", "moderate", "luxury"],
                        "description": "Inferred budget level from conversation"
                    },
                    "budget_amount": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                            "currency": {"type": "string", "default": "USD"}
                        }
                    },
                    "travel_style": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["adventure", "relaxation", "cultural", "family", "romantic", "business", "luxury", "backpacking", "foodie", "photography"]
                        }
                    },
                    "group_composition": {
                        "type": "object",
                        "properties": {
                            "adults": {"type": "integer"},
                            "children": {"type": "integer"},
                            "seniors": {"type": "integer"}
                        }
                    },
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific interests like 'scuba diving', 'wine tasting', 'hiking'"
                    },
                    "accommodation_preference": {
                        "type": "string",
                        "enum": ["hotel", "resort", "airbnb", "hostel", "villa", "camping"]
                    },
                    "pace_preference": {
                        "type": "string",
                        "enum": ["relaxed", "moderate", "packed"],
                        "description": "How busy they want their itinerary"
                    },
                    "must_haves": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Non-negotiable requirements"
                    },
                    "avoid": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Things they want to avoid"
                    }
                },
                "required": []
            }
        }

    def _generate_smart_fallback_response(self, messages: List[Message]) -> Dict:
        # Create a friendly response when we can't reach the AI.
        if not messages:
            return {
                "content": "Hello! I'm your vacation planning assistant. I'd love to help you plan your perfect trip! Where would you like to go?",
                "extracted_preferences": None,
                "confidence_score": 0.8
            }
        
        # Simple generic response
        return {
            "content": "I'd love to help you plan your perfect vacation! 🌍 To get started, could you tell me:\n\n• Where are you dreaming of going?\n• What type of experience are you looking for (adventure, relaxation, culture, etc.)?\n• When are you thinking of traveling?\n• What's your budget range?\n\nI'm here to make your travel dreams come true!",
            "extracted_preferences": None,
            "confidence_score": 0.7
        }

    def _generate_contextual_fallback_response(self, messages: List[Message], user_preferences: Optional[Dict] = None) -> str:
        # Create a helpful response that remembers what we've been talking about.
        if not messages:
            return "Hello! I'm your vacation planning assistant. I'd love to help you plan your perfect trip! Where would you like to go?"
        
        # Remember what we've been talking about
        conversation_context = self._extract_conversation_context(messages)
        last_message = messages[-1].content.lower()
        
        # If we remember the conversation, use that to give a better response
        if conversation_context:
            # See if we know where they want to go
            if "Destinations mentioned:" in conversation_context:
                destinations_line = [line for line in conversation_context.split('\n') if "Destinations mentioned:" in line][0]
                destinations = destinations_line.replace("Destinations mentioned: ", "").split(", ")
                
                # If they're asking about money, give them budget advice for their destination
                if "budget" in last_message or "spend" in last_message or "$" in last_message:
                    primary_dest = destinations[0]
                    return self._get_destination_specific_budget_response(primary_dest)
                
                # If they're asking about timing, give them timing advice for their destination
                if "when" in last_message and ("best" in last_message or "time" in last_message):
                    primary_dest = destinations[0]
                    return self._get_destination_specific_timing_response(primary_dest)
                
                # If they're asking about activities, give them activity advice for their destination
                if any(word in last_message for word in ["adventure", "relax", "culture", "food", "beach", "hiking", "shopping", "see", "do", "visit"]):
                    primary_dest = destinations[0]
                    return self._get_destination_specific_activity_response(primary_dest)
                
                # Give them a general response about their destination
                primary_dest = destinations[0]
                return f"I'm excited to help you plan your {primary_dest} adventure! Based on our conversation, I can help you with specific details about {primary_dest}. What would you like to know more about - the best time to visit, budget considerations, must-see attractions, or accommodation options?"
        
        # If we don't have much context, try to match their message to some popular destinations
        destinations = {
            "mongolia": "Mongolia is absolutely fascinating! The vast steppes, nomadic culture, and the Gobi Desert offer incredible experiences. For your Mongolia trip, I'd recommend considering the best time to visit (June-September for pleasant weather) and whether you're interested in staying in traditional gers with nomadic families. What aspects of Mongolia are most appealing to you?",
            "paris": "Paris, the City of Light! There's so much to explore beyond the iconic Eiffel Tower. Are you more interested in the classic tourist attractions, or would you prefer discovering hidden gems in neighborhoods like Le Marais or Montmartre? I can help you plan the perfect Parisian experience!",
            "bali": "Bali is a paradise for travelers! From the spiritual temples of Ubud to the beautiful beaches of Nusa Dua, there's something for everyone. Are you looking for relaxation, adventure, or cultural experiences? I can help you create the perfect Bali itinerary!",
            "japan": "Japan is incredible! Whether you're interested in the bustling streets of Tokyo, the traditional culture of Kyoto, or the natural beauty of Hokkaido, there's so much to explore. What type of Japanese experience are you dreaming of?",
            "thailand": "Thailand offers amazing diversity! From the bustling markets of Bangkok to the serene beaches of Phuket and the cultural richness of Chiang Mai. What's calling to you most about Thailand?",
            "vietnam": "Vietnam is a gem! The street food in Hanoi, the lanterns of Hoi An, and the Mekong Delta all offer unique experiences. Are you interested in the food scene, history, or natural landscapes?",
            "italy": "Italy is pure magic! From the art and history of Rome to the romantic canals of Venice and the rolling hills of Tuscany. What's your dream Italian experience?",
            "spain": "Spain is vibrant and diverse! The architecture of Barcelona, the flamenco of Seville, and the beaches of the Costa del Sol. What aspects of Spanish culture interest you most?",
            "kazakhstan": "Kazakhstan is a fascinating blend of Central Asian culture and modern development! From the futuristic architecture of Nur-Sultan to the stunning landscapes of the Altai Mountains and the cultural richness of Almaty, there's so much to explore. What aspects of Kazakhstan are you most interested in?"
        }
        
        # See if they mentioned any specific destinations
        for dest, response in destinations.items():
            if dest in last_message:
                return response
        
        # See if they're asking about money
        if "budget" in last_message or "spend" in last_message or "$" in last_message:
            return "I'd be happy to help you with budget planning! To give you the most accurate advice, could you tell me:\n\n• What destination(s) you're considering?\n• How long you're planning to travel?\n• What type of accommodation you prefer (budget, mid-range, luxury)?\n• What activities are most important to you?\n\nThis will help me provide specific budget recommendations tailored to your trip!"
        
        # See if they're asking about timing
        if "when" in last_message and ("best" in last_message or "time" in last_message):
            return "Great question about timing! The best time to visit really depends on your destination and what you want to experience. Could you tell me:\n\n• Which destination(s) you're considering?\n• What type of weather you prefer?\n• Are you flexible with dates or have specific constraints?\n• What activities are most important to you?\n\nI can then give you specific seasonal recommendations!"
        
        # See if they're asking about activities
        if any(word in last_message for word in ["adventure", "relax", "culture", "food", "beach", "hiking", "shopping"]):
            return "I love that you're thinking about what type of experience you want! To help me suggest the perfect destinations and activities, could you tell me:\n\n• What destination(s) are you considering?\n• How long do you have for your trip?\n• What's your budget range?\n• Are you traveling solo, as a couple, or with family/friends?\n\nThis will help me create a personalized recommendation just for you!"
        
        # Give them a friendly welcome message
        return "I'd love to help you plan your perfect vacation! 🌍 To get started, could you tell me:\n\n• Where are you dreaming of going?\n• What type of experience are you looking for (adventure, relaxation, culture, etc.)?\n• When are you thinking of traveling?\n• What's your budget range?\n\nI'm here to make your travel dreams come true!"

    def _get_destination_specific_budget_response(self, destination: str) -> str:
        # Give budget advice for a specific destination.
        budget_responses = {
            "Mongolia": "For your Mongolia trip, here's a realistic budget breakdown:\n\n• **Accommodation (ger stays)**: $20-40/night = $280-560 for 2 weeks\n• **Food**: $15-25/day = $210-350 for 2 weeks\n• **Activities (horseback riding, tours)**: $300-500\n• **Transport**: $200-300\n• **Permits/guides**: $100-200\n\nThis gives you a total of $1,090-1,910 for a 2-week trip. What's your target budget range?",
            "Paris": "For your Paris adventure, here's a typical budget breakdown:\n\n• **Accommodation**: $150-300/night = $2,100-4,200 for 2 weeks\n• **Food**: $50-100/day = $700-1,400 for 2 weeks\n• **Activities (museums, tours)**: $300-500\n• **Transport**: $100-200\n• **Shopping/entertainment**: $200-400\n\nThis gives you a total of $3,400-6,700 for a 2-week trip. What's your budget range?",
            "Bali": "For your Bali vacation, here's a realistic budget breakdown:\n\n• **Accommodation**: $50-150/night = $700-2,100 for 2 weeks\n• **Food**: $20-40/day = $280-560 for 2 weeks\n• **Activities (temple tours, spa)**: $200-400\n• **Transport**: $100-200\n• **Shopping/entertainment**: $150-300\n\nThis gives you a total of $1,430-3,560 for a 2-week trip. What's your budget range?",
            "Japan": "For your Japan journey, here's a typical budget breakdown:\n\n• **Accommodation**: $100-250/night = $1,400-3,500 for 2 weeks\n• **Food**: $40-80/day = $560-1,120 for 2 weeks\n• **Activities (temples, museums)**: $300-500\n• **Transport (JR Pass)**: $400-500\n• **Shopping/entertainment**: $200-400\n\nThis gives you a total of $2,860-6,020 for a 2-week trip. What's your budget range?",
            "Kazakhstan": "For your Kazakhstan exploration, here's a realistic budget breakdown:\n\n• **Accommodation**: $60-120/night = $840-1,680 for 2 weeks\n• **Food**: $25-45/day = $350-630 for 2 weeks\n• **Activities (city tours, museums)**: $200-400\n• **Transport**: $150-250\n• **Shopping/entertainment**: $100-200\n\nThis gives you a total of $1,640-3,160 for a 2-week trip. What's your budget range?"
        }
        
        return budget_responses.get(destination, f"I'd be happy to help you plan your budget for {destination}! To give you the most accurate advice, could you tell me:\n\n• How long you're planning to stay?\n• What type of accommodation you prefer?\n• What activities are most important to you?\n\nThis will help me provide specific budget recommendations for {destination}!")

    def _get_destination_specific_timing_response(self, destination: str) -> str:
        # Give timing advice for a specific destination.
        timing_responses = {
            "Mongolia": "For Mongolia, the **best time to visit is June to September** when the weather is pleasant and the steppes are green. Here's the seasonal breakdown:\n\n• **June-August**: Peak season with warm days (15-25°C) and cool nights\n• **September**: Shoulder season with beautiful autumn colors\n• **Winter (Nov-Mar)**: Very cold (-20 to -40°C) but unique winter experiences\n• **Spring (Apr-May)**: Windy and unpredictable weather\n\nWhat time of year are you considering for your Mongolia trip?",
            "Paris": "Paris is beautiful year-round, but here are the best times to visit:\n\n• **April-June**: Spring blooms and pleasant weather (10-20°C)\n• **September-October**: Autumn colors and fewer crowds (12-22°C)\n• **July-August**: Peak season with warm weather but crowds (18-25°C)\n• **November-March**: Cooler weather (5-15°C) but fewer tourists\n\nWhat season appeals to you most for your Paris adventure?",
            "Bali": "Bali has a tropical climate with two main seasons:\n\n• **Dry Season (April-October)**: Best time to visit with sunny weather (25-32°C)\n• **Wet Season (November-March)**: Rainy but still enjoyable (24-30°C)\n• **Peak Season**: July-August and December-January\n• **Shoulder Season**: April-June and September-November (best value)\n\nWhat time of year are you thinking for your Bali vacation?",
            "Japan": "Japan has four distinct seasons, each offering unique experiences:\n\n• **Spring (March-May)**: Cherry blossom season, mild weather (10-20°C)\n• **Summer (June-August)**: Hot and humid, festivals (20-30°C)\n• **Autumn (September-November)**: Beautiful fall colors, pleasant weather (15-25°C)\n• **Winter (December-February)**: Cold but magical, snow in some areas (0-10°C)\n\nWhat season interests you most for your Japan journey?",
            "Kazakhstan": "Kazakhstan has a continental climate with extreme seasons:\n\n• **Spring (March-May)**: Mild weather, blooming steppes (5-20°C)\n• **Summer (June-August)**: Hot and dry, best for outdoor activities (20-35°C)\n• **Autumn (September-November)**: Pleasant weather, beautiful colors (5-20°C)\n• **Winter (December-February)**: Very cold, snow-covered landscapes (-10 to -30°C)\n\nWhat time of year are you considering for your Kazakhstan exploration?"
        }
        
        return timing_responses.get(destination, f"I'd be happy to help you find the best time to visit {destination}! To give you the most accurate advice, could you tell me:\n\n• What type of weather you prefer?\n• What activities are most important to you?\n• Are you flexible with dates?\n\nThis will help me recommend the perfect timing for your {destination} trip!")

    def _get_destination_specific_activity_response(self, destination: str) -> str:
        # Generate destination-specific activity advice.
        activity_responses = {
            "Mongolia": "Mongolia offers incredible adventure and cultural experiences:\n\n• **Cultural**: Stay in traditional gers with nomadic families\n• **Adventure**: Horseback riding across the steppes, camel trekking in the Gobi\n• **Nature**: Visit Khövsgöl Lake, explore the Gobi Desert\n• **History**: Visit ancient monasteries and historical sites\n• **Wildlife**: Spot wild horses, eagles, and other unique animals\n\nWhat type of experience interests you most for your Mongolia trip?",
            "Paris": "Paris offers endless cultural and romantic experiences:\n\n• **Culture**: Visit the Louvre, Musée d'Orsay, and iconic landmarks\n• **Food**: Enjoy world-class dining, patisseries, and wine\n• **Romance**: Seine River cruises, Eiffel Tower, charming neighborhoods\n• **Shopping**: Fashion boutiques, markets, and luxury stores\n• **Art**: Explore galleries, street art, and cultural events\n\nWhat aspects of Parisian life interest you most?",
            "Bali": "Bali offers a perfect blend of culture, nature, and relaxation:\n\n• **Culture**: Visit ancient temples, traditional villages, and spiritual sites\n• **Nature**: Rice terraces, waterfalls, volcanoes, and beaches\n• **Wellness**: Yoga retreats, spa treatments, meditation\n• **Adventure**: Surfing, hiking, diving, and water sports\n• **Food**: Traditional Balinese cuisine, cooking classes\n\nWhat type of Bali experience are you dreaming of?",
            "Japan": "Japan offers diverse experiences from traditional to modern:\n\n• **Culture**: Visit temples, shrines, and traditional gardens\n• **Food**: Sushi, ramen, street food, and tea ceremonies\n• **Technology**: Modern cities, anime culture, gaming\n• **Nature**: Cherry blossoms, mountains, hot springs\n• **Shopping**: Electronics, fashion, traditional crafts\n\nWhat aspects of Japanese culture interest you most?",
            "Kazakhstan": "Kazakhstan offers unique Central Asian experiences:\n\n• **Culture**: Visit mosques, bazaars, and traditional yurts\n• **Nature**: Explore the Altai Mountains, steppes, and lakes\n• **Cities**: Modern Nur-Sultan, cultural Almaty\n• **Adventure**: Hiking, horseback riding, eagle hunting\n• **History**: Silk Road sites, ancient monuments\n\nWhat type of Kazakhstan experience interests you most?"
        }
        
        return activity_responses.get(destination, f"I'd be happy to help you discover the best activities in {destination}! To give you the most relevant recommendations, could you tell me:\n\n• What type of experiences interest you most?\n• How long will you be staying?\n• What's your activity level?\n\nThis will help me suggest the perfect activities for your {destination} adventure!")

    def _generate_fallback_response(self, last_message: str) -> str:
        # Generate a fallback response when API fails.
        # Create a mock message object for the contextual fallback
        class MockMessage:
            def __init__(self, content):
                self.content = content
                self.role = "user"  # Add role attribute
        
        return self._generate_contextual_fallback_response([MockMessage(last_message)], None)  # 

    def _calculate_response_confidence(self, response: str, messages: List[Message]) -> float:
        # Calculate confidence score for the response.
        # Simple heuristic-based confidence scoring
        score = 0.7  # Base score
        
        # Check if response addresses the user's question
        if messages:
            last_user_message = next((m for m in reversed(messages) if m.role.value == "user"), None)
            if last_user_message:
                # Check for question words
                question_words = ["what", "where", "when", "how", "which", "why"]
                has_question = any(word in last_user_message.content.lower() for word in question_words)
                
                # Check if response seems relevant
                if has_question and len(response) > 100:
                    score += 0.2
                elif not has_question and len(response) > 50:
                    score += 0.1
        
        # Check response quality indicators
        if "I don't" in response or "I cannot" in response:
            score -= 0.3
        if "!" in response:  # Enthusiasm
            score += 0.05
        if response.count("\n") > 2:  # Well-structured
            score += 0.05
        
        return max(0.0, min(1.0, score))

    def _is_travel_related(self, message: str, conversation_history: Optional[List[Message]] = None) -> bool:
        # Robust topic drift detection using LLM intent classification
        # Only the latest user message is checked for travel relevance
        # If 2+ consecutive non-travel responses, lock the conversation to travel and redirect until a travel-related message is detected
        # If the latest message is travel-related, reset the drift lock and counter
        # No keyword/regex heuristics are used
        try:
            if not self.client:
                # Fallback: simple keyword check for travel-related messages
                travel_keywords = [
                    'travel', 'hotel', 'flight', 'vacation', 'trip', 'destination', 'itinerary',
                    'book', 'tour', 'adventure', 'accommodation', 'resort', 'city', 'country',
                    'explore', 'visit', 'plan', 'journey', 'holiday'
                ]
                message_lower = message.lower()
                
                # Check for affirmative responses that are likely travel-related
                affirmative_responses = ['yes', 'sure', 'okay', 'ok', 'that sounds good', 'recommendations', 'recommend']
                if any(response in message_lower for response in affirmative_responses):
                    return True
                
                return any(kw in message_lower for kw in travel_keywords)

            # Only check the latest user message for travel relevance
            prompt = f"""You are a strict travel planning assistant. Your ONLY job is to determine if the following user message is about travel or vacation planning.

            Answer 'yes' if the message is about:
            - Travel/vacation planning
            - Travel logistics (flights, hotels, transportation)
            - Travel experiences and destinations
            - Travel safety and health concerns
            - Travel insurance basics and coverage options
            - Adventure travel and extreme sports planning
            - Travel logistics emergencies (lost passports, flight cancellations, visa issues)
            - Basic travel risk assessment and safety tips
            - Any situation that occurs while traveling or affects travel plans
            - **CRITICAL: Responses like "Yes", "Yes, I want recommendations", "Sure", "That sounds good" when in the middle of a travel planning conversation are ALWAYS travel-related**
            - **CRITICAL: Any affirmative response to travel planning questions is travel-related**

            Answer 'no' if the message is about:
            - General wellness advice not related to travel
            - Mental health advice not related to travel stress
            - Personal finance advice not related to travel budgeting
            - Relationship advice not related to travel companions
            - Medical advice, emergency protocols, or health guidance (even during travel)
            - Legal advice, diplomatic matters, or legal procedures
            - Specialized professional topics (diplomatic immunity, legal protections, insurance claims, risk assessment)
            - Medical emergencies or requests for medical procedures
            - Any other general life advice unrelated to travel

            User message: {message}

            Is this message about travel/vacation planning or travel-related situations? (yes/no):"""

            # Make the API call for intent classification
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=10     # We only need yes/no
            )

            # Extract and parse the response
            content = response.choices[0].message.content
            if not content:
                logger.warning("Couldn't figure out the intent, so we'll assume it's travel-related")
                return True

            # Parse the response
            response_text = content.strip().lower()
            is_travel_related = response_text.startswith('yes')

            # Drift state management
            if is_travel_related:
                self._drift_counter = 0
                self._drift_lock = False
                self._last_drift_state = True
            else:
                self._drift_counter += 1
                self._last_drift_state = False
                if self._drift_counter >= self._drift_lock_threshold:
                    self._drift_lock = True
                    logger.info("User keeps going off-topic, so we're locking the conversation to travel planning")

            logger.info(f"Checked if message '{message[:50]}...' is travel-related: {is_travel_related} (drift_counter={self._drift_counter}, drift_lock={self._drift_lock})")
            return is_travel_related

        except Exception as e:
            logger.error(f"Something went wrong while checking the message intent: {e}")
            # On error, default to allowing the message (fail open)
            return True

    def _generate_topic_redirect_response(self, message: str) -> str:
        # Generate a polite redirect response when the user's message is not travel-related
        redirect_responses = [
            "I'd love to help you with that, but I'm specifically designed to assist with travel planning! Let's get back to planning your perfect vacation. What destination are you thinking about?",
            "That sounds interesting! However, I'm your travel planning assistant. Let me help you plan an amazing trip instead. Where would you like to go?",
            "I'm focused on helping you plan incredible vacations! Let's get back to travel planning. What kind of trip are you dreaming of?",
            "While that's a great topic, I'm here to help with your travel adventures! Let's plan your next vacation. What destination is calling your name?",
            "I'm your travel planning specialist! Let's focus on creating amazing travel experiences. What's your dream destination?"
        ]
        
        import random
        return random.choice(redirect_responses)
    