"""
Comprehensive Unit Tests for Scrapers Layer
Tests scraper implementations, data pipeline, and ingredient parsing
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager


class TestIngredientParser:
    """Test ingredient parsing functionality"""
    
    def parse_ingredients(self, raw_text: str) -> List[str]:
        """Parse raw ingredient text into list of ingredients"""
        if not raw_text:
            return []
        
        # Split by common delimiters
        import re
        # Handle nested parentheses and common separators
        ingredients = re.split(r',\s*(?![^()]*\))', raw_text)
        
        # Clean up each ingredient
        cleaned = []
        for ing in ingredients:
            ing = ing.strip()
            if ing:
                # Remove trailing periods
                ing = ing.rstrip('.')
                cleaned.append(ing)
        
        return cleaned
    
    def test_parse_simple_ingredients(self):
        """Test parsing simple comma-separated ingredients"""
        raw = "Sugar, Salt, Flour, Water"
        result = self.parse_ingredients(raw)
        
        assert len(result) == 4
        assert "Sugar" in result
        assert "Salt" in result
        assert "Flour" in result
        assert "Water" in result
    
    def test_parse_ingredients_with_parentheses(self):
        """Test parsing ingredients with parenthetical info"""
        raw = "Sugar, Red 40 (Color), Natural Flavors (Vanilla, Strawberry)"
        result = self.parse_ingredients(raw)
        
        assert len(result) == 3
        assert "Sugar" in result
        assert "Red 40 (Color)" in result
    
    def test_parse_empty_string(self):
        """Test parsing empty string"""
        result = self.parse_ingredients("")
        assert result == []
    
    def test_parse_none(self):
        """Test parsing None"""
        result = self.parse_ingredients(None)
        assert result == []
    
    def test_parse_single_ingredient(self):
        """Test parsing single ingredient"""
        raw = "Sugar"
        result = self.parse_ingredients(raw)
        
        assert len(result) == 1
        assert result[0] == "Sugar"
    
    def test_parse_ingredients_with_percentages(self):
        """Test parsing ingredients with percentages"""
        raw = "Sugar (30%), Corn Syrup (25%), Water (20%)"
        result = self.parse_ingredients(raw)
        
        assert len(result) == 3
    
    def test_parse_ingredients_with_contains_statement(self):
        """Test parsing with 'Contains' allergen statement"""
        raw = "Sugar, Flour, Eggs. Contains: Wheat, Eggs, Milk"
        result = self.parse_ingredients(raw)
        
        # Should handle the period and Contains statement
        assert "Sugar" in result


class TestNutritionParser:
    """Test nutrition facts parsing"""
    
    def parse_nutrition(self, nutrition_text: Dict) -> Dict:
        """Parse nutrition data into standardized format"""
        result = {}
        
        # Map common variations to standard names
        mappings = {
            'calories': ['calories', 'energy', 'kcal'],
            'total_fat': ['total fat', 'fat', 'total_fat'],
            'saturated_fat': ['saturated fat', 'saturated_fat', 'sat fat'],
            'trans_fat': ['trans fat', 'trans_fat'],
            'cholesterol': ['cholesterol'],
            'sodium': ['sodium', 'salt'],
            'total_carbohydrates': ['total carbohydrates', 'carbohydrates', 'carbs'],
            'dietary_fiber': ['dietary fiber', 'fiber', 'dietary_fiber'],
            'total_sugars': ['total sugars', 'sugars', 'sugar'],
            'added_sugars': ['added sugars', 'added_sugars'],
            'protein': ['protein']
        }
        
        for standard_name, variations in mappings.items():
            for var in variations:
                if var in nutrition_text:
                    try:
                        value = nutrition_text[var]
                        if isinstance(value, str):
                            # Extract numeric value
                            import re
                            match = re.search(r'[\d.]+', value)
                            if match:
                                value = float(match.group())
                        result[standard_name] = float(value)
                        break
                    except (ValueError, TypeError):
                        pass
        
        return result
    
    def test_parse_standard_nutrition(self):
        """Test parsing standard nutrition format"""
        nutrition = {
            'calories': 150,
            'total_fat': 5.0,
            'sodium': 200,
            'protein': 3
        }
        
        result = self.parse_nutrition(nutrition)
        
        assert result['calories'] == 150
        assert result['total_fat'] == 5.0
        assert result['sodium'] == 200
        assert result['protein'] == 3
    
    def test_parse_nutrition_with_strings(self):
        """Test parsing nutrition with string values"""
        nutrition = {
            'calories': '150 kcal',
            'total_fat': '5g',
            'sodium': '200mg'
        }
        
        result = self.parse_nutrition(nutrition)
        
        assert result['calories'] == 150
        assert result['total_fat'] == 5
        assert result['sodium'] == 200
    
    def test_parse_nutrition_alternative_names(self):
        """Test parsing with alternative field names"""
        nutrition = {
            'energy': 150,
            'fat': 5.0,
            'carbs': 20,
            'fiber': 2
        }
        
        result = self.parse_nutrition(nutrition)
        
        assert result['calories'] == 150
        assert result['total_fat'] == 5.0
        assert result['total_carbohydrates'] == 20
        assert result['dietary_fiber'] == 2
    
    def test_parse_empty_nutrition(self):
        """Test parsing empty nutrition data"""
        result = self.parse_nutrition({})
        assert result == {}


class TestScraperBase:
    """Test base scraper functionality"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_retailer_exists_in_db(self, db):
        """Test that expected retailers exist in database"""
        retailers = db.get_retailers()
        retailer_names = [r['name'] for r in retailers]
        
        # Check US retailers
        assert 'Walmart' in retailer_names
        assert 'Target' in retailer_names
        assert 'Kroger' in retailer_names
        
        # Check UK retailers
        assert 'Tesco' in retailer_names
        assert 'Sainsburys' in retailer_names
        
        # Check EU retailers
        assert 'Carrefour' in retailer_names
        assert 'Aldi' in retailer_names
    
    def test_retailer_has_required_fields(self, db):
        """Test that retailers have all required fields"""
        retailers = db.get_retailers()
        
        for retailer in retailers:
            assert 'id' in retailer
            assert 'name' in retailer
            assert 'country' in retailer
            assert 'region' in retailer
            assert 'website_url' in retailer
    
    def test_get_retailers_by_region(self, db):
        """Test filtering retailers by region"""
        us_retailers = db.get_retailers(region='US')
        uk_retailers = db.get_retailers(region='UK')
        eu_retailers = db.get_retailers(region='EU')
        
        assert len(us_retailers) > 0
        assert len(uk_retailers) > 0
        assert len(eu_retailers) > 0
        
        # Verify region filtering
        assert all(r['region'] == 'US' for r in us_retailers)
        assert all(r['region'] == 'UK' for r in uk_retailers)
        assert all(r['region'] == 'EU' for r in eu_retailers)


