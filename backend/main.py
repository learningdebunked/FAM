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

# ==================== Unified Tiered Lookup Endpoint ====================

class TieredLookupRequest(BaseModel):
    barcode: Optional[str] = None
    ingredients: Optional[List[str]] = None
    health_profiles: List[str] = []
    product_name: Optional[str] = None
    use_ai_fallback: bool = True

@app.post("/api/lookup")
async def tiered_product_lookup(request: TieredLookupRequest):
    """
    Unified tiered product lookup with optimal performance.
    
    Flow:
    1. Check local database first (fastest, <50ms)
    2. Fall back to OpenFoodFacts if not found (~200ms)
    3. Analyze using local risk database (fast)
    4. Fall back to AI analysis only if needed (~2-5s)
    5. Cache result for future lookups
    
    Returns complete product info with FAM analysis.
    """
    import time
    start_time = time.time()
    
    result = {
        'product': None,
        'analysis': None,
        'alternatives': [],
        'source': None,
        'cached': False,
        'lookup_time_ms': 0
    }
    
    health_profiles = request.health_profiles if request.health_profiles else ['adult']
    
    # ==================== TIER 1: Local Database ====================
    if request.barcode:
        local_product = product_service.get_product_by_barcode(request.barcode)
        
        if local_product:
            result['product'] = {
                'id': str(local_product.get('id')),
                'name': local_product.get('name'),
                'brand': local_product.get('brand'),
                'barcode': request.barcode,
                'ingredients': local_product.get('ingredients', []),
                'image_url': local_product.get('image_url'),
                'nutrition': local_product.get('nutrition', {})
            }
            result['source'] = 'local_database'
            result['cached'] = True
            
            # Check if we have cached analysis
            if local_product.get('analysis'):
                result['analysis'] = local_product['analysis']
                result['alternatives'] = local_product.get('alternatives', [])
                result['lookup_time_ms'] = int((time.time() - start_time) * 1000)
                return result
    
    # ==================== TIER 2: OpenFoodFacts ====================
    if request.barcode and not result['product']:
        try:
            async with httpx.AsyncClient() as client:
                off_response = await client.get(
                    f"https://world.openfoodfacts.org/api/v2/product/{request.barcode}",
                    params={"fields": "product_name,brands,ingredients_text,image_url,nutriments"},
                    timeout=5.0
                )
                
                if off_response.status_code == 200:
                    off_data = off_response.json()
                    if off_data.get('status') == 1:
                        off_product = off_data.get('product', {})
                        
                        # Parse ingredients
                        ingredients_text = off_product.get('ingredients_text', '')
                        ingredients = [i.strip() for i in ingredients_text.split(',') if i.strip()]
                        
                        # Parse nutrition
                        nutriments = off_product.get('nutriments', {})
                        nutrition = {
                            'calories': nutriments.get('energy-kcal_100g', 0),
                            'sugars': nutriments.get('sugars_100g', 0),
                            'saturated_fat': nutriments.get('saturated-fat_100g', 0),
                            'sodium': nutriments.get('sodium_100g', 0) * 1000,  # Convert to mg
                            'fiber': nutriments.get('fiber_100g', 0),
                            'protein': nutriments.get('proteins_100g', 0)
                        }
                        
                        result['product'] = {
                            'id': request.barcode,
                            'name': off_product.get('product_name', 'Unknown Product'),
                            'brand': off_product.get('brands'),
                            'barcode': request.barcode,
                            'ingredients': ingredients,
                            'image_url': off_product.get('image_url'),
                            'nutrition': nutrition
                        }
                        result['source'] = 'openfoodfacts'
        except Exception as e:
            print(f"OpenFoodFacts lookup failed: {e}")
    
    # If we have ingredients from request, use those
    if request.ingredients and not result['product']:
        result['product'] = {
            'id': 'manual-entry',
            'name': request.product_name or 'Manual Entry',
            'brand': None,
            'barcode': None,
            'ingredients': request.ingredients,
            'image_url': None,
            'nutrition': {}
        }
        result['source'] = 'manual_entry'
    
    # ==================== TIER 3: Analysis ====================
    if result['product'] and result['product'].get('ingredients'):
        ingredients = result['product']['ingredients']
        nutrition = result['product'].get('nutrition', {})
        
        # Try local risk database analysis first (fast)
        try:
            local_analysis = product_service.analyze_ingredients(
                ingredients,
                health_profiles,
                nutrition=nutrition
            )
            result['analysis'] = local_analysis
            
            # Get alternatives
            alternatives = product_service.get_alternatives(
                ingredients=ingredients,
                health_profiles=health_profiles
            )
            result['alternatives'] = alternatives
            
        except Exception as e:
            print(f"Local analysis failed: {e}")
        
        # ==================== TIER 4: AI Fallback ====================
        # Only use AI if:
        # 1. Local analysis found few/no flags
        # 2. AI fallback is enabled
        # 3. We have ingredients to analyze
        if (request.use_ai_fallback and 
            result['analysis'] and 
            len(result['analysis'].get('risk_flags', [])) < 2):
            try:
                ai_analysis = await AIIngredientAnalyzer.analyze_ingredients(
                    ingredients,
                    health_profiles
                )
                
                if ai_analysis.get('is_ai_analyzed'):
                    # Merge AI insights with local analysis
                    result['analysis']['ai_insights'] = ai_analysis.get('risk_flags', [])
                    result['analysis']['ai_recommendations'] = ai_analysis.get('recommendations', [])
                    result['analysis']['has_ai_enhancement'] = True
                    
            except Exception as e:
                print(f"AI analysis failed (non-critical): {e}")
    
    # ==================== Cache Result ====================
    # TODO: Cache to local database for future lookups
    # if result['source'] == 'openfoodfacts' and result['product']:
    #     product_service.cache_product(result['product'], result['analysis'])
    
    result['lookup_time_ms'] = int((time.time() - start_time) * 1000)
    return result

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

