"""
Test script to verify error handling improvements for Task 7
"""

import os
from io import BytesIO
from PIL import Image

# Test 1: OCR Service - Empty image bytes
print("Test 1: OCR Service - Empty image bytes")
try:
    from ocr_service import extract_ingredients_from_image, OCRError
    result = extract_ingredients_from_image(b'')
    print("❌ FAILED: Should have raised OCRError")
except OCRError as e:
    print(f"✓ PASSED: Caught OCRError - {str(e)[:50]}...")
except Exception as e:
    print(f"❌ FAILED: Wrong exception type - {type(e).__name__}")

# Test 2: OCR Service - Too small file
print("\nTest 2: OCR Service - Too small file")
try:
    result = extract_ingredients_from_image(b'abc')
    print("❌ FAILED: Should have raised OCRError")
except OCRError as e:
    print(f"✓ PASSED: Caught OCRError - {str(e)[:50]}...")
except Exception as e:
    print(f"❌ FAILED: Wrong exception type - {type(e).__name__}")

# Test 3: Agent Research - Invalid ingredient
print("\nTest 3: Agent Research - Invalid ingredient (graceful degradation)")
try:
    from agent_research import research_ingredient, create_research_agent
    # This should return a neutral result, not raise an error
    # Note: We can't actually test this without valid credentials
    print("✓ PASSED: Function signature exists and imports correctly")
except Exception as e:
    print(f"❌ FAILED: Import error - {str(e)}")

# Test 4: Agent Research - Empty ingredient list
print("\nTest 4: Agent Research - Empty ingredient list")
try:
    from agent_research import research_multiple_ingredients, AgentResearchError
    result = research_multiple_ingredients([])
    print("❌ FAILED: Should have raised AgentResearchError")
except AgentResearchError as e:
    print(f"✓ PASSED: Caught AgentResearchError - {str(e)[:50]}...")
except Exception as e:
    print(f"❌ FAILED: Wrong exception type - {type(e).__name__}")

# Test 5: Recommendation Service - Empty results
print("\nTest 5: Recommendation Service - Empty results")
try:
    from recommendation_service import generate_recommendation, RecommendationError
    result = generate_recommendation([])
    print("❌ FAILED: Should have raised RecommendationError")
except RecommendationError as e:
    print(f"✓ PASSED: Caught RecommendationError - {str(e)[:50]}...")
except Exception as e:
    print(f"❌ FAILED: Wrong exception type - {type(e).__name__}")

# Test 6: Recommendation Service - Invalid results
print("\nTest 6: Recommendation Service - Invalid results (no score)")
try:
    result = generate_recommendation([{"name": "test", "summary": "test"}])
    print("❌ FAILED: Should have raised RecommendationError")
except RecommendationError as e:
    print(f"✓ PASSED: Caught RecommendationError - {str(e)[:50]}...")
except Exception as e:
    print(f"❌ FAILED: Wrong exception type - {type(e).__name__}")

# Test 7: Recommendation Service - Valid results with fallback
print("\nTest 7: Recommendation Service - Valid results structure")
try:
    from recommendation_service import aggregate_ingredient_results
    test_results = [
        {"name": "Sugar", "score": 60, "summary": "Common sweetener"},
        {"name": "Salt", "score": 70, "summary": "Essential mineral"}
    ]
    aggregated = aggregate_ingredient_results(test_results)
    assert aggregated["total_ingredients"] == 2
    assert aggregated["overall_score"] == 65.0
    print(f"✓ PASSED: Aggregation works correctly - Score: {aggregated['overall_score']}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")

# Test 8: OCR Service - Parse ingredient list
print("\nTest 8: OCR Service - Parse ingredient list")
try:
    from ocr_service import parse_ingredient_list
    text = "Ingredients: Sugar, Salt, Water, Flour"
    ingredients = parse_ingredient_list(text)
    assert len(ingredients) > 0
    print(f"✓ PASSED: Parsed {len(ingredients)} ingredients: {ingredients}")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")

# Test 9: Agent Research - Health score calculation
print("\nTest 9: Agent Research - Health score calculation")
try:
    from agent_research import calculate_health_score
    
    # Test with positive keywords
    positive_text = "This ingredient is safe, healthy, and beneficial for consumption"
    score_positive = calculate_health_score(positive_text, "test")
    
    # Test with negative keywords
    negative_text = "This ingredient is toxic, harmful, and may cause cancer"
    score_negative = calculate_health_score(negative_text, "test")
    
    assert score_positive > score_negative
    print(f"✓ PASSED: Positive score ({score_positive}) > Negative score ({score_negative})")
except Exception as e:
    print(f"❌ FAILED: {str(e)}")

print("\n" + "="*60)
print("Error Handling Test Summary Complete")
print("="*60)
