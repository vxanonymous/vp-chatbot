"""
Tests for the enhanced preference extraction functions in chat.py.
"""
import pytest
from datetime import datetime
from app.api.chat import _extract_budget_info, _extract_date_info


class TestBudgetExtraction:
    """Test the _extract_budget_info function."""
    
    def test_dollar_amount_extraction(self):
        """Test extraction of dollar amounts."""
        # Test basic dollar amounts
        assert _extract_budget_info("I have a budget of $1000") == {
            "budget_amount": {"max": 1000, "currency": "USD"}
        }
        
        # Test comma-separated amounts
        assert _extract_budget_info("My budget is $1,500") == {
            "budget_amount": {"max": 1500, "currency": "USD"}
        }
        
        # Test decimal amounts
        assert _extract_budget_info("Budget: $2,500.00") == {
            "budget_amount": {"max": 2500, "currency": "USD"}
        }
    
    def test_text_amount_extraction(self):
        """Test extraction of text-based amounts."""
        # Test "dollars" format
        assert _extract_budget_info("I have 1000 dollars") == {
            "budget_amount": {"max": 1000, "currency": "USD"}
        }
        
        # Test "USD" format
        assert _extract_budget_info("Budget is 1500 USD") == {
            "budget_amount": {"max": 1500, "currency": "USD"}
        }
    
    def test_budget_level_extraction(self):
        """Test extraction of budget levels."""
        # Test ultra_budget
        assert _extract_budget_info("I'm on a shoestring budget") == {
            "budget_range": "ultra_budget"
        }
        
        # Test budget
        assert _extract_budget_info("I need something cheap") == {
            "budget_range": "budget"
        }
        
        # Test moderate
        assert _extract_budget_info("I want something comfortable") == {
            "budget_range": "moderate"
        }
        
        # Test luxury
        assert _extract_budget_info("I want luxury accommodations") == {
            "budget_range": "luxury"
        }
    
    def test_combined_budget_extraction(self):
        """Test extraction when both amount and level are present."""
        result = _extract_budget_info("I have $2000 for a luxury trip")
        assert "budget_amount" in result
        assert "budget_range" in result
        assert result["budget_amount"]["max"] == 2000
        assert result["budget_range"] == "luxury"
    
    def test_no_budget_extraction(self):
        """Test when no budget information is present."""
        assert _extract_budget_info("I want to go to Paris") is None
        assert _extract_budget_info("") is None
        assert _extract_budget_info("Just some random text") is None
    
    def test_case_insensitive_extraction(self):
        """Test that extraction works regardless of case."""
        assert _extract_budget_info("BUDGET of $1000") == {
            "budget_amount": {"max": 1000, "currency": "USD"}
        }
        assert _extract_budget_info("LUXURY accommodations") == {
            "budget_range": "luxury"
        }


