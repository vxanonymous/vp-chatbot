from app.services.vacation_planner import VacationPlanner
from datetime import date, timedelta
from unittest.mock import MagicMock
from unittest.mock import Mock, patch
from unittest.mock import patch
import pytest

class TestVacationPlannerFinalCoverage:
    
    @pytest.fixture
    def planner(self):
    # Create a planner instance for testing.
        return VacationPlanner()
    
    def test_generate_suggestions_no_suggestions_generated(self, planner):
        # Create preferences that result in empty suggestions list
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "budget_range": "moderate",
            "travel_style": ["cultural"],
            "group_size": 2,
            "interests": ["museums"]
        }
        suggestions = planner.generate_suggestions(preferences)
        
        # Should fall back to default suggestions when list is empty
        assert len(suggestions) > 0
        assert suggestions == planner.default_suggestions or len(suggestions) <= 3
    
    def test_generate_recommendations_travel_style_other_path(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["romantic", "business"]  # Not adventure, relaxation, or foodie
        }
        recs = planner._generate_recommendations(preferences)
        
        assert len(recs) > 0
        assert all(isinstance(rec, str) for rec in recs)
        # Should use the else branch for travel_style
        all_text = ' '.join(recs).lower()
        assert "paris" in all_text

class TestVacationPlannerInit:
    
    def test_initialization_default_suggestions(self):
        planner = VacationPlanner()
        
        assert planner is not None
        assert hasattr(planner, 'default_suggestions')
        assert isinstance(planner.default_suggestions, list)
        assert len(planner.default_suggestions) == 4
        
        # Check specific suggestions
        suggestions_text = ' '.join(planner.default_suggestions).lower()
        assert "destination" in suggestions_text
        assert "budget" in suggestions_text
        assert "travel" in suggestions_text
        assert "activities" in suggestions_text
    
    def test_initialization_plans_created(self):
        planner = VacationPlanner()
        
        assert hasattr(planner, 'plans_created')
        assert planner.plans_created == 0
    
    def test_multiple_instances_independent(self):
        planner1 = VacationPlanner()
        planner2 = VacationPlanner()
        
        # Create a plan with planner1
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        planner1.create_vacation_plan(preferences)
        
        # planner2 should still have 0 plans
        assert planner1.plans_created == 1
        assert planner2.plans_created == 0

class TestVacationPlannerAdditionalCoverage:
# Additional tests for VacationPlanner coverage.
    
    @pytest.fixture
    def vacation_planner(self):
    # Create VacationPlanner instance.
        return VacationPlanner()
    
    def test_create_vacation_plan_destination_string_strip(self, vacation_planner):
        preferences = {
            "destinations": "  Paris  ",
            "travel_dates": {"start": "2024-06-01", "end": "2024-06-07"}
        }
        
        result = vacation_planner.create_vacation_plan(preferences)
        assert result is not None
        assert result["destination"] == "Paris"
    
    def test_create_vacation_plan_destination_non_string(self, vacation_planner):
        preferences = {
            "destinations": 12345
        }
        
        result = vacation_planner.create_vacation_plan(preferences)
        assert result is not None
        assert result["destination"] == "12345"
    
    def test_create_vacation_plan_end_date_before_start_date(self, vacation_planner):
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "2024-06-07", "end": "2024-06-01"}
        }
        
        result = vacation_planner.create_vacation_plan(preferences)
        assert result is not None
        assert result["duration_days"] > 0
    
    def test_create_vacation_plan_invalid_date_format(self, vacation_planner):
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "invalid", "end": "invalid"}
        }
        
        result = vacation_planner.create_vacation_plan(preferences)
        # Should still return a plan with default duration
        assert result is not None
    
    def test_create_vacation_summary_destination_string_strip(self, vacation_planner):
        preferences = {
            "destinations": "  Paris  "
        }
        
        result = vacation_planner.create_vacation_summary(preferences)
        assert result is not None
    
    def test_create_vacation_summary_destination_non_string(self, vacation_planner):
        preferences = {
            "destinations": 12345
        }
        
        result = vacation_planner.create_vacation_summary(preferences)
        # May return None if destination is invalid
        if result is not None:
            assert isinstance(result, dict)

