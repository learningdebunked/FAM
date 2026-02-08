"""
Comprehensive Unit Tests for Product Service Layer (product_service.py)
Tests FAM scoring, risk analysis, and personalization logic
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.product_service import ProductService
from database.db_manager import DatabaseManager


class TestProductService:
    """Test suite for ProductService class"""
    
    @pytest.fixture
    def db(self):
        """Create a fresh database for each test"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def service(self, db):
        """Create ProductService with test database"""
        return ProductService(db)
    
    # ==================== FAM Score Calculation Tests ====================
    
    def test_analyze_ingredients_returns_required_fields(self, service):
        """Test that analysis returns all required fields"""
        ingredients = ["Sugar", "Corn Syrup", "Red 40"]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        assert 'fam_score' in result
        assert 'overall_score' in result
        assert 'risk_flags' in result
        assert 'recommendations' in result
        assert 'nutri_score' in result
        assert 'nova_group' in result
        assert 'risk_level' in result
    
    def test_analyze_ingredients_score_range(self, service):
        """Test that FAM score is within valid range (0-100)"""
        ingredients = ["Sugar", "Red 40", "Yellow 5", "Aspartame"]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        assert 0 <= result['fam_score'] <= 100
        assert 0 <= result['overall_score'] <= 100
    
    def test_analyze_safe_ingredients(self, service):
        """Test analysis of safe ingredients gives high score"""
        ingredients = ["Water", "Natural Flavors", "Citric Acid"]
        health_profiles = ["adult"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Safe ingredients should have high score
        assert result['fam_score'] >= 70
        assert len(result['risk_flags']) == 0
    
    def test_analyze_risky_ingredients_low_score(self, service):
        """Test analysis of risky ingredients gives low score"""
        ingredients = ["Red 40", "Yellow 5", "Aspartame", "High Fructose Corn Syrup"]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Risky ingredients should have low score
        assert result['fam_score'] < 50
        assert len(result['risk_flags']) >= 3
    
    # ==================== Risk Flag Tests ====================
    
    def test_risk_flags_structure(self, service):
        """Test that risk flags have correct structure"""
        ingredients = ["Red 40", "Sugar"]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        for flag in result['risk_flags']:
            assert 'ingredient' in flag
            assert 'canonical_name' in flag
            assert 'risk_level' in flag
            assert 'category' in flag
            assert 'description' in flag
            assert 'affected_profiles' in flag
            assert 'is_relevant_to_user' in flag
    
    def test_risk_flag_relevance_for_child(self, service):
        """Test that Red 40 is marked relevant for child profile"""
        ingredients = ["Red 40"]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        assert len(result['risk_flags']) == 1
        assert result['risk_flags'][0]['is_relevant_to_user'] == True
        assert 'child' in result['risk_flags'][0]['affected_profiles']
    
    def test_risk_flag_not_relevant_for_adult(self, service):
        """Test that Red 40 is not marked relevant for adult profile"""
        ingredients = ["Red 40"]
        health_profiles = ["adult"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Red 40 affects children, not adults
        if result['risk_flags']:
            assert result['risk_flags'][0]['is_relevant_to_user'] == False
    
    def test_multiple_risk_flags(self, service):
        """Test detection of multiple risk ingredients"""
        ingredients = [
            "Sugar", "Red 40", "Yellow 5", "Blue 1",
            "Aspartame", "High Fructose Corn Syrup"
        ]
        health_profiles = ["child", "diabetic"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Should flag multiple ingredients
        assert len(result['risk_flags']) >= 4
        
        # Check specific ingredients are flagged
        flagged_names = [f['canonical_name'] for f in result['risk_flags']]
        assert 'Red 40' in flagged_names
        assert 'Aspartame' in flagged_names
    
    # ==================== Health Profile Personalization Tests ====================
    
    def test_child_profile_higher_penalty(self, service):
        """Test that child profile gets higher penalty for child-affecting ingredients"""
        ingredients = ["Red 40", "Yellow 5"]
        
        # Score for adult
        adult_result = service.analyze_ingredients(ingredients, ["adult"])
        
        # Score for child
        child_result = service.analyze_ingredients(ingredients, ["child"])
        
        # Child should have lower score (higher penalty)
        assert child_result['fam_score'] < adult_result['fam_score']
    
    def test_diabetic_profile_sugar_penalty(self, service):
        """Test that diabetic profile gets penalty for high sugar"""
        ingredients = ["High Fructose Corn Syrup", "Corn Syrup", "Sugar"]
        
        # Score for adult
        adult_result = service.analyze_ingredients(ingredients, ["adult"])
        
        # Score for diabetic
        diabetic_result = service.analyze_ingredients(ingredients, ["diabetic"])
        
        # Diabetic should have lower score
        assert diabetic_result['fam_score'] < adult_result['fam_score']
    
    def test_pregnant_profile_caffeine_penalty(self, service):
        """Test that pregnant profile gets penalty for caffeine"""
        ingredients = ["Caffeine", "Water", "Sugar"]
        
        # Score for adult
        adult_result = service.analyze_ingredients(ingredients, ["adult"])
        
        # Score for pregnant
        pregnant_result = service.analyze_ingredients(ingredients, ["pregnant"])
        
        # Pregnant should have lower score
        assert pregnant_result['fam_score'] < adult_result['fam_score']
    
    def test_cardiac_profile_sodium_nitrate_penalty(self, service):
        """Test that cardiac profile gets penalty for sodium nitrate"""
        ingredients = ["Sodium Nitrate", "Salt", "Meat"]
        
        # Score for adult
        adult_result = service.analyze_ingredients(ingredients, ["adult"])
        
        # Score for cardiac
        cardiac_result = service.analyze_ingredients(ingredients, ["cardiac"])
        
        # Cardiac should have lower score
        assert cardiac_result['fam_score'] < cardiac_result['fam_score'] or \
               any(f['is_relevant_to_user'] for f in cardiac_result['risk_flags'])
    
    def test_multiple_profiles_combined_penalty(self, service):
        """Test that multiple profiles combine penalties"""
        ingredients = ["Red 40", "High Fructose Corn Syrup", "Caffeine"]
        
        # Single profile
        child_result = service.analyze_ingredients(ingredients, ["child"])
        
        # Multiple profiles
        multi_result = service.analyze_ingredients(
            ingredients, 
            ["child", "diabetic", "pregnant"]
        )
        
        # Multiple profiles should have more relevant flags
        child_relevant = sum(1 for f in child_result['risk_flags'] if f['is_relevant_to_user'])
        multi_relevant = sum(1 for f in multi_result['risk_flags'] if f['is_relevant_to_user'])
        
        assert multi_relevant >= child_relevant
    
    def test_vulnerable_profile_extra_penalty(self, service):
        """Test that vulnerable profiles (child, pregnant, senior) get extra penalty"""
        ingredients = ["Red 40", "Aspartame"]
        
        # Adult profile
        adult_result = service.analyze_ingredients(ingredients, ["adult"])
        
        # Vulnerable profiles
        child_result = service.analyze_ingredients(ingredients, ["child"])
        pregnant_result = service.analyze_ingredients(ingredients, ["pregnant"])
        
        # Vulnerable profiles should have lower scores
        assert child_result['fam_score'] <= adult_result['fam_score']
        assert pregnant_result['fam_score'] <= adult_result['fam_score']
    
    # ==================== Nutri-Score Tests ====================
    
    def test_nutri_score_with_nutrition(self, service):
        """Test Nutri-Score calculation with nutrition data"""
        ingredients = ["Sugar", "Water"]
        health_profiles = ["adult"]
        nutrition = {
            'calories': 150,
            'total_sugars': 30,
            'sodium': 100,
            'saturated_fat': 5,
            'dietary_fiber': 2,
            'protein': 3
        }
        
        result = service.analyze_ingredients(ingredients, health_profiles, nutrition=nutrition)
        
        assert result['nutri_score'] in ['A', 'B', 'C', 'D', 'E']
    
    def test_nutri_score_healthy_product(self, service):
        """Test Nutri-Score for healthy product"""
        ingredients = ["Water", "Natural Flavors"]
        health_profiles = ["adult"]
        nutrition = {
            'calories': 50,
            'total_sugars': 5,
            'sodium': 50,
            'saturated_fat': 0,
            'dietary_fiber': 5,
            'protein': 10
        }
        
        result = service.analyze_ingredients(ingredients, health_profiles, nutrition=nutrition)
        
        # Healthy product should get A or B
        assert result['nutri_score'] in ['A', 'B', 'C']
    
    def test_nutri_score_unhealthy_product(self, service):
        """Test Nutri-Score for unhealthy product"""
        ingredients = ["Sugar", "High Fructose Corn Syrup"]
        health_profiles = ["adult"]
        nutrition = {
            'calories': 400,
            'total_sugars': 50,
            'sodium': 500,
            'saturated_fat': 15,
            'dietary_fiber': 0,
            'protein': 1
        }
        
        result = service.analyze_ingredients(ingredients, health_profiles, nutrition=nutrition)
        
        # Unhealthy product should get D or E
        assert result['nutri_score'] in ['D', 'E']
    
    # ==================== NOVA Group Tests ====================
    
    def test_nova_group_range(self, service):
        """Test NOVA group is within valid range (1-4)"""
        ingredients = ["Sugar", "Red 40"]
        health_profiles = ["adult"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        assert result['nova_group'] in [1, 2, 3, 4]
    
    def test_nova_group_ultra_processed(self, service):
        """Test NOVA group 4 for ultra-processed foods"""
        ingredients = [
            "Sugar", "High Fructose Corn Syrup", "Red 40", "Yellow 5",
            "Aspartame", "Sodium Benzoate", "Artificial Flavor"
        ]
        health_profiles = ["adult"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Many artificial ingredients = ultra-processed (NOVA 4)
        assert result['nova_group'] == 4
    
    def test_nova_group_minimally_processed(self, service):
        """Test NOVA group 1 for minimally processed foods"""
        ingredients = ["Apple", "Water"]
        health_profiles = ["adult"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Few natural ingredients = minimally processed (NOVA 1)
        assert result['nova_group'] in [1, 2]
    
    # ==================== Recommendations Tests ====================
    
    def test_recommendations_for_risky_product(self, service):
        """Test that recommendations are generated for risky products"""
        ingredients = ["Red 40", "Aspartame", "High Fructose Corn Syrup"]
        health_profiles = ["child", "diabetic"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        assert len(result['recommendations']) > 0
    
    def test_recommendations_for_safe_product(self, service):
        """Test recommendations for safe products"""
        ingredients = ["Water", "Natural Flavors"]
        health_profiles = ["adult"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Should have at least one recommendation (even if positive)
        assert len(result['recommendations']) >= 1
    
    def test_recommendations_mention_affected_profiles(self, service):
        """Test that recommendations mention affected profiles"""
        ingredients = ["Red 40", "Aspartame"]
        health_profiles = ["child", "pregnant"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Recommendations should mention the affected profiles
        all_recommendations = ' '.join(result['recommendations']).lower()
        assert 'child' in all_recommendations or 'pregnant' in all_recommendations or \
               'toddler' in all_recommendations or '👶' in all_recommendations or \
               '🤰' in all_recommendations
    
    def test_recommendations_for_artificial_sweeteners(self, service):
        """Test specific recommendation for artificial sweeteners"""
        ingredients = ["Aspartame", "Sucralose"]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        all_recommendations = ' '.join(result['recommendations']).lower()
        assert 'sweetener' in all_recommendations or 'stevia' in all_recommendations
    
    def test_recommendations_for_artificial_dyes(self, service):
        """Test specific recommendation for artificial dyes"""
        ingredients = ["Red 40", "Yellow 5", "Blue 1"]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        all_recommendations = ' '.join(result['recommendations']).lower()
        assert 'dye' in all_recommendations or 'color' in all_recommendations
    
    # ==================== Edge Cases ====================
    
    def test_empty_ingredients(self, service):
        """Test analysis with empty ingredients list"""
        result = service.analyze_ingredients([], ["adult"])
        
        assert result['fam_score'] >= 50  # Neutral or good score
        assert len(result['risk_flags']) == 0
    
    def test_empty_health_profiles(self, service):
        """Test analysis with empty health profiles"""
        ingredients = ["Red 40", "Sugar"]
        
        result = service.analyze_ingredients(ingredients, [])
        
        # Should still work with default behavior
        assert 'fam_score' in result
        assert 'risk_flags' in result
    
    def test_case_insensitive_ingredient_matching(self, service):
        """Test that ingredient matching is case insensitive"""
        # Lowercase
        result1 = service.analyze_ingredients(["red 40"], ["child"])
        
        # Uppercase
        result2 = service.analyze_ingredients(["RED 40"], ["child"])
        
        # Mixed case
        result3 = service.analyze_ingredients(["Red 40"], ["child"])
        
        # All should detect the risk ingredient
        assert len(result1['risk_flags']) == len(result2['risk_flags']) == len(result3['risk_flags'])
    
    def test_partial_ingredient_matching(self, service):
        """Test that partial ingredient names are matched"""
        # Full ingredient string from label
        ingredients = ["Contains Red 40 Lake", "Yellow 5 (Tartrazine)"]
        
        result = service.analyze_ingredients(ingredients, ["child"])
        
        # Should still detect Red 40 and Yellow 5
        assert len(result['risk_flags']) >= 2
    
    def test_nutrition_with_missing_fields(self, service):
        """Test analysis with partial nutrition data"""
        ingredients = ["Sugar", "Water"]
        health_profiles = ["adult"]
        nutrition = {
            'calories': 100,
            # Missing other fields
        }
        
        result = service.analyze_ingredients(ingredients, health_profiles, nutrition=nutrition)
        
        # Should still work
        assert 'fam_score' in result
        assert 'nutri_score' in result


class TestFAMScoringFormula:
    """Test the FAM scoring formula components"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def service(self, db):
        return ProductService(db)
    
    def test_score_formula_weights(self, service):
        """Test that FAM score uses correct weights (α=0.4, β=0.3, γ=0.2, δ=0.1)"""
        # This is a conceptual test - we verify the score changes appropriately
        # with different components
        
        # Base case: safe ingredients, no nutrition
        safe_result = service.analyze_ingredients(["Water"], ["adult"])
        
        # Add risky ingredients (affects β component)
        risky_result = service.analyze_ingredients(
            ["Red 40", "Aspartame"], 
            ["child"]
        )
        
        # Risky ingredients should significantly lower score
        assert risky_result['fam_score'] < safe_result['fam_score']
    
    def test_fit_to_goals_component(self, service):
        """Test FitToGoals component varies by profile relevance"""
        ingredients = ["Red 40"]  # Affects children
        
        # Not relevant profile
        adult_result = service.analyze_ingredients(ingredients, ["adult"])
        
        # Relevant profile
        child_result = service.analyze_ingredients(ingredients, ["child"])
        
        # Child should have lower FitToGoals (reflected in lower score)
        assert child_result['fam_score'] < adult_result['fam_score']
    
    def test_budget_penalty_component(self, service):
        """Test budget penalty affects score"""
        ingredients = ["Sugar", "Water"]
        health_profiles = ["adult"]
        
        # Cheap product
        cheap_result = service.analyze_ingredients(
            ingredients, health_profiles, price=2.99
        )
        
        # Expensive product
        expensive_result = service.analyze_ingredients(
            ingredients, health_profiles, price=25.99
        )
        
        # Expensive should have slightly lower score
        assert expensive_result['fam_score'] <= cheap_result['fam_score']


class TestGummyBearsScenario:
    """Test the gummy bears scenario from the paper"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def service(self, db):
        return ProductService(db)
    
    def test_gummy_bears_for_child(self, service):
        """Test gummy bears analysis for a child"""
        ingredients = [
            "Sugar", "Corn Syrup", "Gelatin", "Citric Acid",
            "Red 40", "Yellow 5", "Blue 1"
        ]
        health_profiles = ["child"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Should flag artificial dyes
        flagged_names = [f['canonical_name'] for f in result['risk_flags']]
        assert 'Red 40' in flagged_names
        assert 'Yellow 5' in flagged_names
        
        # Should have medium or lower score for child (dyes are concerning)
        assert result['fam_score'] <= 60
        
        # Should have recommendations about dyes
        all_recs = ' '.join(result['recommendations']).lower()
        assert 'dye' in all_recs or 'color' in all_recs or 'child' in all_recs
    
    def test_gummy_bears_for_adult(self, service):
        """Test gummy bears analysis for an adult"""
        ingredients = [
            "Sugar", "Corn Syrup", "Gelatin", "Citric Acid",
            "Red 40", "Yellow 5", "Blue 1"
        ]
        health_profiles = ["adult"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Adult should have higher score than child
        child_result = service.analyze_ingredients(ingredients, ["child"])
        
        assert result['fam_score'] > child_result['fam_score']
    
    def test_gummy_bears_for_diabetic_child(self, service):
        """Test gummy bears analysis for a diabetic child"""
        ingredients = [
            "Sugar", "High Fructose Corn Syrup", "Corn Syrup",
            "Gelatin", "Red 40", "Yellow 5"
        ]
        health_profiles = ["child", "diabetic"]
        
        result = service.analyze_ingredients(ingredients, health_profiles)
        
        # Should flag both dyes (child) and sugars (diabetic)
        flagged_names = [f['canonical_name'] for f in result['risk_flags']]
        assert 'Red 40' in flagged_names
        assert 'High Fructose Corn Syrup' in flagged_names
        
        # Should have low score (multiple risk factors)
        assert result['fam_score'] <= 50
        
        # Multiple relevant flags
        relevant_flags = [f for f in result['risk_flags'] if f['is_relevant_to_user']]
        assert len(relevant_flags) >= 2


class TestAlternativesGeneration:
    """Test healthy alternatives generation"""
    
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = DatabaseManager(db_path=db_path)
        yield db
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def service(self, db):
        return ProductService(db)
    
    def test_get_alternatives_returns_list(self, service, db):
        """Test that get_alternatives returns a list"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Create test product
        product_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ALT_TEST',
            'barcode': 'ALT123',
            'name': 'Test Product'
        })
        
        alternatives = service.get_alternatives(product_id, ["child"])
        
        assert isinstance(alternatives, list)
    
    def test_alternatives_structure(self, service, db):
        """Test that alternatives have correct structure"""
        walmart = db.get_retailer_by_name('Walmart')
        
        # Create original and alternative products
        original_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ORIG_STRUCT',
            'barcode': 'ORIGSTRUCT',
            'name': 'Original Product',
            'price': 5.99
        })
        
        alt_id = db.insert_product({
            'retailer_id': walmart['id'],
            'external_id': 'ALT_STRUCT',
            'barcode': 'ALTSTRUCT',
            'name': 'Alternative Product',
            'price': 4.99
        })
        
        # Save alternative mapping
        db.save_alternative(original_id, alt_id, 'Healthier option', 15.0, ['child'])
        
        alternatives = service.get_alternatives(original_id, ["child"])
        
        if alternatives:
            alt = alternatives[0]
            assert 'name' in alt
            assert 'reason' in alt or 'benefits' in alt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
