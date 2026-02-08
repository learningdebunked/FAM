"""
FAM Machine Learning Models
Multi-task learning for food-health relationship prediction

Key Models:
1. IngredientRiskClassifier - Predicts risk level of unknown ingredients
2. HealthFitPredictor - Predicts product-profile compatibility score
3. AlternativeRecommender - Finds healthier alternatives using embeddings
4. PersonalizationEngine - Learns from user feedback to improve recommendations
"""

import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import json
import pickle
from pathlib import Path
import logging
from datetime import datetime

from .features import FeatureExtractor, ProductFeatures, ProfileFeatures

logger = logging.getLogger(__name__)

# Check for ML library availability
try:
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.neighbors import NearestNeighbors
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed. Using rule-based fallbacks.")


class IngredientRiskClassifier:
    """
    ML model to classify ingredient risk levels
    
    Training data: risk_ingredients table + expanded from research
    Features: Character n-grams (captures chemical name patterns)
    
    This allows classifying NEW ingredients not in the curated database
    by learning patterns like:
    - "-ose" suffix → likely sugar
    - "-ate" suffix → likely salt/preservative
    - "E" + 3 digits → European additive code
    """
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.classes = ['safe', 'low', 'medium', 'high', 'critical']
        self.is_trained = False
        
    def train(self, ingredients: List[str], risk_levels: List[str]):
        """Train on labeled ingredient data"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot train: scikit-learn not available")
            return
        
        # Use character n-grams to capture chemical name patterns
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 5),
            max_features=500,
            lowercase=True
        )
        
        X = self.vectorizer.fit_transform(ingredients)
        
        # Map risk levels to numeric
        level_map = {level: i for i, level in enumerate(self.classes)}
        y = np.array([level_map.get(r.lower(), 0) for r in risk_levels])
        
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            random_state=42
        )
        self.model.fit(X, y)
        self.is_trained = True
        
        logger.info(f"Trained ingredient classifier on {len(ingredients)} samples")
    
    def predict(self, ingredient: str) -> Tuple[str, float]:
        """Predict risk level for an ingredient"""
        if not self.is_trained or self.model is None:
            return 'unknown', 0.0
        
        X = self.vectorizer.transform([ingredient.lower()])
        proba = self.model.predict_proba(X)[0]
        pred_idx = np.argmax(proba)
        
        return self.classes[pred_idx], float(proba[pred_idx])
    
    def save(self, path: str):
        """Save model to disk"""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'vectorizer': self.vectorizer,
                'classes': self.classes,
                'is_trained': self.is_trained
            }, f)
    
    def load(self, path: str):
        """Load model from disk"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.vectorizer = data['vectorizer']
            self.classes = data['classes']
            self.is_trained = data['is_trained']


