"""
Feature Extraction for FAM ML Models
Converts raw product and profile data into ML-ready features
"""

import numpy as np
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
import re
import json


@dataclass
class ProductFeatures:
    """Features extracted from a product"""
    # Basic counts
    num_ingredients: int = 0
    num_additives: int = 0
    ingredient_list_length: int = 0  # Character length
    
    # Risk ingredient flags
    has_artificial_sweetener: bool = False
    has_artificial_dye: bool = False
    has_preservative: bool = False
    has_trans_fat: bool = False
    has_high_sugar: bool = False
    has_msg: bool = False
    
    # Nutrition (per 100g, normalized)
    calories: float = 0.0
    total_fat: float = 0.0
    saturated_fat: float = 0.0
    trans_fat: float = 0.0
    sodium: float = 0.0
    total_carbs: float = 0.0
    fiber: float = 0.0
    sugars: float = 0.0
    protein: float = 0.0
    
    # Derived scores
    nova_group: int = 1  # 1-4
    nutri_score_value: int = 50  # 0-100
    
    # Text embedding (set externally)
    ingredient_embedding: np.ndarray = field(default_factory=lambda: np.zeros(100))
    
    def to_vector(self) -> np.ndarray:
        """Convert to feature vector for ML models"""
        return np.array([
            # Counts (normalized)
            self.num_ingredients / 30.0,
            self.num_additives / 10.0,
            self.ingredient_list_length / 500.0,
            
            # Binary flags
            float(self.has_artificial_sweetener),
            float(self.has_artificial_dye),
            float(self.has_preservative),
            float(self.has_trans_fat),
            float(self.has_high_sugar),
            float(self.has_msg),
            
            # Nutrition (already normalized in extraction)
            self.calories,
            self.total_fat,
            self.saturated_fat,
            self.trans_fat,
            self.sodium,
            self.total_carbs,
            self.fiber,
            self.sugars,
            self.protein,
            
            # Derived
            self.nova_group / 4.0,
            self.nutri_score_value / 100.0,
        ])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'num_ingredients': self.num_ingredients,
            'num_additives': self.num_additives,
            'has_artificial_sweetener': self.has_artificial_sweetener,
            'has_artificial_dye': self.has_artificial_dye,
            'has_preservative': self.has_preservative,
            'has_trans_fat': self.has_trans_fat,
            'has_high_sugar': self.has_high_sugar,
            'nova_group': self.nova_group,
            'nutri_score_value': self.nutri_score_value,
        }


@dataclass  
class ProfileFeatures:
    """Features extracted from a health profile"""
    # Age group one-hot
    is_toddler: bool = False
    is_child: bool = False
    is_adult: bool = False
    is_senior: bool = False
    is_pregnant: bool = False
    
    # Health conditions
    has_diabetes: bool = False
    has_hypertension: bool = False
    has_heart_condition: bool = False
    has_obesity: bool = False
    has_celiac: bool = False
    has_lactose_intolerance: bool = False
    
    # Allergies
    has_nut_allergy: bool = False
    has_gluten_allergy: bool = False
    has_dairy_allergy: bool = False
    has_shellfish_allergy: bool = False
    
    # Dietary preferences
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_halal: bool = False
    is_kosher: bool = False
    
    def to_vector(self) -> np.ndarray:
        """Convert to feature vector"""
        return np.array([
            float(self.is_toddler),
            float(self.is_child),
            float(self.is_adult),
            float(self.is_senior),
            float(self.is_pregnant),
            float(self.has_diabetes),
            float(self.has_hypertension),
            float(self.has_heart_condition),
            float(self.has_obesity),
            float(self.has_celiac),
            float(self.has_lactose_intolerance),
            float(self.has_nut_allergy),
            float(self.has_gluten_allergy),
            float(self.has_dairy_allergy),
            float(self.has_shellfish_allergy),
            float(self.is_vegetarian),
            float(self.is_vegan),
            float(self.is_halal),
            float(self.is_kosher),
        ])
    
    @classmethod
    def from_health_profiles(cls, profiles: List[str]) -> 'ProfileFeatures':
        """Create from list of profile strings"""
        features = cls()
        profiles_lower = [p.lower() for p in profiles]
        
        # Age groups
        features.is_toddler = any(p in profiles_lower for p in ['toddler', 'infant', 'baby'])
        features.is_child = any(p in profiles_lower for p in ['child', 'kid', 'children'])
        features.is_adult = 'adult' in profiles_lower
        features.is_senior = any(p in profiles_lower for p in ['senior', 'elderly', 'older'])
        features.is_pregnant = any(p in profiles_lower for p in ['pregnant', 'pregnancy', 'expecting'])
        
        # Conditions
        features.has_diabetes = any(p in profiles_lower for p in ['diabetes', 'diabetic', 'type 2', 'type 1'])
        features.has_hypertension = any(p in profiles_lower for p in ['hypertension', 'hypertensive', 'high blood pressure'])
        features.has_heart_condition = any(p in profiles_lower for p in ['cardiac', 'heart', 'cardiovascular'])
        features.has_obesity = any(p in profiles_lower for p in ['obesity', 'obese', 'overweight'])
        features.has_celiac = any(p in profiles_lower for p in ['celiac', 'coeliac'])
        features.has_lactose_intolerance = any(p in profiles_lower for p in ['lactose', 'dairy intolerant'])
        
        return features


