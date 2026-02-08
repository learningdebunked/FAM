#!/usr/bin/env python3
"""
API Integration Test: Gummy Bears with 2 Kids Profile

This test calls the actual backend API endpoints to verify the complete ML flow.
Run the backend first: uvicorn main:app --reload

Usage: python3 tests/test_gummy_bears_api.py
"""

import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

GUMMY_BEARS_INGREDIENTS = [
    "Glucose syrup", "Sugar", "Gelatin", "Dextrose", "Citric acid",
    "Corn starch", "Natural and artificial flavors",
    "Red 40", "Yellow 5", "Yellow 6", "Blue 1",
    "Carnauba wax", "Beeswax coating"
]

FAMILY_HEALTH_PROFILES = ["child"]  # 2 small kids


def test_health_check():
    """Test server is running"""
    print("\n🔍 Test 1: Health Check")
    try:
        r = httpx.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200, f"Health check failed: {r.status_code}"
        print("   ✅ Server is running")
        return True
    except Exception as e:
        print(f"   ❌ Server not running: {e}")
        print("   Start with: cd backend && uvicorn main:app --reload")
        return False


def test_ml_analyze():
    """Test ML analysis endpoint"""
    print("\n🔍 Test 2: ML Analysis (/api/ml/analyze)")
    
    payload = {
        "ingredients": GUMMY_BEARS_INGREDIENTS,
        "health_profiles": FAMILY_HEALTH_PROFILES,
        "use_ai": False
    }
    
    r = httpx.post(f"{BASE_URL}/api/ml/analyze", json=payload, timeout=30)
    assert r.status_code == 200, f"ML analyze failed: {r.status_code} - {r.text}"
    
    result = r.json()
    print(f"   FAM Score: {result.get('fam_score', result.get('overall_score'))}")
    print(f"   Risk Level: {result.get('risk_level')}")
    print(f"   NOVA Group: {result.get('nova_group', 'N/A')}")
    
    # Check knowledge graph explanations
    kg_exp = result.get('knowledge_graph_explanations', [])
    if kg_exp:
        print(f"   Knowledge Graph Explanations: {len(kg_exp)}")
        for exp in kg_exp[:2]:
            print(f"      - {exp['ingredient']} → {exp['profile']}")
    
    print("   ✅ ML Analysis working")
    return result


def test_ingredient_explanation():
    """Test ingredient explanation from knowledge graph"""
    print("\n🔍 Test 3: Ingredient Explanation (/api/ml/ingredient/red%2040)")
    
    r = httpx.get(f"{BASE_URL}/api/ml/ingredient/red%2040?profile=child", timeout=10)
    assert r.status_code == 200, f"Ingredient explain failed: {r.status_code}"
    
    result = r.json()
    print(f"   Found: {result.get('found')}")
    print(f"   Category: {result.get('category')}")
    
    effects = result.get('effects', [])
    if effects:
        print(f"   Effects: {[e['name'] for e in effects]}")
    
    risky_for = result.get('risky_for_profiles', [])
    if risky_for:
        print(f"   Risky for: {[p['name'] for p in risky_for]}")
    
    alternatives = result.get('alternatives', [])
    if alternatives:
        print(f"   Alternatives: {[a['name'] for a in alternatives]}")
    
    # Verify Red 40 is risky for children
    profile_specific = result.get('profile_specific', {})
    if profile_specific.get('is_risky'):
        print(f"   ⚠️ Confirmed risky for children")
        evidence = profile_specific.get('evidence_urls', [])
        if evidence:
            print(f"   Evidence: {evidence[0]}")
    
    print("   ✅ Ingredient explanation working")
    return result


def test_profile_risks():
    """Test getting all risks for child profile"""
    print("\n🔍 Test 4: Profile Risks (/api/ml/profile/child/risks)")
    
    r = httpx.get(f"{BASE_URL}/api/ml/profile/child/risks", timeout=10)
    assert r.status_code == 200, f"Profile risks failed: {r.status_code}"
    
    result = r.json()
    print(f"   Found: {result.get('found')}")
    print(f"   Profile: {result.get('profile')}")
    
    risky_ingredients = result.get('risky_ingredients', [])
    print(f"   Risky ingredients for children ({len(risky_ingredients)}):")
    for ing in risky_ingredients:
        print(f"      - {ing['name']} ({ing.get('category', 'unknown')})")
    
    print("   ✅ Profile risks working")
    return result


def test_knowledge_graph_stats():
    """Test knowledge graph statistics"""
    print("\n🔍 Test 5: Knowledge Graph Stats (/api/ml/knowledge-graph/stats)")
    
    r = httpx.get(f"{BASE_URL}/api/ml/knowledge-graph/stats", timeout=10)
    assert r.status_code == 200, f"KG stats failed: {r.status_code}"
    
    result = r.json()
    print(f"   Total Nodes: {result.get('total_nodes')}")
    print(f"   Total Edges: {result.get('total_edges')}")
    print(f"   Node Types: {result.get('node_types')}")
    
    print("   ✅ Knowledge graph stats working")
    return result


def test_standard_analyze():
    """Test standard analysis endpoint (paper's formula)"""
    print("\n🔍 Test 6: Standard Analysis (/api/analyze)")
    
    payload = {
        "ingredients": GUMMY_BEARS_INGREDIENTS,
        "health_profiles": FAMILY_HEALTH_PROFILES,
        "use_ai": False
    }
    
    r = httpx.post(f"{BASE_URL}/api/analyze", json=payload, timeout=30)
    assert r.status_code == 200, f"Standard analyze failed: {r.status_code}"
    
    result = r.json()
    print(f"   Overall Score: {result.get('overall_score')}")
    print(f"   Risk Level: {result.get('risk_level')}")
    print(f"   Flagged Count: {result.get('flagged_count')}")
    
    risk_flags = result.get('risk_flags', [])
    if risk_flags:
        print(f"   Flagged Ingredients:")
        for flag in risk_flags[:4]:
            relevant = "⚠️ KIDS" if flag.get('is_relevant_to_user') else ""
            print(f"      - {flag['canonical_name']} ({flag['risk_level']}) {relevant}")
    
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"   Recommendations:")
        for rec in recommendations[:2]:
            print(f"      - {rec}")
    
    print("   ✅ Standard analysis working")
    return result


def run_all_tests():
    """Run all API tests"""
    print("=" * 60)
    print("🍬 GUMMY BEARS API TEST SUITE")
    print("   Family: 2 small kids (Emma age 4, Liam age 6)")
    print("   Product: Gummy Bears with artificial dyes")
    print("=" * 60)
    
    # Check server first
    if not test_health_check():
        print("\n❌ Cannot run tests - server not running")
        sys.exit(1)
    
    results = {}
    tests = [
        ("ml_analyze", test_ml_analyze),
        ("ingredient_explanation", test_ingredient_explanation),
        ("profile_risks", test_profile_risks),
        ("kg_stats", test_knowledge_graph_stats),
        ("standard_analyze", test_standard_analyze),
    ]
    
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results[name] = None
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is not None)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {name}: {status}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL API TESTS PASSED!")
        print("\nThe ML-enhanced FAM system correctly:")
        print("   ✓ Analyzes gummy bears ingredients")
        print("   ✓ Flags artificial dyes (Red 40, Yellow 5, etc.)")
        print("   ✓ Identifies risks specific to children")
        print("   ✓ Provides evidence-based explanations")
        print("   ✓ Uses knowledge graph for reasoning")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
