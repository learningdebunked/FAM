from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Import AI service
from services.ai_service import AIIngredientAnalyzer

# Load environment variables
load_dotenv()

app = FastAPI(
    title="FAM Backend API",
    description="Backend API for Food-as-Medicine Nudger with AI Analysis",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENFOODFACTS_BASE_URL = "https://world.openfoodfacts.org/api/v2"

class AnalysisRequest(BaseModel):
    ingredients: List[str]
    health_profiles: List[str]
    use_ai: bool = True

@app.get("/api/products")
async def get_products(
    category: str = "beverages,snacks,cereals", 
    page_size: int = 50,
    use_ai: bool = False
):
    """
    Fetch products from OpenFoodFacts API with optional AI analysis
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENFOODFACTS_BASE_URL}/search",
                params={
                    "categories_tags_en": category,
                    "fields": "product_name,ingredients_text,image_url",
                    "size": page_size
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            products = []
            for product in data.get("products", []):
                ingredients = []
                if product.get("ingredients_text"):
                    # Basic ingredient parsing - can be enhanced
                    ingredients = [i.strip() for i in product["ingredients_text"].split(",") if i.strip()]
                
                products.append({
                    "name": product.get("product_name", "Unknown Product"),
                    "ingredients": ingredients,
                    "image_url": product.get("image_url", ""),
                })
            
            return {"products": products}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_ingredients(request: AnalysisRequest):
    """
    Analyze ingredients with AI based on health profiles
    """
    try:
        if not request.ingredients:
            raise HTTPException(status_code=400, detail="No ingredients provided")
        
        if not request.health_profiles:
            raise HTTPException(status_code=400, detail="No health profiles provided")
        
        if request.use_ai:
            # Use AI for analysis
            analysis = await AIIngredientAnalyzer.analyze_ingredients(
                request.ingredients,
                request.health_profiles
            )
            return analysis
        else:
            # Fallback to basic analysis
            return {
                "score": 50,
                "concerns": ["AI analysis not enabled"],
                "recommendations": [],
                "is_ai_analyzed": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
