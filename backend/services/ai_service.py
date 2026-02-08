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
            # Fall back to rule-based analysis
            return AIIngredientAnalyzer._rule_based_analysis(ingredients, health_profiles)
    
    @staticmethod
    def _rule_based_analysis(ingredients: List[str], health_profiles: List[str]) -> Dict[str, Any]:
        """
        Rule-based fallback analysis when AI is unavailable.
        Based on the Food-as-Medicine paper's risk ingredient categories.
        """
        risk_flags = []
        recommendations = []
        
        # Convert to lowercase for matching
        ingredients_lower = [i.lower() for i in ingredients]
        profiles_lower = [p.lower() for p in health_profiles]
        
        # Risk ingredient mappings
        risk_mappings = {
            "aspartame": {
                "risk_level": "high",
                "concern": "Artificial sweetener linked to potential metabolic and neurological concerns",
                "affected_profiles": ["child", "pregnant", "toddler"]
            },
            "sucralose": {
                "risk_level": "medium",
                "concern": "Artificial sweetener that may affect gut microbiome",
                "affected_profiles": ["child", "pregnant", "diabetic"]
            },
            "red 40": {
                "risk_level": "high",
                "concern": "Artificial dye associated with hyperactivity in children",
                "affected_profiles": ["child", "toddler"]
            },
            "yellow 5": {
                "risk_level": "medium",
                "concern": "Artificial dye that may cause allergic reactions",
                "affected_profiles": ["child", "toddler"]
            },
            "yellow 6": {
                "risk_level": "medium",
                "concern": "Artificial dye linked to hyperactivity",
                "affected_profiles": ["child", "toddler"]
            },
            "blue 1": {
                "risk_level": "low",
                "concern": "Artificial dye with limited safety data",
                "affected_profiles": ["child", "toddler"]
            },
            "high fructose corn syrup": {
                "risk_level": "high",
                "concern": "Associated with obesity, diabetes, and metabolic syndrome",
                "affected_profiles": ["diabetic", "obesity", "cardiac"]
            },
            "hfcs": {
                "risk_level": "high",
                "concern": "High fructose corn syrup - associated with metabolic issues",
                "affected_profiles": ["diabetic", "obesity", "cardiac"]
            },
            "sodium nitrate": {
                "risk_level": "high",
                "concern": "Preservative linked to increased cancer risk and harmful during pregnancy",
                "affected_profiles": ["pregnant", "cardiac"]
            },
            "sodium nitrite": {
                "risk_level": "high",
                "concern": "Preservative that may form carcinogenic compounds",
                "affected_profiles": ["pregnant", "cardiac"]
            },
            "caffeine": {
                "risk_level": "medium",
                "concern": "Stimulant that can affect sleep, blood pressure, and fetal development",
                "affected_profiles": ["pregnant", "child", "hypertensive", "senior"]
            },
            "msg": {
                "risk_level": "low",
                "concern": "May cause sensitivity reactions in some individuals",
                "affected_profiles": ["adult"]
            },
            "monosodium glutamate": {
                "risk_level": "low",
                "concern": "May cause sensitivity reactions in some individuals",
                "affected_profiles": ["adult"]
            },
            "partially hydrogenated": {
                "risk_level": "high",
                "concern": "Contains trans fats linked to heart disease",
                "affected_profiles": ["cardiac", "hypertensive", "diabetic"]
            },
            "trans fat": {
                "risk_level": "high",
                "concern": "Strongly linked to cardiovascular disease",
                "affected_profiles": ["cardiac", "hypertensive"]
            },
            "bha": {
                "risk_level": "medium",
                "concern": "Preservative classified as possibly carcinogenic",
                "affected_profiles": ["pregnant", "child"]
            },
            "bht": {
                "risk_level": "medium",
                "concern": "Preservative with potential endocrine disruption",
                "affected_profiles": ["pregnant", "child"]
            },
            "sodium benzoate": {
                "risk_level": "low",
                "concern": "Preservative that may form benzene when combined with vitamin C",
                "affected_profiles": ["child"]
            }
        }
        
        # Check each ingredient against risk mappings
        for ingredient in ingredients_lower:
            for risk_name, risk_info in risk_mappings.items():
                if risk_name in ingredient:
                    # Check if any affected profile matches user's profiles
                    affected = [p for p in risk_info["affected_profiles"] if p in profiles_lower]
                    if affected or not profiles_lower:
                        risk_flags.append({
                            "ingredient": ingredient,
                            "risk_level": risk_info["risk_level"],
                            "concern": risk_info["concern"],
                            "affected_profiles": risk_info["affected_profiles"]
                        })
                        break
        
        # Calculate overall risk score (0-100, higher = more risk)
        risk_score = 0
        for flag in risk_flags:
            if flag["risk_level"] == "high":
                risk_score += 25
            elif flag["risk_level"] == "medium":
                risk_score += 15
            else:
                risk_score += 5
        
        risk_score = min(risk_score, 100)
        
        # Generate recommendations
        if risk_flags:
            recommendations.append(f"Found {len(risk_flags)} ingredient(s) of concern for your health profile.")
            if any(f["risk_level"] == "high" for f in risk_flags):
                recommendations.append("Consider looking for alternatives without high-risk ingredients.")
        else:
            recommendations.append("No significant concerns found for your health profile.")
        
        return {
            "risk_flags": risk_flags,
            "overall_risk_score": risk_score,
            "recommendations": recommendations,
            "is_ai_analyzed": False
        }
    
    @staticmethod
    async def generate_alternatives(
        ingredients: List[str], 
        health_profiles: List[str],
        risk_flags: List[Dict[str, Any]],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate healthy alternative suggestions based on flagged ingredients.
        """
        try:
            if not risk_flags:
                return []
            
            # Build prompt for alternatives
            flagged_ingredients = [f["ingredient"] for f in risk_flags]
            concerns = [f["concern"] for f in risk_flags]
            
            prompt = f"""
            Based on these flagged ingredients and concerns, suggest 3 healthy alternatives:
            
            Flagged ingredients: {', '.join(flagged_ingredients)}
            Concerns: {', '.join(concerns)}
            Health profiles to consider: {', '.join(health_profiles)}
            Product category: {category or 'general food'}
            
            For each alternative, provide:
            1. A specific product type or swap suggestion
            2. Why it's healthier
            3. Key benefits
            """
            
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "report_alternatives",
                        "description": "Report healthy alternative suggestions",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "alternatives": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string", "description": "Name of the alternative product or swap"},
                                            "reason": {"type": "string", "description": "Why this is a healthier choice"},
                                            "benefits": {"type": "array", "items": {"type": "string"}, "description": "List of health benefits"},
                                            "score": {"type": "integer", "minimum": 0, "maximum": 100, "description": "Health score of the alternative"}
                                        },
                                        "required": ["name", "reason", "benefits", "score"]
                                    }
                                }
                            },
                            "required": ["alternatives"]
                        }
                    }
                }
            ]
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a nutritionist AI that suggests healthy food alternatives based on dietary concerns and health profiles."},
                    {"role": "user", "content": prompt}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "report_alternatives"}},
                temperature=0.5,
                max_tokens=1000
            )
            
            message = response.choices[0].message
            if message.tool_calls and len(message.tool_calls) > 0:
                function_args = json.loads(message.tool_calls[0].function.arguments)
                alternatives = function_args.get("alternatives", [])
                
                # Add product_id to each alternative
                for i, alt in enumerate(alternatives):
                    alt["product_id"] = f"alt-{i+1}"
                    alt["brand"] = None
                    alt["image_url"] = None
                    alt["price_difference"] = None
                
                return alternatives
            
            return []
            
        except Exception as e:
            print(f"Error generating alternatives: {str(e)}")
            # Fall back to rule-based alternatives
            return AIIngredientAnalyzer._rule_based_alternatives(risk_flags, health_profiles)
    
    @staticmethod
    def _rule_based_alternatives(risk_flags: List[Dict[str, Any]], health_profiles: List[str]) -> List[Dict[str, Any]]:
        """
        Generate rule-based alternative suggestions when AI is unavailable.
        """
        alternatives = []
        
        # Map risk ingredients to alternatives
        alternative_mappings = {
            "aspartame": {
                "name": "Stevia or monk fruit sweetened beverage",
                "reason": "Natural sweeteners without the metabolic concerns of artificial sweeteners",
                "benefits": ["No artificial sweeteners", "Natural origin", "Zero glycemic impact"],
                "score": 85
            },
            "sucralose": {
                "name": "Honey or maple syrup sweetened option",
                "reason": "Natural sweeteners that are easier on the digestive system",
                "benefits": ["Natural sweetener", "Contains trace nutrients", "No artificial additives"],
                "score": 80
            },
            "red 40": {
                "name": "Products with natural colorings (beet juice, turmeric)",
                "reason": "Natural colorings without the behavioral concerns of synthetic dyes",
                "benefits": ["No artificial dyes", "Natural colors from plants", "Safe for children"],
                "score": 90
            },
            "yellow 5": {
                "name": "Naturally colored alternatives",
                "reason": "Avoid synthetic dyes that may cause sensitivities",
                "benefits": ["No artificial colors", "Hypoallergenic", "Child-friendly"],
                "score": 85
            },
            "high fructose corn syrup": {
                "name": "Products sweetened with cane sugar or fruit",
                "reason": "Less processed sweeteners with lower metabolic impact",
                "benefits": ["No HFCS", "Lower glycemic impact", "Less processed"],
                "score": 75
            },
            "sodium nitrate": {
                "name": "Uncured or nitrate-free meat products",
                "reason": "Avoid preservatives linked to health concerns",
                "benefits": ["No nitrates", "Safer for pregnancy", "Reduced cancer risk"],
                "score": 85
            },
            "caffeine": {
                "name": "Decaffeinated or caffeine-free alternatives",
                "reason": "Avoid stimulants that affect sleep and blood pressure",
                "benefits": ["No caffeine", "Better for sleep", "Safe during pregnancy"],
                "score": 90
            },
            "trans fat": {
                "name": "Products made with olive oil or avocado oil",
                "reason": "Healthy fats that support cardiovascular health",
                "benefits": ["Heart-healthy fats", "No trans fats", "Anti-inflammatory"],
                "score": 90
            },
            "partially hydrogenated": {
                "name": "Products with natural oils (coconut, olive)",
                "reason": "Avoid trans fats from hydrogenation process",
                "benefits": ["No hydrogenated oils", "Natural fats", "Heart-healthy"],
                "score": 85
            }
        }
        
        seen_alternatives = set()
        
        for flag in risk_flags:
            ingredient = flag.get("ingredient", "").lower()
            for risk_name, alt_info in alternative_mappings.items():
                if risk_name in ingredient and alt_info["name"] not in seen_alternatives:
                    seen_alternatives.add(alt_info["name"])
                    alternatives.append({
                        "product_id": f"alt-{len(alternatives)+1}",
                        "name": alt_info["name"],
                        "brand": None,
                        "image_url": None,
                        "score": alt_info["score"],
                        "reason": alt_info["reason"],
                        "benefits": alt_info["benefits"],
                        "price_difference": None
                    })
                    break
        
        # Add a generic healthy alternative if none found
        if not alternatives:
            alternatives.append({
                "product_id": "alt-generic",
                "name": "Whole, unprocessed food alternative",
                "brand": None,
                "image_url": None,
                "score": 95,
                "reason": "Whole foods provide nutrients without additives",
                "benefits": ["No additives", "Nutrient-dense", "Minimally processed"],
                "price_difference": None
            })
        
        return alternatives[:3]  # Return max 3 alternatives