class HealthFitPredictor:
    """
    Predicts how well a product fits a health profile (0-100 score)
    
    This is the CORE ML model that learns:
    - Product features → Base healthiness
    - Profile features → User constraints
    - Interaction features → Product×Profile compatibility
    
    Training data sources:
    - Expert-labeled products (from nutritionists)
    - User feedback (thumbs up/down)
    - Health outcome correlations (from research)
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_extractor = FeatureExtractor()
        self.is_trained = False
        
        # Feature importance tracking
        self.feature_names = []
        self.feature_importances = {}
    
    def _build_features(self, product: Dict, profile: List[str]) -> np.ndarray:
        """Build feature vector from product and profile"""
        # Extract structured features
        prod_features = self.feature_extractor.extract_product_features(product)
        prof_features = ProfileFeatures.from_health_profiles(profile)
        
        # Get individual feature vectors
        prod_vec = prod_features.to_vector()
        prof_vec = prof_features.to_vector()
        
        # Compute interaction features
        interaction_vec = self.feature_extractor.compute_interaction_features(
            prod_features, prof_features
        )
        
        # Concatenate all features
        return np.concatenate([prod_vec, prof_vec, interaction_vec])
    
    def train(self, products: List[Dict], profiles: List[List[str]], 
              scores: List[float]):
        """
        Train the health fit predictor
        
        Args:
            products: List of product dicts with 'ingredients' and 'nutrition'
            profiles: List of health profile string lists
            scores: Ground truth fit scores (0-100)
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot train: scikit-learn not available")
            return
        
        # Build feature matrix
        X = np.array([
            self._build_features(prod, prof)
            for prod, prof in zip(products, profiles)
        ])
        y = np.array(scores)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train gradient boosting regressor
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
        # Store feature importances
        self.feature_importances = dict(zip(
            range(X.shape[1]),
            self.model.feature_importances_
        ))
        
        logger.info(f"Trained health fit predictor on {len(products)} samples")
    
    def predict(self, product: Dict, profile: List[str]) -> float:
        """Predict health fit score (0-100)"""
        if not self.is_trained:
            # Fallback to rule-based scoring
            return self._rule_based_score(product, profile)
        
        X = self._build_features(product, profile).reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        score = self.model.predict(X_scaled)[0]
        return float(np.clip(score, 0, 100))
    
    def _rule_based_score(self, product: Dict, profile: List[str]) -> float:
        """Fallback rule-based scoring when ML model not trained"""
        prod_features = self.feature_extractor.extract_product_features(product)
        prof_features = ProfileFeatures.from_health_profiles(profile)
        
        # Start with Nutri-Score
        score = prod_features.nutri_score_value
        
        # Penalize for risk ingredients
        if prod_features.has_artificial_sweetener:
            score -= 10
            if prof_features.has_diabetes or prof_features.is_child:
                score -= 15
        
        if prod_features.has_artificial_dye:
            score -= 5
            if prof_features.is_child or prof_features.is_toddler:
                score -= 15
        
        if prod_features.has_preservative:
            score -= 5
            if prof_features.is_pregnant:
                score -= 10
        
        if prod_features.has_trans_fat:
            score -= 15
            if prof_features.has_heart_condition:
                score -= 20
        
        # Penalize for high sodium
        if prod_features.sodium > 0.3:  # >600mg
            score -= 10
            if prof_features.has_hypertension or prof_features.is_senior:
                score -= 15
        
        # Penalize for NOVA 4
        if prod_features.nova_group == 4:
            score -= 10
        
        return float(np.clip(score, 0, 100))
    
    def explain_score(self, product: Dict, profile: List[str]) -> Dict:
        """Explain why a product got its score"""
        prod_features = self.feature_extractor.extract_product_features(product)
        prof_features = ProfileFeatures.from_health_profiles(profile)
        
        explanations = []
        
        # Check each risk factor
        if prod_features.has_artificial_sweetener:
            exp = "Contains artificial sweeteners"
            if prof_features.has_diabetes:
                exp += " (concerning for diabetic profiles)"
            if prof_features.is_child:
                exp += " (concerning for children)"
            explanations.append({"factor": "artificial_sweetener", "explanation": exp, "impact": -15})
        
        if prod_features.has_artificial_dye:
            exp = "Contains artificial dyes"
            if prof_features.is_child or prof_features.is_toddler:
                exp += " (linked to hyperactivity in children)"
            explanations.append({"factor": "artificial_dye", "explanation": exp, "impact": -10})
        
        if prod_features.has_trans_fat:
            exp = "Contains trans fats"
            if prof_features.has_heart_condition:
                exp += " (dangerous for heart conditions)"
            explanations.append({"factor": "trans_fat", "explanation": exp, "impact": -20})
        
        if prod_features.sodium > 0.3:
            exp = "High sodium content"
            if prof_features.has_hypertension:
                exp += " (dangerous for hypertension)"
            explanations.append({"factor": "high_sodium", "explanation": exp, "impact": -15})
        
        if prod_features.nova_group == 4:
            explanations.append({
                "factor": "ultra_processed",
                "explanation": "Ultra-processed food (NOVA 4)",
                "impact": -10
            })
        
        return {
            "base_score": prod_features.nutri_score_value,
            "final_score": self.predict(product, profile),
            "factors": explanations,
            "nova_group": prod_features.nova_group,
            "product_features": prod_features.to_dict()
        }
    
    def save(self, path: str):
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'feature_importances': self.feature_importances
            }, f)
    
    def load(self, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_trained = data['is_trained']
            self.feature_importances = data.get('feature_importances', {})


class AlternativeRecommender:
    """
    Recommends healthier alternatives using embedding similarity
    
    Approach:
    1. Embed products in a vector space (ingredients + nutrition)
    2. Find similar products (same category, similar taste profile)
    3. Filter to those with higher health scores
    4. Rank by similarity × health improvement
    """
    
    def __init__(self):
        self.product_embeddings = {}  # product_id -> embedding
        self.product_data = {}  # product_id -> product dict
        self.nn_model = None  # Nearest neighbors model
        self.embedding_matrix = None
        self.product_ids = []
        self.feature_extractor = FeatureExtractor()
        
    def _compute_embedding(self, product: Dict) -> np.ndarray:
        """Compute embedding for a product"""
        features = self.feature_extractor.extract_product_features(product)
        
        # Use product features as embedding
        base_embedding = features.to_vector()
        
        # Add category one-hot if available
        category = product.get('category', 'unknown').lower()
        category_map = {
            'beverages': 0, 'snacks': 1, 'cereals': 2, 'frozen': 3,
            'canned': 4, 'dairy': 5, 'bakery': 6, 'candy': 7
        }
        category_vec = np.zeros(len(category_map))
        for cat, idx in category_map.items():
            if cat in category:
                category_vec[idx] = 1
                break
        
        return np.concatenate([base_embedding, category_vec])
    
    def index_products(self, products: List[Dict]):
        """Index products for similarity search"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Cannot index: scikit-learn not available")
            return
        
        self.product_ids = []
        embeddings = []
        
        for product in products:
            product_id = product.get('id') or product.get('external_id') or product.get('name')
            if not product_id:
                continue
            
            embedding = self._compute_embedding(product)
            
            self.product_ids.append(product_id)
            self.product_data[product_id] = product
            self.product_embeddings[product_id] = embedding
            embeddings.append(embedding)
        
        if embeddings:
            self.embedding_matrix = np.array(embeddings)
            self.nn_model = NearestNeighbors(n_neighbors=20, metric='cosine')
            self.nn_model.fit(self.embedding_matrix)
            
            logger.info(f"Indexed {len(embeddings)} products for similarity search")
    
    def find_alternatives(self, product: Dict, profile: List[str],
                         health_predictor: HealthFitPredictor,
                         n_alternatives: int = 5) -> List[Dict]:
        """
        Find healthier alternatives for a product
        
        Args:
            product: The product to find alternatives for
            profile: User's health profile
            health_predictor: Model to score health fit
            n_alternatives: Number of alternatives to return
        """
        if self.nn_model is None:
            return []
        
        # Get embedding for query product
        query_embedding = self._compute_embedding(product)
        query_score = health_predictor.predict(product, profile)
        
        # Find similar products
        distances, indices = self.nn_model.kneighbors(
            query_embedding.reshape(1, -1),
            n_neighbors=min(50, len(self.product_ids))
        )
        
        alternatives = []
        for dist, idx in zip(distances[0], indices[0]):
            product_id = self.product_ids[idx]
            candidate = self.product_data[product_id]
            
            # Skip if same product
            if candidate.get('name') == product.get('name'):
                continue
            
            # Score the candidate
            candidate_score = health_predictor.predict(candidate, profile)
            
            # Only include if healthier
            if candidate_score > query_score:
                improvement = candidate_score - query_score
                similarity = 1 - dist  # Convert distance to similarity
                
                alternatives.append({
                    'product_id': product_id,
                    'name': candidate.get('name'),
                    'brand': candidate.get('brand'),
                    'image_url': candidate.get('image_url'),
                    'score': candidate_score,
                    'improvement': improvement,
                    'similarity': similarity,
                    'reason': self._generate_reason(product, candidate, improvement),
                    'benefits': self._list_benefits(product, candidate)
                })
        
        # Sort by improvement × similarity
        alternatives.sort(key=lambda x: x['improvement'] * x['similarity'], reverse=True)
        
        return alternatives[:n_alternatives]
    
    def _generate_reason(self, original: Dict, alternative: Dict, improvement: float) -> str:
        """Generate human-readable reason for recommendation"""
        orig_features = self.feature_extractor.extract_product_features(original)
        alt_features = self.feature_extractor.extract_product_features(alternative)
        
        reasons = []
        
        if orig_features.has_artificial_sweetener and not alt_features.has_artificial_sweetener:
            reasons.append("no artificial sweeteners")
        
        if orig_features.has_artificial_dye and not alt_features.has_artificial_dye:
            reasons.append("no artificial dyes")
        
        if orig_features.nova_group > alt_features.nova_group:
            reasons.append("less processed")
        
        if orig_features.sugars > alt_features.sugars + 0.1:
            reasons.append("lower sugar")
        
        if orig_features.sodium > alt_features.sodium + 0.1:
            reasons.append("lower sodium")
        
        if reasons:
            return f"Better choice: {', '.join(reasons)}"
        else:
            return f"Healthier option (+{improvement:.0f} points)"
    
    def _list_benefits(self, original: Dict, alternative: Dict) -> List[str]:
        """List specific benefits of the alternative"""
        orig_features = self.feature_extractor.extract_product_features(original)
        alt_features = self.feature_extractor.extract_product_features(alternative)
        
        benefits = []
        
        if not alt_features.has_artificial_sweetener:
            benefits.append("No artificial sweeteners")
        if not alt_features.has_artificial_dye:
            benefits.append("No artificial dyes")
        if not alt_features.has_preservative:
            benefits.append("No harmful preservatives")
        if alt_features.nova_group <= 2:
            benefits.append("Minimally processed")
        if alt_features.fiber > 0.1:
            benefits.append("Good fiber content")
        if alt_features.protein > 0.15:
            benefits.append("Good protein content")
        
        return benefits[:4]  # Limit to 4 benefits


class PersonalizationEngine:
    """
    Learns from user feedback to personalize recommendations
    
    Tracks:
    - Products user liked/disliked
    - Swaps user accepted/rejected
    - Ingredients user seems to avoid
    - Time-of-day preferences
    
    Uses this to:
    - Adjust scores for individual users
    - Prioritize certain types of alternatives
    - Learn implicit preferences
    """
    
    def __init__(self):
        self.user_preferences = {}  # user_id -> preferences dict
        self.feedback_history = []  # List of feedback events
        self.preference_model = None
        
    def record_feedback(self, user_id: str, product_id: str, 
                       feedback_type: str, context: Dict = None):
        """
        Record user feedback
        
        feedback_type: 'like', 'dislike', 'swap_accepted', 'swap_rejected', 'purchased'
        """
        event = {
            'user_id': user_id,
            'product_id': product_id,
            'feedback_type': feedback_type,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        self.feedback_history.append(event)
        
        # Update user preferences
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'liked_products': set(),
                'disliked_products': set(),
                'accepted_swaps': [],
                'rejected_swaps': [],
                'avoided_ingredients': {},
                'preferred_categories': {},
            }
        
        prefs = self.user_preferences[user_id]
        
        if feedback_type == 'like':
            prefs['liked_products'].add(product_id)
        elif feedback_type == 'dislike':
            prefs['disliked_products'].add(product_id)
            # Track which ingredients might be avoided
            if context and 'flagged_ingredients' in context:
                for ing in context['flagged_ingredients']:
                    prefs['avoided_ingredients'][ing] = prefs['avoided_ingredients'].get(ing, 0) + 1
        elif feedback_type == 'swap_accepted':
            prefs['accepted_swaps'].append({
                'original': context.get('original_product'),
                'alternative': product_id
            })
        elif feedback_type == 'swap_rejected':
            prefs['rejected_swaps'].append({
                'original': context.get('original_product'),
                'alternative': product_id
            })
    
    def get_score_adjustment(self, user_id: str, product: Dict) -> float:
        """
        Get personalized score adjustment for a product
        
        Returns adjustment to add to base score (-20 to +20)
        """
        if user_id not in self.user_preferences:
            return 0.0
        
        prefs = self.user_preferences[user_id]
        adjustment = 0.0
        
        product_id = product.get('id') or product.get('external_id')
        
        # Check if user previously liked/disliked
        if product_id in prefs['liked_products']:
            adjustment += 10
        if product_id in prefs['disliked_products']:
            adjustment -= 15
        
        # Check for avoided ingredients
        ingredients = product.get('ingredients', [])
        ingredients_text = ' '.join(ingredients).lower() if ingredients else ''
        
        for avoided_ing, count in prefs['avoided_ingredients'].items():
            if avoided_ing.lower() in ingredients_text:
                adjustment -= min(count * 5, 15)  # Cap at -15
        
        return np.clip(adjustment, -20, 20)
    
    def get_user_insights(self, user_id: str) -> Dict:
        """Get insights about user preferences"""
        if user_id not in self.user_preferences:
            return {'message': 'No preference data yet'}
        
        prefs = self.user_preferences[user_id]
        
        # Find most avoided ingredients
        avoided = sorted(
            prefs['avoided_ingredients'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_products_rated': len(prefs['liked_products']) + len(prefs['disliked_products']),
            'like_rate': len(prefs['liked_products']) / max(1, len(prefs['liked_products']) + len(prefs['disliked_products'])),
            'swap_acceptance_rate': len(prefs['accepted_swaps']) / max(1, len(prefs['accepted_swaps']) + len(prefs['rejected_swaps'])),
            'most_avoided_ingredients': [{'ingredient': ing, 'times_avoided': count} for ing, count in avoided],
        }
    
    def save(self, path: str):
        """Save personalization data"""
        # Convert sets to lists for JSON serialization
        data = {}
        for user_id, prefs in self.user_preferences.items():
            data[user_id] = {
                'liked_products': list(prefs['liked_products']),
                'disliked_products': list(prefs['disliked_products']),
                'accepted_swaps': prefs['accepted_swaps'],
                'rejected_swaps': prefs['rejected_swaps'],
                'avoided_ingredients': prefs['avoided_ingredients'],
                'preferred_categories': prefs['preferred_categories'],
            }
        
        with open(path, 'w') as f:
            json.dump({
                'user_preferences': data,
                'feedback_history': self.feedback_history[-10000:]  # Keep last 10k
            }, f)
    
    def load(self, path: str):
        """Load personalization data"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        self.feedback_history = data.get('feedback_history', [])
        
        for user_id, prefs in data.get('user_preferences', {}).items():
            self.user_preferences[user_id] = {
                'liked_products': set(prefs['liked_products']),
                'disliked_products': set(prefs['disliked_products']),
                'accepted_swaps': prefs['accepted_swaps'],
                'rejected_swaps': prefs['rejected_swaps'],
                'avoided_ingredients': prefs['avoided_ingredients'],
                'preferred_categories': prefs['preferred_categories'],
            }


class FAMMLEngine:
    """
    Main ML Engine that orchestrates all models
    
    This is the primary interface for the FAM app to use ML features.
    """
    
    def __init__(self, model_dir: str = None):
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent / 'trained_models'
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.ingredient_classifier = IngredientRiskClassifier()
        self.health_predictor = HealthFitPredictor()
        self.alternative_recommender = AlternativeRecommender()
        self.personalization = PersonalizationEngine()
        
        # Try to load pre-trained models
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if available"""
        try:
            ing_path = self.model_dir / 'ingredient_classifier.pkl'
            if ing_path.exists():
                self.ingredient_classifier.load(str(ing_path))
                logger.info("Loaded ingredient classifier")
        except Exception as e:
            logger.warning(f"Could not load ingredient classifier: {e}")
        
        try:
            health_path = self.model_dir / 'health_predictor.pkl'
            if health_path.exists():
                self.health_predictor.load(str(health_path))
                logger.info("Loaded health predictor")
        except Exception as e:
            logger.warning(f"Could not load health predictor: {e}")
        
        try:
            pers_path = self.model_dir / 'personalization.json'
            if pers_path.exists():
                self.personalization.load(str(pers_path))
                logger.info("Loaded personalization data")
        except Exception as e:
            logger.warning(f"Could not load personalization: {e}")
    
    def save_models(self):
        """Save all models"""
        self.ingredient_classifier.save(str(self.model_dir / 'ingredient_classifier.pkl'))
        self.health_predictor.save(str(self.model_dir / 'health_predictor.pkl'))
        self.personalization.save(str(self.model_dir / 'personalization.json'))
        logger.info("Saved all models")
    
    def analyze_product(self, product: Dict, profile: List[str], 
                       user_id: str = None) -> Dict:
        """
        Complete product analysis with ML enhancements
        
        Returns:
            Dict with score, explanations, and recommendations
        """
        # Get base health fit score
        base_score = self.health_predictor.predict(product, profile)
        
        # Apply personalization adjustment
        adjustment = 0.0
        if user_id:
            adjustment = self.personalization.get_score_adjustment(user_id, product)
        
        final_score = np.clip(base_score + adjustment, 0, 100)
        
        # Get detailed explanation
        explanation = self.health_predictor.explain_score(product, profile)
        
        # Classify any unknown ingredients
        ingredients = product.get('ingredients', [])
        ingredient_risks = []
        for ing in ingredients:
            risk_level, confidence = self.ingredient_classifier.predict(ing)
            if risk_level not in ['safe', 'unknown'] and confidence > 0.6:
                ingredient_risks.append({
                    'ingredient': ing,
                    'predicted_risk': risk_level,
                    'confidence': confidence
                })
        
        return {
            'fam_score': round(final_score, 1),
            'base_score': round(base_score, 1),
            'personalization_adjustment': round(adjustment, 1),
            'risk_level': self._score_to_risk_level(final_score),
            'explanation': explanation,
            'ml_ingredient_risks': ingredient_risks,
            'nova_group': explanation.get('nova_group', 0),
            'nutri_score_value': explanation.get('base_score', 50),
        }
    
    def get_alternatives(self, product: Dict, profile: List[str],
                        n_alternatives: int = 5) -> List[Dict]:
        """Get healthier alternatives for a product"""
        return self.alternative_recommender.find_alternatives(
            product, profile, self.health_predictor, n_alternatives
        )
    
    def record_feedback(self, user_id: str, product_id: str,
                       feedback_type: str, context: Dict = None):
        """Record user feedback for personalization"""
        self.personalization.record_feedback(user_id, product_id, feedback_type, context)
    
    def index_products(self, products: List[Dict]):
        """Index products for alternative recommendations"""
        self.alternative_recommender.index_products(products)
    
    def train_from_database(self, db_manager):
        """Train models from database data"""
        # Get risk ingredients for classifier training
        risk_ingredients = db_manager.get_risk_ingredients()
        if risk_ingredients:
            ingredients = [r['canonical_name'] for r in risk_ingredients]
            risk_levels = [r['risk_level'] for r in risk_ingredients]
            self.ingredient_classifier.train(ingredients, risk_levels)
        
        # Get products for indexing
        products = db_manager.search_products('', limit=10000)
        if products:
            self.index_products(products)
        
        logger.info("Trained models from database")
    
    def _score_to_risk_level(self, score: float) -> str:
        """Convert score to risk level string"""
        if score >= 80:
            return 'safe'
        elif score >= 60:
            return 'low'
        elif score >= 40:
            return 'medium'
        elif score >= 20:
            return 'high'
        else:
            return 'critical'
