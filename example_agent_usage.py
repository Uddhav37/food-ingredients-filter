"""
Example usage of the agent research service.

This script demonstrates how to use the LangChain agent to research
ingredient health impacts.

Note: Requires valid API credentials (GCP_PROJECT_ID, TAVILY_API_KEY, 
GOOGLE_APPLICATION_CREDENTIALS) to run.
"""

import os
from agent_research import (
    create_research_agent,
    research_ingredient,
    research_multiple_ingredients,
    get_research_summary,
    AgentResearchError
)


def example_single_ingredient():
    """
    Example: Research a single ingredient.
    """
    print("Example 1: Single Ingredient Research")
    print("=" * 60)
    
    try:
        # Create agent
        print("Creating research agent...")
        agent = create_research_agent()
        print("✓ Agent created\n")
        
        # Research an ingredient
        ingredient = "aspartame"
        print(f"Researching: {ingredient}")
        print("-" * 60)
        
        result = research_ingredient(agent, ingredient)
        
        # Display results
        print(f"\nIngredient: {result['name']}")
        print(f"Health Score: {result['score']}/100")
        print(f"\nSummary:")
        print(f"{result['summary']}")
        print(f"\nDetails:")
        print(f"  Benefits: {len(result['details']['benefits'])}")
        print(f"  Concerns: {len(result['details']['concerns'])}")
        print(f"  Facts: {len(result['details']['facts'])}")
        
    except AgentResearchError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60 + "\n")


def example_multiple_ingredients():
    """
    Example: Research multiple ingredients with progress tracking.
    """
    print("Example 2: Multiple Ingredients Research")
    print("=" * 60)
    
    ingredients = [
        "sugar",
        "sodium benzoate",
        "vitamin C",
        "high fructose corn syrup",
        "natural flavors"
    ]
    
    print(f"Researching {len(ingredients)} ingredients...\n")
    
    def progress_callback(current, total, ingredient):
        """Display progress during research."""
        print(f"[{current}/{total}] Researching: {ingredient}")
    
    try:
        # Research all ingredients
        results = research_multiple_ingredients(ingredients, progress_callback)
        
        print(f"\n✓ Research completed!\n")
        print("=" * 60)
        
        # Display summary
        summary = get_research_summary(results)
        print(f"\nOverall Summary:")
        print(f"  Total ingredients: {summary['total_ingredients']}")
        print(f"  Average health score: {summary['average_score']}/100")
        print(f"  Healthy ingredients (≥70): {summary['healthy_count']}")
        print(f"  Concerning ingredients (<50): {summary['concerning_count']}")
        print(f"  Score range: {summary['score_range'][0]}-{summary['score_range'][1]}")
        
        # Display individual results
        print(f"\nIndividual Results:")
        print("-" * 60)
        for result in results:
            status = "✓" if result['score'] >= 70 else "⚠" if result['score'] >= 50 else "✗"
            print(f"{status} {result['name']}: {result['score']}/100")
            print(f"   {result['summary'][:80]}...")
            print()
        
    except AgentResearchError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("=" * 60 + "\n")


def example_with_product_ingredients():
    """
    Example: Analyze a complete product ingredient list.
    """
    print("Example 3: Complete Product Analysis")
    print("=" * 60)
    
    # Simulated ingredient list from OCR
    product_name = "Energy Drink"
    ingredients = [
        "Carbonated Water",
        "Sugar",
        "Citric Acid",
        "Taurine",
        "Caffeine",
        "Artificial Flavors",
        "Sodium Benzoate",
        "Yellow 5"
    ]
    
    print(f"Product: {product_name}")
    print(f"Ingredients: {', '.join(ingredients)}\n")
    
    try:
        # Research all ingredients
        print("Analyzing ingredients...")
        results = research_multiple_ingredients(
            ingredients,
            lambda c, t, i: print(f"  [{c}/{t}] {i}")
        )
        
        # Get summary
        summary = get_research_summary(results)
        
        print(f"\n{'=' * 60}")
        print(f"PRODUCT ANALYSIS RESULTS")
        print(f"{'=' * 60}\n")
        
        # Overall recommendation
        avg_score = summary['average_score']
        if avg_score >= 70:
            recommendation = "✓ BUY - Generally safe ingredients"
            color = "green"
        elif avg_score >= 50:
            recommendation = "⚠ CAUTION - Some concerning ingredients"
            color = "yellow"
        else:
            recommendation = "✗ DON'T BUY - Multiple health concerns"
            color = "red"
        
        print(f"Recommendation: {recommendation}")
        print(f"Overall Health Score: {avg_score}/100")
        print(f"\nIngredient Breakdown:")
        print(f"  Healthy: {summary['healthy_count']}")
        print(f"  Concerning: {summary['concerning_count']}")
        
        # Show concerning ingredients
        concerning = [r for r in results if r['score'] < 50]
        if concerning:
            print(f"\nIngredients of Concern:")
            for ing in concerning:
                print(f"  ✗ {ing['name']} ({ing['score']}/100)")
        
    except AgentResearchError as e:
        print(f"✗ Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60 + "\n")


def check_credentials():
    """Check if required credentials are configured."""
    required = {
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    }
    
    missing = [k for k, v in required.items() if not v]
    
    if missing:
        print("⚠ Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease configure your .env file before running examples.")
        print("See .env.example for reference.\n")
        return False
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Agent Research Service - Usage Examples")
    print("=" * 60 + "\n")
    
    # Check credentials
    if not check_credentials():
        print("Exiting due to missing credentials.\n")
        exit(1)
    
    # Run examples
    try:
        example_single_ingredient()
        example_multiple_ingredients()
        example_with_product_ingredients()
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.\n")
    
    print("=" * 60)
    print("Examples completed")
    print("=" * 60 + "\n")
