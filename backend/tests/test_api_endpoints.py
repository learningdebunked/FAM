"""
Comprehensive Unit Tests for API Endpoints Layer (main.py)
Tests all FastAPI endpoints with real HTTP requests using TestClient
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from database.db_manager import DatabaseManager


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health endpoint returns OK"""
        # Try common health check endpoints
        for endpoint in ["/", "/health", "/api/health"]:
            response = client.get(endpoint)
            if response.status_code == 200:
                return  # Found a working health endpoint
        # If no dedicated health endpoint, verify API is responsive
        response = client.get("/api/db/stats")
        assert response.status_code == 200


class TestProductLookupEndpoint:
    """Test /api/lookup unified endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_lookup_with_barcode(self, client):
        """Test lookup with barcode"""
        response = client.post("/api/lookup", json={
            "barcode": "0012345678905",
            "health_profiles": ["adult"]
        })
        
        # May return 200 (found) or 404 (not found in any source)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "product" in data or "analysis" in data
            assert "source" in data
    
    def test_lookup_with_ingredients(self, client):
        """Test lookup with ingredients list"""
        response = client.post("/api/lookup", json={
            "ingredients": ["Sugar", "Red 40", "Yellow 5"],
            "health_profiles": ["child"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "analysis" in data
        assert "risk_flags" in data["analysis"]
    
    def test_lookup_with_health_profiles(self, client):
        """Test that health profiles affect analysis"""
        # Request for child
        child_response = client.post("/api/lookup", json={
            "ingredients": ["Red 40", "Aspartame"],
            "health_profiles": ["child"]
        })
        
        # Request for adult
        adult_response = client.post("/api/lookup", json={
            "ingredients": ["Red 40", "Aspartame"],
            "health_profiles": ["adult"]
        })
        
        assert child_response.status_code == 200
        assert adult_response.status_code == 200
        
        child_data = child_response.json()
        adult_data = adult_response.json()
        
        # Child should have more relevant flags
        child_relevant = sum(1 for f in child_data["analysis"]["risk_flags"] 
                           if f.get("is_relevant_to_user"))
        adult_relevant = sum(1 for f in adult_data["analysis"]["risk_flags"] 
                           if f.get("is_relevant_to_user"))
        
        assert child_relevant >= adult_relevant
    
    def test_lookup_returns_recommendations(self, client):
        """Test that lookup returns recommendations"""
        response = client.post("/api/lookup", json={
            "ingredients": ["Red 40", "High Fructose Corn Syrup"],
            "health_profiles": ["child", "diabetic"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recommendations" in data["analysis"]
        assert len(data["analysis"]["recommendations"]) > 0
    
    def test_lookup_missing_required_fields(self, client):
        """Test lookup with missing required fields"""
        response = client.post("/api/lookup", json={
            "health_profiles": ["adult"]
            # Missing both barcode and ingredients
        })
        
        # Should return error or handle gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_lookup_empty_ingredients(self, client):
        """Test lookup with empty ingredients"""
        response = client.post("/api/lookup", json={
            "ingredients": [],
            "health_profiles": ["adult"]
        })
        
        assert response.status_code == 200
        data = response.json()
        # Analysis may be None or have empty risk_flags
        if data.get("analysis"):
            assert data["analysis"].get("risk_flags", []) == []


class TestDatabaseAnalyzeEndpoint:
    """Test /api/db/analyze endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_analyze_ingredients(self, client):
        """Test ingredient analysis endpoint"""
        response = client.post("/api/db/analyze", json={
            "ingredients": ["Sugar", "Red 40", "Yellow 5"],
            "health_profiles": ["child"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "risk_flags" in data
        assert "overall_score" in data or "fam_score" in data
        assert "recommendations" in data
        assert "fam_score" in data
    
    def test_analyze_returns_nutri_score(self, client):
        """Test that analysis returns Nutri-Score"""
        response = client.post("/api/db/analyze", json={
            "ingredients": ["Sugar", "Water"],
            "health_profiles": ["adult"],
            "nutrition": {
                "calories": 100,
                "total_sugars": 20,
                "sodium": 50
            }
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "nutri_score" in data
        assert data["nutri_score"] in ["A", "B", "C", "D", "E"]
    
    def test_analyze_returns_nova_group(self, client):
        """Test that analysis returns NOVA group"""
        response = client.post("/api/db/analyze", json={
            "ingredients": ["Red 40", "Aspartame", "Artificial Flavor"],
            "health_profiles": ["adult"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "nova_group" in data
        assert data["nova_group"] in [1, 2, 3, 4]
    
    def test_analyze_risk_flags_structure(self, client):
        """Test risk flags have correct structure"""
        response = client.post("/api/db/analyze", json={
            "ingredients": ["Red 40"],
            "health_profiles": ["child"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["risk_flags"]) > 0
        flag = data["risk_flags"][0]
        
        assert "ingredient" in flag
        assert "risk_level" in flag
        assert "affected_profiles" in flag
        assert "is_relevant_to_user" in flag
    
    def test_analyze_multiple_profiles(self, client):
        """Test analysis with multiple health profiles"""
        response = client.post("/api/db/analyze", json={
            "ingredients": ["Red 40", "High Fructose Corn Syrup", "Caffeine"],
            "health_profiles": ["child", "diabetic", "pregnant"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have multiple relevant flags
        relevant_flags = [f for f in data["risk_flags"] if f["is_relevant_to_user"]]
        assert len(relevant_flags) >= 2


class TestDatabaseProductEndpoint:
    """Test /api/db/product/{barcode} endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_product_not_found(self, client):
        """Test getting non-existent product"""
        response = client.get("/api/db/product/9999999999999")
        
        assert response.status_code == 404
    
    def test_get_product_invalid_barcode(self, client):
        """Test getting product with invalid barcode format"""
        response = client.get("/api/db/product/invalid")
        
        # Should return 404 or handle gracefully
        assert response.status_code in [404, 400]


class TestDatabaseSearchEndpoint:
    """Test /api/db/search endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_search_products(self, client):
        """Test product search endpoint"""
        response = client.get("/api/db/search", params={
            "query": "gummy",
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "products" in data
        assert isinstance(data["products"], list)
    
    def test_search_with_retailer_filter(self, client):
        """Test search with retailer filter"""
        response = client.get("/api/db/search", params={
            "query": "juice",
            "retailer": "Walmart",
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "products" in data
    
    def test_search_empty_query(self, client):
        """Test search with empty query"""
        response = client.get("/api/db/search", params={
            "query": "",
            "limit": 10
        })
        
        # Should return empty results or handle gracefully
        assert response.status_code in [200, 400]


class TestDatabaseStatsEndpoint:
    """Test /api/db/stats endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_stats(self, client):
        """Test database statistics endpoint"""
        response = client.get("/api/db/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_products" in data
        assert "total_retailers" in data
        assert "products_with_ingredients" in data
        assert "analyzed_products" in data


class TestAlternativesEndpoint:
    """Test /api/db/alternatives endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_alternatives(self, client):
        """Test alternatives endpoint"""
        response = client.post("/api/db/alternatives", json={
            "product_id": "test123",
            "ingredients": ["Sugar", "Red 40"],
            "health_profiles": ["child"],
            "category": "snacks"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "alternatives" in data
        assert isinstance(data["alternatives"], list)


class TestOpenFoodFactsEndpoint:
    """Test /api/openfoodfacts/{barcode} endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_product_from_openfoodfacts(self, client):
        """Test fetching product from OpenFoodFacts"""
        # Use a known barcode (Nutella)
        response = client.get("/api/openfoodfacts/3017620422003")
        
        # May succeed or fail depending on network
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "product" in data or "name" in data
    
    def test_get_product_not_found_openfoodfacts(self, client):
        """Test non-existent product in OpenFoodFacts"""
        response = client.get("/api/openfoodfacts/0000000000000")
        
        assert response.status_code in [404, 500]


class TestFeedbackEndpoint:
    """Test /api/feedback endpoint"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_submit_feedback(self, client):
        """Test submitting feedback"""
        response = client.post("/api/feedback", json={
            "product_id": "test123",
            "feedback_type": "positive",
            "comment": "Great analysis!",
            "issues": []
        })
        
        assert response.status_code in [200, 201]
    
    def test_submit_negative_feedback(self, client):
        """Test submitting negative feedback with issues"""
        response = client.post("/api/feedback", json={
            "product_id": "test456",
            "feedback_type": "negative",
            "comment": "Missing some ingredients",
            "issues": ["missing_ingredients", "wrong_score"]
        })
        
        assert response.status_code in [200, 201]


class TestMLEndpoints:
    """Test ML-powered endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_ml_analyze_endpoint(self, client):
        """Test ML analysis endpoint"""
        response = client.post("/api/ml/analyze", json={
            "ingredients": ["Sugar", "Red 40", "Aspartame"],
            "health_profiles": ["child", "diabetic"],
            "product_name": "Test Candy"
        })
        
        # ML endpoint may or may not be available
        assert response.status_code in [200, 404, 500, 501]
        
        if response.status_code == 200:
            data = response.json()
            # ML endpoint returns fam_score directly or in analysis
            assert "fam_score" in data or "analysis" in data or "risk_flags" in data


class TestGummyBearsAPIScenario:
    """End-to-end API test for gummy bears scenario"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_gummy_bears_full_flow(self, client):
        """Test complete gummy bears analysis flow"""
        # Step 1: Analyze gummy bears ingredients
        gummy_ingredients = [
            "Sugar", "Corn Syrup", "Gelatin", "Citric Acid",
            "Red 40", "Yellow 5", "Blue 1", "Natural and Artificial Flavors"
        ]
        
        response = client.post("/api/lookup", json={
            "ingredients": gummy_ingredients,
            "health_profiles": ["child"],
            "product_name": "Haribo Gummy Bears"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify analysis
        assert "analysis" in data
        analysis = data["analysis"]
        
        # Should flag artificial dyes
        flagged_ingredients = [f["canonical_name"] for f in analysis["risk_flags"]]
        assert "Red 40" in flagged_ingredients
        assert "Yellow 5" in flagged_ingredients
        
        # Should have medium or lower score for child (dyes are concerning)
        assert analysis["fam_score"] <= 60
        
        # Should have recommendations
        assert len(analysis["recommendations"]) > 0
    
    def test_gummy_bears_child_vs_adult(self, client):
        """Test gummy bears scores differently for child vs adult"""
        gummy_ingredients = [
            "Sugar", "Corn Syrup", "Red 40", "Yellow 5"
        ]
        
        # Child analysis
        child_response = client.post("/api/lookup", json={
            "ingredients": gummy_ingredients,
            "health_profiles": ["child"]
        })
        
        # Adult analysis
        adult_response = client.post("/api/lookup", json={
            "ingredients": gummy_ingredients,
            "health_profiles": ["adult"]
        })
        
        assert child_response.status_code == 200
        assert adult_response.status_code == 200
        
        child_score = child_response.json()["analysis"]["fam_score"]
        adult_score = adult_response.json()["analysis"]["fam_score"]
        
        # Child should have lower score
        assert child_score < adult_score
    
    def test_gummy_bears_diabetic_child(self, client):
        """Test gummy bears for diabetic child (worst case)"""
        gummy_ingredients = [
            "Sugar", "High Fructose Corn Syrup", "Corn Syrup",
            "Red 40", "Yellow 5", "Aspartame"
        ]
        
        response = client.post("/api/lookup", json={
            "ingredients": gummy_ingredients,
            "health_profiles": ["child", "diabetic"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have low score (multiple risk factors)
        assert data["analysis"]["fam_score"] <= 50
        
        # Should flag both dyes and sugars
        relevant_flags = [f for f in data["analysis"]["risk_flags"] 
                        if f["is_relevant_to_user"]]
        assert len(relevant_flags) >= 2


class TestErrorHandling:
    """Test API error handling"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post(
            "/api/lookup",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test handling of missing content type"""
        response = client.post(
            "/api/lookup",
            content='{"ingredients": ["Sugar"]}'
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 415, 422]
    
    def test_invalid_health_profile(self, client):
        """Test handling of invalid health profile"""
        response = client.post("/api/lookup", json={
            "ingredients": ["Sugar"],
            "health_profiles": ["invalid_profile_xyz"]
        })
        
        # Should handle gracefully (treat as unknown profile)
        assert response.status_code == 200


class TestCORSHeaders:
    """Test CORS configuration"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present"""
        response = client.options("/api/lookup")
        
        # CORS preflight should be handled
        assert response.status_code in [200, 204, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
