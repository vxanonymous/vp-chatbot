from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date
from enum import Enum


class TravelStyle(str, Enum):
    """Travel style preferences for vacation planning."""
    ADVENTURE = "adventure"
    RELAXATION = "relaxation"
    CULTURAL = "cultural"
    FAMILY = "family"
    ROMANTIC = "romantic"
    BUSINESS = "business"
    FOODIE = "foodie"


class BudgetRange(str, Enum):
    """Budget range options for vacation planning."""
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"


class VacationPreferences(BaseModel):
    """User preferences for vacation planning."""
    destinations: Optional[List[str]] = []
    travel_dates: Optional[Dict[str, date]] = None
    budget_range: Optional[BudgetRange] = None
    travel_style: Optional[List[TravelStyle]] = []
    group_size: Optional[int] = None
    interests: Optional[List[str]] = []
    dietary_restrictions: Optional[List[str]] = []
    accessibility_needs: Optional[List[str]] = []


class VacationPlan(BaseModel):
    """Complete vacation plan with recommendations and details."""
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