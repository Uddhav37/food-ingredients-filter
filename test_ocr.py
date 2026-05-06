"""
Simple test script for OCR service functionality.
Tests the parsing and cleaning logic without requiring actual API calls.
"""

from ocr_service import (
    parse_ingredient_list,
    normalize_text,
    extract_ingredient_section,
    clean_ingredient,
    get_ocr_stats
)


def test_normalize_text():
    """Test text normalization"""
    print("Testing normalize_text...")
    
    test_cases = [
        ("Hello\nWorld\n\nTest", "Hello World Test"),
        ("Multiple   spaces", "Multiple spaces"),
        ("  Leading and trailing  ", "Leading and trailing"),
    ]
    
    for input_text, expected in test_cases:
        result = normalize_text(input_text)
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"  ✓ '{input_text[:20]}...' -> '{result[:20]}...'")
    
    print("  All normalize_text tests passed!\n")


def test_clean_ingredient():
    """Test ingredient cleaning"""
    print("Testing clean_ingredient...")
    
    test_cases = [
        ("sugar (glucose)", "Sugar"),
        ("Water (80%)", "Water"),
        ("1. Salt", "Salt"),
        ("Vitamin C (Ascorbic Acid)", "Vitamin C"),
        ("  wheat flour  ", "Wheat Flour"),
        ("E621", "E621"),
        ("and", None),  # Filter out common words
        ("a", None),  # Too short
    ]
    
    for input_text, expected in test_cases:
        result = clean_ingredient(input_text)
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"  ✓ '{input_text}' -> '{result}'")
    
    print("  All clean_ingredient tests passed!\n")


def test_extract_ingredient_section():
    """Test ingredient section extraction"""
    print("Testing extract_ingredient_section...")
    
    test_cases = [
        (
            "Product Name: Test. Ingredients: Sugar, Salt, Water. Allergen: Contains nuts.",
            "Sugar, Salt, Water"
        ),
        (
            "INGREDIENTS: Wheat flour, water, yeast. NUTRITION: 100g contains...",
            "Wheat flour, water, yeast"
        ),
        (
            "Contains: Milk, Eggs, Soy. Storage: Keep refrigerated.",
            "Milk, Eggs, Soy"
        ),
    ]
    
    for input_text, expected_substring in test_cases:
        result = extract_ingredient_section(input_text)
        assert expected_substring.lower() in result.lower(), \
            f"Expected substring '{expected_substring}' in '{result}'"
        print(f"  ✓ Found ingredient section")
    
    print("  All extract_ingredient_section tests passed!\n")


def test_parse_ingredient_list():
    """Test full ingredient list parsing"""
    print("Testing parse_ingredient_list...")
    
    test_text = """
    Product: Healthy Snack Bar
    Ingredients: Oats (40%), Honey (20%), Almonds (15%), 
    Dark Chocolate (10%), Vanilla Extract, Sea Salt.
    Allergen Information: Contains nuts.
    """
    
    ingredients = parse_ingredient_list(test_text)
    
    print(f"  Extracted {len(ingredients)} ingredients:")
    for ing in ingredients:
        print(f"    - {ing}")
    
    # Check that we got reasonable results
    assert len(ingredients) > 0, "Should extract at least one ingredient"
    assert any('oat' in ing.lower() for ing in ingredients), "Should find 'Oats'"
    assert any('honey' in ing.lower() for ing in ingredients), "Should find 'Honey'"
    
    print("  ✓ parse_ingredient_list test passed!\n")


def test_get_ocr_stats():
    """Test OCR statistics"""
    print("Testing get_ocr_stats...")
    
    test_text = "Ingredients: Sugar, Salt, Water"
    stats = get_ocr_stats(test_text)
    
    assert 'total_characters' in stats
    assert 'total_words' in stats
    assert 'has_ingredient_marker' in stats
    assert stats['has_ingredient_marker'] == True
    
    print(f"  Stats: {stats}")
    print("  ✓ get_ocr_stats test passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Running OCR Service Tests")
    print("=" * 60 + "\n")
    
    try:
        test_normalize_text()
        test_clean_ingredient()
        test_extract_ingredient_section()
        test_parse_ingredient_list()
        test_get_ocr_stats()
        
        print("=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        exit(1)