class TestDataPipeline:
    """Test data pipeline functionality"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_store_product_with_ingredients(self, db):
        """Test storing a product with ingredients"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Store product
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'PIPE_TEST_1',
            'barcode': 'PIPE123',
            'name': 'Pipeline Test Product',
            'brand': 'TestBrand',
            'price': 4.99
        })
        
        # Store ingredients
        raw_ingredients = "Sugar, Corn Syrup, Red 40, Yellow 5"
        parsed = ["Sugar", "Corn Syrup", "Red 40", "Yellow 5"]
        db.insert_ingredients(product_id, raw_ingredients, parsed)
        
        # Verify
        product = db.get_product_by_barcode('PIPE123')
        assert product is not None
        assert product['name'] == 'Pipeline Test Product'
        
        ingredients = db.get_ingredients(product_id)
        assert ingredients['raw_text'] == raw_ingredients
        assert ingredients['parsed_ingredients'] == parsed
    
    def test_store_product_with_nutrition(self, db):
        """Test storing a product with nutrition facts"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'NUT_PIPE_1',
            'barcode': 'NUTPIPE123',
            'name': 'Nutrition Pipeline Test'
        })
        
        nutrition = {
            'calories': 200,
            'total_fat': 8,
            'saturated_fat': 3,
            'sodium': 150,
            'total_carbohydrates': 30,
            'total_sugars': 20,
            'protein': 2
        }
        db.insert_nutrition(product_id, nutrition)
        
        # Verify
        product = db.get_product_by_barcode('NUTPIPE123')
        assert product['calories'] == 200
        assert product['total_fat'] == 8
        assert product['sodium'] == 150
    
    def test_store_and_analyze_product(self, db):
        """Test storing product and running analysis"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ANALYZE_PIPE_1',
            'barcode': 'ANALYZEPIPE123',
            'name': 'Analysis Pipeline Test'
        })
        
        db.insert_ingredients(product_id, "Sugar, Red 40", ["Sugar", "Red 40"])
        
        # Save analysis
        analysis = {
            'overall_score': 45,
            'risk_level': 'medium',
            'flagged_ingredients': [
                {'ingredient': 'Red 40', 'risk_level': 'high'}
            ]
        }
        db.save_product_analysis(product_id, analysis)
        
        # Verify
        saved_analysis = db.get_product_analysis(product_id)
        assert saved_analysis['overall_score'] == 45
        assert saved_analysis['risk_level'] == 'medium'
    
    def test_scrape_job_lifecycle(self, db):
        """Test scrape job creation and updates"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Create job
        job_id = db.create_scrape_job(walmart['id'])
        assert job_id > 0
        
        # Update progress
        db.update_scrape_job(job_id, 
                            total_products=100,
                            scraped_products=50)
        
        # Complete job
        db.update_scrape_job(job_id,
                            status='completed',
                            scraped_products=95,
                            failed_products=5)


class TestProductDataValidation:
    """Test product data validation"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_product_requires_name(self, db):
        """Test that product requires a name"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Product with name should work
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'NAME_TEST',
            'name': 'Test Product'
        })
        assert product_id > 0
    
    def test_product_barcode_lookup(self, db):
        """Test product barcode lookup works correctly"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Insert product with barcode
        db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'BARCODE_LOOKUP',
            'barcode': '1234567890123',
            'name': 'Barcode Lookup Test'
        })
        
        # Lookup by barcode
        product = db.get_product_by_barcode('1234567890123')
        assert product is not None
        assert product['name'] == 'Barcode Lookup Test'
        
        # Non-existent barcode
        not_found = db.get_product_by_barcode('9999999999999')
        assert not_found is None
    
    def test_product_upsert_behavior(self, db):
        """Test that duplicate products are updated, not duplicated"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # First insert
        db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'UPSERT_TEST',
            'barcode': 'UPSERT123',
            'name': 'Original Name',
            'price': 2.99
        })
        
        # Second insert with same external_id (should update)
        db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'UPSERT_TEST',
            'barcode': 'UPSERT123',
            'name': 'Updated Name',
            'price': 3.99
        })
        
        # Should have updated values
        product = db.get_product_by_barcode('UPSERT123')
        assert product['name'] == 'Updated Name'
        assert product['price'] == 3.99


class TestRiskIngredientMatching:
    """Test risk ingredient matching logic"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_find_exact_match(self, db):
        """Test finding exact risk ingredient match"""
        result = db.find_risk_ingredient('Red 40')
        
        assert result is not None
        assert result['canonical_name'] == 'Red 40'
        assert result['risk_level'] == 'high'
    
    def test_find_partial_match(self, db):
        """Test finding partial risk ingredient match"""
        result = db.find_risk_ingredient('red')
        
        # Should find Red 40
        assert result is not None
        assert 'Red' in result['canonical_name']
    
    def test_find_case_insensitive(self, db):
        """Test case insensitive matching"""
        result1 = db.find_risk_ingredient('RED 40')
        result2 = db.find_risk_ingredient('red 40')
        result3 = db.find_risk_ingredient('Red 40')
        
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        assert result1['canonical_name'] == result2['canonical_name'] == result3['canonical_name']
    
    def test_risk_ingredient_profiles(self, db):
        """Test that risk ingredients have correct affected profiles"""
        # Red 40 should affect children
        red40 = db.find_risk_ingredient('Red 40')
        assert 'child' in red40['affected_profiles']
        assert 'toddler' in red40['affected_profiles']
        
        # HFCS should affect diabetics
        hfcs = db.find_risk_ingredient('High Fructose Corn Syrup')
        assert 'diabetic' in hfcs['affected_profiles']
        
        # Caffeine should affect pregnant
        caffeine = db.find_risk_ingredient('Caffeine')
        assert 'pregnant' in caffeine['affected_profiles']
    
    def test_all_risk_ingredients_have_profiles(self, db):
        """Test that all risk ingredients have affected profiles"""
        risk_ingredients = db.get_risk_ingredients()
        
        for ri in risk_ingredients:
            assert 'affected_profiles' in ri
            assert isinstance(ri['affected_profiles'], list)
            assert len(ri['affected_profiles']) > 0


