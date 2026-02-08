"""
FAM Machine Learning Module
Provides ML-powered scoring, personalization, and recommendations
"""

from .models import (
    FAMMLEngine,
    IngredientRiskClassifier,
    HealthFitPredictor,
    AlternativeRecommender,
    PersonalizationEngine,
)

from .knowledge_graph import FoodHealthKnowledgeGraph

from .features import FeatureExtractor, ProductFeatures, ProfileFeatures

__all__ = [
    'FAMMLEngine',
    'IngredientRiskClassifier', 
    'HealthFitPredictor',
    'AlternativeRecommender',
    'PersonalizationEngine',
    'FoodHealthKnowledgeGraph',
    'FeatureExtractor',
    'ProductFeatures',
    'ProfileFeatures',
]
