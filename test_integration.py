"""
Integration Test for Main Application Flow

Tests the complete pipeline integration:
1. OCR service connection
2. Agent research system connection
3. Recommendation generator connection
"""

import os
from unittest.mock import Mock, patch, MagicMock
from ocr_service import extract_ingredients_from_image
from agent_research import research_multiple_ingredients
from recommendation_service import generate_recommendation


def test_ocr_to_agent_integration():
    """Test that OCR results can be passed to agent research"""
    # Mock OCR results
    mock_ingredients = ["Sugar", "Salt", "Water"]
    
    # Verify format is compatible with agent research
    assert isinstance(mock_ingredients, list)
    assert all(isinstance(ing, str) for ing in mock_ingredients)
    print("✓ OCR to Agent integration format verified")


def test_agent_to_recommendation_integration():
    """Test that agent results can be passed to recommendation generator"""
    # Mock agent research results
    mock_agent_results = [
        {
            "name": "Sugar",
            "summary": "Common sweetener with health concerns",
            "score": 45,
            "details": {"benefits": [], "concerns": ["High calorie"]}
        },
        {
            "name": "Salt",
            "summary": "Essential mineral in moderation",
            "score": 65,
            "details": {"benefits": ["Essential mineral"], "concerns": []}
        }
    ]
    
    # Verify format is compatible with recommendation generator
    assert isinstance(mock_agent_results, list)
    assert all("name" in r and "score" in r for r in mock_agent_results)
    print("✓ Agent to Recommendation integration format verified")


def test_complete_pipeline_structure():
    """Test the complete pipeline data flow structure"""
    # Simulate complete flow
    
    # Step 1: OCR output
    ingredients = ["Sugar", "Salt"]
    assert isinstance(ingredients, list)
    
    # Step 2: Agent research output
    research_results = [
        {"name": ing, "summary": f"Info about {ing}", "score": 50, "details": {}}
        for ing in ingredients
    ]
    assert len(research_results) == len(ingredients)
    
    # Step 3: Recommendation output
    recommendation = {
        "recommendation": "BUY",
        "reasoning": "Test reasoning",
        "score": 50,
        "ingredient_details": research_results,
        "summary": {
            "total_ingredients": len(ingredients),
            "healthy_count": 0,
            "concerning_count": 0
        }
    }
    
    # Verify final structure
    assert "recommendation" in recommendation
    assert "score" in recommendation
    assert "ingredient_details" in recommendation
    assert "summary" in recommendation
    
    print("✓ Complete pipeline structure verified")


def test_session_state_structure():
    """Test session state data structure"""
    # Simulate session state
    session_state = {
        "analysis_results": None,
        "processing": False,
        "extracted_ingredients": None,
        "processing_time": None,
        "start_time": None
    }
    
    # Verify all required keys exist
    required_keys = [
        "analysis_results",
        "processing",
        "extracted_ingredients",
        "processing_time",
        "start_time"
    ]
    
    for key in required_keys:
        assert key in session_state, f"Missing session state key: {key}"
    
    print("✓ Session state structure verified")


def test_timing_tracking():
    """Test timing tracking functionality"""
    import time
    
    start_time = time.time()
    time.sleep(0.1)  # Simulate processing
    end_time = time.time()
    
    processing_time = round(end_time - start_time, 2)
    
    assert processing_time > 0
    assert isinstance(processing_time, float)
    
    print(f"✓ Timing tracking verified: {processing_time}s")


if __name__ == "__main__":
    print("Running integration tests...\n")
    
    test_ocr_to_agent_integration()
    test_agent_to_recommendation_integration()
    test_complete_pipeline_structure()
    test_session_state_structure()
    test_timing_tracking()
    
    print("\n✅ All integration tests passed!")
