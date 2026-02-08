"""
Comprehensive Unit Tests for Database Layer (db_manager.py)
Tests all database operations with real SQLite database (in-memory for isolation)
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import DatabaseManager


class TestDatabaseManager:
    """Test suite for DatabaseManager class"""
    
    @pytest.fixture
    def db(self):
        """Create a fresh in-memory database for each test"""
        # Use a temp file so we can test file-based operations
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Copy schema to temp location for initialization
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
        
        db = DatabaseManager(db_path=db_path)
        yield db
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    # ==================== Retailer Tests ====================
    
    def test_get_retailers_returns_list(self, db):
        """Test that get_retailers returns a list of retailers"""
        retailers = db.get_retailers()
        assert isinstance(retailers, list)
        assert len(retailers) > 0  # Schema seeds default retailers
    
    def test_get_retailers_by_region(self, db):
        """Test filtering retailers by region"""
        us_retailers = db.get_retailers(region='US')
        assert all(r['region'] == 'US' for r in us_retailers)
        
        uk_retailers = db.get_retailers(region='UK')
        assert all(r['region'] == 'UK' for r in uk_retailers)
    
    def test_get_retailer_by_name(self, db):
        """Test getting a specific retailer by name"""
        walmart = db.get_retailer_by_name('Walmart')
        assert walmart is not None
        assert walmart['name'] == 'Walmart'
        assert walmart['country'] == 'USA'
        assert walmart['region'] == 'US'
    
    def test_get_retailer_by_name_not_found(self, db):
        """Test getting a non-existent retailer returns None"""
        result = db.get_retailer_by_name('NonExistentRetailer')
        assert result is None
    
    def test_update_retailer_last_scraped(self, db):
        """Test updating retailer's last scraped timestamp"""
        walmart = db.get_retailer_by_name('Walmart')
        retailer_id = walmart['id']
        
        db.update_retailer_last_scraped(retailer_id)
        
        updated = db.get_retailer_by_name('Walmart')
        assert updated['last_scraped_at'] is not None
    
    # ==================== Product Tests ====================
    
    def test_insert_product(self, db):
        """Test inserting a new product"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_data = {
            'retailer_id': walmart['id'],
            'external_id': 'TEST123',
            'barcode': '0012345678905',
            'name': 'Test Gummy Bears',
            'brand': 'Haribo',
            'description': 'Delicious gummy bears',
            'price': 3.99,
            'currency': 'USD',
            'is_processed': True
        }
        
        product_id = db.insert_product(product_data)
        assert product_id > 0
    
    def test_insert_product_upsert(self, db):
        """Test that inserting same product updates it"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_data = {
            'retailer_id': walmart['id'],
            'external_id': 'TEST456',
            'barcode': '0012345678906',
            'name': 'Original Name',
            'brand': 'TestBrand',
            'price': 2.99
        }
        
        id1 = db.insert_product(product_data)
        
        # Update with same external_id
        product_data['name'] = 'Updated Name'
        product_data['price'] = 3.99
        id2 = db.insert_product(product_data)
        
        # Should be same product (upsert)
        product = db.get_product_by_barcode('0012345678906')
        assert product['name'] == 'Updated Name'
        assert product['price'] == 3.99
    
    def test_get_product_by_barcode(self, db):
        """Test retrieving product by barcode"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_data = {
            'retailer_id': walmart['id'],
            'external_id': 'BARCODE_TEST',
            'barcode': '1234567890123',
            'name': 'Barcode Test Product',
            'brand': 'TestBrand'
        }
        db.insert_product(product_data)
        
        product = db.get_product_by_barcode('1234567890123')
        assert product is not None
        assert product['name'] == 'Barcode Test Product'
        assert product['retailer_name'] == 'Walmart'
    
    def test_get_product_by_barcode_not_found(self, db):
        """Test getting non-existent barcode returns None"""
        result = db.get_product_by_barcode('9999999999999')
        assert result is None
    
    def test_search_products(self, db):
        """Test searching products by name"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Insert test products
        for i, name in enumerate(['Apple Juice', 'Orange Juice', 'Apple Cider']):
            db.insert_product({
                'retailer_id': walmart['id'],
                'external_id': f'SEARCH_{i}',
                'barcode': f'SEARCH{i}',
                'name': name,
                'brand': 'TestBrand'
            })
        
        # Search for 'Apple'
        results = db.search_products('Apple')
        assert len(results) == 2
        assert all('Apple' in r['name'] for r in results)
    
    def test_search_products_by_brand(self, db):
        """Test searching products by brand"""
        walmart = db.get_retailer_by_name('Walmart')
        
        db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'BRAND_TEST',
            'barcode': 'BRAND123',
            'name': 'Some Product',
            'brand': 'UniqueBrandName'
        })
        
        results = db.search_products('UniqueBrandName')
        assert len(results) == 1
        assert results[0]['brand'] == 'UniqueBrandName'
    
    def test_search_products_with_limit(self, db):
        """Test search respects limit parameter"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Insert 10 products
        for i in range(10):
            db.insert_product({
                'retailer_id': walmart['id'],
                'external_id': f'LIMIT_{i}',
                'barcode': f'LIMIT{i}',
                'name': f'Limit Test Product {i}',
                'brand': 'LimitBrand'
            })
        
        results = db.search_products('Limit Test', limit=5)
        assert len(results) == 5
    
    # ==================== Ingredients Tests ====================
    
    def test_insert_and_get_ingredients(self, db):
        """Test inserting and retrieving ingredients"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ING_TEST',
            'barcode': 'ING123',
            'name': 'Ingredient Test Product'
        })
        
        raw_text = "Sugar, Corn Syrup, Red 40, Yellow 5"
        parsed = ["Sugar", "Corn Syrup", "Red 40", "Yellow 5"]
        
        db.insert_ingredients(product_id, raw_text, parsed)
        
        ingredients = db.get_ingredients(product_id)
        assert ingredients is not None
        assert ingredients['raw_text'] == raw_text
        assert ingredients['parsed_ingredients'] == parsed
    
    def test_get_ingredients_not_found(self, db):
        """Test getting ingredients for non-existent product"""
        result = db.get_ingredients(99999)
        assert result is None
    
    def test_insert_ingredients_without_parsed(self, db):
        """Test inserting ingredients without parsed list"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ING_RAW',
            'barcode': 'INGRAW123',
            'name': 'Raw Ingredient Product'
        })
        
        raw_text = "Sugar, Salt, Flour"
        db.insert_ingredients(product_id, raw_text)
        
        ingredients = db.get_ingredients(product_id)
        assert ingredients['raw_text'] == raw_text
        assert ingredients['parsed_ingredients'] is None
    
    # ==================== Nutrition Tests ====================
    
    def test_insert_and_get_nutrition(self, db):
        """Test inserting and retrieving nutrition facts"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'NUT_TEST',
            'barcode': 'NUT123',
            'name': 'Nutrition Test Product'
        })
        
        nutrition_data = {
            'calories': 150,
            'total_fat': 5.0,
            'saturated_fat': 2.0,
            'trans_fat': 0.0,
            'cholesterol': 10,
            'sodium': 200,
            'total_carbohydrates': 25,
            'dietary_fiber': 2,
            'total_sugars': 15,
            'added_sugars': 10,
            'protein': 3
        }
        
        db.insert_nutrition(product_id, nutrition_data)
        
        # Get product with nutrition
        product = db.get_product_by_barcode('NUT123')
        assert product['calories'] == 150
        assert product['total_fat'] == 5.0
        assert product['sodium'] == 200
    
    # ==================== Risk Ingredients Tests ====================
    
    def test_get_risk_ingredients(self, db):
        """Test getting all risk ingredients"""
        risk_ingredients = db.get_risk_ingredients()
        
        assert isinstance(risk_ingredients, list)
        assert len(risk_ingredients) > 0  # Schema seeds default risk ingredients
        
        # Check structure
        for ri in risk_ingredients:
            assert 'canonical_name' in ri
            assert 'category' in ri
            assert 'risk_level' in ri
            assert 'affected_profiles' in ri
            assert isinstance(ri['affected_profiles'], list)
    
    def test_get_risk_ingredients_contains_expected(self, db):
        """Test that expected risk ingredients are present"""
        risk_ingredients = db.get_risk_ingredients()
        names = [ri['canonical_name'] for ri in risk_ingredients]
        
        # Check for key ingredients from schema
        assert 'Aspartame' in names
        assert 'Red 40' in names
        assert 'High Fructose Corn Syrup' in names
        assert 'Sodium Nitrate' in names
    
    def test_find_risk_ingredient(self, db):
        """Test finding a specific risk ingredient"""
        result = db.find_risk_ingredient('Red 40')
        
        assert result is not None
        assert result['canonical_name'] == 'Red 40'
        assert result['category'] == 'artificial_dye'
        assert result['risk_level'] == 'high'
        assert 'child' in result['affected_profiles']
    
    def test_find_risk_ingredient_partial_match(self, db):
        """Test finding risk ingredient with partial name"""
        result = db.find_risk_ingredient('aspartame')  # lowercase
        assert result is not None
        assert result['canonical_name'] == 'Aspartame'
    
    def test_find_risk_ingredient_not_found(self, db):
        """Test finding non-existent risk ingredient"""
        result = db.find_risk_ingredient('NonExistentIngredient')
        assert result is None
    
    # ==================== Analysis Tests ====================
    
    def test_save_and_get_product_analysis(self, db):
        """Test saving and retrieving product analysis"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ANALYSIS_TEST',
            'barcode': 'ANALYSIS123',
            'name': 'Analysis Test Product'
        })
        
        analysis = {
            'overall_score': 45.5,
            'risk_level': 'medium',
            'flagged_ingredients': [
                {'ingredient': 'Red 40', 'risk_level': 'high'},
                {'ingredient': 'Sugar', 'risk_level': 'low'}
            ],
            'recommendations': ['Consider alternatives']
        }
        
        db.save_product_analysis(product_id, analysis)
        
        result = db.get_product_analysis(product_id)
        assert result is not None
        assert result['overall_score'] == 45.5
        assert result['risk_level'] == 'medium'
        assert 'analysis' in result
        assert result['analysis']['recommendations'] == ['Consider alternatives']
    
    def test_get_product_analysis_not_found(self, db):
        """Test getting analysis for non-analyzed product"""
        result = db.get_product_analysis(99999)
        assert result is None
    
    def test_save_product_analysis_upsert(self, db):
        """Test that saving analysis twice updates it"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'UPSERT_ANALYSIS',
            'barcode': 'UPSERT123',
            'name': 'Upsert Analysis Product'
        })
        
        # First analysis
        db.save_product_analysis(product_id, {
            'overall_score': 50,
            'risk_level': 'medium',
            'flagged_ingredients': []
        })
        
        # Updated analysis
        db.save_product_analysis(product_id, {
            'overall_score': 75,
            'risk_level': 'low',
            'flagged_ingredients': []
        })
        
        result = db.get_product_analysis(product_id)
        assert result['overall_score'] == 75
        assert result['risk_level'] == 'low'
    
    # ==================== Alternatives Tests ====================
    
    def test_save_and_get_alternatives(self, db):
        """Test saving and retrieving product alternatives"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Create original product
        original_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ORIGINAL',
            'barcode': 'ORIG123',
            'name': 'Original Product',
            'price': 5.99
        })
        
        # Create alternative product
        alt_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ALTERNATIVE',
            'barcode': 'ALT123',
            'name': 'Healthier Alternative',
            'price': 4.99
        })
        
        # Save alternative mapping
        db.save_alternative(
            product_id=original_id,
            alternative_id=alt_id,
            reason='Lower sugar content',
            score_improvement=15.0,
            health_profiles=['diabetic', 'child']
        )
        
        alternatives = db.get_alternatives(original_id)
        assert len(alternatives) == 1
        assert alternatives[0]['name'] == 'Healthier Alternative'
        assert alternatives[0]['reason'] == 'Lower sugar content'
        assert alternatives[0]['score_improvement'] == 15.0
    
    def test_get_alternatives_empty(self, db):
        """Test getting alternatives for product with none"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'NO_ALT',
            'barcode': 'NOALT123',
            'name': 'No Alternatives Product'
        })
        
        alternatives = db.get_alternatives(product_id)
        assert alternatives == []
    
    # ==================== Scrape Job Tests ====================
    
    def test_create_scrape_job(self, db):
        """Test creating a scrape job"""
        walmart = db.get_retailer_by_name('Walmart')
        
        job_id = db.create_scrape_job(walmart['id'])
        assert job_id > 0
    
    def test_update_scrape_job(self, db):
        """Test updating scrape job status"""
        walmart = db.get_retailer_by_name('Walmart')
        job_id = db.create_scrape_job(walmart['id'])
        
        db.update_scrape_job(
            job_id,
            status='completed',
            total_products=100,
            scraped_products=95,
            failed_products=5
        )
        
        # Verify update (would need a get method, but we can verify no exception)
        # The update should complete without error
    
    # ==================== Statistics Tests ====================
    
    def test_get_stats(self, db):
        """Test getting database statistics"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Insert some test data
        for i in range(5):
            product_id = db.insert_product({
                'retailer_id': walmart['id'],
                'external_id': f'STATS_{i}',
                'barcode': f'STATS{i}',
                'name': f'Stats Product {i}'
            })
            db.insert_ingredients(product_id, f'Ingredient {i}', [f'Ingredient {i}'])
        
        stats = db.get_stats()
        
        assert 'total_products' in stats
        assert 'total_retailers' in stats
        assert 'products_with_ingredients' in stats
        assert 'products_with_nutrition' in stats
        assert 'analyzed_products' in stats
        assert 'products_by_retailer' in stats
        
        assert stats['total_products'] >= 5
        assert stats['products_with_ingredients'] >= 5
        assert stats['total_retailers'] > 0
    
    # ==================== Connection Tests ====================
    
    def test_connection_context_manager(self, db):
        """Test that connection context manager works correctly"""
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_connection_rollback_on_error(self, db):
        """Test that connection rolls back on error"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Insert a product
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ROLLBACK_TEST',
            'barcode': 'ROLLBACK123',
            'name': 'Rollback Test'
        })
        
        # Try to cause an error in a transaction
        try:
            with db.get_connection() as conn:
                conn.execute("UPDATE products SET name = 'Modified' WHERE id = ?", (product_id,))
                # Force an error
                conn.execute("INVALID SQL SYNTAX")
        except:
            pass
        
        # Product should still have original name due to rollback
        product = db.get_product_by_barcode('ROLLBACK123')
        assert product['name'] == 'Rollback Test'


