from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Import AI service
from services.ai_service import AIIngredientAnalyzer
from services.product_service import get_product_service

# Load environment variables
load_dotenv()

app = FastAPI(
    title="FAM Backend API",
    description="Backend API for Food-as-Medicine Nudger with AI Analysis and Local Product Database",
    version="2.0.0"
)

# Initialize product service
product_service = get_product_service()

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

class AlternativesRequest(BaseModel):
    product_id: str
    ingredients: List[str]
    health_profiles: List[str]
    category: Optional[str] = None

class FeedbackRequest(BaseModel):
    product_id: str
    feedback_type: str  # 'positive' or 'negative'
    comment: Optional[str] = None
    issues: Optional[List[str]] = None
    timestamp: Optional[str] = None

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
        
        # Use default health profiles if none provided
        health_profiles = request.health_profiles if request.health_profiles else ["adult"]
        
        if request.use_ai:
            # Use AI for analysis
            analysis = await AIIngredientAnalyzer.analyze_ingredients(
                request.ingredients,
                health_profiles
            )
            return analysis
        else:
            # Fallback to basic analysis
            return {
                "risk_flags": [],
                "overall_risk_score": 50,
                "recommendations": ["AI analysis not enabled. Enable AI for detailed ingredient analysis."],
                "is_ai_analyzed": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/alternatives")
async def get_alternatives(request: AlternativesRequest):
    """
    Get healthy alternative suggestions based on flagged ingredients and health profiles
    """
    try:
        # First analyze the current product
        analysis = await AIIngredientAnalyzer.analyze_ingredients(
            request.ingredients,
            request.health_profiles
        )
        
        # Generate alternatives based on risk flags
        alternatives = await AIIngredientAnalyzer.generate_alternatives(
            request.ingredients,
            request.health_profiles,
            analysis.get('risk_flags', []),
            request.category
        )
        
        return {"alternatives": alternatives}
        
    except Exception as e:
        # Return empty alternatives on error
        print(f"Error getting alternatives: {e}")
        return {"alternatives": []}

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for telemetry and improvement
    """
    try:
        # Log feedback for telemetry (in production, store in database)
        print(f"Feedback received: {request.feedback_type} for product {request.product_id}")
        if request.comment:
            print(f"Comment: {request.comment}")
        if request.issues:
            print(f"Issues: {request.issues}")
        
        return {"status": "success", "message": "Feedback recorded"}
        
    except Exception as e:
        print(f"Error recording feedback: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

# ==================== New Database-Backed Endpoints ====================

@app.get("/api/db/search")
async def search_products_db(
    query: str = Query(..., description="Search query"),
    retailer: Optional[str] = Query(None, description="Filter by retailer name"),
    limit: int = Query(20, description="Max results")
):
    """
    Search products in local database
    """
    try:
        products = product_service.search_products(query, retailer=retailer, limit=limit)
        return {"products": products, "count": len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/db/product/{barcode}")
async def get_product_by_barcode(barcode: str):
    """
    Get product by barcode from local database
    """
    try:
        product = product_service.get_product_by_barcode(barcode)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/analyze")
async def analyze_with_database(request: AnalysisRequest):
    """
    Analyze ingredients using local risk database
    Falls back to AI if needed
    """
    try:
        if not request.ingredients:
            raise HTTPException(status_code=400, detail="No ingredients provided")
        
        health_profiles = request.health_profiles if request.health_profiles else ["adult"]
        
        # Use local database analysis
        analysis = product_service.analyze_ingredients(
            request.ingredients,
            health_profiles
        )
        
        # If AI is requested and we have few flags, try AI for more detail
        if request.use_ai and len(analysis.get('risk_flags', [])) < 2:
            try:
                ai_analysis = await AIIngredientAnalyzer.analyze_ingredients(
                    request.ingredients,
                    health_profiles
                )
                if ai_analysis.get('is_ai_analyzed'):
                    return ai_analysis
            except:
                pass  # Fall back to database analysis
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/alternatives")
async def get_alternatives_from_db(request: AlternativesRequest):
    """
    Get healthy alternatives using local database
    """
    try:
        alternatives = product_service.get_alternatives(
            ingredients=request.ingredients,
            health_profiles=request.health_profiles,
            category=request.category
        )
        return {"alternatives": alternatives}
    except Exception as e:
        return {"alternatives": [], "error": str(e)}

@app.get("/api/db/retailers")
async def get_retailers(region: Optional[str] = None):
    """
    Get list of supported retailers
    """
    try:
        from database.db_manager import get_db
        db = get_db()
        retailers = db.get_retailers(region=region)
        return {"retailers": retailers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/db/stats")
async def get_database_stats():
    """
    Get database statistics
    """
    try:
        from database.db_manager import get_db
        db = get_db()
        stats = db.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pipeline/run")
async def run_scraping_pipeline(
    retailers: Optional[List[str]] = None,
    max_products: int = Query(50, description="Max products per category")
):
    """
    Trigger the scraping pipeline (async, returns immediately)
    """
    import asyncio
    from scrapers.pipeline import DataPipeline
    
    # Run pipeline in background
    async def run_in_background():
        pipeline = DataPipeline()
        await pipeline.run_full_pipeline(
            retailers=retailers,
            max_products_per_category=max_products
        )
    
    asyncio.create_task(run_in_background())
    
    return {
        "status": "started",
        "message": f"Pipeline started for retailers: {retailers or 'all'}",
        "max_products_per_category": max_products
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