class FeatureExtractor:
    """
    Extracts ML features from raw product and profile data
    
    This is the bridge between scraped data and ML models.
    """
    
    # Risk ingredient patterns
    ARTIFICIAL_SWEETENERS = {
        'aspartame', 'sucralose', 'saccharin', 'acesulfame', 'acesulfame-k',
        'neotame', 'advantame', 'cyclamate', 'e950', 'e951', 'e952', 'e954', 'e955'
    }
    
    ARTIFICIAL_DYES = {
        'red 40', 'red 3', 'yellow 5', 'yellow 6', 'blue 1', 'blue 2',
        'green 3', 'e102', 'e110', 'e122', 'e124', 'e129', 'e131', 'e132', 'e133',
        'tartrazine', 'allura red', 'sunset yellow', 'brilliant blue'
    }
    
    PRESERVATIVES = {
        'sodium nitrate', 'sodium nitrite', 'potassium nitrate', 'bha', 'bht',
        'tbhq', 'sodium benzoate', 'potassium benzoate', 'sulfites', 'sulfur dioxide',
        'e250', 'e251', 'e252', 'e320', 'e321', 'e319'
    }
    
    TRANS_FAT_INDICATORS = {
        'partially hydrogenated', 'hydrogenated oil', 'shortening', 'margarine'
    }
    
    HIGH_SUGAR_INDICATORS = {
        'high fructose corn syrup', 'hfcs', 'corn syrup', 'glucose syrup',
        'dextrose', 'maltose', 'invert sugar'
    }
    
    ULTRA_PROCESSED_MARKERS = {
        'maltodextrin', 'modified starch', 'hydrolyzed', 'isolate',
        'natural flavor', 'natural flavour', 'artificial flavor', 'artificial flavour',
        'emulsifier', 'stabilizer', 'thickener', 'anti-caking', 'humectant'
    }
    
    def __init__(self):
        self.ingredient_vectorizer = None  # Can be set for text embeddings
    
    def extract_product_features(self, product: Dict) -> ProductFeatures:
        """Extract features from a product dictionary"""
        features = ProductFeatures()
        
        # Get ingredients
        ingredients = product.get('ingredients', [])
        if isinstance(ingredients, str):
            ingredients = [i.strip() for i in ingredients.split(',')]
        
        ingredients_text = ' '.join(ingredients).lower()
        
        # Basic counts
        features.num_ingredients = len(ingredients)
        features.ingredient_list_length = len(ingredients_text)
        
        # Count additives (E-numbers and known additives)
        e_number_pattern = r'\be\d{3}\b'
        e_numbers = re.findall(e_number_pattern, ingredients_text)
        features.num_additives = len(e_numbers) + sum(
            1 for marker in self.ULTRA_PROCESSED_MARKERS 
            if marker in ingredients_text
        )
        
        # Risk ingredient flags
        features.has_artificial_sweetener = any(
            s in ingredients_text for s in self.ARTIFICIAL_SWEETENERS
        )
        features.has_artificial_dye = any(
            d in ingredients_text for d in self.ARTIFICIAL_DYES
        )
        features.has_preservative = any(
            p in ingredients_text for p in self.PRESERVATIVES
        )
        features.has_trans_fat = any(
            t in ingredients_text for t in self.TRANS_FAT_INDICATORS
        )
        features.has_high_sugar = any(
            s in ingredients_text for s in self.HIGH_SUGAR_INDICATORS
        )
        features.has_msg = 'monosodium glutamate' in ingredients_text or 'msg' in ingredients_text
        
        # Nutrition features (normalize per 100g)
        nutrition = product.get('nutrition', {})
        features.calories = min(nutrition.get('calories', 0) / 500.0, 1.0)
        features.total_fat = min(nutrition.get('fat', nutrition.get('total_fat', 0)) / 50.0, 1.0)
        features.saturated_fat = min(nutrition.get('saturated_fat', 0) / 20.0, 1.0)
        features.trans_fat = min(nutrition.get('trans_fat', 0) / 5.0, 1.0)
        features.sodium = min(nutrition.get('sodium', 0) / 2000.0, 1.0)
        features.total_carbs = min(nutrition.get('carbohydrates', nutrition.get('total_carbohydrates', 0)) / 100.0, 1.0)
        features.fiber = min(nutrition.get('fiber', nutrition.get('dietary_fiber', 0)) / 30.0, 1.0)
        features.sugars = min(nutrition.get('sugars', nutrition.get('total_sugars', 0)) / 50.0, 1.0)
        features.protein = min(nutrition.get('protein', 0) / 50.0, 1.0)
        
        # Calculate NOVA group
        features.nova_group = self._calculate_nova(ingredients_text, features)
        
        # Calculate Nutri-Score value
        features.nutri_score_value = self._calculate_nutri_score(nutrition)
        
        return features
    
    def _calculate_nova(self, ingredients_text: str, features: ProductFeatures) -> int:
        """Calculate NOVA food processing group (1-4)"""
        ultra_processed_count = sum(
            1 for marker in self.ULTRA_PROCESSED_MARKERS
            if marker in ingredients_text
        )
        
        has_high_risk = (
            features.has_artificial_sweetener or 
            features.has_artificial_dye or
            features.has_trans_fat
        )
        
        if ultra_processed_count >= 3 or (ultra_processed_count >= 1 and has_high_risk):
            return 4  # Ultra-processed
        elif ultra_processed_count >= 1 or features.has_preservative:
            return 3  # Processed
        elif features.num_ingredients > 5:
            return 2  # Processed culinary ingredients
        else:
            return 1  # Minimally processed
    
    def _calculate_nutri_score(self, nutrition: Dict) -> int:
        """Calculate Nutri-Score value (0-100)"""
        score = 50  # Start at middle
        
        # Negative points for bad nutrients
        calories = nutrition.get('calories', 0)
        sugars = nutrition.get('sugars', nutrition.get('total_sugars', 0))
        sat_fat = nutrition.get('saturated_fat', 0)
        sodium = nutrition.get('sodium', 0)
        
        # Positive points for good nutrients
        fiber = nutrition.get('fiber', nutrition.get('dietary_fiber', 0))
        protein = nutrition.get('protein', 0)
        
        # Deductions
        if calories > 335: score -= 10
        elif calories > 250: score -= 5
        
        if sugars > 22.5: score -= 15
        elif sugars > 12.5: score -= 10
        elif sugars > 5: score -= 5
        
        if sat_fat > 5: score -= 15
        elif sat_fat > 2.5: score -= 10
        elif sat_fat > 1: score -= 5
        
        if sodium > 600: score -= 15
        elif sodium > 400: score -= 10
        elif sodium > 200: score -= 5
        
        # Additions
        if fiber > 4.7: score += 15
        elif fiber > 2.8: score += 10
        elif fiber > 0.9: score += 5
        
        if protein > 8: score += 10
        elif protein > 4.7: score += 5
        
        return max(0, min(100, score))
    
    def compute_interaction_features(self, 
                                     product_features: ProductFeatures,
                                     profile_features: ProfileFeatures) -> np.ndarray:
        """
        Compute interaction features between product and profile
        
        These capture the key relationships like:
        - Artificial sweetener × Diabetic = High risk
        - High sodium × Hypertensive = High risk
        - Artificial dye × Child = High risk
        """
        interactions = []
        
        # Sweetener interactions
        interactions.append(float(product_features.has_artificial_sweetener and profile_features.has_diabetes))
        interactions.append(float(product_features.has_artificial_sweetener and profile_features.is_child))
        interactions.append(float(product_features.has_artificial_sweetener and profile_features.is_pregnant))
        
        # Dye interactions
        interactions.append(float(product_features.has_artificial_dye and profile_features.is_child))
        interactions.append(float(product_features.has_artificial_dye and profile_features.is_toddler))
        
        # Sodium interactions
        high_sodium = product_features.sodium > 0.3  # >600mg
        interactions.append(float(high_sodium and profile_features.has_hypertension))
        interactions.append(float(high_sodium and profile_features.has_heart_condition))
        interactions.append(float(high_sodium and profile_features.is_senior))
        
        # Sugar interactions
        high_sugar = product_features.sugars > 0.45  # >22.5g
        interactions.append(float(high_sugar and profile_features.has_diabetes))
        interactions.append(float(high_sugar and profile_features.has_obesity))
        interactions.append(float(high_sugar and profile_features.is_child))
        
        # Trans fat interactions
        interactions.append(float(product_features.has_trans_fat and profile_features.has_heart_condition))
        interactions.append(float(product_features.has_trans_fat and profile_features.has_hypertension))
        
        # Preservative interactions
        interactions.append(float(product_features.has_preservative and profile_features.is_pregnant))
        interactions.append(float(product_features.has_preservative and profile_features.is_toddler))
        
        # NOVA group interactions
        ultra_processed = product_features.nova_group == 4
        interactions.append(float(ultra_processed and profile_features.is_child))
        interactions.append(float(ultra_processed and profile_features.has_obesity))
        interactions.append(float(ultra_processed and profile_features.has_diabetes))
        
        return np.array(interactions)
