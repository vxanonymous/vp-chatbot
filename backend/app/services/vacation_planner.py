from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class VacationPlanner:
    """
    Helps create personalized vacation plans and gives helpful suggestions.
    
    Takes what users tell us about their preferences and creates detailed vacation
    recommendations, itineraries, and planning help for their dream trip.
    """
    
    def __init__(self):
        # These are the basic questions we ask when someone's just starting to plan
        self.default_suggestions = [
            "Tell me about your dream destination",
            "What's your budget like?",
            "When do you want to travel?",
            "What kind of activities do you enjoy?"
        ]
        
        # Keep track of how many plans we've created (just for fun)
        self.plans_created = 0
    
    def generate_suggestions(self, preferences: Optional[Dict]) -> List[str]:
        """Come up with helpful suggestions based on what we know about their vacation plans."""
        suggestions = []
        
        # If they haven't told us anything yet, just ask the basics
        if not preferences:
            return self.default_suggestions
        
        # Ask about their specific destination if they've mentioned one
        if preferences.get("destinations"):
            destinations = preferences["destinations"]
            if isinstance(destinations, list) and destinations:
                dest = destinations[0]
            else:
                dest = destinations
            suggestions.append(f"Tell me more about your plans for {dest}.")
        
        # Now let's see what they're missing and help them fill in the gaps
        has_destination = preferences.get("destinations")
        
        if has_destination and not preferences.get("travel_dates"):
            suggestions.append("When do you want to travel?")
        if has_destination and not preferences.get("budget_range"):
            suggestions.append("What's your budget like?")
        if has_destination and not preferences.get("travel_style"):
            suggestions.append("What kind of activities do you enjoy?")
        if has_destination and not preferences.get("group_size"):
            suggestions.append("How many people are coming with you?")
        if has_destination and not preferences.get("interests"):
            suggestions.append("What are you most interested in for this trip?")
        
        # If we didn't come up with anything specific, fall back to the basics
        if not suggestions:
            suggestions = self.default_suggestions
        
        # Only give them 3 suggestions so they don't get overwhelmed
        return suggestions[:3]
    
    def create_vacation_plan(self, preferences: Optional[Dict]) -> Optional[Dict]:
        """Create a detailed vacation plan based on what they've told us about their preferences."""
        # Can't create a plan if they haven't told us where they want to go
        if not preferences or not preferences.get("destinations"):
            return None
        
        try:
            # Get their destination - handle both list and string formats
            destinations = preferences["destinations"]
            if isinstance(destinations, list) and destinations:
                dest = destinations[0]
            else:
                dest = destinations
            
            # Clean up the destination name a bit (remove extra spaces, etc.)
            dest = dest.strip() if isinstance(dest, str) else str(dest)
            
            # Figure out how long their vacation will be
            duration_days = 7  # Default to a week if they haven't told us
            if preferences.get("travel_dates"):
                try:
                    from datetime import datetime
                    start_date = datetime.fromisoformat(preferences["travel_dates"]["start"])
                    end_date = datetime.fromisoformat(preferences["travel_dates"]["end"])
                    
                    # Make sure the dates make sense
                    if end_date < start_date:
                        # If they put the dates in backwards, swap them
                        start_date, end_date = end_date, start_date
                    
                    # Calculate the difference and add 1 to include the end date
                    date_difference = end_date - start_date
                    duration_days = date_difference.days + 1
                    
                    # Don't let them plan for more than 30 days (that's a really long vacation!)
                    if duration_days > 30:
                        duration_days = 30
                        
                except Exception as date_error:
                    # If something goes wrong with the dates, just use a week
                    logger.warning(f"Had trouble with their dates: {date_error}")
                    duration_days = 7
            
            # Now let's gather all the information we need for their plan
            # Start with the activities they might enjoy
            suggested_activities = self._generate_destination_activities(dest, preferences)
            
            # Figure out where they should stay
            accommodation_recommendations = self._generate_accommodation_recommendations(dest, preferences)
            
            # How they'll get around
            transportation_options = self._generate_transportation_options(dest, preferences)
            
            # Some helpful tips for their destination
            local_tips = self._generate_local_tips(dest, preferences)
            
            # What the weather might be like
            weather_info = self._generate_weather_info(dest, preferences)
            
            # Build the vacation plan step by step
            plan = {}
            
            # The basics
            plan["destination"] = dest
            plan["duration_days"] = duration_days
            
            # Money stuff
            plan["estimated_budget"] = self._generate_budget_estimate(preferences)
            
            # What to do
            plan["suggested_activities"] = suggested_activities
            plan["accommodation_recommendations"] = accommodation_recommendations
            plan["transportation_options"] = transportation_options
            
            # Helpful info
            plan["best_time_to_visit"] = self._generate_best_time_to_visit(dest, preferences)
            plan["weather_info"] = weather_info
            plan["local_tips"] = local_tips
            
            # Their daily schedule
            plan["itinerary"] = self._generate_itinerary(dest, duration_days, preferences)
            
            # Keep track of how many plans we've created
            self.plans_created += 1
            
            # Add any extra information they've given us (if they provided it)
            if preferences.get("travel_dates"):
                plan["travel_dates"] = preferences["travel_dates"]
            
            if preferences.get("budget_range"):
                plan["budget_range"] = preferences["budget_range"]
            
            if preferences.get("travel_style"):
                plan["travel_style"] = preferences["travel_style"]
            
            if preferences.get("group_size"):
                plan["group_size"] = preferences["group_size"]
            
            if preferences.get("interests"):
                plan["interests"] = preferences["interests"]
            
            # Add a little note about when this plan was created
            from datetime import datetime
            plan["created_at"] = datetime.now().isoformat()
            
            return plan
            
        except Exception as e:
            logger.error(f"Something went wrong while creating the vacation plan: {e}")
            return None
    
    def create_vacation_summary(self, preferences: Optional[Dict]) -> Optional[Dict]:
        """Create a summary of their vacation plans from what they've told us."""
        # Can't create a summary if they haven't told us where they want to go
        if not preferences or not preferences.get("destinations"):
            return None
        
        try:
            # Get their destination - handle both list and string formats
            destinations = preferences["destinations"]
            if isinstance(destinations, list) and destinations:
                dest = destinations[0]
            else:
                dest = destinations
            
            # Clean up the destination name (same as in create_vacation_plan)
            dest = dest.strip() if isinstance(dest, str) else str(dest)
            
            # Let's see what they've told us and what they're still missing
            missing_info = []
            
            # Check each important piece of information
            if not preferences.get("budget_range"):
                missing_info.append("Budget range")
            if not preferences.get("travel_dates"):
                missing_info.append("Travel dates")
            if not preferences.get("travel_style"):
                missing_info.append("Travel style")
            if not preferences.get("group_size"):
                missing_info.append("Group size")
            
            # Figure out how complete their plan is
            completeness = self._calculate_completeness_percentage(preferences)
            
            # Create the summary step by step
            summary = {}
            
            # The basics
            summary["destination"] = dest
            summary["budget_range"] = preferences.get("budget_range", "Not specified")
            summary["completeness_percentage"] = completeness
            summary["missing_info"] = missing_info
            
            # Get some helpful recommendations for them
            summary["recommendations"] = self._generate_recommendations(preferences)
            
            # Add any extra details they've provided
            if preferences.get("travel_dates"):
                summary["travel_dates"] = preferences["travel_dates"]
            
            if preferences.get("travel_style"):
                summary["travel_style"] = preferences["travel_style"]
            
            if preferences.get("group_size"):
                summary["group_size"] = preferences["group_size"]
            
            if preferences.get("interests"):
                summary["interests"] = preferences["interests"]
            
            # Add a little note about when this summary was created
            from datetime import datetime
            summary["created_at"] = datetime.now().isoformat()
            
            # Add a friendly status message based on how complete their plan is
            if completeness >= 80:
                summary["status"] = "Great! You're almost ready to go!"
            elif completeness >= 60:
                summary["status"] = "Good progress! Just a few more details to nail down."
            elif completeness >= 40:
                summary["status"] = "Getting there! You've got the basics covered."
            else:
                summary["status"] = "Just getting started! Let's fill in some more details."
            
            return summary
            
        except Exception as e:
            logger.error(f"Something went wrong while creating the vacation summary: {e}")
            return None
    
    def _calculate_completeness_percentage(self, preferences: Dict) -> int:
        """See how much information we have about their vacation plans."""
        # These are the main things we need to know to create a good plan
        essential_fields = [
            "destinations", "travel_dates", "budget_range", 
            "travel_style", "group_size"
        ]
        
        # Count how many fields they've filled out
        completed = 0
        for field in essential_fields:
            if preferences.get(field) and preferences[field]:
                completed += 1
        
        # Calculate the percentage - if they have everything, that's 100%
        percentage = (completed / len(essential_fields)) * 100
        return int(percentage)
    
    def _generate_recommendations(self, preferences: Dict) -> List[str]:
        """Come up with good recommendations based on what we know about them."""
        # Get their destination, or use a default if they haven't specified one
        destinations = preferences.get("destinations", ["your destination"])
        dest = destinations[0]
        
        # Clean up the destination name
        dest = dest.strip() if isinstance(dest, str) else str(dest)
        
        # Get their travel style, or use a default
        travel_style = preferences.get("travel_style", ["cultural"])
        budget = preferences.get("budget_range", "moderate")
        
        # Create some personalized recommendations
        recommendations = []
        
        # First recommendation based on their budget and destination
        if budget == "budget":
            first_rec = f"For your budget-friendly trip to {dest}, look for free walking tours, local markets, and street food to save money while experiencing the real culture."
        elif budget == "luxury":
            first_rec = f"For your luxury trip to {dest}, consider booking exclusive experiences, fine dining reservations, and private tours to make the most of your premium budget."
        else:
            first_rec = f"For your {budget} trip to {dest}, consider these must-see attractions and experiences: local landmarks, food tours, and unique cultural events."
        recommendations.append(first_rec)
        
        # Second recommendation about planning around their interests
        if travel_style and len(travel_style) > 0:
            # If they have specific interests, personalize the recommendation
            if "adventure" in travel_style:
                second_rec = f"Since you're into adventure, look for hiking trails, outdoor activities, and adrenaline-pumping experiences in {dest}."
            elif "relaxation" in travel_style:
                second_rec = f"Since you want to relax, focus on spa experiences, peaceful gardens, and quiet cafes in {dest}."
            elif "food" in travel_style or "foodie" in travel_style:
                second_rec = f"Since you're a food lover, make sure to try the local specialties, visit food markets, and maybe take a cooking class in {dest}."
            else:
                style_text = ', '.join(travel_style)
                second_rec = f"To make the most of your time in {dest}, plan your days around your interests: {style_text} activities, local cuisine, and hidden gems."
        else:
            second_rec = f"To make the most of your time in {dest}, plan your days around local cuisine, cultural sites, and hidden gems."
        recommendations.append(second_rec)
        
        # Third recommendation about timing and practical tips
        if preferences.get("travel_dates"):
            third_rec = f"Since you have your dates set, check the weather forecast for {dest} during your stay and pack accordingly."
        else:
            third_rec = f"Don't forget to check the best time to visit {dest} for ideal weather and fewer crowds."
        recommendations.append(third_rec)
        
        # Fourth recommendation based on group size
        group_size = preferences.get("group_size")
        if group_size:
            if group_size == 1:
                fourth_rec = f"As a solo traveler in {dest}, consider joining group tours or staying in social hostels to meet other travelers."
            elif group_size >= 4:
                fourth_rec = f"With a group of {group_size} people, look for family-friendly activities and consider booking accommodations with multiple rooms in {dest}."
            else:
                fourth_rec = f"With {group_size} people, you'll have a great balance of flexibility and company while exploring {dest}."
            recommendations.append(fourth_rec)
        
        # Make sure the recommendations are helpful (not too short)
        helpful_recommendations = []
        for rec in recommendations:
            if len(rec) > 10:
                helpful_recommendations.append(rec)
        
        # Return only the first 3 recommendations so they don't get overwhelmed
        return helpful_recommendations[:3]
    
    def _generate_destination_activities(self, destination: str, preferences: Dict) -> List[str]:
        """Come up with activities that are specific to their destination."""
        activities = []
        dest_lower = destination.lower()
        
        # Check if it's one of the places we know well
        if "paris" in dest_lower:
            activities = [
                f"Visit the Eiffel Tower in {destination}",
                f"Explore the Louvre Museum in {destination}",
                f"Walk along the Champs-Élysées in {destination}",
                f"Take a Seine River cruise in {destination}",
                f"Visit Notre-Dame Cathedral in {destination}"
            ]
        elif "tokyo" in dest_lower:
            activities = [
                f"Visit Senso-ji Temple in {destination}",
                f"Explore Shibuya Crossing in {destination}",
                f"Visit the Tokyo Skytree in {destination}",
                f"Walk through Meiji Shrine in {destination}",
                f"Experience Tsukiji Fish Market in {destination}"
            ]
        elif "bali" in dest_lower:
            activities = [
                f"Visit Tanah Lot Temple in {destination}",
                f"Explore Ubud Monkey Forest in {destination}",
                f"Relax at Nusa Dua Beach in {destination}",
                f"Take a rice terrace tour in {destination}",
                f"Experience traditional Balinese dance in {destination}"
            ]
        else:
            # For places we don't know as well, give general suggestions
            activities = [
                f"Explore the main attractions in {destination}",
                f"Visit local museums and cultural sites in {destination}",
                f"Try local cuisine in {destination}",
                f"Take a guided tour of {destination}",
                f"Experience local markets in {destination}"
            ]
        
        # Only return the first 5 so they don't get overwhelmed
        return activities[:5]
    
    def _generate_accommodation_recommendations(self, destination: str, preferences: Dict) -> List[Dict]:
        """Suggest places to stay based on their budget and destination."""
        budget_range = preferences.get("budget_range", "moderate")
        recommendations = []
        
        # Suggest different types of places based on their budget
        if budget_range == "budget":
            recommendations = [
                {"type": "Hostel", "description": f"Budget-friendly hostels in {destination}"},
                {"type": "Guesthouse", "description": f"Local guesthouses in {destination}"},
                {"type": "Budget Hotel", "description": f"Affordable hotels in {destination}"}
            ]
        elif budget_range == "luxury":
            recommendations = [
                {"type": "Luxury Hotel", "description": f"5-star hotels in {destination}"},
                {"type": "Resort", "description": f"Exclusive resorts in {destination}"},
                {"type": "Boutique Hotel", "description": f"Luxury boutique hotels in {destination}"}
            ]
        else:  # moderate budget
            recommendations = [
                {"type": "Hotel", "description": f"Comfortable hotels in {destination}"},
                {"type": "Apartment", "description": f"Vacation rentals in {destination}"},
                {"type": "B&B", "description": f"Bed and breakfasts in {destination}"}
            ]
        
        return recommendations
    
    def _generate_transportation_options(self, destination: str, preferences: Dict) -> List[Dict]:
        """Suggest ways to get around their destination."""
        return [
            {"type": "Public Transit", "description": f"Metro, buses, and trains in {destination}"},
            {"type": "Walking", "description": f"Explore {destination} on foot"},
            {"type": "Bicycle", "description": f"Rent a bike to explore {destination}"},
            {"type": "Taxi/Rideshare", "description": f"Convenient transportation in {destination}"}
        ]
    
    def _generate_local_tips(self, destination: str, preferences: Dict) -> List[str]:
        """Give them helpful tips for their destination."""
        tips = [
            f"Learn a few basic phrases in the local language of {destination}",
            f"Research local customs and etiquette in {destination}",
            f"Check the weather forecast for {destination} before packing",
            f"Download offline maps for {destination}",
            f"Keep emergency contact numbers for {destination}"
        ]
        return tips
    
    def _generate_weather_info(self, destination: str, preferences: Dict) -> Dict:
        """Give them weather information for their destination."""
        return {
            "current": "Check local weather forecast",
            "best_months": "Research best time to visit",
            "packing_tips": "Pack according to season and activities"
        }
    
    def _generate_best_time_to_visit(self, destination: str, preferences: Dict) -> str:
        """Tell them the best time to visit their destination."""
        return f"Research the best time to visit {destination} based on weather and crowds"
    
    def _generate_budget_estimate(self, preferences: Dict) -> Dict[str, float]:
        """Give them an idea of how much their trip might cost."""
        budget_range = preferences.get("budget_range", "moderate")
        
        # Give them rough estimates based on their budget preference
        if budget_range == "budget":
            return {"min": 50, "max": 150, "currency": "USD"}
        elif budget_range == "luxury":
            return {"min": 300, "max": 1000, "currency": "USD"}
        else:  # moderate budget
            return {"min": 150, "max": 300, "currency": "USD"}
    
    def _generate_itinerary(self, destination: str, duration_days: int, preferences: Dict) -> List[Dict]:
        """Create a sample itinerary for their trip."""
        itinerary = []
        
        # Limit to 7 days maximum so it doesn't get too overwhelming
        max_days = min(duration_days, 7)
        
        # Create a plan for each day
        for day in range(1, max_days + 1):
            day_plan = {
                "day": day,
                "activities": [
                    f"Explore {destination}",
                    f"Visit local attractions in {destination}",
                    f"Enjoy local cuisine in {destination}"
                ]
            }
            itinerary.append(day_plan)
        
        return itinerary
    
    def get_planner_stats(self) -> Dict[str, int]:
        """Just a fun little method to show how many plans we've created."""
        return {
            "plans_created": self.plans_created,
            "total_suggestions_given": self.plans_created * 3  # Rough estimate
        }