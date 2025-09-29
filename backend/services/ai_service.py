from pathlib import Path
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

# Load environment variables from the .env file in the backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client with the API key
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the .env file")
    print("OpenAI API Key loaded successfully")
    client = OpenAI(api_key=api_key)
except Exception as e:
    print(f"Error initializing OpenAI: {str(e)}")
    raise

class RiskFlag(BaseModel):
    """Represents a risk flag for an ingredient."""
    ingredient: str = Field(..., description="The ingredient that poses a risk")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="Risk level of the ingredient")
    concern: str = Field(..., description="Explanation of the health concern")
    affected_profiles: List[str] = Field(..., description="List of health profiles affected by this ingredient")

class AnalysisResult(BaseModel):
    """Structured result of ingredient analysis."""
    risk_flags: List[RiskFlag] = Field(..., description="List of identified risk flags")
    overall_risk_score: int = Field(..., ge=0, le=100, description="Overall risk score from 0-100")
    recommendations: List[str] = Field(..., description="List of recommendations based on the analysis")
    is_ai_analyzed: bool = Field(True, description="Whether the analysis was performed by AI")

class AIIngredientAnalyzer:
    """Analyzes ingredients for potential health risks based on user profiles."""
    
    RISK_LEVELS = {
        "low": 1,
        "medium": 2,
        "high": 3
    }
    
    @staticmethod
    def _create_analysis_prompt(ingredients: List[str], health_profiles: List[str]) -> str:
        """Create a prompt for the AI to analyze ingredients."""
        return f"""
        Analyze these ingredients for potential health risks:
        Ingredients: {', '.join(ingredients)}
        
        Health profiles to consider: {', '.join(health_profiles)}
        
        For each ingredient that poses a risk, provide:
        1. The specific health concern
        2. The risk level (low, medium, high)
        3. Which health profiles are affected
        
        Also provide an overall risk score from 0-100 and specific recommendations.
        """
    
    @staticmethod
    async def analyze_ingredients(ingredients: List[str], health_profiles: List[str]) -> Dict[str, Any]:
        """
        Analyze ingredients for potential health risks.
        
        Args:
            ingredients: List of ingredients to analyze
            health_profiles: List of health profiles to consider (e.g., ['diabetic', 'hypertensive'])
            
        Returns:
            Dict containing risk analysis results
        """
        try:
            print(f"Starting analysis for {len(ingredients)} ingredients")
            
            # Define the tool schema for structured output
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "report_ingredient_analysis",
                        "description": "Report the analysis of ingredients for health risks",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "risk_flags": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "ingredient": {"type": "string"},
                                            "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                                            "concern": {"type": "string"},
                                            "affected_profiles": {"type": "array", "items": {"type": "string"}}
                                        },
                                        "required": ["ingredient", "risk_level", "concern", "affected_profiles"]
                                    }
                                },
                                "overall_risk_score": {"type": "integer", "minimum": 0, "maximum": 100},
                                "recommendations": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["risk_flags", "overall_risk_score", "recommendations"]
                        }
                    }
                }
            ]
            
            # Make the API call with tool calling
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a nutritionist AI that analyzes food ingredients for health risks."},
                    {"role": "user", "content": AIIngredientAnalyzer._create_analysis_prompt(ingredients, health_profiles)}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "report_ingredient_analysis"}},
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse the tool call response
            message = response.choices[0].message
            if message.tool_calls and len(message.tool_calls) > 0:
                function_args = json.loads(message.tool_calls[0].function.arguments)
                
                # Validate the response against our Pydantic model
                result = AnalysisResult(**function_args)
                return result.dict()
            else:
                raise ValueError("No function call in the response")
                
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return {
                "risk_flags": [],
                "overall_risk_score": 50,
                "recommendations": [f"AI analysis failed: {str(e)}. Please try again or contact support."],
                "is_ai_analyzed": False
            }