"""
Agent Research Service for Ingredient Health Analysis

This module provides LangChain-based AI agent functionality to research
ingredient health impacts using Gemini Pro and web search capabilities.
"""

import os
import re
from typing import Dict, List, Optional
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_community.tools.tavily_search import TavilySearchResults


class AgentResearchError(Exception):
    """Custom exception for agent research errors"""
    pass


def create_research_agent():
    """
    Create a LangChain agent configured for ingredient health research.
    
    Uses:
    - Gemini Pro via Vertex AI for reasoning
    - Tavily Search for web research
    - Zero-shot ReAct agent configuration
    
    Returns:
        Configured LangChain agent
        
    Raises:
        AgentResearchError: If agent initialization fails
    """
    try:
        # Validate GCP Project ID
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise AgentResearchError(
                "❌ GCP_PROJECT_ID environment variable not set.\n\n"
                "Setup instructions:\n"
                "1. Create a Google Cloud project\n"
                "2. Set GCP_PROJECT_ID in your .env file\n"
                "3. Ensure Vertex AI API is enabled\n\n"
                "See README.md for detailed setup instructions."
            )
        
        if not project_id.strip():
            raise AgentResearchError(
                "❌ GCP_PROJECT_ID is empty. Please provide a valid Google Cloud project ID."
            )
        
        # Initialize Gemini Pro model via Vertex AI
        try:
            llm = ChatVertexAI(
                model_name="gemini-pro",
                temperature=0.2,  # Lower temperature for more factual responses
                project=project_id,
                max_output_tokens=1024
            )
        except Exception as e:
            raise AgentResearchError(
                f"❌ Failed to initialize Gemini Pro model.\n\n"
                f"Please ensure:\n"
                f"1. Vertex AI API is enabled in project '{project_id}'\n"
                f"2. Your service account has 'Vertex AI User' role\n"
                f"3. Billing is enabled for your GCP project\n\n"
                f"Error details: {str(e)}"
            )
        
        # Validate Tavily API key
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise AgentResearchError(
                "❌ TAVILY_API_KEY environment variable not set.\n\n"
                "Setup instructions:\n"
                "1. Get a free API key from https://tavily.com\n"
                "2. Set TAVILY_API_KEY in your .env file\n\n"
                "Tavily provides web search capabilities for ingredient research."
            )
        
        if not tavily_api_key.strip():
            raise AgentResearchError(
                "❌ TAVILY_API_KEY is empty. Please provide a valid Tavily API key."
            )
        
        # Set up Tavily search tool for web research
        try:
            search = TavilySearchResults(api_key=tavily_api_key)
        except Exception as e:
            raise AgentResearchError(
                f"❌ Failed to initialize Tavily search.\n\n"
                f"Please check:\n"
                f"1. Your Tavily API key is valid\n"
                f"2. You have internet connectivity\n"
                f"3. Tavily service is accessible\n\n"
                f"Error details: {str(e)}"
            )
        
        tools = [
            Tool(
                name="Search",
                func=search.run,
                description=(
                    "Search the web for health information about ingredients. "
                    "Use this to find information about health benefits, risks, "
                    "safety concerns, and regulatory status of food ingredients."
                )
            )
        ]
        
        # Create agent with zero-shot ReAct configuration
        try:
            agent = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=False,  # Set to True for debugging
                handle_parsing_errors=True,
                max_iterations=3  # Limit iterations to control costs
            )
        except Exception as e:
            raise AgentResearchError(
                f"❌ Failed to initialize research agent.\n\n"
                f"Error details: {str(e)}"
            )
        
        return agent
        
    except Exception as e:
        if isinstance(e, AgentResearchError):
            raise
        raise AgentResearchError(
            f"❌ Unexpected error initializing research agent: {str(e)}\n\n"
            "Please check your configuration and try again."
        )