# ==================== ML-Powered Endpoints ====================

@app.post("/api/ml/analyze")
async def analyze_with_ml(request: AnalysisRequest):
    """
    Analyze product using ML models and knowledge graph
    
    Provides:
    - ML-based health fit score
    - Knowledge graph explanations with evidence
    - Personalized adjustments based on user history
    """
    try:
        from services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        # Build product dict from request
        product = {
            'ingredients': request.ingredients,
            'nutrition': {}  # Can be extended to include nutrition data
        }
        
        health_profiles = request.health_profiles if request.health_profiles else ['adult']
        
        analysis = ml_service.analyze_product_ml(
            product, 
            health_profiles,
            user_id=None  # Can be extended to include user_id
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml/alternatives")
async def get_ml_alternatives(request: AlternativesRequest):
    """
    Get smart alternatives using ML embeddings
    """
    try:
        from services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        product = {
            'ingredients': request.ingredients,
            'category': request.category
        }
        
        health_profiles = request.health_profiles if request.health_profiles else ['adult']
        
        alternatives = ml_service.get_smart_alternatives(product, health_profiles)
        
        return {"alternatives": alternatives}
        
    except Exception as e:
        return {"alternatives": [], "error": str(e)}

@app.get("/api/ml/ingredient/{ingredient}")
async def explain_ingredient(
    ingredient: str,
    profile: Optional[str] = Query(None, description="Health profile for specific risks")
):
    """
    Get detailed explanation for an ingredient from knowledge graph
    """
    try:
        from services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        explanation = ml_service.explain_ingredient(ingredient, profile)
        return explanation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/profile/{profile}/risks")
async def get_profile_risks(profile: str):
    """
    Get all ingredients risky for a specific health profile
    """
    try:
        from services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        risks = ml_service.get_profile_risks(profile)
        return risks
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ml/feedback")
async def record_feedback(
    user_id: str,
    product_id: str,
    feedback_type: str,  # 'like', 'dislike', 'swap_accepted', 'swap_rejected'
    context: Optional[Dict] = None
):
    """
    Record user feedback for personalization
    """
    try:
        from services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        ml_service.record_user_feedback(user_id, product_id, feedback_type, context)
        
        return {"status": "recorded", "feedback_type": feedback_type}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/user/{user_id}/insights")
async def get_user_insights(user_id: str):
    """
    Get personalization insights for a user
    """
    try:
        from services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        insights = ml_service.get_user_insights(user_id)
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ml/knowledge-graph/stats")
async def get_kg_stats():
    """
    Get knowledge graph statistics
    """
    try:
        from services.ml_service import get_ml_service
        ml_service = get_ml_service()
        
        stats = ml_service.get_knowledge_graph_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
