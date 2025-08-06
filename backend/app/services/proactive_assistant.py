from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ProactiveAssistant:
    """
    Helps users plan their vacation by thinking ahead and offering helpful suggestions.
    
    This service tries to anticipate what users might need next and gives them
    friendly suggestions to make their vacation planning easier and more fun.
    """
    
    def get_proactive_suggestions(
        self, 
        context: Dict,
        preferences: Dict,
        message_count: int
    ) -> List[Dict]:
        """Give users helpful suggestions based on where they are in planning their trip."""
        suggestions = []
        # Welcome them if they're just getting started
        if message_count <= 3:
            suggestions.append({
                "type": "welcome",
                "content": "👋 **Getting Started**: I'm here to help you plan your perfect vacation! " +
                          "Tell me about your travel dreams and I'll guide you through the planning process.",
                "priority": 9.0
            })
        # Check what stage they're at in planning
        stage = context.get("stage", "exploring")
        if stage == "planning" and message_count > 5:
            suggestions.append({
                "type": "accommodation",
                "content": "🏨 **Where to Stay**: Let's find you a great place to stay for your trip.",
                "priority": 8.0
            })
            suggestions.append({
                "type": "activities",
                "content": "🎯 **What to Do**: What experiences and attractions are on your must-see list?",
                "priority": 7.0
            })
        elif stage == "exploring":
            suggestions.append({
                "type": "destination",
                "content": "🌍 **Where to Go**: Would you like some destination ideas, or do you have a place in mind?",
                "priority": 8.0
            })
        elif stage == "comparing":
            suggestions.append({
                "type": "comparison",
                "content": "🔍 **Comparing Places**: Need help weighing the pros and cons of your top choices?",
                "priority": 8.0
            })
        elif stage == "finalizing":
            suggestions.append({
                "type": "booking",
                "content": "📋 **Wrapping Up**: Let's finalize your bookings and get you ready for your trip.",
                "priority": 8.0
            })
        # Help them explore their chosen destination
        if preferences.get("destinations"):
            dest = preferences["destinations"][0] if isinstance(preferences["destinations"], list) else preferences["destinations"]
            suggestions.append({
                "type": "destination",
                "content": f"🗺️ **{dest} Highlights**: I can help you discover the best attractions, local cuisine, and hidden gems in {dest}!",
                "priority": 6.0
            })
        # Help them think about their budget
        if not preferences.get("budget_range") and not preferences.get("budget_amount"):
            suggestions.append({
                "type": "budget",
                "content": "💰 **Budget Talk**: Understanding your budget helps me suggest the best options for your dream vacation.",
                "priority": 7.0
            })
        # Give them something helpful to think about
        if not suggestions:
            suggestions.append({
                "type": "general",
                "content": "🌟 **What's Next**: Let's continue planning your perfect vacation! What would you like to know more about?",
                "priority": 5.0
            })
        return suggestions[:3]
    
    def _calculate_days_until_travel(self, travel_dates: Dict) -> Optional[int]:
        """See how many days until their trip starts."""
        if not travel_dates or "start" not in travel_dates:
            return None
        
        try:
            # Handle different date formats
            if isinstance(travel_dates["start"], str):
                travel_date = datetime.fromisoformat(travel_dates["start"])
            else:
                travel_date = travel_dates["start"]
            
            days_until = (travel_date - datetime.now()).days
            return days_until  # Allow negative values for past dates
        except Exception as e:
            logger.warning(f"Couldn't figure out how many days until travel: {e}")
            return None
    
    def anticipate_next_questions(
        self,
        stage: str,
        preferences: Dict,
        recent_topics: List[str]
    ) -> List[str]:
        """Guess what the user might want to ask next."""
        anticipated = []
        # Give them some basic ideas if they haven't talked about much yet
        if not recent_topics:
            anticipated.extend(["where to travel", "destination options", "budget considerations"])
        if stage == "exploring":
            if "destination" not in recent_topics:
                anticipated.append("where to travel")
            if "budget" not in recent_topics:
                anticipated.append("budget considerations")
            if "weather" not in recent_topics:
                anticipated.append("best time to visit")
            if "duration" not in recent_topics:
                anticipated.append("how long to stay")
        elif stage == "comparing":
            if "preferences" not in recent_topics:
                anticipated.append("which destination do you prefer")
            if "style" not in recent_topics:
                anticipated.append("what travel style do you prefer")
            if "activities" not in recent_topics:
                anticipated.append("what activities do you prefer")
            if "accommodation" not in recent_topics:
                anticipated.append("where to stay")
        elif stage == "planning":
            if "hotel" not in recent_topics and "accommodation" not in recent_topics:
                anticipated.append("where to stay and hotel options")
                anticipated.append("accommodation preferences and booking")
            else:
                # If they've already talked about accommodation, get more specific
                anticipated.append("hotel booking and reservation details")
                anticipated.append("accommodation preferences and room types")
            if "activities" not in recent_topics:
                anticipated.append("what activities to include")
            if "itinerary" not in recent_topics:
                anticipated.append("daily itinerary planning")
            if "transport" not in recent_topics:
                anticipated.append("transportation options")
            if "documents" not in recent_topics:
                anticipated.append("travel documents needed")
            if "insurance" not in recent_topics:
                anticipated.append("travel insurance")
            if "packing" not in recent_topics:
                anticipated.append("what to pack")
        elif stage == "finalizing":
            if "booking" not in recent_topics:
                anticipated.append("when to book")
            if "documents" not in recent_topics:
                anticipated.append("what documents needed")
            if "checklist" not in recent_topics:
                anticipated.append("final checklist")
        else:
            if "destination" not in recent_topics:
                anticipated.append("destination options")
            if "budget" not in recent_topics:
                anticipated.append("budget considerations")
            if "timing" not in recent_topics:
                anticipated.append("best travel times")
        # Make sure we give them at least one idea
        if not anticipated:
            anticipated.append("where to travel")
        return anticipated[:3]
    
    def generate_suggestions(self, conversation, user_preferences) -> List[str]:
        """Come up with helpful suggestions based on what is talked about."""
        suggestions = []
        
        # Give them some basic questions to think about
        suggestions.extend([
            "What's your budget for this trip?",
            "When are you planning to travel?",
            "How long are you staying?"
        ])
        
        # Add suggestions based on where they are in planning
        if hasattr(conversation, 'vacation_preferences'):
            stage = conversation.vacation_preferences.get('stage', 'exploring')
            
            if stage == 'planning':
                suggestions.extend([
                    "Have you thought about travel insurance?",
                    "Do you need help finding a place to stay?",
                    "What activities interest you the most?"
                ])
        
        # Add suggestions based on what we know about them
        if user_preferences:
            if 'destinations' in user_preferences and not user_preferences.get('travel_dates'):
                suggestions.append("When would you like to visit these destinations?")
            
            if 'budget' not in user_preferences:
                suggestions.append("What's your budget range for this trip?")
        
        return suggestions[:3]  # Give them the top 3 suggestions