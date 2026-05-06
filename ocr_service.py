"""
OCR Service for Ingredient Extraction

This module provides functionality to extract ingredient text from product label images
using Google Cloud Vision API and parse the extracted text into a clean list of ingredients.
"""

import re
from typing import List, Dict, Optional
from google.cloud import vision
from google.api_core import exceptions as google_exceptions


class OCRError(Exception):
    """Custom exception for OCR-related errors"""
    pass


def extract_ingredients_from_image(image_bytes: bytes) -> List[str]:
    """
    Extract and parse ingredients from a product label image using Google Cloud Vision API.
    
    Args:
        image_bytes: Raw bytes of the image file
        
    Returns:
        List of cleaned ingredient names
        
    Raises:
        OCRError: If OCR processing fails or no text is detected
    """
    # Validate input
    if not image_bytes or len(image_bytes) == 0:
        raise OCRError("Image data is empty. Please provide a valid image file.")
    
    # Check minimum file size (at least 100 bytes for a valid image)
    if len(image_bytes) < 100:
        raise OCRError("Image file is too small or corrupted. Please upload a valid image.")
    
    # Check maximum file size (10MB limit for Vision API)
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image_bytes) > max_size:
        raise OCRError(
            f"Image file is too large ({len(image_bytes) / (1024*1024):.1f}MB). "
            "Maximum size is 10MB. Please compress the image or use a smaller file."
        )
    
    try:
        # Initialize Vision API client
        client = vision.ImageAnnotatorClient()
        
        # Create image object
        image = vision.Image(content=image_bytes)
        
        # Perform text detection
        response = client.text_detection(image=image)
        
        # Check for API errors
        if response.error.message:
            raise OCRError(f"Google Cloud Vision API error: {response.error.message}")
        
        # Extract full text from response
        if not response.text_annotations:
            raise OCRError(
                "No text detected in the image. Please ensure:\n"
                "- The image is clear and well-lit\n"
                "- Text is visible and not blurry\n"
                "- The ingredients section is in focus\n"
                "- Try taking a new photo with better lighting"
            )
        
        # First annotation contains the full detected text
        full_text = response.text_annotations[0].description
        
        if not full_text or not full_text.strip():
            raise OCRError(
                "No readable text found in the image. The image may be:\n"
                "- Too blurry or out of focus\n"
                "- Too dark or poorly lit\n"
                "- At an angle that makes text unreadable\n"
                "Please try taking a clearer photo."
            )
        
        # Parse ingredients from the extracted text
        ingredients = parse_ingredient_list(full_text)
        
        if not ingredients or len(ingredients) == 0:
            raise OCRError(
                "Could not identify an ingredient list in the extracted text.\n"
                "Please ensure:\n"
                "- The image shows the ingredients section clearly\n"
                "- The word 'Ingredients' or 'Contains' is visible\n"
                "- Ingredients are listed in a readable format\n"
                "- Try capturing just the ingredients section"
            )
        
        # Validate we have reasonable ingredients (at least 1, max 100)
        if len(ingredients) > 100:
            raise OCRError(
                f"Detected {len(ingredients)} ingredients, which seems unusually high. "
                "The image may contain extra text. Please try capturing only the ingredients section."
            )
        
        return ingredients
        
    except google_exceptions.Unauthenticated as e:
        raise OCRError(
            "❌ Authentication failed with Google Cloud.\n\n"
            "Please check:\n"
            "1. GOOGLE_APPLICATION_CREDENTIALS environment variable is set\n"
            "2. The credentials file exists and is valid JSON\n"
            "3. The service account key hasn't expired\n\n"
            f"Error details: {str(e)}"
        )
    except google_exceptions.PermissionDenied as e:
        raise OCRError(
            "❌ Permission denied for Google Cloud Vision API.\n\n"
            "Please ensure:\n"
            "1. Cloud Vision API is enabled in your GCP project\n"
            "2. Your service account has 'Cloud Vision API User' role\n"
            "3. Billing is enabled for your GCP project\n\n"
            f"Error details: {str(e)}"
        )
    except google_exceptions.ResourceExhausted as e:
        raise OCRError(
            "❌ API quota exceeded.\n\n"
            "You've reached the rate limit for Cloud Vision API.\n"
            "Please wait a moment and try again.\n\n"
            f"Error details: {str(e)}"
        )
    except google_exceptions.GoogleAPIError as e:
        raise OCRError(
            f"❌ Google Cloud Vision API error: {str(e)}\n\n"
            "This may be due to:\n"
            "- Network connectivity issues\n"
            "- Temporary API outage\n"
            "- Invalid API configuration\n\n"
            "Please check your internet connection and try again."
        )
    except Exception as e:
        if isinstance(e, OCRError):
            raise
        raise OCRError(
            f"❌ Unexpected error during OCR processing: {str(e)}\n\n"
            "Please try again or contact support if the issue persists."
        )


