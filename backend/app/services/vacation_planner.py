import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class VacationPlanner:
    # Generates vacation suggestions, plans, and summaries.

    def __init__(self):
        self.default_suggestions = [
            "Tell me about your dream destination",
            "What's your budget like?",
            "When do you want to travel?",
            "What kind of activities do you enjoy?"
        ]
        self.plans_created = 0

    def generate_suggestions(self, preferences: Optional[Dict]) -> List[str]:
        if not preferences:
            return list(self.default_suggestions)

        destinations = preferences.get("destinations")
        if not destinations:
            return list(self.default_suggestions)

        if isinstance(destinations, list) and destinations:
            dest = destinations[0]
        else:
            dest = destinations
        dest = dest.strip() if isinstance(dest, str) else str(dest)

        suggestions: List[str] = [f"Tell me more about your plans for {dest}."]
        missing_prompts = [
            ("travel_dates", "When do you want to travel?"),
            ("budget_range", "What's your budget like?"),
            ("travel_style", "What kind of activities do you enjoy?"),
            ("group_size", "How many people are coming with you?"),
            ("interests", "What are you most interested in for this trip?")
        ]

        for field, prompt in missing_prompts:
            if not preferences.get(field):
                suggestions.append(prompt)

        if not suggestions:
            return self.default_suggestions[:3]

        return suggestions[:3]

    def create_vacation_plan(self, preferences: Optional[Dict]) -> Optional[Dict]:
        if not preferences or not preferences.get("destinations"):
            return None

        try:
            destinations = preferences["destinations"]
            if isinstance(destinations, list) and destinations:
                dest = destinations[0]
            else:
                dest = destinations
            dest = dest.strip() if isinstance(dest, str) else str(dest)

            duration_days = 7
            if preferences.get("travel_dates"):
                try:
                    travel_dates = preferences["travel_dates"]
                    start_date = datetime.fromisoformat(travel_dates["start"])
                    end_date = datetime.fromisoformat(travel_dates["end"])
                    if end_date < start_date:
                        start_date, end_date = end_date, start_date
                    duration_days = min((end_date - start_date).days + 1, 30)
                except Exception as date_error:
                    logger.warning(f"Had trouble with their dates: {date_error}")
                    duration_days = 7

            plan = {
                "destination": dest,
                "duration_days": duration_days,
                "estimated_budget": self._generate_budget_estimate(preferences),
                "suggested_activities": self._generate_destination_activities(dest, preferences),
                "accommodation_recommendations": self._generate_accommodation_recommendations(dest, preferences),
                "transportation_options": self._generate_transportation_options(dest, preferences),
                "best_time_to_visit": self._generate_best_time_to_visit(dest, preferences),
                "weather_info": self._generate_weather_info(dest, preferences),
                "local_tips": self._generate_local_tips(dest, preferences),
                "itinerary": self._generate_itinerary(dest, duration_days, preferences)
            }

            self.plans_created += 1

            for field in ["travel_dates", "budget_range", "travel_style", "group_size", "interests"]:
                if preferences.get(field):
                    plan[field] = preferences[field]

            plan["created_at"] = datetime.now().isoformat()
            return plan
        except Exception as e:
            logger.error(f"Something went wrong while creating the vacation plan: {e}")
            return None

    def create_vacation_summary(self, preferences: Optional[Dict]) -> Optional[Dict]:
        if not preferences or not preferences.get("destinations"):
            return None

        try:
            destinations = preferences["destinations"]
            if isinstance(destinations, list) and destinations:
                filtered_destinations = [d for d in destinations if isinstance(d, str) and d.lower().strip() not in {
                    "visit", "go", "travel", "trip", "vacation", "holiday", "journey",
                    "explore", "see", "tour", "plan", "planning", "want", "like", "love"
                }]
                if filtered_destinations:
                    # Prioritize landmarks/monuments, then cities, then countries
                    # Sort by length (shorter = more specific landmark/city, longer = country)
                    # But prefer cities/countries over just landmarks for the primary destination
                    landmark_keywords = {"tower", "palace", "temple", "monument", "museum", "bridge", "cathedral", "mosque"}
                    has_landmark = any(any(kw in d.lower() for kw in landmark_keywords) for d in filtered_destinations)
                    
                    if has_landmark and len(filtered_destinations) > 1:
                        # If we have a landmark + city/country, prefer the city/country for primary, but keep landmark in the list
                        city_country = [d for d in filtered_destinations if not any(kw in d.lower() for kw in landmark_keywords)]
                        if city_country:
                            dest = city_country[0]
                            destination_list = filtered_destinations
                        else:
                            dest = filtered_destinations[0]
                            destination_list = filtered_destinations
                    else:
                        dest = filtered_destinations[0]
                        destination_list = filtered_destinations
                else:
                    # Fallback to first destination if all were filtered
                    dest = destinations[0]
                    destination_list = destinations
            else:
                dest = destinations
                destination_list = [dest]
            dest = dest.strip() if isinstance(dest, str) else str(dest)

            missing_info = []
            if not preferences.get("budget_range"):
                missing_info.append("Budget range")
            if not preferences.get("travel_dates"):
                missing_info.append("Travel dates")
            if not preferences.get("travel_style"):
                missing_info.append("Travel style")
            if not preferences.get("group_size"):
                missing_info.append("Group size")

            completeness = self._calculate_completeness_percentage(preferences)

            summary = {
                "destination": dest,
                "destinations": destination_list,
                "budget_range": preferences.get("budget_range", "Not specified"),
                "completeness_percentage": completeness,
                "missing_info": missing_info,
                "recommendations": self._generate_recommendations(preferences),
                "created_at": datetime.now().isoformat()
            }
            if preferences.get("budget_amount"):
                summary["budget_amount"] = preferences.get("budget_amount")

            for field in ["travel_dates", "travel_style", "group_size", "interests"]:
                if preferences.get(field):
                    summary[field] = preferences[field]

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

    def _calculate_completeness_percentage(self, preferences: Optional[Dict]) -> int:
        if not preferences:
            return 0

        essential_fields = [
            "destinations", "travel_dates", "budget_range",
            "travel_style", "group_size"
        ]
        completed = sum(1 for field in essential_fields if preferences.get(field))
        percentage = (completed / len(essential_fields)) * 100
        return int(percentage)

    def _generate_recommendations(self, preferences: Dict) -> List[str]:
        destinations = preferences.get("destinations") or ["your destination"]
        dest = destinations[0] if isinstance(destinations, list) else destinations
        dest = dest.strip() if isinstance(dest, str) else str(dest)

        travel_style = preferences.get("travel_style") or []
        budget = preferences.get("budget_range", "moderate")

        recommendations: List[str] = []

        if budget == "budget":
            recommendations.append(
                f"For your budget-friendly trip to {dest}, look for free walking tours, street food, and local markets."
            )
        elif budget == "luxury":
            recommendations.append(
                f"For your luxury trip to {dest}, consider private guides, fine dining, and exclusive experiences."
            )
        else:
            recommendations.append(
                f"For your {budget} trip to {dest}, mix famous attractions with local experiences and food tours."
            )

        if travel_style:
            style_lower = [style.lower() for style in travel_style if isinstance(style, str)]
            if "adventure" in style_lower:
                recommendations.append(f"Since you love adventure, plan hikes and outdoor activities in {dest}.")
            elif "relaxation" in style_lower:
                recommendations.append(f"Since relaxation matters, add spa time and scenic strolls in {dest}.")
            elif "food" in style_lower or "foodie" in style_lower:
                recommendations.append(f"As a food lover, try markets, street food, and cooking classes in {dest}.")
            else:
                style_text = ", ".join(travel_style)
                recommendations.append(f"Plan your days in {dest} around your interests: {style_text}.")
        else:
            recommendations.append(f"Plan your days in {dest} around local cuisine, cultural sites, and hidden gems.")

        if preferences.get("travel_dates"):
            recommendations.append(f"Since your dates are set, check the forecast for {dest} and pack accordingly.")
        else:
            recommendations.append(f"Don't forget to research the best time to visit {dest} before choosing dates.")

        group_size = preferences.get("group_size")
        if group_size:
            if group_size == 1:
                recommendations.append(f"As a solo traveler in {dest}, consider group tours or hostels to meet people.")
            elif group_size >= 4:
                recommendations.append(f"With a group of {group_size}, book larger stays and plan shared activities in {dest}.")
            else:
                recommendations.append(f"With {group_size} travelers, keep plans flexible so everyone enjoys {dest}.")

        return [rec for rec in recommendations if len(rec) > 10][:3]

    def _generate_destination_activities(self, destination: str, preferences: Dict) -> List[str]:
        activities: List[str]
        dest_lower = destination.lower()

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
            activities = [
                f"Explore the main attractions in {destination}",
                f"Visit local museums and cultural sites in {destination}",
                f"Try local cuisine in {destination}",
                f"Take a guided tour of {destination}",
                f"Experience local markets in {destination}"
            ]

        return activities[:5]

    def _generate_accommodation_recommendations(self, destination: str, preferences: Dict) -> List[Dict]:
        budget_range = preferences.get("budget_range", "moderate")
        if budget_range == "budget":
            return [
                {"type": "Hostel", "description": f"Budget-friendly hostels in {destination}"},
                {"type": "Guesthouse", "description": f"Local guesthouses in {destination}"},
                {"type": "Budget Hotel", "description": f"Affordable hotels in {destination}"}
            ]
        if budget_range == "luxury":
            return [
                {"type": "Luxury Hotel", "description": f"5-star hotels in {destination}"},
                {"type": "Resort", "description": f"Exclusive resorts in {destination}"},
                {"type": "Boutique Hotel", "description": f"Luxury boutique hotels in {destination}"}
            ]
        return [
            {"type": "Hotel", "description": f"Comfortable hotels in {destination}"},
            {"type": "Apartment", "description": f"Vacation rentals in {destination}"},
            {"type": "B&B", "description": f"Bed and breakfasts in {destination}"}
        ]

    def _generate_transportation_options(self, destination: str, preferences: Dict) -> List[Dict]:
        return [
            {"type": "Public Transit", "description": f"Metro, buses, and trains in {destination}"},
            {"type": "Walking", "description": f"Explore {destination} on foot"},
            {"type": "Bicycle", "description": f"Rent a bike to explore {destination}"},
            {"type": "Taxi/Rideshare", "description": f"Convenient transportation in {destination}"}
        ]

    def _generate_local_tips(self, destination: str, preferences: Dict) -> List[str]:
        return [
            f"Learn a few basic phrases in the local language of {destination}.",
            f"Research local customs and etiquette in {destination}.",
            f"Check the weather forecast for {destination} before packing.",
            f"Download offline maps for {destination} and mark key spots.",
            f"Keep emergency contact numbers handy while traveling in {destination}."
        ]

    def _generate_weather_info(self, destination: str, preferences: Dict) -> Dict:
        return {
            "current": f"Check local weather forecast for {destination} before departure.",
            "best_months": f"Research the best time to visit {destination} for ideal weather.",
            "packing_tips": "Pack layers and comfortable shoes to adapt to activities."
        }

    def _generate_best_time_to_visit(self, destination: str, preferences: Dict) -> str:
        return f"Research the best time to visit {destination} based on weather and local events."

    def _generate_budget_estimate(self, preferences: Dict) -> Dict[str, float]:
        budget_range = preferences.get("budget_range", "moderate")
        if budget_range == "budget":
            return {"min": 50, "max": 150, "currency": "USD"}
        if budget_range == "luxury":
            return {"min": 300, "max": 1000, "currency": "USD"}
        return {"min": 150, "max": 300, "currency": "USD"}

    def _generate_itinerary(self, destination: str, duration_days: int, preferences: Dict) -> List[Dict]:
        itinerary: List[Dict] = []
        max_days = min(max(duration_days, 1), 7)

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
        return {
            "plans_created": self.plans_created,
            "total_suggestions_given": self.plans_created * 3
        }
