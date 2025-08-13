from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="FAM Backend API",
    description="Backend API for Food-as-Medicine Nudger",
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

@app.get("/api/products")
async def get_products(category: str = "beverages,snacks,cereals", page_size: int = 50):
    """
    Fetch products from OpenFoodFacts API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENFOODFACTS_BASE_URL}/search",
                params={
                    "categories_tags_en": category,
                    "fields": "product_name,ingredients_text",
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
                    ingredients = [i.strip() for i in product["ingredients_text"].split(",") if i.strip()]
                
                products.append({
                    "name": product.get("product_name", "Unnamed Product"),
                    "ingredients": ingredients
                })
            
            return {"products": products}
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Failed to fetch from OpenFoodFacts")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add more endpoints for classification as needed

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
