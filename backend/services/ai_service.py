from pathlib import Path
import os
import json
import openai
from dotenv import load_dotenv

# Load environment variables from the .env file in the backend directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize OpenAI client with the API key
try:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not openai.api_key:
        raise ValueError("OPENAI_API_KEY is not set in the .env file")
    print(f"OpenAI API Key loaded successfully: {openai.api_key[:5]}...")  # Print first 5 chars for verification
except Exception as e:
    print(f"Error initializing OpenAI: {str(e)}")
    raise

class AIIngredientAnalyzer:
    @staticmethod
    async def analyze_ingredients(ingredients, health_profiles):
        try:
            print(f"Starting analysis for {len(ingredients)} ingredients")
            
            # Test the API key with a simple call
            test_response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'test'"}],
                max_tokens=5
            )
            print("OpenAI API test successful")

            # Rest of your analysis code...
            prompt = AIIngredientAnalyzer._create_analysis_prompt(ingredients, health_profiles)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a nutritionist AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content
            return AIIngredientAnalyzer._parse_llm_response(analysis)
            
        except Exception as e:
            print(f"Error in AI analysis: {str(e)}")
            return {
                "score": 50,
                "concerns": [f"AI analysis failed: {str(e)}"],
                "recommendations": [],
                "is_ai_analyzed": False
            }