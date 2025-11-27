from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class TravelStyle(str, Enum):
    # ADVENTURE = "adventure"
    # RELAXATION = "relaxation"
    # CULTURAL = "cultural"
    # FAMILY = "family"
    # ROMANTIC = "romantic"
    # BUSINESS = "business"
    # FOODIE = "foodie"
    # s BudgetRange(str, Enum):
    # """Budget range options for vacation planning.
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"


class VacationPreferences(BaseModel):
    # destinations: Optional[List[str]] = []
    # travel_dates: Optional[Dict[str, date]] = None
    # budget_range: Optional[BudgetRange] = None
    # travel_style: Optional[List[TravelStyle]] = []
    # group_size: Optional[int] = None
    # interests: Optional[List[str]] = []
    # dietary_restrictions: Optional[List[str]] = []
    # accessibility_needs: Optional[List[str]] = []
    # s VacationPlan(BaseModel):
    # """Complete vacation plan with recommendations and details.
    destination: str
    duration_days: int
    estimated_budget: Dict[str, float]
    suggested_activities: List[str]
    accommodation_recommendations: List[Dict]
    transportation_options: List[Dict]
    best_time_to_visit: str
    weather_info: Dict
    local_tips: List[str]
    itinerary: Optional[List[Dict]] = None