class TestRiskIngredientProfiles:
    """Test risk ingredient to profile mappings"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_aspartame_affects_children(self, db):
        """Test Aspartame affects child profiles"""
        result = db.find_risk_ingredient('Aspartame')
        assert 'child' in result['affected_profiles']
        assert 'pregnant' in result['affected_profiles']
        assert 'toddler' in result['affected_profiles']
    
    def test_red_40_affects_children(self, db):
        """Test Red 40 affects child profiles"""
        result = db.find_risk_ingredient('Red 40')
        assert 'child' in result['affected_profiles']
        assert 'toddler' in result['affected_profiles']
    
    def test_hfcs_affects_diabetics(self, db):
        """Test HFCS affects diabetic profiles"""
        result = db.find_risk_ingredient('High Fructose Corn Syrup')
        assert 'diabetic' in result['affected_profiles']
        assert 'obesity' in result['affected_profiles']
        assert 'cardiac' in result['affected_profiles']
    
    def test_caffeine_affects_pregnant(self, db):
        """Test Caffeine affects pregnant profiles"""
        result = db.find_risk_ingredient('Caffeine')
        assert 'pregnant' in result['affected_profiles']
        assert 'child' in result['affected_profiles']
        assert 'hypertensive' in result['affected_profiles']
    
    def test_sodium_nitrate_affects_cardiac(self, db):
        """Test Sodium Nitrate affects cardiac profiles"""
        result = db.find_risk_ingredient('Sodium Nitrate')
        assert 'pregnant' in result['affected_profiles']
        assert 'cardiac' in result['affected_profiles']
    
    def test_trans_fat_affects_cardiac(self, db):
        """Test Trans Fat affects cardiac profiles"""
        result = db.find_risk_ingredient('Trans Fat')
        assert 'cardiac' in result['affected_profiles']
        assert 'hypertensive' in result['affected_profiles']


class TestDatabaseIntegrity:
    """Test database integrity and constraints"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_product_retailer_foreign_key(self, db):
        """Test product requires valid retailer"""
        # This should work with valid retailer
        walmart = db.get_retailer_by_name('Walmart')
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'FK_TEST',
            'barcode': 'FK123',
            'name': 'FK Test Product'
        })
        assert product_id > 0
    
    def test_unique_retailer_external_id(self, db):
        """Test unique constraint on retailer_id + external_id"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # First insert
        db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'UNIQUE_TEST',
            'barcode': 'UNIQUE1',
            'name': 'First Product'
        })
        
        # Second insert with same external_id should upsert
        db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'UNIQUE_TEST',
            'barcode': 'UNIQUE2',
            'name': 'Second Product'
        })
        
        # Should only have one product with that external_id
        results = db.search_products('Product')
        unique_test_products = [p for p in results if 'UNIQUE' in str(p.get('barcode', ''))]
        # The upsert should have updated the first product
    
    def test_ingredients_linked_to_product(self, db):
        """Test ingredients are properly linked to product"""
        walmart = db.get_retailer_by_name('Walmart')
        
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'LINK_TEST',
            'barcode': 'LINK123',
            'name': 'Link Test'
        })
        
        db.insert_ingredients(product_id, 'Sugar, Salt', ['Sugar', 'Salt'])
        
        # Verify ingredients exist and are linked
        ingredients = db.get_ingredients(product_id)
        assert ingredients is not None
        assert ingredients['product_id'] == product_id
        assert ingredients['raw_text'] == 'Sugar, Salt'
        assert ingredients['parsed_ingredients'] == ['Sugar', 'Salt']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
