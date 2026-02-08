"""
ML Service for FAM
Provides ML-powered analysis, scoring, and recommendations
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.models import FAMMLEngine
from ml.knowledge_graph import FoodHealthKnowledgeGraph
from database.db_manager import get_db

logger = logging.getLogger(__name__)


class MLService:
    """
    Service layer for ML-powered features
    
    Provides:
    - Enhanced product analysis with ML scoring
    - Knowledge graph-based explanations
    - Personalized recommendations
    - Smart alternative suggestions
    """
    
    def __init__(self):
        self.ml_engine = FAMMLEngine()
        self.knowledge_graph = FoodHealthKnowledgeGraph()
        self.db = get_db()
        self._initialized = False
    
    def initialize(self):
        """Initialize ML models with database data"""
        if self._initialized:
            return
        
        try:
            # Train models from database
            self.ml_engine.train_from_database(self.db)
            self._initialized = True
            logger.info("ML Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ML Service: {e}")
    
    def analyze_product_ml(self, product: Dict, health_profiles: List[str],
                          user_id: str = None) -> Dict:
        """
        Analyze a product using ML models
        
        This provides:
        1. ML-based health fit score
        2. Knowledge graph explanations
        3. Personalized adjustments
        4. Evidence-based risk explanations
        """
        # Get ML analysis
        ml_analysis = self.ml_engine.analyze_product(product, health_profiles, user_id)
        
        # Enhance with knowledge graph explanations
        ingredients = product.get('ingredients', [])
        kg_explanations = []
        
        for ingredient in ingredients:
            risks = self.knowledge_graph.get_ingredient_risks(ingredient)
            if risks.get('found') and risks.get('risky_for_profiles'):
                # Check if any user profile matches
                for profile in health_profiles:
                    explanation = self.knowledge_graph.explain_risk(ingredient, profile)
                    if explanation.get('is_risky'):
                        kg_explanations.append({
                            'ingredient': ingredient,
                            'profile': profile,
                            'explanation_chain': explanation.get('explanation_chain', []),
                            'evidence': explanation.get('evidence_urls', []),
                            'alternatives': explanation.get('alternatives', [])
                        })
        
        # Combine results
        return {
            **ml_analysis,
            'knowledge_graph_explanations': kg_explanations,
            'has_kg_data': len(kg_explanations) > 0
        }
    
    def get_smart_alternatives(self, product: Dict, health_profiles: List[str],
                              n_alternatives: int = 5) -> List[Dict]:
        """
        Get smart alternatives using ML embeddings and knowledge graph
        """
        # Get ML-based alternatives
        ml_alternatives = self.ml_engine.get_alternatives(product, health_profiles, n_alternatives)
        
        # Enhance with knowledge graph alternatives for specific ingredients
        ingredients = product.get('ingredients', [])
        kg_alternatives = {}
        
        for ingredient in ingredients:
            alts = self.knowledge_graph.get_safe_alternatives(ingredient)
            if alts:
                kg_alternatives[ingredient] = alts
        
        # Add ingredient-level alternatives to response
        for alt in ml_alternatives:
            alt['ingredient_swaps'] = kg_alternatives
        
        return ml_alternatives
    
    def explain_ingredient(self, ingredient: str, profile: str = None) -> Dict:
        """
        Get detailed explanation for an ingredient
        """
        # Get knowledge graph data
        risks = self.knowledge_graph.get_ingredient_risks(ingredient)
        
        if profile:
            explanation = self.knowledge_graph.explain_risk(ingredient, profile)
            risks['profile_specific'] = explanation
        
        # Get ML classification
        risk_level, confidence = self.ml_engine.ingredient_classifier.predict(ingredient)
        risks['ml_classification'] = {
            'predicted_risk': risk_level,
            'confidence': confidence
        }
        
        return risks
    
    def get_profile_risks(self, profile: str) -> Dict:
        """
        Get all ingredients risky for a specific health profile
        """
        return self.knowledge_graph.query_by_profile(profile)
    
    def record_user_feedback(self, user_id: str, product_id: str,
                            feedback_type: str, context: Dict = None):
        """
        Record user feedback for personalization
        """
        self.ml_engine.record_feedback(user_id, product_id, feedback_type, context)
    
    def get_user_insights(self, user_id: str) -> Dict:
        """
        Get insights about user preferences
        """
        return self.ml_engine.personalization.get_user_insights(user_id)
    
    def get_knowledge_graph_stats(self) -> Dict:
        """
        Get statistics about the knowledge graph
        """
        return self.knowledge_graph.get_stats()


# Singleton instance
_ml_service = None

def get_ml_service() -> MLService:
    """Get singleton ML service instance"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService()
        _ml_service.initialize()
    return _ml_service
