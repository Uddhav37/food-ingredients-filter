"""
Example usage of the OCR service.

This script demonstrates how to use the OCR service to extract ingredients
from product label images.

Note: Requires valid Google Cloud credentials to run with actual images.
"""

import os
from ocr_service import extract_ingredients_from_image, OCRError


def example_with_image_file(image_path: str):
    """
    Example: Extract ingredients from an image file.
    
    Args:
        image_path: Path to the image file
    """
    print(f"Processing image: {image_path}")
    print("-" * 60)
    
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Extract ingredients
        ingredients = extract_ingredients_from_image(image_bytes)
        
        # Display results
        print(f"✓ Successfully extracted {len(ingredients)} ingredients:\n")
        for i, ingredient in enumerate(ingredients, 1):
            print(f"  {i}. {ingredient}")
        
        print("\n" + "=" * 60)
        
    except OCRError as e:
        print(f"✗ OCR Error: {e}")
    except FileNotFoundError:
        print(f"✗ Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def example_error_handling():
    """
    Example: Demonstrate error handling with invalid input.
    """
    print("\nDemonstrating error handling:")
    print("-" * 60)
    
    # Example 1: Empty image
    try:
        ingredients = extract_ingredients_from_image(b'')
        print(f"Extracted: {ingredients}")
    except OCRError as e:
        print(f"✓ Caught expected error: {e}")
    
    # Example 2: Invalid image data
    try:
        ingredients = extract_ingredients_from_image(b'not an image')
        print(f"Extracted: {ingredients}")
    except OCRError as e:
        print(f"✓ Caught expected error: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("OCR Service Usage Examples")
    print("=" * 60 + "\n")
    
    # Check if credentials are set
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("⚠ Warning: GOOGLE_APPLICATION_CREDENTIALS not set")
        print("To run with actual images, set up your Google Cloud credentials:")
        print("  export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
        print("\nFor now, showing error handling examples only.\n")
        example_error_handling()
    else:
        print("✓ Google Cloud credentials found\n")
        
        # Example with actual image (if provided)
        import sys
        if len(sys.argv) > 1:
            image_path = sys.argv[1]
            example_with_image_file(image_path)
        else:
            print("Usage: python example_ocr_usage.py <path_to_image>")
            print("\nExample:")
            print("  python example_ocr_usage.py product_label.jpg")
            print("\nShowing error handling examples:\n")
            example_error_handling()
