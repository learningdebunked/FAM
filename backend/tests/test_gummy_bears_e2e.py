"""
End-to-End Test: Gummy Bears Analysis with Family Profile (2 Kids)

This test simulates the complete flow:
1. Set up family profile with 2 small kids
2. Analyze gummy bears ingredients
3. Verify ML model flags artificial dyes as high risk for children
4. Check that alternatives are suggested

Run with: python -m pytest tests/test_gummy_bears_e2e.py -v
Or directly: python tests/test_gummy_bears_e2e.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import asyncio
from typing import Dict, List

# Test data
GUMMY_BEARS_INGREDIENTS = [
    "Glucose syrup",
    "Sugar", 
    "Gelatin",
    "Dextrose",
    "Citric acid",
    "Corn starch",
    "Natural and artificial flavors",
    "Red 40",
    "Yellow 5", 
    "Yellow 6",
    "Blue 1",
    "Carnauba wax",
    "Beeswax coating"
]

FAMILY_PROFILE = {
    "members": [
        {"name": "Emma", "type": "child", "age": 4},
        {"name": "Liam", "type": "child", "age": 6}
    ],
    "health_profiles": ["child"]  # Both are children
}


def test_gummy_bears_with_rule_based_scoring():
    """Test using the rule-based product service (paper's formula)"""
    print("\n" + "="*60)
    print("TEST 1: Rule-Based Scoring (Paper's Formula)")
    print("="*60)
    
    from services.product_service import ProductService
    
    service = ProductService()
    
    # Analyze gummy bears for children
    result = service.analyze_ingredients(
        ingredients=GUMMY_BEARS_INGREDIENTS,
        health_profiles=["child"]
    )
    
    print(f"\n📊 Analysis Results:")
    print(f"   FAM Score: {result['overall_score']}/100")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Total Ingredients: {result.get('total_ingredients', len(GUMMY_BEARS_INGREDIENTS))}")
    print(f"   Flagged Count: {result.get('flagged_count', len(result.get('risk_flags', [])))}")
    
    # Check flagged ingredients
    risk_flags = result.get('risk_flags', [])
    print(f"\n🚩 Flagged Ingredients ({len(risk_flags)}):")
    for flag in risk_flags:
        relevance = "⚠️ RELEVANT TO KIDS" if flag.get('is_relevant_to_user') else ""
        print(f"   - {flag['canonical_name']} ({flag['risk_level']}) {relevance}")
    
    # Verify expected flags
    flagged_names = [f['canonical_name'].lower() for f in risk_flags]
    
    # Artificial dyes should be flagged
    assert any('red' in name or 'yellow' in name or 'blue' in name for name in flagged_names), \
        "Artificial dyes should be flagged"
    
    # Check recommendations
    recommendations = result.get('recommendations', [])
    print(f"\n💡 Recommendations ({len(recommendations)}):")
    for rec in recommendations:
        print(f"   - {rec}")
    
    # Score should be low for gummy bears (lots of artificial ingredients)
    assert result['overall_score'] < 70, \
        f"Score should be below 70 for gummy bears, got {result['overall_score']}"
    
    print(f"\n✅ Rule-based test PASSED")
    return result


def test_gummy_bears_with_ml_scoring():
    """Test using the ML-enhanced scoring"""
    print("\n" + "="*60)
    print("TEST 2: ML-Enhanced Scoring")
    print("="*60)
    
    from services.ml_service import get_ml_service
    
    ml_service = get_ml_service()
    
    # Build product dict
    product = {
        'name': 'Gummy Bears',
        'ingredients': GUMMY_BEARS_INGREDIENTS,
        'nutrition': {
            'calories': 140,
            'sugars': 28,
            'protein': 3,
            'fat': 0,
            'sodium': 25
        }
    }
    
    # Analyze with ML
    result = ml_service.analyze_product_ml(
        product=product,
        health_profiles=["child"],
        user_id="test_user_123"
    )
    
    print(f"\n📊 ML Analysis Results:")
    print(f"   FAM Score: {result['fam_score']}/100")
    print(f"   Base Score: {result['base_score']}")
    print(f"   Personalization Adjustment: {result['personalization_adjustment']}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   NOVA Group: {result.get('nova_group', 'N/A')}")
    
    # Check knowledge graph explanations
    kg_explanations = result.get('knowledge_graph_explanations', [])
    print(f"\n📚 Knowledge Graph Explanations ({len(kg_explanations)}):")
    for exp in kg_explanations:
        print(f"\n   Ingredient: {exp['ingredient']}")
        print(f"   Profile: {exp['profile']}")
        for chain in exp.get('explanation_chain', []):
            print(f"      → {chain}")
        if exp.get('evidence'):
            print(f"   Evidence: {exp['evidence'][0]}")
        if exp.get('alternatives'):
            alt_names = [a['name'] for a in exp['alternatives']]
            print(f"   Alternatives: {', '.join(alt_names)}")
    
    # Check ML ingredient risks
    ml_risks = result.get('ml_ingredient_risks', [])
    if ml_risks:
        print(f"\n🤖 ML-Predicted Ingredient Risks:")
        for risk in ml_risks:
            print(f"   - {risk['ingredient']}: {risk['predicted_risk']} (confidence: {risk['confidence']:.2f})")
    
    # Score should be low
    assert result['fam_score'] < 70, \
        f"ML Score should be below 70 for gummy bears, got {result['fam_score']}"
    
    print(f"\n✅ ML-enhanced test PASSED")
    return result


def test_knowledge_graph_for_kids():
    """Test knowledge graph queries for child profile"""
    print("\n" + "="*60)
    print("TEST 3: Knowledge Graph - Risks for Children")
    print("="*60)
    
    from ml.knowledge_graph import FoodHealthKnowledgeGraph
    
    kg = FoodHealthKnowledgeGraph()
    
    # Query all risky ingredients for children
    child_risks = kg.query_by_profile("child")
    
    print(f"\n👶 Ingredients risky for children ({child_risks['count']}):")
    for ing in child_risks.get('risky_ingredients', []):
        print(f"   - {ing['name']} ({ing.get('category', 'unknown')})")
    
    # Test specific ingredient explanations
    print(f"\n🔍 Detailed explanation for Red 40 + Child:")
    red40_explanation = kg.explain_risk("red 40", "child")
    
    if red40_explanation.get('is_risky'):
        print(f"   Is Risky: Yes")
        for chain in red40_explanation.get('explanation_chain', []):
            print(f"   → {chain}")
        print(f"   Evidence: {red40_explanation.get('evidence_urls', ['N/A'])[0]}")
        
        alts = red40_explanation.get('alternatives', [])
        if alts:
            print(f"   Suggested alternatives: {[a['name'] for a in alts]}")
    
    # Verify Red 40 is flagged for children
    assert red40_explanation.get('is_risky'), "Red 40 should be risky for children"
    
    print(f"\n✅ Knowledge graph test PASSED")
    return child_risks


def test_alternatives_for_gummy_bears():
    """Test alternative recommendations"""
    print("\n" + "="*60)
    print("TEST 4: Alternative Recommendations")
    print("="*60)
    
    from services.product_service import ProductService
    
    service = ProductService()
    
    # Get alternatives based on flagged ingredients
    alternatives = service.get_alternatives(
        ingredients=GUMMY_BEARS_INGREDIENTS,
        health_profiles=["child"],
        category="candy"
    )
    
    print(f"\n🔄 Suggested Alternatives ({len(alternatives)}):")
    for alt in alternatives:
        print(f"\n   📦 {alt['name']}")
        print(f"      Score: {alt['score']}/100")
        print(f"      Reason: {alt['reason']}")
        if alt.get('benefits'):
            print(f"      Benefits: {', '.join(alt['benefits'])}")
        if alt.get('replaces'):
            print(f"      Replaces: {alt['replaces']}")
    
    # Should have at least one alternative
    assert len(alternatives) > 0, "Should suggest at least one alternative"
    
    print(f"\n✅ Alternatives test PASSED")
    return alternatives


def test_full_api_flow():
    """Test the complete API flow as the mobile app would call it"""
    print("\n" + "="*60)
    print("TEST 5: Full API Flow Simulation")
    print("="*60)
    
    import httpx
    
    # Check if server is running
    try:
        response = httpx.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code != 200:
            print("⚠️ Backend server not running. Start with: uvicorn main:app --reload")
            print("   Skipping API test...")
            return None
    except:
        print("⚠️ Backend server not running. Start with: uvicorn main:app --reload")
        print("   Skipping API test...")
        return None
    
    print("✅ Backend server is running")
    
    # Test ML analyze endpoint
    print("\n📡 Calling /api/ml/analyze...")
    response = httpx.post(
        "http://localhost:8000/api/ml/analyze",
        json={
            "ingredients": GUMMY_BEARS_INGREDIENTS,
            "health_profiles": ["child"],
            "use_ai": False
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   FAM Score: {result.get('fam_score', result.get('overall_score'))}")
        print(f"   Risk Level: {result.get('risk_level')}")
        print(f"   Flagged: {result.get('flagged_count', len(result.get('risk_flags', [])))}")
        print("✅ API test PASSED")
        return result
    else:
        print(f"❌ API returned {response.status_code}: {response.text}")
        return None


def run_all_tests():
    """Run all tests and print summary"""
    print("\n" + "🧪"*30)
    print("   GUMMY BEARS E2E TEST SUITE")
    print("   Family Profile: 2 Kids (Emma age 4, Liam age 6)")
    print("🧪"*30)
    
    results = {}
    
    # Test 1: Rule-based scoring
    try:
        results['rule_based'] = test_gummy_bears_with_rule_based_scoring()
    except Exception as e:
        print(f"❌ Rule-based test FAILED: {e}")
        results['rule_based'] = None
    
    # Test 2: ML-enhanced scoring
    try:
        results['ml_enhanced'] = test_gummy_bears_with_ml_scoring()
    except Exception as e:
        print(f"❌ ML-enhanced test FAILED: {e}")
        results['ml_enhanced'] = None
    
    # Test 3: Knowledge graph
    try:
        results['knowledge_graph'] = test_knowledge_graph_for_kids()
    except Exception as e:
        print(f"❌ Knowledge graph test FAILED: {e}")
        results['knowledge_graph'] = None
    
    # Test 4: Alternatives
    try:
        results['alternatives'] = test_alternatives_for_gummy_bears()
    except Exception as e:
        print(f"❌ Alternatives test FAILED: {e}")
        results['alternatives'] = None
    
    # Test 5: Full API flow
    try:
        results['api_flow'] = test_full_api_flow()
    except Exception as e:
        print(f"❌ API flow test FAILED: {e}")
        results['api_flow'] = None
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is not None)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result is not None else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    return results


if __name__ == "__main__":
    run_all_tests()