class TestDateExtraction:
    """Test the _extract_date_info function."""
    
    def test_month_extraction(self):
        """Test extraction of specific months."""
        current_year = datetime.now().year
        
        # Test January
        result = _extract_date_info("I want to travel in January")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-01-01",
                "end": f"{current_year}-01-31"
            }
        }
        
        # Test February (leap year handling)
        result = _extract_date_info("I want to travel in February")
        expected_end = "29" if current_year % 4 == 0 else "28"
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-02-01",
                "end": f"{current_year}-02-{expected_end}"
            }
        }
        
        # Test April (30 days)
        result = _extract_date_info("I want to travel in April")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-04-01",
                "end": f"{current_year}-04-30"
            }
        }
    
    def test_season_extraction(self):
        """Test extraction of seasons."""
        current_year = datetime.now().year
        
        # Test spring
        result = _extract_date_info("I want to travel in spring")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-03-20",
                "end": f"{current_year}-06-20"
            }
        }
        
        # Test summer
        result = _extract_date_info("I want to travel in summer")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-06-21",
                "end": f"{current_year}-09-22"
            }
        }
        
        # Test fall/autumn
        result = _extract_date_info("I want to travel in fall")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-09-23",
                "end": f"{current_year}-12-20"
            }
        }
        
        # Test winter (crosses year boundary)
        result = _extract_date_info("I want to travel in winter")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-12-21",
                "end": f"{current_year + 1}-03-19"
            }
        }
    
    def test_relative_date_extraction(self):
        """Test extraction of relative dates."""
        # Test "next week"
        result = _extract_date_info("I want to travel next week")
        assert "travel_dates" in result
        assert "start" in result["travel_dates"]
        assert "end" in result["travel_dates"]
        
        # Verify it's a 7-day range
        from datetime import datetime
        start_date = datetime.strptime(result["travel_dates"]["start"], "%Y-%m-%d")
        end_date = datetime.strptime(result["travel_dates"]["end"], "%Y-%m-%d")
        assert (end_date - start_date).days == 6  # 7 days total
    
    def test_no_date_extraction(self):
        """Test when no date information is present."""
        assert _extract_date_info("I want to go to Paris") is None
        assert _extract_date_info("") is None
        assert _extract_date_info("Just some random text") is None
    
    def test_case_insensitive_extraction(self):
        """Test that extraction works regardless of case."""
        current_year = datetime.now().year
        
        # Test month case insensitivity
        result = _extract_date_info("I want to travel in JUNE")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-06-01",
                "end": f"{current_year}-06-30"
            }
        }
        
        # Test season case insensitivity
        result = _extract_date_info("I want to travel in SUMMER")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-06-21",
                "end": f"{current_year}-09-22"
            }
        }
    
    def test_priority_extraction(self):
        """Test that month extraction takes priority over season."""
        current_year = datetime.now().year
        
        # When both "June" and "summer" are mentioned, month should take priority
        result = _extract_date_info("I want to travel in June during summer")
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-06-01",
                "end": f"{current_year}-06-30"
            }
        }


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_strings(self):
        """Test handling of empty strings."""
        assert _extract_budget_info("") is None
        assert _extract_date_info("") is None
    
    def test_none_values(self):
        """Test handling of None values."""
        with pytest.raises(TypeError):
            _extract_budget_info(None)
        with pytest.raises(TypeError):
            _extract_date_info(None)
    
    def test_very_long_text(self):
        """Test handling of very long text."""
        long_text = "I want to travel " + "with a budget " * 1000 + "of $1000"
        result = _extract_budget_info(long_text)
        assert result == {
            "budget_amount": {"max": 1000, "currency": "USD"}
        }
    
    def test_special_characters(self):
        """Test handling of special characters."""
        result = _extract_budget_info("Budget: $1,000!@#$%")
        assert result == {
            "budget_amount": {"max": 1000, "currency": "USD"}
        }
        
        result = _extract_date_info("Travel in June!@#$%")
        current_year = datetime.now().year
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-06-01",
                "end": f"{current_year}-06-30"
            }
        }
    
    def test_multiple_matches(self):
        """Test handling of multiple matches."""
        # Multiple budget amounts - should take the first one
        result = _extract_budget_info("I have $1000 but also $2000")
        assert result == {
            "budget_amount": {"max": 1000, "currency": "USD"}
        }
        
        # Multiple months - should take the first one
        result = _extract_date_info("I want to travel in June or July")
        current_year = datetime.now().year
        assert result == {
            "travel_dates": {
                "start": f"{current_year}-06-01",
                "end": f"{current_year}-06-30"
            }
        }


class TestIntegration:
    """Test integration scenarios."""
    
    def test_complete_travel_request(self):
        """Test a complete travel request with both budget and date."""
        text = "I want to go to Paris in June with a budget of $2000"
        
        budget_result = _extract_budget_info(text)
        date_result = _extract_date_info(text)
        
        assert budget_result == {
            "budget_amount": {"max": 2000, "currency": "USD"}
        }
        
        current_year = datetime.now().year
        assert date_result == {
            "travel_dates": {
                "start": f"{current_year}-06-01",
                "end": f"{current_year}-06-30"
            }
        }
    
    def test_realistic_conversation_text(self):
        """Test with realistic conversation text."""
        text = """
        Hi! I'm planning a trip to Europe. I'm thinking about going to Paris 
        in the summer, probably June or July. My budget is around $3000, 
        but I'd like to keep it under $2500 if possible. I'm looking for 
        comfortable accommodations, nothing too fancy but not a hostel either.
        """
        
        budget_result = _extract_budget_info(text)
        date_result = _extract_date_info(text)
        
        # Should extract the first budget amount found
        assert budget_result == {
            "budget_amount": {"max": 3000, "currency": "USD"}
        }
        
        # Should extract the first month mentioned
        current_year = datetime.now().year
        assert date_result == {
            "travel_dates": {
                "start": f"{current_year}-06-01",
                "end": f"{current_year}-06-30"
            }
        } 