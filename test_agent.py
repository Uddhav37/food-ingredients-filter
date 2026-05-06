"""
Test script for agent research functionality.

This script tests the LangChain agent for ingredient health research.
"""

import os
from agent_research import (
    create_research_agent,
    research_ingredient,
    research_multiple_ingredients,
    calculate_health_score,
    get_research_summary,
    AgentResearchError
)


def test_health_score_calculation():
    """Test the health score calculation logic."""
    print("Testing health score calculation...")
    print("-" * 60)
    
    # Test cases with expected score ranges
    test_cases = [
        ("Contains beneficial vitamins and minerals, safe for consumption", 75, 95),
        ("May cause cancer, toxic substance, harmful effects", 0, 30),
        ("Generally recognized as safe, no major concerns", 65, 85),
        ("Artificial preservative, some concerns about long-term use", 40, 65),
    ]
    
    for text, min_expected, max_expected in test_cases:
        score = calculate_health_score(text, "test ingredient")
        status = "✓" if min_expected <= score <= max_expected else "✗"
        print(f"{status} Score: {score} (expected {min_expected}-{max_expected})")
        print(f"   Text: {text[:60]}...")
    
    print("\n" + "=" * 60 + "\n")


def test_agent_creation():
    """Test agent initialization."""
    print("Testing agent creation...")
    print("-" * 60)
    
    try:
        agent = create_research_agent()
        print("✓ Agent created successfully")
        print(f"   Type: {type(agent)}")
        return agent
    except AgentResearchError as e:
        print(f"✗ Agent creation failed: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None
    finally:
        print("\n" + "=" * 60 + "\n")


def test_single_ingredient_research(agent):
    """Test researching a single ingredient."""
    if not agent:
        print("⊘ Skipping single ingredient test (no agent)")
        return
    
    print("Testing single ingredient research...")
    print("-" * 60)
    
    test_ingredient = "vitamin C"
    
    try:
        print(f"Researching: {test_ingredient}")
        result = research_ingredient(agent, test_ingredient)
        
        print(f"✓ Research completed")
        print(f"   Name: {result['name']}")
        print(f"   Score: {result['score']}/100")
        print(f"   Summary: {result['summary'][:100]}...")
        print(f"   Benefits: {len(result['details']['benefits'])}")
        print(f"   Concerns: {len(result['details']['concerns'])}")
        
    except Exception as e:
        print(f"✗ Research failed: {e}")
    
    print("\n" + "=" * 60 + "\n")


def test_multiple_ingredients_research():
    """Test researching multiple ingredients."""
    print("Testing multiple ingredients research...")
    print("-" * 60)
    
    test_ingredients = ["sugar", "salt", "vitamin C"]
    
    def progress_callback(current, total, ingredient):
        print(f"   [{current}/{total}] Researching: {ingredient}")
    
    try:
        results = research_multiple_ingredients(test_ingredients, progress_callback)
        
        print(f"\n✓ Researched {len(results)} ingredients")
        
        # Show summary
        summary = get_research_summary(results)
        print(f"\nSummary:")
        print(f"   Average score: {summary['average_score']}/100")
        print(f"   Healthy ingredients: {summary['healthy_count']}")
        print(f"   Concerning ingredients: {summary['concerning_count']}")
        print(f"   Score range: {summary['score_range']}")
        
        # Show individual results
        print(f"\nIndividual results:")
        for result in results:
            print(f"   - {result['name']}: {result['score']}/100")
        
    except AgentResearchError as e:
        print(f"✗ Research failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print("\n" + "=" * 60 + "\n")


def check_environment():
    """Check if required environment variables are set."""
    print("Checking environment configuration...")
    print("-" * 60)
    
    required_vars = {
        "GCP_PROJECT_ID": os.getenv("GCP_PROJECT_ID"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"✓ {var_name}: Set")
        else:
            print(f"✗ {var_name}: Not set")
            all_set = False
    
    print("\n" + "=" * 60 + "\n")
    
    if not all_set:
        print("⚠ Warning: Some environment variables are not set")
        print("Please configure your .env file with:")
        print("  - GCP_PROJECT_ID")
        print("  - TAVILY_API_KEY")
        print("  - GOOGLE_APPLICATION_CREDENTIALS")
        print("\nTests requiring API access will be skipped.\n")
    
    return all_set


if __name__ == "__main__":
    print("=" * 60)
    print("Agent Research Service Tests")
    print("=" * 60 + "\n")
    
    # Check environment
    env_ready = check_environment()
    
    # Always test score calculation (no API needed)
    test_health_score_calculation()
    
    # Test agent functionality if environment is ready
    if env_ready:
        agent = test_agent_creation()
        test_single_ingredient_research(agent)
        test_multiple_ingredients_research()
    else:
        print("Skipping API-dependent tests due to missing configuration.\n")
    
    print("=" * 60)
    print("Tests completed")
    print("=" * 60)