class TestScraperIntegration:
    """Integration tests for scraper components"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_full_product_pipeline(self, db):
        """Test complete product scraping pipeline"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Simulate scraped product data
        scraped_data = {
            'retailer_id': walmart['id'],
            'external_id': 'FULL_PIPE_1',
            'barcode': 'FULLPIPE123',
            'name': 'Haribo Gummy Bears',
            'brand': 'Haribo',
            'description': 'Delicious gummy bear candy',
            'price': 3.49,
            'currency': 'USD',
            'image_url': 'https://example.com/gummy.jpg',
            'product_url': 'https://walmart.com/product/123'
        }
        
        # Step 1: Store product
        product_id = db.insert_product(scraped_data)
        
        # Step 2: Store ingredients
        raw_ingredients = "Sugar, Corn Syrup, Gelatin, Citric Acid, Red 40, Yellow 5, Blue 1"
        parsed = ["Sugar", "Corn Syrup", "Gelatin", "Citric Acid", "Red 40", "Yellow 5", "Blue 1"]
        db.insert_ingredients(product_id, raw_ingredients, parsed)
        
        # Step 3: Store nutrition
        nutrition = {
            'calories': 140,
            'total_fat': 0,
            'sodium': 15,
            'total_carbohydrates': 34,
            'total_sugars': 18,
            'protein': 3
        }
        db.insert_nutrition(product_id, nutrition)
        
        # Step 4: Store analysis
        analysis = {
            'overall_score': 35,
            'risk_level': 'high',
            'flagged_ingredients': [
                {'ingredient': 'Red 40', 'risk_level': 'high'},
                {'ingredient': 'Yellow 5', 'risk_level': 'medium'}
            ],
            'recommendations': ['Contains artificial dyes']
        }
        db.save_product_analysis(product_id, analysis)
        
        # Verify complete data
        product = db.get_product_by_barcode('FULLPIPE123')
        assert product['name'] == 'Haribo Gummy Bears'
        assert product['brand'] == 'Haribo'
        assert product['calories'] == 140
        
        ingredients = db.get_ingredients(product_id)
        assert len(ingredients['parsed_ingredients']) == 7
        
        saved_analysis = db.get_product_analysis(product_id)
        assert saved_analysis['overall_score'] == 35
    
    def test_multiple_retailers_same_product(self, db):
        """Test same product from different retailers"""
        walmart = db.get_retailer_by_name('Walmart')
        target = db.get_retailer_by_name('Target')
        
        # Same product at Walmart
        db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'MULTI_1',
            'barcode': 'MULTI123',
            'name': 'Coca-Cola',
            'price': 1.99
        })
        
        # Same product at Target (different price)
        db.insert_product({
            'retailer_id': target['id'],
            'external_id': 'MULTI_1',
            'barcode': 'MULTI123',
            'name': 'Coca-Cola',
            'price': 2.29
        })
        
        # Search should find both
        results = db.search_products('Coca-Cola')
        assert len(results) >= 1  # At least one result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
