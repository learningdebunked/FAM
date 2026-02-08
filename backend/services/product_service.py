"""
Product Service for FAM
Integrates the local product database with the analysis and recommendation engine
"""

import sys
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import get_db, DatabaseManager


class ProductService:
    """
    Service layer for product operations
    Combines database lookups with AI analysis
    """
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or get_db()
        self._risk_ingredients_cache = None
    
    def _get_risk_ingredients(self) -> Dict[str, Dict]:
        """Get risk ingredients map (cached)"""
        if self._risk_ingredients_cache is None:
            risk_list = self.db.get_risk_ingredients()
            self._risk_ingredients_cache = {
                r['canonical_name'].lower(): r for r in risk_list
            }
        return self._risk_ingredients_cache
    
    def search_products(self, query: str, retailer: str = None, 
                       limit: int = 20) -> List[Dict]:
        """Search products in local database"""
        retailer_id = None
        if retailer:
            r = self.db.get_retailer_by_name(retailer)
            retailer_id = r['id'] if r else None
        
        products = self.db.search_products(query, retailer_id=retailer_id, limit=limit)
        
        # Enrich with analysis if available
        for product in products:
            analysis = self.db.get_product_analysis(product['id'])
            if analysis:
                product['analysis'] = analysis.get('analysis', {})
        
        return products
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Dict]:
        """Get product by barcode from local database"""
        product = self.db.get_product_by_barcode(barcode)
        
        if product:
            # Get analysis
            analysis = self.db.get_product_analysis(product['id'])
            if analysis:
                product['analysis'] = analysis.get('analysis', {})
            
            # Get alternatives
            alternatives = self.db.get_alternatives(product['id'])
            product['alternatives'] = alternatives
        
        return product
    
    def analyze_ingredients(self, ingredients: List[str], 
                           health_profiles: List[str],
                           nutrition: Dict = None,
                           price: float = None) -> Dict[str, Any]:
        """
        Analyze ingredients using local risk database
        
        This implements the FAM scoring formula from the paper:
        Score(item, profile) = α·NutriScore − β·RiskFlags + γ·FitToGoals − δ·BudgetPenalty
        
        Where:
        - α = 0.4 (weight for nutritional quality)
        - β = 0.3 (weight for risk ingredients)
        - γ = 0.2 (weight for fit to health goals)
        - δ = 0.1 (weight for budget penalty)
        """
        # Scoring weights from paper
        ALPHA = 0.4  # NutriScore weight
        BETA = 0.3   # RiskFlags weight
        GAMMA = 0.2  # FitToGoals weight
        DELTA = 0.1  # BudgetPenalty weight
        
        risk_map = self._get_risk_ingredients()
        profiles_lower = [p.lower() for p in health_profiles]
        
        risk_flags = []
        risk_score = 0
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Check against each risk ingredient
            for risk_name, risk_info in risk_map.items():
                if risk_name in ingredient_lower:
                    # Check if this risk affects the user's profiles
                    affected_profiles = risk_info.get('affected_profiles', [])
                    is_relevant = any(p in profiles_lower for p in affected_profiles)
                    
                    # Always flag, but mark relevance
                    flag = {
                        'ingredient': ingredient,
                        'canonical_name': risk_info['canonical_name'],
                        'risk_level': risk_info['risk_level'],
                        'category': risk_info['category'],
                        'description': risk_info['description'],
                        'concern': risk_info['description'],
                        'affected_profiles': affected_profiles,
                        'is_relevant_to_user': is_relevant,
                        'evidence_url': f"https://www.ewg.org/foodscores/content/natural-vs-artificial-ingredients"
                    }
                    risk_flags.append(flag)
                    
                    # Weight risk score based on relevance
                    multiplier = 1.5 if is_relevant else 1.0
                    
                    if risk_info['risk_level'] == 'high':
                        risk_score += 25 * multiplier
                    elif risk_info['risk_level'] == 'medium':
                        risk_score += 15 * multiplier
                    elif risk_info['risk_level'] == 'low':
                        risk_score += 5 * multiplier
                    
                    break  # Only match once per ingredient
        
        # ==================== FAM Score Calculation ====================
        
        # 1. NutriScore component (0-100)
        nutri_score_value = self._calculate_nutri_score(nutrition) if nutrition else 50
        nutri_score_component = nutri_score_value * ALPHA
        
        # 2. RiskFlags component (0-100, inverted so higher = worse)
        risk_flags_value = min(risk_score, 100)
        risk_flags_component = risk_flags_value * BETA
        
        # 3. FitToGoals component (0-100)
        fit_to_goals_value = self._calculate_fit_to_goals(risk_flags, health_profiles)
        fit_to_goals_component = fit_to_goals_value * GAMMA
        
        # 4. BudgetPenalty component (0-100)
        budget_penalty_value = self._calculate_budget_penalty(price) if price else 0
        budget_penalty_component = budget_penalty_value * DELTA
        
        # Final FAM Score: α·NutriScore − β·RiskFlags + γ·FitToGoals − δ·BudgetPenalty
        fam_score = (
            nutri_score_component 
            - risk_flags_component 
            + fit_to_goals_component 
            - budget_penalty_component
        )
        
        # Normalize to 0-100 range
        overall_score = max(0, min(100, fam_score + 50))  # Center around 50
        
        # Determine NOVA group based on ingredients
        nova_group = self._calculate_nova_group(ingredients, risk_flags)
        
        # Determine Nutri-Score letter
        nutri_score_letter = self._get_nutri_score_letter(nutri_score_value)
        
        # Determine risk level
        if overall_score >= 80:
            risk_level = 'safe'
        elif overall_score >= 60:
            risk_level = 'low'
        elif overall_score >= 40:
            risk_level = 'medium'
        elif overall_score >= 20:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_flags, health_profiles)
        
        return {
            # Core scores
            'overall_score': int(overall_score),
            'fam_score': int(overall_score),
            'risk_level': risk_level,
            
            # Score components (for breakdown display)
            'nutri_score_component': round(nutri_score_component, 1),
            'risk_flags_component': round(risk_flags_component, 1),
            'fit_to_goals_component': round(fit_to_goals_component, 1),
            'budget_penalty_component': round(budget_penalty_component, 1),
            
            # Classification scores
            'nutri_score': nutri_score_letter,
            'nutri_score_value': int(nutri_score_value),
            'nova_group': nova_group,
            
            # Ingredient analysis
            'risk_flags': risk_flags,
            'total_ingredients': len(ingredients),
            'flagged_count': len(risk_flags),
            
            # Recommendations
            'recommendations': recommendations,
            
            # Meta
            'is_ai_analyzed': False,
            'analysis_source': 'local_database'
        }
    
    def _calculate_nutri_score(self, nutrition: Dict) -> int:
        """
        Calculate Nutri-Score value (0-100) based on nutrition data
        Based on Open Food Facts algorithm
        """
        if not nutrition:
            return 50  # Default middle score
        
        score = 50  # Start at middle
        
        # Negative points for bad nutrients (per 100g)
        energy = nutrition.get('calories', 0)
        sugars = nutrition.get('sugars', 0)
        saturated_fat = nutrition.get('saturated_fat', 0)
        sodium = nutrition.get('sodium', 0)
        
        # Positive points for good nutrients
        fiber = nutrition.get('fiber', 0)
        protein = nutrition.get('protein', 0)
        
        # Deduct for bad nutrients
        if energy > 335: score -= 10
        elif energy > 250: score -= 5
        
        if sugars > 22.5: score -= 15
        elif sugars > 12.5: score -= 10
        elif sugars > 5: score -= 5
        
        if saturated_fat > 5: score -= 15
        elif saturated_fat > 2.5: score -= 10
        elif saturated_fat > 1: score -= 5
        
        if sodium > 600: score -= 15
        elif sodium > 400: score -= 10
        elif sodium > 200: score -= 5
        
        # Add for good nutrients
        if fiber > 4.7: score += 15
        elif fiber > 2.8: score += 10
        elif fiber > 0.9: score += 5
        
        if protein > 8: score += 10
        elif protein > 4.7: score += 5
        
        return max(0, min(100, score))
    
    def _get_nutri_score_letter(self, value: int) -> str:
        """Convert numeric Nutri-Score to letter grade"""
        if value >= 80: return 'A'
        if value >= 60: return 'B'
        if value >= 40: return 'C'
        if value >= 20: return 'D'
        return 'E'
    
    def _calculate_nova_group(self, ingredients: List[str], risk_flags: List[Dict]) -> int:
        """
        Calculate NOVA food processing classification (1-4)
        1 = Unprocessed/minimally processed
        2 = Processed culinary ingredients
        3 = Processed foods
        4 = Ultra-processed foods
        """
        # Ultra-processed indicators
        ultra_processed_markers = [
            'high fructose corn syrup', 'maltodextrin', 'dextrose',
            'hydrogenated', 'modified starch', 'hydrolyzed',
            'artificial', 'natural flavor', 'natural flavour',
            'color', 'colour', 'emulsifier', 'stabilizer',
            'thickener', 'anti-caking', 'bulking agent'
        ]
        
        ingredients_lower = ' '.join(ingredients).lower()
        
        # Check for ultra-processed markers
        ultra_processed_count = sum(
            1 for marker in ultra_processed_markers 
            if marker in ingredients_lower
        )
        
        # Check for high-risk additives
        high_risk_count = len([f for f in risk_flags if f['risk_level'] == 'high'])
        
        if ultra_processed_count >= 3 or high_risk_count >= 2:
            return 4  # Ultra-processed
        elif ultra_processed_count >= 1 or high_risk_count >= 1:
            return 3  # Processed
        elif len(ingredients) > 5:
            return 2  # Processed culinary ingredients
        else:
            return 1  # Minimally processed
    
    def _calculate_fit_to_goals(self, risk_flags: List[Dict], 
                                health_profiles: List[str]) -> int:
        """
        Calculate how well the product fits user's health goals (0-100)
        Higher = better fit
        """
        if not health_profiles:
            return 50  # Neutral if no profile
        
        score = 100
        
        # Penalize for relevant risk flags
        relevant_flags = [f for f in risk_flags if f.get('is_relevant_to_user')]
        
        for flag in relevant_flags:
            if flag['risk_level'] == 'high':
                score -= 30
            elif flag['risk_level'] == 'medium':
                score -= 15
            elif flag['risk_level'] == 'low':
                score -= 5
        
        return max(0, score)
    
    def _calculate_budget_penalty(self, price: float) -> int:
        """
        Calculate budget penalty (0-100)
        Higher = more expensive (worse)
        """
        if price is None:
            return 0
        
        # Simple threshold-based penalty
        if price > 20: return 30
        if price > 10: return 20
        if price > 5: return 10
        return 0
    
    def _generate_recommendations(self, risk_flags: List[Dict], 
                                  health_profiles: List[str]) -> List[str]:
        """Generate recommendations based on flagged ingredients"""
        recommendations = []
        
        if not risk_flags:
            recommendations.append("No significant concerns found for your health profile.")
            return recommendations
        
        # Count by risk level
        high_risk = [f for f in risk_flags if f['risk_level'] == 'high']
        medium_risk = [f for f in risk_flags if f['risk_level'] == 'medium']
        relevant_flags = [f for f in risk_flags if f.get('is_relevant_to_user')]
        
        if high_risk:
            recommendations.append(
                f"Found {len(high_risk)} high-risk ingredient(s). "
                "Consider avoiding this product or finding alternatives."
            )
        
        if relevant_flags:
            profiles_affected = set()
            for f in relevant_flags:
                for p in f.get('affected_profiles', []):
                    if p.lower() in [hp.lower() for hp in health_profiles]:
                        profiles_affected.add(p)
            
            if profiles_affected:
                recommendations.append(
                    f"This product contains ingredients that may affect: {', '.join(profiles_affected)}."
                )
        
        # Specific recommendations by category
        categories = set(f['category'] for f in risk_flags)
        
        if 'artificial_sweetener' in categories:
            recommendations.append(
                "Contains artificial sweeteners. Consider products with natural sweeteners like stevia."
            )
        
        if 'artificial_dye' in categories:
            recommendations.append(
                "Contains artificial dyes. Look for products with natural colorings."
            )
        
        if 'high_sugar' in categories:
            recommendations.append(
                "High in added sugars. Consider low-sugar or sugar-free alternatives."
            )
        
        if 'preservative' in categories:
            recommendations.append(
                "Contains preservatives of concern. Fresh or minimally processed options may be better."
            )
        
        return recommendations
    
    def get_alternatives(self, product_id: int = None, 
                        ingredients: List[str] = None,
                        health_profiles: List[str] = None,
                        category: str = None) -> List[Dict]:
        """
        Get healthy alternatives for a product
        
        Can work with:
        1. Product ID (looks up in database)
        2. Ingredients list (generates suggestions)
        """
        alternatives = []
        
        # If we have a product ID, check database first
        if product_id:
            db_alternatives = self.db.get_alternatives(product_id)
            if db_alternatives:
                return self._format_alternatives(db_alternatives)
        
        # Generate alternatives based on ingredients
        if ingredients:
            alternatives = self._generate_alternatives_from_ingredients(
                ingredients, health_profiles or [], category
            )
        
        return alternatives
    
    def _generate_alternatives_from_ingredients(self, ingredients: List[str],
                                                health_profiles: List[str],
                                                category: str = None) -> List[Dict]:
        """Generate alternative suggestions based on flagged ingredients"""
        # First analyze the ingredients
        analysis = self.analyze_ingredients(ingredients, health_profiles)
        risk_flags = analysis.get('risk_flags', [])
        
        if not risk_flags:
            return [{
                'product_id': 'alt-generic',
                'name': 'This product appears healthy for your profile',
                'brand': None,
                'image_url': None,
                'score': 90,
                'reason': 'No concerning ingredients found',
                'benefits': ['No flagged ingredients'],
                'price_difference': None
            }]
        
        # Generate alternatives based on flagged categories
        alternatives = []
        seen = set()
        
        alternative_suggestions = {
            'artificial_sweetener': {
                'name': 'Products with natural sweeteners (stevia, monk fruit)',
                'reason': 'Natural sweeteners without metabolic concerns',
                'benefits': ['No artificial sweeteners', 'Natural origin', 'Lower glycemic impact'],
                'score': 85
            },
            'artificial_dye': {
                'name': 'Products with natural colorings',
                'reason': 'Natural colors from fruits and vegetables',
                'benefits': ['No artificial dyes', 'Safe for children', 'No hyperactivity concerns'],
                'score': 88
            },
            'high_sugar': {
                'name': 'Low-sugar or naturally sweetened alternatives',
                'reason': 'Reduced sugar content for better metabolic health',
                'benefits': ['Lower sugar', 'Better for diabetics', 'Reduced calorie intake'],
                'score': 82
            },
            'preservative': {
                'name': 'Fresh or minimally preserved options',
                'reason': 'Fewer preservatives means fewer potential health concerns',
                'benefits': ['No harmful preservatives', 'Fresher ingredients', 'Cleaner label'],
                'score': 86
            },
            'harmful_fat': {
                'name': 'Products with healthy fats (olive oil, avocado)',
                'reason': 'Heart-healthy fats instead of trans fats',
                'benefits': ['No trans fats', 'Heart-healthy', 'Anti-inflammatory'],
                'score': 90
            },
            'stimulant': {
                'name': 'Caffeine-free alternatives',
                'reason': 'No stimulants that affect sleep or blood pressure',
                'benefits': ['No caffeine', 'Better for sleep', 'Safe during pregnancy'],
                'score': 88
            }
        }
        
        for flag in risk_flags:
            category = flag.get('category')
            if category in alternative_suggestions and category not in seen:
                seen.add(category)
                suggestion = alternative_suggestions[category]
                alternatives.append({
                    'product_id': f'alt-{len(alternatives)+1}',
                    'name': suggestion['name'],
                    'brand': None,
                    'image_url': None,
                    'score': suggestion['score'],
                    'reason': suggestion['reason'],
                    'benefits': suggestion['benefits'],
                    'price_difference': None,
                    'replaces': flag['canonical_name']
                })
        
        # Try to find actual products from database
        if category:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT p.id, p.name, p.brand, p.image_url, p.price,
                           pa.overall_score
                    FROM products p
                    JOIN product_analysis pa ON p.id = pa.product_id
                    JOIN categories c ON p.category_id = c.id
                    WHERE LOWER(c.name) LIKE LOWER(?)
                    AND pa.overall_score >= 75
                    ORDER BY pa.overall_score DESC
                    LIMIT 3
                """, (f"%{category}%",))
                
                db_products = cursor.fetchall()
                
                for prod in db_products:
                    alternatives.append({
                        'product_id': str(prod['id']),
                        'name': prod['name'],
                        'brand': prod['brand'],
                        'image_url': prod['image_url'],
                        'score': prod['overall_score'],
                        'reason': 'Healthier option from our database',
                        'benefits': ['Higher health score', 'Fewer concerning ingredients'],
                        'price_difference': None
                    })
        
        return alternatives[:5]  # Return max 5 alternatives
    
    def _format_alternatives(self, db_alternatives: List[Dict]) -> List[Dict]:
        """Format database alternatives for API response"""
        return [{
            'product_id': str(alt.get('alternative_product_id')),
            'name': alt.get('name'),
            'brand': alt.get('brand'),
            'image_url': alt.get('image_url'),
            'score': alt.get('alternative_score', 0),
            'reason': alt.get('reason', ''),
            'benefits': ['Healthier alternative'],
            'price_difference': None
        } for alt in db_alternatives]


# Singleton instance
_product_service = None

def get_product_service() -> ProductService:
    """Get singleton product service instance"""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service
