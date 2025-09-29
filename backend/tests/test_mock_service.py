"""Test script to verify the mock AI service works as expected."""
import asyncio
import json
from pathlib import Path
from services.mock_ai_service import MockAIIngredientAnalyzer

async def test_mock_service():
    """Test the mock AI service with sample inputs"""
    print("Testing Mock AI Service...")
    
    # Test case 1: Known test case with HFCS and Red 40
    print("\nTest Case 1: HFCS and Red 40")
    result1 = await MockAIIngredientAnalyzer.analyze_ingredients(
        "carbonated water, high fructose corn syrup, artificial colors, red 40, natural flavors, phosphoric acid",
        ["diabetic", "child"]
    )
    print("Result 1:", json.dumps(result1, indent=2))
    
    # Test case 2: Known test case with Aspartame and Caffeine
    print("\nTest Case 2: Aspartame and Caffeine")
    result2 = await MockAIIngredientAnalyzer.analyze_ingredients(
        "carbonated water, caramel color, aspartame, phosphoric acid, potassium benzoate, caffeine, natural flavors",
        ["diabetic", "child"]
    )
    print("Result 2:", json.dumps(result2, indent=2))
    
    # Test case 3: Unknown test case
    print("\nTest Case 3: Unknown ingredients")
    result3 = await MockAIIngredientAnalyzer.analyze_ingredients(
        "water, natural flavors",
        []
    )
    print("Result 3:", json.dumps(result3, indent=2))

if __name__ == "__main__":
    asyncio.run(test_mock_service())
