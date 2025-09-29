"""
Mock AI Service for testing the evaluation framework without making actual API calls.
This simulates the behavior of the real AI service with predefined responses.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class MockRiskFlag(BaseModel):
    """Mock risk flag model"""
    ingredient: str
    risk_level: str
    concern: str
    affected_profiles: List[str]

class MockAnalysisResult(BaseModel):
    """Mock analysis result model"""
    risk_flags: List[MockRiskFlag]
    overall_risk_score: int
    recommendations: List[str]
    is_ai_analyzed: bool = True

class MockAIIngredientAnalyzer:
    """Mock AI service that returns predefined responses for testing"""
    
    # Map of test case IDs to their expected risk flags
    TEST_CASE_RESPONSES = {
        'test_001': {
            'risk_flags': [
                {
                    'ingredient': 'high fructose corn syrup',
                    'risk_level': 'high',
                    'concern': 'May cause blood sugar spikes',
                    'affected_profiles': ['diabetic']
                },
                {
                    'ingredient': 'artificial colors',
                    'risk_level': 'medium',
                    'concern': 'May cause hyperactivity in children',
                    'affected_profiles': ['child']
                },
                {
                    'ingredient': 'red 40',
                    'risk_level': 'medium',
                    'concern': 'Artificial color that may cause allergic reactions',
                    'affected_profiles': ['child']
                }
            ],
            'overall_risk_score': 75,
            'recommendations': [
                'Consider products with natural sweeteners instead of high fructose corn syrup',
                'Look for products without artificial colors'
            ]
        },
        'test_002': {
            'risk_flags': [
                {
                    'ingredient': 'organic cane sugar',
                    'risk_level': 'medium',
                    'concern': 'High sugar content may affect blood sugar levels',
                    'affected_profiles': ['diabetic']
                },
                {
                    'ingredient': 'sea salt',
                    'risk_level': 'low',
                    'concern': 'Sodium content may affect blood pressure',
                    'affected_profiles': ['hypertensive']
                }
            ],
            'overall_risk_score': 40,
            'recommendations': [
                'Monitor portion size due to sugar content',
                'Be mindful of sodium intake'
            ]
        },
        'test_003': {
            'risk_flags': [
                {
                    'ingredient': 'aspartame',
                    'risk_level': 'high',
                    'concern': 'May trigger migraines in sensitive individuals',
                    'affected_profiles': ['migraine']
                },
                {
                    'ingredient': 'acesulfame potassium',
                    'risk_level': 'medium',
                    'concern': 'Artificial sweetener that may affect blood sugar levels',
                    'affected_profiles': []
                }
            ],
            'overall_risk_score': 65,
            'recommendations': [
                'Consider natural sweeteners instead of artificial ones',
                'Monitor for any adverse reactions'
            ]
        },
        'test_004': {
            'risk_flags': [
                {
                    'ingredient': 'sucralose',
                    'risk_level': 'medium',
                    'concern': 'May cause digestive discomfort in some individuals',
                    'affected_profiles': ['digestive_issues']
                },
                {
                    'ingredient': 'sodium nitrate',
                    'risk_level': 'high',
                    'concern': 'Preservative that may cause digestive issues',
                    'affected_profiles': ['digestive_issues']
                }
            ],
            'overall_risk_score': 70,
            'recommendations': [
                'Consider nitrate-free alternatives',
                'Monitor for any digestive discomfort'
            ]
        },
        'test_005': {
            'risk_flags': [
                {
                    'ingredient': 'caffeine',
                    'risk_level': 'high',
                    'concern': 'May increase heart rate and anxiety',
                    'affected_profiles': ['anxiety', 'heart_conditions']
                }
            ],
            'overall_risk_score': 80,
            'recommendations': [
                'Consider caffeine-free alternatives',
                'Consult with a healthcare provider if you have heart conditions'
            ]
        }
    }
    
    @staticmethod
    async def analyze_ingredients(ingredients_raw: str, health_profiles: List[str]) -> Dict[str, Any]:
        """
        Mock implementation of ingredient analysis
        
        Args:
            ingredients_raw: Raw ingredients string
            health_profiles: List of health profiles to consider
            
        Returns:
            Dict containing mock analysis results
        """
        # Convert to lowercase for case-insensitive matching
        ingredients_lower = ingredients_raw.lower()
        
        # Check if we have a predefined response for this test case
        test_case_id = None
        
        # Match test cases based on ingredient patterns
        if ('high fructose corn syrup' in ingredients_lower and 
            'artificial colors' in ingredients_lower and 
            'red 40' in ingredients_lower):
            test_case_id = 'test_001'
        elif ('organic cane sugar' in ingredients_lower and 
              'sea salt' in ingredients_lower):
            test_case_id = 'test_002'
        elif ('aspartame' in ingredients_lower and 
              'acesulfame potassium' in ingredients_lower):
            test_case_id = 'test_003'
        elif ('sucralose' in ingredients_lower and 
              'sodium nitrate' in ingredients_lower):
            test_case_id = 'test_004'
        elif ('caffeine' in ingredients_lower and 
              'taurine' in ingredients_lower):
            test_case_id = 'test_005'
        
        if test_case_id and test_case_id in MockAIIngredientAnalyzer.TEST_CASE_RESPONSES:
            # Return the predefined response for this test case
            return MockAIIngredientAnalyzer.TEST_CASE_RESPONSES[test_case_id]
        
        # Default response for unknown test cases
        return {
            'risk_flags': [],
            'overall_risk_score': 0,
            'recommendations': ['No specific health risks identified'],
            'is_ai_analyzed': True
        }