def parse_ingredient_list(text: str) -> List[str]:
    """
    Parse ingredient list from extracted text.
    
    Handles common ingredient list formats:
    - Comma-separated lists
    - Ingredients with parentheses (e.g., "Sugar (Glucose)")
    - Ingredients with percentages (e.g., "Water (80%)")
    - Multi-line ingredient lists
    
    Args:
        text: Raw text extracted from image
        
    Returns:
        List of cleaned ingredient names
    """
    # Normalize text
    text = normalize_text(text)
    
    # Find ingredient section
    ingredient_text = extract_ingredient_section(text)
    
    if not ingredient_text:
        return []
    
    # Split by commas and clean each ingredient
    raw_ingredients = ingredient_text.split(',')
    
    ingredients = []
    for ingredient in raw_ingredients:
        cleaned = clean_ingredient(ingredient)
        if cleaned:
            ingredients.append(cleaned)
    
    return ingredients


def normalize_text(text: str) -> str:
    """
    Normalize extracted text for consistent parsing.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Normalized text
    """
    # Replace newlines with spaces
    text = text.replace('\n', ' ')
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_ingredient_section(text: str) -> Optional[str]:
    """
    Extract the ingredient section from the full text.
    
    Looks for common patterns like "Ingredients:", "INGREDIENTS:", etc.
    
    Args:
        text: Normalized text
        
    Returns:
        Ingredient section text or None if not found
    """
    # Common ingredient section markers
    patterns = [
        r'ingredients?\s*:?\s*(.+?)(?:allergen|contains|nutrition|storage|best before|use by|$)',
        r'composition\s*:?\s*(.+?)(?:allergen|contains|nutrition|storage|best before|use by|$)',
        r'contains\s*:?\s*(.+?)(?:allergen|nutrition|storage|best before|use by|$)',
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
        if match:
            # Extract the corresponding section from original text
            start_pos = match.start(1)
            end_pos = match.end(1)
            return text[start_pos:end_pos].strip()
    
    # If no marker found, try to use the entire text
    # This handles cases where the image only shows ingredients
    return text


def clean_ingredient(ingredient: str) -> Optional[str]:
    """
    Clean and normalize a single ingredient string.
    
    Removes:
    - Percentages in parentheses
    - Extra whitespace
    - Special characters
    - Numbers at the start
    
    Args:
        ingredient: Raw ingredient string
        
    Returns:
        Cleaned ingredient name or None if invalid
    """
    # Remove content in parentheses (percentages, clarifications)
    # But keep the main ingredient name
    ingredient = re.sub(r'\([^)]*\)', '', ingredient)
    
    # Remove percentages not in parentheses
    ingredient = re.sub(r'\d+\.?\d*\s*%', '', ingredient)
    
    # Remove leading numbers and dots (e.g., "1. Sugar" -> "Sugar")
    ingredient = re.sub(r'^\d+\.?\s*', '', ingredient)
    
    # Remove special characters except hyphens and spaces
    ingredient = re.sub(r'[^\w\s\-]', '', ingredient)
    
    # Clean up whitespace
    ingredient = ' '.join(ingredient.split())
    
    # Strip and convert to title case for consistency
    ingredient = ingredient.strip().title()
    
    # Filter out very short or empty strings
    if len(ingredient) < 2:
        return None
    
    # Filter out common non-ingredient words
    non_ingredients = {'and', 'or', 'the', 'a', 'an', 'of', 'in', 'with'}
    if ingredient.lower() in non_ingredients:
        return None
    
    return ingredient


def get_ocr_stats(text: str) -> Dict[str, any]:
    """
    Get statistics about the OCR extraction.
    
    Useful for debugging and quality assessment.
    
    Args:
        text: Extracted text
        
    Returns:
        Dictionary with OCR statistics
    """
    return {
        'total_characters': len(text),
        'total_words': len(text.split()),
        'has_ingredient_marker': bool(re.search(r'ingredient', text, re.IGNORECASE)),
        'text_preview': text[:100] + '...' if len(text) > 100 else text
    }
