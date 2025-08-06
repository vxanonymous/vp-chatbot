from typing import Dict, List, Optional, Any
import logging
import random

logger = logging.getLogger(__name__)


class ErrorRecoveryService:
    """
    Helps keep vacation planning conversations flowing smoothly when things go wrong.
    
    When something doesn't work as expected, we provide friendly responses to help
    users get back to planning their dream vacation without feeling frustrated.
    """
    
    def __init__(self):
        self.fallback_responses = self._init_fallback_responses()
    
    def _init_fallback_responses(self) -> Dict[str, List[str]]:
        """Set up friendly responses to help users when something goes wrong."""
        return {
            "general_error": [
                "I apologize for the confusion; let me help you plan your perfect vacation. What destination are you considering?",
                "Let's get back on track with your travel planning. What aspects are the most important of your trip?",
                "I'm here to help make your vacation planning easier. What are your concerns about your upcoming trip?"
            ],
            "no_context": [
                "I'd love to help you plan an amazing trip! Where are you thinking of?",
                "Let's start planning your adventure! Do you have a destination in mind, or would you like some suggestions?",
                "Ready to plan something special? Tell me about your travel dreams!"
            ],
            "unclear_input": [
                "I want to make sure I understand correctly. Could you tell me more about what you're looking for?",
                "Allow me to help you better with your travel planning. Are you asking about destinations, planning tips, or something specific?",
                "I'm here to help with your vacation planning! Could you elaborate on what aspect of travel you'd like to discuss?"
            ],
            "off_topic": [
                "I'm specialized in vacation planning! Let's talk about your next adventure. Where would you like to go?",
                "My expertise is in helping you plan amazing trips. What travel dreams can I help you with?",
                "Let's focus on creating your perfect vacation. What destinations have you been dreaming about?"
            ],
            "api_error": [
                "I'm having a moment of technical difficulty, but I'm still here to help plan your dream vacation! What destination are you considering?",
                "Let me refocus on your travel plans. What's the most important aspect of your trip?",
                "I apologize for the brief interruption; let's continue planning your perfect trip! What aspects of your vacation are most important to you?"
            ]
        }

    def handle_technical_error(self):
        """Let the user know we're having a tech hiccup, but we're still here for them."""
        return "Oops, looks like I'm having a technical hiccup! But don't worry, I'm still here to help you plan your dream vacation. Where would you like to go next?"


    def handle_ambiguous_request(self, message):
        """Ask for clarification in a friendly, approachable way."""
        return "Hmm, I want to make sure I get this right. Could you clarify a bit more about what you're looking for in your trip?"


    def handle_off_topic_message(self, message):
        """Gently nudge the user back to vacation planning in a warm way."""
        return "I’m all about travel planning! Let’s get back to your next adventure—any destinations on your mind?"

    
    def get_recovery_response(
        self, 
        error_type: str, 
        context: Optional[Dict] = None
    ) -> str:
        """Give users a friendly response to help them get back to vacation planning when something goes wrong."""
        
        # Figure out what kind of response would be most helpful
        if error_type == "api_error":
            responses = self.fallback_responses["api_error"]
        elif error_type == "no_context":
            responses = self.fallback_responses["no_context"]
        elif error_type == "unclear_input":
            responses = self.fallback_responses["unclear_input"]
        elif error_type == "off_topic":
            responses = self.fallback_responses["off_topic"]
        else:
            responses = self.fallback_responses["general_error"]
        
        # Pick a friendly response to help them get back to planning their trip
        base_response = random.choice(responses)
        
        # Make it more personal if we know something about their vacation plans
        if context:
            base_response = self._enhance_with_context(base_response, context)
        
        return base_response
    
    def _enhance_with_context(self, base_response: str, context: Dict) -> str:
        """Make responses more personal by adding what we know about their vacation plans."""
        if context.get("last_destination"):
            base_response += f"\n\nWere you still interested in {context['last_destination']}?"
        elif context.get("stage") == "planning":
            base_response += "\n\nShall we continue planning your trip?"
        
        return base_response
    
    def validate_conversation_flow(
        self, 
        messages: List[Dict],
        new_message: str
    ) -> Dict[str, Any]:
        """Check if the conversation is flowing smoothly and naturally."""
        
        validation = {
            "is_valid": True,
            "issues": [],
            "suggestions": []
        }
        
        # See if the user is asking the same things repeatedly
        if len(messages) > 2:
            recent_user_messages = [
                m["content"].lower() 
                for m in messages[-4:] 
                if m["role"] == "user"
            ]
            
            if len(set(recent_user_messages)) < len(recent_user_messages) * 0.7:
                validation["issues"].append("repetitive_questions")
                validation["suggestions"].append(
                    "It seems we might be going in circles. Let me summarize what we've discussed so far."
                )
        
        # Check if they're staying on topic
        if new_message:
            has_travel_context = self._has_travel_context(new_message)
            
            if not has_travel_context and len(new_message) > 20:
                validation["issues"].append("possibly_off_topic")
                validation["is_valid"] = False
        
        return validation
    
    def _has_travel_context(self, message: str) -> bool:
        """See if the message is about travel or vacation planning"""
        travel_keywords = [
            "travel", "trip", "vacation", "visit", "go", "fly", "stay",
            "hotel", "flight", "destination", "holiday", "tour", "booking",
            "reservation", "itinerary", "accommodation", "transportation"
        ]
        return any(
            keyword in message.lower()
            for keyword in travel_keywords
        )

    def recover_from_error(self, error: str) -> str:
        """Help the user get back on track in a natural, supportive way."""
        error_lower = error.lower()
        if "off topic" in error_lower or "unrelated" in error_lower:
            # Gently nudge the user back to travel planning
            return self.handle_off_topic_message(error)
        elif "ambiguous" in error_lower or "unclear" in error_lower:
            # Ask for clarification in a warm, approachable way
            return self.handle_ambiguous_request(error)
        elif "technical" in error_lower or "api" in error_lower:
            # Let the user know we're having a tech hiccup, but we're still here for them
            return self.handle_technical_error()
        else:
            # If we can't tell, just offer a friendly fallback
            return self.get_recovery_response("general_error")