def research_ingredient(agent, ingredient: str) -> Dict[str, any]:
    """
    Research health impacts of a single ingredient using the AI agent.
    
    The agent will:
    1. Search for health information about the ingredient
    2. Analyze benefits, concerns, and risks
    3. Provide a summary with key findings
    
    Implements graceful degradation - returns partial results on failure.
    
    Args:
        agent: Configured LangChain agent
        ingredient: Name of the ingredient to research
        
    Returns:
        Dictionary containing:
            - name: Ingredient name
            - summary: Research summary (2-3 sentences)
            - score: Health score (0-100)
            - details: Detailed findings
            - error: Error message if research failed (optional)
    """
    # Validate input
    if not ingredient or not ingredient.strip():
        return {
            "name": ingredient or "Unknown",
            "summary": "Invalid ingredient name provided",
            "score": 50,
            "details": {"error": "Empty or invalid ingredient name"},
            "error": "Invalid input"
        }
    
    try:
        # Create focused research prompt
        prompt = f"""
Research the health impacts of the food ingredient: {ingredient}

Focus on these specific aspects:
1. Major health benefits (if any)
2. Health concerns or potential risks
3. Safety for general consumption
4. Any regulatory warnings or restrictions

Provide a brief, factual summary in 2-3 sentences with the most important points.
Be objective and cite specific health impacts.
"""
        
        # Execute agent research with timeout handling
        try:
            result = agent.run(prompt)
        except Exception as agent_error:
            # Graceful degradation - return neutral result
            return {
                "name": ingredient,
                "summary": f"Research unavailable for {ingredient}. Using neutral assessment.",
                "score": 50,
                "details": {
                    "benefits": [],
                    "concerns": [],
                    "facts": ["Research could not be completed due to API limitations"]
                },
                "error": str(agent_error)
            }
        
        # Validate result
        if not result or not result.strip():
            return {
                "name": ingredient,
                "summary": f"No research data available for {ingredient}",
                "score": 50,
                "details": {"benefits": [], "concerns": [], "facts": []},
                "error": "Empty research result"
            }
        
        # Calculate health score based on research results
        score = calculate_health_score(result, ingredient)
        
        # Extract key details
        details = extract_key_details(result)
        
        return {
            "name": ingredient,
            "summary": result.strip(),
            "score": score,
            "details": details
        }
        
    except Exception as e:
        # Graceful degradation - return partial result on error
        return {
            "name": ingredient,
            "summary": f"Research incomplete for {ingredient}. Using neutral assessment.",
            "score": 50,
            "details": {
                "benefits": [],
                "concerns": [],
                "facts": ["Research could not be completed"],
                "error": str(e)
            },
            "error": str(e)
        }


def calculate_health_score(research_text: str, ingredient: str) -> int:
    """
    Calculate a simple health score (0-100) based on research findings.
    
    Scoring logic:
    - Start at 70 (neutral/safe baseline)
    - Subtract points for negative keywords
    - Add points for positive keywords
    - Cap between 0 and 100
    
    Args:
        research_text: Research summary text
        ingredient: Ingredient name
        
    Returns:
        Health score from 0 (unhealthy) to 100 (very healthy)
    """
    score = 70  # Start with neutral baseline
    
    text_lower = research_text.lower()
    
    # Negative indicators (subtract points)
    negative_keywords = {
        'cancer': -25,
        'carcinogen': -25,
        'toxic': -20,
        'harmful': -15,
        'dangerous': -15,
        'banned': -20,
        'restricted': -15,
        'warning': -10,
        'risk': -8,
        'concern': -6,
        'adverse': -10,
        'allergic': -6,
        'artificial': -4,
        'processed': -3,
        'preservative': -4,
        'additive': -3,
        'avoid': -12,
        'limit': -6,
        'excessive': -6,
        'unhealthy': -15
    }
    
    # Positive indicators (add points)
    positive_keywords = {
        'safe': 8,
        'healthy': 12,
        'beneficial': 12,
        'natural': 8,
        'vitamin': 10,
        'mineral': 10,
        'nutrient': 10,
        'antioxidant': 12,
        'essential': 10,
        'approved': 6,
        'generally recognized as safe': 12,
        'gras': 12,
        'benefit': 8,
        'good': 6,
        'positive': 6,
        'recommended': 8
    }
    
    # Apply negative keywords
    for keyword, penalty in negative_keywords.items():
        if keyword in text_lower:
            score += penalty  # penalty is negative
    
    # Apply positive keywords
    for keyword, bonus in positive_keywords.items():
        if keyword in text_lower:
            score += bonus
    
    # Common safe ingredients get a boost
    safe_ingredients = ['water', 'salt', 'sugar', 'flour', 'milk', 'egg', 'butter']
    if ingredient.lower() in safe_ingredients:
        score += 5
    
    # Cap score between 0 and 100
    score = max(0, min(100, score))
    
    return score


