"""
Recommendation Generation Service

This module generates buy/don't buy recommendations based on ingredient research results.
"""

from typing import Dict, List
from langchain_google_vertexai import ChatVertexAI
import os


class RecommendationError(Exception):
    """Custom exception for recommendation generation errors"""
    pass


def aggregate_ingredient_results(ingredient_results: List[Dict]) -> Dict:
    """
    Aggregate ingredient research results into summary statistics.
    
    Args:
        ingredient_results: List of ingredient research results
        
    Returns:
        Dictionary with aggregated statistics
    """
    if not ingredient_results:
        return {
            "total_ingredients": 0,
            "overall_score": 0,
            "healthy_count": 0,
            "concerning_count": 0,
            "ingredients": []
        }
    
    scores = [r["score"] for r in ingredient_results]
    overall_score = sum(scores) / len(scores)
    
    healthy_count = sum(1 for s in scores if s >= 70)
    concerning_count = sum(1 for s in scores if s < 50)
    
    return {
        "total_ingredients": len(ingredient_results),
        "overall_score": round(overall_score, 1),
        "healthy_count": healthy_count,
        "concerning_count": concerning_count,
        "ingredients": ingredient_results
    }


def generate_recommendation(ingredient_results: List[Dict]) -> Dict:
    """
    Generate buy/don't buy recommendation with reasoning.
    
    Args:
        ingredient_results: List of ingredient research results
        
    Returns:
        Dictionary containing:
            - recommendation: "BUY" or "DON'T BUY"
            - reasoning: Explanation for the recommendation
            - score: Overall health score (0-100)
            - ingredient_details: List of ingredient results
            - summary: Summary statistics
            
    Raises:
        RecommendationError: If recommendation generation fails
    """
    # Validate input
    if not ingredient_results:
        raise RecommendationError(
            "No ingredient results provided. Cannot generate recommendation without data."
        )
    
    if not isinstance(ingredient_results, list):
        raise RecommendationError(
            f"Invalid input type: expected list, got {type(ingredient_results).__name__}"
        )
    
    # Filter out invalid results
    valid_results = [r for r in ingredient_results if isinstance(r, dict) and 'score' in r]
    
    if len(valid_results) == 0:
        raise RecommendationError(
            "No valid ingredient results found. All ingredient research failed."
        )
    
    try:
        # Aggregate results
        aggregated = aggregate_ingredient_results(valid_results)
        
        if aggregated["total_ingredients"] == 0:
            raise RecommendationError("No ingredient results to analyze")
        
        overall_score = aggregated["overall_score"]
        
        # Validate score
        if not isinstance(overall_score, (int, float)) or overall_score < 0 or overall_score > 100:
            raise RecommendationError(f"Invalid overall score calculated: {overall_score}")
        
        # Generate reasoning using Gemini Pro with fallback
        try:
            reasoning = _generate_reasoning_with_llm(valid_results, overall_score)
        except Exception as e:
            # Fallback to simple reasoning if LLM fails
            reasoning = _generate_fallback_reasoning(valid_results, overall_score)
        
        # Validate reasoning
        if not reasoning or not reasoning.strip():
            reasoning = _generate_fallback_reasoning(valid_results, overall_score)
        
        # Determine recommendation based on score
        recommendation = "BUY" if overall_score >= 60 else "DON'T BUY"
        
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "score": overall_score,
            "ingredient_details": valid_results,
            "summary": {
                "total_ingredients": aggregated["total_ingredients"],
                "healthy_count": aggregated["healthy_count"],
                "concerning_count": aggregated["concerning_count"]
            }
        }
        
    except Exception as e:
        if isinstance(e, RecommendationError):
            raise
        raise RecommendationError(
            f"❌ Failed to generate recommendation: {str(e)}\n\n"
            "This may be due to:\n"
            "- Invalid ingredient research data\n"
            "- API connectivity issues\n"
            "- Unexpected data format\n\n"
            "Please try again or contact support if the issue persists."
        )


def _generate_reasoning_with_llm(ingredient_results: List[Dict], overall_score: float) -> str:
    """
    Use Gemini Pro to generate human-readable reasoning.
    
    Args:
        ingredient_results: List of ingredient research results
        overall_score: Calculated overall health score
        
    Returns:
        Reasoning text (2-3 sentences)
        
    Raises:
        Exception: If LLM generation fails (caller should handle with fallback)
    """
    try:
        # Validate environment
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise RecommendationError(
                "GCP_PROJECT_ID not set. Cannot generate AI-powered reasoning."
            )
        
        # Initialize LLM
        try:
            llm = ChatVertexAI(
                model_name="gemini-pro",
                temperature=0.3,
                project=project_id,
                max_output_tokens=256
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini Pro: {str(e)}")
        
        # Build ingredient summaries (limit to prevent token overflow)
        summaries = []
        for r in ingredient_results[:20]:  # Limit to first 20 ingredients
            summary_text = r.get('summary', 'No summary available')
            # Truncate long summaries
            if len(summary_text) > 100:
                summary_text = summary_text[:100] + "..."
            summaries.append(f"- {r['name']} (score: {r['score']}/100): {summary_text}")
        
        summaries_text = "\n".join(summaries)
        
        # Add note if we truncated
        if len(ingredient_results) > 20:
            summaries_text += f"\n... and {len(ingredient_results) - 20} more ingredients"
        
        prompt = f"""Based on these ingredient analyses, provide a clear recommendation reasoning:

{summaries_text}

Overall Health Score: {overall_score}/100

Provide 2-3 sentences explaining whether this product should be purchased, focusing on the most important health impacts. Be direct and specific."""
        
        # Generate reasoning with timeout handling
        try:
            reasoning = llm.predict(prompt)
        except Exception as e:
            raise Exception(f"LLM prediction failed: {str(e)}")
        
        # Validate output
        if not reasoning or not reasoning.strip():
            raise Exception("LLM returned empty reasoning")
        
        return reasoning.strip()
        
    except Exception as e:
        # Re-raise to trigger fallback in caller
        raise Exception(f"LLM reasoning generation failed: {str(e)}")


def _generate_fallback_reasoning(ingredient_results: List[Dict], overall_score: float) -> str:
    """
    Generate simple reasoning without LLM as fallback.
    
    Args:
        ingredient_results: List of ingredient research results
        overall_score: Overall health score
        
    Returns:
        Basic reasoning text
    """
    concerning = [r for r in ingredient_results if r['score'] < 50]
    healthy = [r for r in ingredient_results if r['score'] >= 70]
    
    if overall_score >= 70:
        return f"This product contains mostly safe ingredients with {len(healthy)} healthy components. Overall health profile is good."
    elif overall_score >= 60:
        return f"This product has a moderate health profile with {len(concerning)} ingredients of concern. Generally acceptable for occasional consumption."
    elif overall_score >= 40:
        concern_names = ", ".join([r['name'] for r in concerning[:3]])
        return f"This product contains {len(concerning)} concerning ingredients including {concern_names}. Consider alternatives."
    else:
        concern_names = ", ".join([r['name'] for r in concerning[:3]])
        return f"This product has multiple health concerns with ingredients like {concern_names}. Not recommended for regular consumption."