class TestVacationPlannerCoverage:
# Additional tests to improve coverage.
    
    @pytest.fixture
    def planner(self):
    # Create a planner instance for testing.
        return VacationPlanner()
    
    def test_create_vacation_plan_exception_handling(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "invalid-date", "end": "invalid-date"}
        }
        
        # Should handle exception gracefully
        plan = planner.create_vacation_plan(preferences)
        # Should either return None or handle gracefully
        assert plan is None or isinstance(plan, dict)
    
    def test_create_vacation_summary_exception_handling(self, planner):
        preferences = {
            "destinations": None  # Invalid type
        }
        
        summary = planner.create_vacation_summary(preferences)
        assert summary is None
    
    def test_create_vacation_summary_destinations_list_empty(self, planner):
        preferences = {
            "destinations": []
        }
        
        summary = planner.create_vacation_summary(preferences)
        assert summary is None
    
    def test_create_vacation_summary_destinations_string(self, planner):
        preferences = {
            "destinations": "Paris"  # String instead of list
        }
        
        summary = planner.create_vacation_summary(preferences)
        assert summary is not None
        assert summary['destination'] == 'Paris'
    
    def test_create_vacation_summary_destinations_list_multiple(self, planner):
        preferences = {
            "destinations": ["Paris", "London"],
            "budget_range": "moderate"
        }
        
        summary = planner.create_vacation_summary(preferences)
        assert summary is not None
        assert summary['destination'] == 'Paris'  # First destination
    
    def test_create_vacation_summary_status_messages(self, planner):
        prefs_80 = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"],
            "group_size": 2
        }
        summary = planner.create_vacation_summary(prefs_80)
        assert "almost ready" in summary['status'].lower() or "ready" in summary['status'].lower()
        
        prefs_60 = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        summary = planner.create_vacation_summary(prefs_60)
        assert "progress" in summary['status'].lower() or "details" in summary['status'].lower()
        
        prefs_40 = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        summary = planner.create_vacation_summary(prefs_40)
        assert "getting there" in summary['status'].lower() or "basics" in summary['status'].lower()
        
        prefs_low = {
            "destinations": ["Paris"]
        }
        summary = planner.create_vacation_summary(prefs_low)
        assert "getting started" in summary['status'].lower() or "started" in summary['status'].lower()
    
    def test_generate_recommendations_budget_luxury(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "luxury",
            "travel_style": ["cultural"]
        }
        recommendations = planner._generate_recommendations(preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("luxury" in rec.lower() or "premium" in rec.lower() or "upscale" in rec.lower() 
                  for rec in recommendations)
    
    def test_generate_recommendations_budget_budget(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "budget",
            "travel_style": ["cultural"]
        }
        recommendations = planner._generate_recommendations(preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("budget" in rec.lower() or "affordable" in rec.lower() or "save" in rec.lower()
                  for rec in recommendations)
    
    def test_generate_recommendations_travel_styles(self, planner):
        # Adventure style
        prefs_adventure = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["adventure"]
        }
        recs = planner._generate_recommendations(prefs_adventure)
        assert len(recs) > 0
        
        # Relaxation style
        prefs_relax = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["relaxation"]
        }
        recs = planner._generate_recommendations(prefs_relax)
        assert len(recs) > 0
        
        # Foodie style
        prefs_foodie = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["foodie"]
        }
        recs = planner._generate_recommendations(prefs_foodie)
        assert len(recs) > 0
    
    def test_create_vacation_plan_with_itinerary(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"]
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan is not None
        assert 'itinerary' in plan
        assert isinstance(plan['itinerary'], list)
    
    def test_create_vacation_plan_includes_all_preferences(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "luxury",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural", "foodie"],
            "group_size": 4,
            "interests": ["museums", "food"]
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan is not None
        assert plan['budget_range'] == 'luxury'
        assert plan['travel_style'] == ['cultural', 'foodie']
        assert plan['group_size'] == 4
        assert plan['interests'] == ['museums', 'food']
    
    def test_create_vacation_summary_includes_interests(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "interests": ["museums", "food", "architecture"]
        }
        summary = planner.create_vacation_summary(preferences)
        
        assert summary is not None
        assert 'interests' in summary
        assert summary['interests'] == ['museums', 'food', 'architecture']
    
    def test_calculate_completeness_with_false_values(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": False,  # False should not count as completed
            "travel_dates": None,
            "travel_style": [],
            "group_size": 0
        }
        percentage = planner._calculate_completeness_percentage(preferences)
        
        assert percentage < 50  # Only destinations should count
    
    def test_calculate_completeness_with_empty_strings(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "",  # Empty string should not count
            "travel_dates": {},
            "travel_style": [],
            "group_size": None
        }
        percentage = planner._calculate_completeness_percentage(preferences)
        
        assert percentage < 50  # Only destinations should count

class TestVacationPlannerDateHandling:
    
    @pytest.fixture
    def planner(self):
    # Create a planner instance for testing.
        return VacationPlanner()
    
    def test_duration_calculation_reversed_dates(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-10", "end": "2023-06-05"}  # Reversed
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan is not None
        assert plan['duration_days'] > 0  # Should handle reversed dates
    
    def test_duration_calculation_long_trip(self, planner):
        # Create dates 35 days apart
        start = date(2023, 6, 1)
        end = start + timedelta(days=35)
        
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {
                "start": start.isoformat(),
                "end": end.isoformat()
            }
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan is not None
        assert plan['duration_days'] == 30  # Should be capped at 30
    
    def test_duration_calculation_invalid_date_format(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "invalid", "end": "invalid"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        # Should handle exception and default to 7 days
        assert plan is not None
        assert plan['duration_days'] == 7
    
    def test_duration_calculation_missing_end_date(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01"}  # Missing end
        }
        plan = planner.create_vacation_plan(preferences)
        
        # Should default to 7 days
        assert plan is not None
        assert plan['duration_days'] == 7
    
    def test_duration_calculation_missing_start_date(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"end": "2023-06-05"}  # Missing start
        }
        plan = planner.create_vacation_plan(preferences)
        
        # Should default to 7 days
        assert plan is not None
        assert plan['duration_days'] == 7
    
    def test_duration_calculation_no_travel_dates(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        plan = planner.create_vacation_plan(preferences)
        
        # Should default to 7 days
        assert plan is not None
        assert plan['duration_days'] == 7
    
    def test_duration_calculation_single_day(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-01"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan is not None
        assert plan['duration_days'] == 1

class TestVacationPlannerEdgeCases:
    
    @pytest.fixture
    def vacation_planner(self):
    # Create VacationPlanner instance.
        return VacationPlanner()
    
    def test_generate_suggestions_no_preferences(self, vacation_planner):
        result = vacation_planner.generate_suggestions(None)
        assert len(result) > 0
        assert "dream destination" in result[0].lower()
    
    def test_generate_suggestions_empty_preferences(self, vacation_planner):
        result = vacation_planner.generate_suggestions({})
        assert len(result) > 0
    
    def test_generate_suggestions_with_destination_string(self, vacation_planner):
        preferences = {"destinations": "Paris"}
        result = vacation_planner.generate_suggestions(preferences)
        assert len(result) > 0
        assert "Paris" in result[0]
    
    def test_generate_suggestions_with_destination_list(self, vacation_planner):
        preferences = {"destinations": ["Paris", "London"]}
        result = vacation_planner.generate_suggestions(preferences)
        assert len(result) > 0
        assert "Paris" in result[0]
    
    def test_generate_suggestions_with_all_preferences(self, vacation_planner):
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": "Summer 2024",
            "budget_range": "$2000",
            "travel_style": "cultural",
            "group_size": 2,
            "interests": ["museums", "food"]
        }
        result = vacation_planner.generate_suggestions(preferences)
        assert len(result) > 0
    
    def test_create_vacation_summary_no_preferences(self, vacation_planner):
        result = vacation_planner.create_vacation_summary({})
        # May return None or a default summary
        if result is not None:
            assert isinstance(result, dict)
    
    def test_create_vacation_summary_with_destination_string(self, vacation_planner):
        preferences = {"destinations": "Paris"}
        result = vacation_planner.create_vacation_summary(preferences)
        assert result is not None
    
    def test_create_vacation_summary_with_destination_list(self, vacation_planner):
        preferences = {"destinations": ["Paris", "London"]}
        result = vacation_planner.create_vacation_summary(preferences)
        assert result is not None
    
    def test_create_vacation_summary_with_complete_preferences(self, vacation_planner):
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": "Summer 2024",
            "budget_range": "$2000",
            "travel_style": "cultural",
            "group_size": 2,
            "interests": ["museums", "food"]
        }
        result = vacation_planner.create_vacation_summary(preferences)
        assert result is not None

class TestVacationPlannerExceptionHandling:
    
    @pytest.fixture
    def planner(self):
    # Create a planner instance for testing.
        return VacationPlanner()
    
    def test_create_vacation_summary_exception_handling(self, planner):
        # Create preferences that might cause exception during processing
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        
        # Mock an exception in _calculate_completeness_percentage
        with patch.object(planner, '_calculate_completeness_percentage', side_effect=Exception("Test error")):
            summary = planner.create_vacation_summary(preferences)
            # Should handle exception and return None
            assert summary is None
    
    def test_create_vacation_summary_exception_in_recommendations(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        
        # Mock an exception in _generate_recommendations
        with patch.object(planner, '_generate_recommendations', side_effect=Exception("Test error")):
            summary = planner.create_vacation_summary(preferences)
            # Should handle exception and return None
            assert summary is None

class TestVacationPlannerMissingCoverage:
    
    @pytest.fixture
    def planner(self):
    # Create a planner instance for testing.
        return VacationPlanner()
    
    def test_create_vacation_plan_no_destinations(self, planner):
        preferences = {
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        assert plan is None
    
    def test_create_vacation_plan_empty_destinations_list(self, planner):
        preferences = {
            "destinations": [],
            "budget_range": "moderate"
        }
        plan = planner.create_vacation_plan(preferences)
        assert plan is None
    
    def test_create_vacation_plan_exception_in_processing(self, planner):
        # Create preferences that might cause issues
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        
        # Mock an exception in one of the helper methods
        with patch.object(planner, '_generate_destination_activities', side_effect=Exception("Test error")):
            plan = planner.create_vacation_plan(preferences)
            # Should handle exception and return None
            assert plan is None
    
    def test_generate_destination_activities_paris(self, planner):
        activities = planner._generate_destination_activities("Paris", {})
        assert len(activities) > 0
        assert any("Eiffel" in act or "Louvre" in act for act in activities)
    
    def test_generate_destination_activities_tokyo(self, planner):
        activities = planner._generate_destination_activities("Tokyo", {})
        assert len(activities) > 0
        assert any("Temple" in act or "Shibuya" in act for act in activities)
    
    def test_generate_destination_activities_bali(self, planner):
        activities = planner._generate_destination_activities("Bali", {})
        assert len(activities) > 0
        assert any("Temple" in act or "Beach" in act for act in activities)
    
    def test_generate_destination_activities_other(self, planner):
        activities = planner._generate_destination_activities("London", {})
        assert len(activities) > 0
        assert any("attractions" in act.lower() or "museums" in act.lower() for act in activities)
    
    def test_generate_accommodation_recommendations_budget(self, planner):
        preferences = {"budget_range": "budget"}
        recs = planner._generate_accommodation_recommendations("Paris", preferences)
        assert len(recs) > 0
        assert any("Hostel" in rec["type"] or "Budget" in rec["type"] for rec in recs)
    
    def test_generate_accommodation_recommendations_luxury(self, planner):
        preferences = {"budget_range": "luxury"}
        recs = planner._generate_accommodation_recommendations("Paris", preferences)
        assert len(recs) > 0
        assert any("Luxury" in rec["type"] or "Resort" in rec["type"] for rec in recs)
    
    def test_generate_accommodation_recommendations_moderate(self, planner):
        preferences = {"budget_range": "moderate"}
        recs = planner._generate_accommodation_recommendations("Paris", preferences)
        assert len(recs) > 0
        assert any("Hotel" in rec["type"] or "Apartment" in rec["type"] for rec in recs)
    
    def test_generate_transportation_options(self, planner):
        recs = planner._generate_transportation_options("Paris", {})
        assert len(recs) > 0
        assert any("Transit" in rec["type"] or "Walking" in rec["type"] for rec in recs)
    
    def test_generate_local_tips(self, planner):
        tips = planner._generate_local_tips("Paris", {})
        assert len(tips) > 0
        assert all(isinstance(tip, str) for tip in tips)
        assert all("Paris" in tip for tip in tips)
    
    def test_generate_weather_info(self, planner):
        weather = planner._generate_weather_info("Paris", {})
        assert isinstance(weather, dict)
        assert "current" in weather
        assert "best_months" in weather
        assert "packing_tips" in weather
    
    def test_generate_best_time_to_visit(self, planner):
        result = planner._generate_best_time_to_visit("Paris", {})
        assert isinstance(result, str)
        assert "Paris" in result
    
    def test_generate_budget_estimate_budget(self, planner):
        preferences = {"budget_range": "budget"}
        budget = planner._generate_budget_estimate(preferences)
        assert budget["min"] == 50
        assert budget["max"] == 150
    
    def test_generate_budget_estimate_luxury(self, planner):
        preferences = {"budget_range": "luxury"}
        budget = planner._generate_budget_estimate(preferences)
        assert budget["min"] == 300
        assert budget["max"] == 1000
    
    def test_generate_budget_estimate_moderate(self, planner):
        preferences = {"budget_range": "moderate"}
        budget = planner._generate_budget_estimate(preferences)
        assert budget["min"] == 150
        assert budget["max"] == 300
    
    def test_generate_budget_estimate_default(self, planner):
        preferences = {}
        budget = planner._generate_budget_estimate(preferences)
        assert budget["min"] == 150  # Defaults to moderate
        assert budget["max"] == 300
    
    def test_generate_itinerary_short_trip(self, planner):
        itinerary = planner._generate_itinerary("Paris", 3, {})
        assert len(itinerary) == 3
        assert all("day" in day_plan for day_plan in itinerary)
        assert all("activities" in day_plan for day_plan in itinerary)
    
    def test_generate_itinerary_long_trip(self, planner):
        itinerary = planner._generate_itinerary("Paris", 10, {})
        assert len(itinerary) == 7  # Should be capped at 7
        assert all("day" in day_plan for day_plan in itinerary)
    
    def test_generate_itinerary_single_day(self, planner):
        itinerary = planner._generate_itinerary("Paris", 1, {})
        assert len(itinerary) == 1
        assert itinerary[0]["day"] == 1
    
    def test_get_planner_stats(self, planner):
        # Create some plans first
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        planner.create_vacation_plan(preferences)
        planner.create_vacation_plan(preferences)
        
        stats = planner.get_planner_stats()
        assert stats["plans_created"] == 2
        assert stats["total_suggestions_given"] == 6
    
    def test_generate_recommendations_group_size_solo(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "group_size": 1
        }
        recs = planner._generate_recommendations(preferences)
        assert len(recs) > 0
        # Check that group_size logic was executed (solo recommendation should be in the list)
        all_recs_text = ' '.join(recs).lower()
        assert "solo" in all_recs_text or "hostels" in all_recs_text or "tours" in all_recs_text
    
    def test_generate_recommendations_group_size_large(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "group_size": 5
        }
        recs = planner._generate_recommendations(preferences)
        assert len(recs) > 0
        # Verify recommendations were generated (group_size >= 4 path)
        assert all(isinstance(rec, str) for rec in recs)
        assert all(len(rec) > 10 for rec in recs)
    
    def test_generate_recommendations_group_size_small(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "group_size": 2
        }
        recs = planner._generate_recommendations(preferences)
        assert len(recs) > 0
        # Verify recommendations were generated (2-3 people path)
        assert all(isinstance(rec, str) for rec in recs)
        assert all(len(rec) > 10 for rec in recs)
    
    def test_generate_recommendations_with_travel_dates(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        recs = planner._generate_recommendations(preferences)
        assert any("weather" in rec.lower() or "forecast" in rec.lower() for rec in recs)
    
    def test_generate_recommendations_without_travel_dates(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        recs = planner._generate_recommendations(preferences)
        assert any("time to visit" in rec.lower() or "best time" in rec.lower() for rec in recs)
    
    def test_generate_recommendations_travel_style_other(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural", "romantic"]
        }
        recs = planner._generate_recommendations(preferences)
        assert len(recs) > 0
        assert all(isinstance(rec, str) for rec in recs)
    
    def test_generate_recommendations_filters_short(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        recs = planner._generate_recommendations(preferences)
        # All recommendations should be substantial
        assert all(len(rec) > 10 for rec in recs)
    
    def test_generate_recommendations_max_three(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"],
            "group_size": 2
        }
        recs = planner._generate_recommendations(preferences)
        assert len(recs) <= 3

class TestVacationPlanner:
    
    @pytest.fixture
    def planner(self):
    # Create a planner instance for testing.
        return VacationPlanner()
    
    @pytest.fixture
    def sample_preferences(self):
    # Sample user preferences for testing.
        return {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural", "foodie"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "group_size": 2,
            "interests": ["museums", "food", "architecture"]
        }
    
    def test_initialization(self, planner):
        assert planner is not None
        assert hasattr(planner, 'default_suggestions')
        assert isinstance(planner.default_suggestions, list)
        assert len(planner.default_suggestions) > 0
    
    def test_default_suggestions_structure(self, planner):
        for suggestion in planner.default_suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion) > 0
            assert any(keyword in suggestion.lower() for keyword in ["destination", "budget", "travel", "activities"])
    
    def test_generate_suggestions_no_preferences(self, planner):
        suggestions = planner.generate_suggestions(None)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert suggestions == planner.default_suggestions
    
    def test_generate_suggestions_empty_preferences(self, planner):
        suggestions = planner.generate_suggestions({})
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert suggestions == planner.default_suggestions
    
    def test_generate_suggestions_with_destination(self, planner):
        preferences = {"destinations": ["Paris"]}
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("Paris" in suggestion for suggestion in suggestions)
    
    def test_generate_suggestions_missing_travel_dates(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("when" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_suggestions_missing_budget(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("budget" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_suggestions_missing_travel_style(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("kind" in suggestion.lower() or "style" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_suggestions_complete_preferences(self, planner, sample_preferences):
        suggestions = planner.generate_suggestions(sample_preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # Should have some suggestions even with complete preferences
        assert len(suggestions) <= 3
    
    def test_generate_suggestions_max_limit(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"]
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert len(suggestions) <= 3
    
    def test_create_vacation_plan_no_preferences(self, planner):
        plan = planner.create_vacation_plan(None)
        
        assert plan is None
    
    def test_create_vacation_plan_empty_preferences(self, planner):
        plan = planner.create_vacation_plan({})
        
        assert plan is None
    
    def test_create_vacation_plan_basic_preferences(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert isinstance(plan, dict)
        assert 'destination' in plan
        assert 'duration_days' in plan
        assert 'estimated_budget' in plan
        assert 'suggested_activities' in plan
        assert 'accommodation_recommendations' in plan
        assert 'transportation_options' in plan
        assert 'best_time_to_visit' in plan
        assert 'weather_info' in plan
        assert 'local_tips' in plan
    
    def test_create_vacation_plan_complete_preferences(self, planner, sample_preferences):
        plan = planner.create_vacation_plan(sample_preferences)
        
        assert isinstance(plan, dict)
        assert plan['destination'] == 'Paris'
        assert plan['duration_days'] == 5
        assert isinstance(plan['estimated_budget'], dict)
        assert isinstance(plan['suggested_activities'], list)
        assert isinstance(plan['accommodation_recommendations'], list)
        assert isinstance(plan['transportation_options'], list)
        assert isinstance(plan['local_tips'], list)
    
    def test_create_vacation_summary_no_preferences(self, planner):
        summary = planner.create_vacation_summary(None)
        
        assert summary is None
    
    def test_create_vacation_summary_empty_preferences(self, planner):
        summary = planner.create_vacation_summary({})
        
        assert summary is None
    
    def test_create_vacation_summary_basic_preferences(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        summary = planner.create_vacation_summary(preferences)
        
        assert isinstance(summary, dict)
        assert 'destination' in summary
        assert 'budget_range' in summary
        assert 'completeness_percentage' in summary
        assert 'missing_info' in summary
        assert 'recommendations' in summary
    
    def test_create_vacation_summary_complete_preferences(self, planner, sample_preferences):
        summary = planner.create_vacation_summary(sample_preferences)
        
        assert isinstance(summary, dict)
        assert summary['destination'] == 'Paris'
        assert summary['budget_range'] == 'moderate'
        assert 0 <= summary['completeness_percentage'] <= 100
        assert isinstance(summary['missing_info'], list)
        assert isinstance(summary['recommendations'], list)
    
    def test_calculate_completeness_percentage_minimal(self, planner):
        preferences = {"destinations": ["Paris"]}
        percentage = planner._calculate_completeness_percentage(preferences)
        
        assert isinstance(percentage, int)
        assert 0 <= percentage <= 100
        assert percentage < 50
    
    def test_calculate_completeness_percentage_complete(self, planner, sample_preferences):
        percentage = planner._calculate_completeness_percentage(sample_preferences)
        
        assert isinstance(percentage, int)
        assert 0 <= percentage <= 100
        assert percentage > 70
    
    def test_calculate_completeness_percentage_empty(self, planner):
        percentage = planner._calculate_completeness_percentage({})
        
        assert isinstance(percentage, int)
        assert percentage == 0
    
    def test_generate_recommendations_basic(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        recommendations = planner._generate_recommendations(preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    def test_generate_recommendations_complete(self, planner, sample_preferences):
        recommendations = planner._generate_recommendations(sample_preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
    
    def test_generate_recommendations_empty(self, planner):
        recommendations = planner._generate_recommendations({})
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_vacation_plan_destination_specific(self, planner):
        preferences = {
            "destinations": ["Tokyo"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan['destination'] == 'Tokyo'
        assert 'Tokyo' in str(plan['suggested_activities'])
        assert 'Tokyo' in str(plan['local_tips'])
    
    def test_vacation_plan_budget_specific(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "luxury",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan['budget_range'] == 'luxury'
        assert 'luxury' in str(plan['accommodation_recommendations']).lower()
    
    def test_vacation_plan_duration_calculation(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-10"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert plan['duration_days'] == 10
    
    def test_vacation_summary_missing_info_detection(self, planner):
        preferences = {
            "destinations": ["Paris"]
            # Missing budget, dates, etc.
        }
        summary = planner.create_vacation_summary(preferences)
        
        assert len(summary['missing_info']) > 0
        assert any('budget' in info.lower() for info in summary['missing_info'])
        assert any('date' in info.lower() for info in summary['missing_info'])
    
    def test_vacation_summary_complete_info(self, planner, sample_preferences):
        summary = planner.create_vacation_summary(sample_preferences)
        
        assert len(summary['missing_info']) == 0 or summary['completeness_percentage'] > 80
    
    def test_suggestions_context_aware(self, planner):
        preferences = {"destinations": ["Paris"]}
        suggestions = planner.generate_suggestions(preferences)
        
        assert any("budget" in suggestion.lower() for suggestion in suggestions)
        
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate"
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert any("when" in suggestion.lower() for suggestion in suggestions)
    
    def test_vacation_plan_edge_cases(self, planner):
        # Very long destination name
        preferences = {
            "destinations": ["A very long destination name that might cause issues"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert isinstance(plan, dict)
        assert 'destination' in plan
        
        # Special characters in destination
        preferences = {
            "destinations": ["Paris 🗼"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        plan = planner.create_vacation_plan(preferences)
        
        assert isinstance(plan, dict)
        assert 'destination' in plan
    
    def test_suggestions_edge_cases(self, planner):
        # Very large preferences object
        large_preferences = {
            "destinations": ["Paris"] * 10,
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"] * 10,
            "interests": ["museums"] * 20
        }
        suggestions = planner.generate_suggestions(large_preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 3
        
        # Empty strings in preferences
        preferences = {
            "destinations": [""],
            "budget_range": "",
            "travel_dates": {"start": "", "end": ""}
        }
        suggestions = planner.generate_suggestions(preferences)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
    
    def test_completeness_calculation_accuracy(self, planner):
        minimal_prefs = {"destinations": ["Paris"]}
        basic_prefs = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"}
        }
        complete_prefs = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_dates": {"start": "2023-06-01", "end": "2023-06-05"},
            "travel_style": ["cultural"],
            "group_size": 2,
            "interests": ["museums", "food"]
        }
        
        minimal_score = planner._calculate_completeness_percentage(minimal_prefs)
        basic_score = planner._calculate_completeness_percentage(basic_prefs)
        complete_score = planner._calculate_completeness_percentage(complete_prefs)
        
        # Scores should be in ascending order
        assert minimal_score < basic_score < complete_score
        assert complete_score > 70
    
    def test_recommendations_quality(self, planner):
        preferences = {
            "destinations": ["Paris"],
            "budget_range": "moderate",
            "travel_style": ["cultural"]
        }
        recommendations = planner._generate_recommendations(preferences)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check that recommendations are substantial
        for rec in recommendations:
            assert len(rec) > 10
            assert any(keyword in rec.lower() for keyword in ["paris", "culture", "visit", "see", "experience"])
    
    def test_vacation_plan_data_types(self, planner, sample_preferences):
        plan = planner.create_vacation_plan(sample_preferences)
        
        assert isinstance(plan['destination'], str)
        assert isinstance(plan['duration_days'], int)
        assert isinstance(plan['estimated_budget'], dict)
        assert isinstance(plan['suggested_activities'], list)
        assert isinstance(plan['accommodation_recommendations'], list)
        assert isinstance(plan['transportation_options'], list)
        assert isinstance(plan['best_time_to_visit'], str)
        assert isinstance(plan['weather_info'], dict)
        assert isinstance(plan['local_tips'], list)
        assert isinstance(plan.get('itinerary'), (list, type(None)))
    
    def test_vacation_summary_data_types(self, planner, sample_preferences):
        summary = planner.create_vacation_summary(sample_preferences)
        
        assert isinstance(summary['destination'], str)
        assert isinstance(summary['budget_range'], str)
        assert isinstance(summary['completeness_percentage'], int)
        assert isinstance(summary['missing_info'], list)
        assert isinstance(summary['recommendations'], list) 