def extract_key_details(research_text: str) -> Dict[str, List[str]]:
    """
    Extract structured details from research text.
    
    Attempts to identify:
    - Health benefits
    - Health concerns
    - Key facts
    
    Args:
        research_text: Research summary text
        
    Returns:
        Dictionary with categorized details
    """
    details = {
        "benefits": [],
        "concerns": [],
        "facts": []
    }
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', research_text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_lower = sentence.lower()
        
        # Categorize based on keywords
        if any(word in sentence_lower for word in ['benefit', 'good', 'healthy', 'positive', 'essential', 'vitamin', 'nutrient']):
            details["benefits"].append(sentence)
        elif any(word in sentence_lower for word in ['risk', 'concern', 'harmful', 'warning', 'avoid', 'dangerous', 'adverse']):
            details["concerns"].append(sentence)
        else:
            details["facts"].append(sentence)
    
    return details


def research_multiple_ingredients(ingredients: List[str], progress_callback=None) -> List[Dict[str, any]]:
    """
    Research multiple ingredients using the agent with graceful degradation.
    
    If some ingredients fail to research, continues with others and returns
    partial results rather than failing completely.
    
    Args:
        ingredients: List of ingredient names
        progress_callback: Optional callback function(current, total, ingredient)
        
    Returns:
        List of research results for each ingredient (may include partial results)
        
    Raises:
        AgentResearchError: Only if agent creation fails completely
    """
    # Validate input
    if not ingredients or len(ingredients) == 0:
        raise AgentResearchError("No ingredients provided for research")
    
    # Filter out invalid ingredients
    valid_ingredients = [ing for ing in ingredients if ing and ing.strip()]
    
    if len(valid_ingredients) == 0:
        raise AgentResearchError("No valid ingredients provided for research")
    
    # Create agent once for all ingredients
    try:
        agent = create_research_agent()
    except AgentResearchError:
        # Re-raise agent creation errors
        raise
    except Exception as e:
        raise AgentResearchError(f"Failed to create research agent: {str(e)}")
    
    results = []
    total = len(valid_ingredients)
    failed_count = 0
    
    for i, ingredient in enumerate(valid_ingredients, 1):
        # Call progress callback if provided
        if progress_callback:
            try:
                progress_callback(i, total, ingredient)
            except Exception:
                pass  # Don't let callback errors stop processing
        
        # Research ingredient with graceful degradation
        try:
            result = research_ingredient(agent, ingredient)
            results.append(result)
            
            # Track failures for reporting
            if result.get('error'):
                failed_count += 1
                
        except Exception as e:
            # Even if research_ingredient fails completely, add a fallback result
            failed_count += 1
            results.append({
                "name": ingredient,
                "summary": f"Research failed for {ingredient}",
                "score": 50,
                "details": {"error": str(e)},
                "error": str(e)
            })
    
    # Ensure we have at least some results
    if len(results) == 0:
        raise AgentResearchError("Failed to research any ingredients")
    
    return results


def get_research_summary(results: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Generate summary statistics from research results.
    
    Args:
        results: List of ingredient research results
        
    Returns:
        Summary dictionary with statistics
    """
    if not results:
        return {
            "total_ingredients": 0,
            "average_score": 0,
            "healthy_count": 0,
            "concerning_count": 0
        }
    
    scores = [r["score"] for r in results]
    avg_score = sum(scores) / len(scores)
    
    # Count healthy (score >= 70) and concerning (score < 50)
    healthy_count = sum(1 for s in scores if s >= 70)
    concerning_count = sum(1 for s in scores if s < 50)
    
    return {
        "total_ingredients": len(results),
        "average_score": round(avg_score, 1),
        "healthy_count": healthy_count,
        "concerning_count": concerning_count,
        "score_range": (min(scores), max(scores))
    }
