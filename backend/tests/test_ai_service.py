import json
import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any, List
from ..services.ai_service import AIIngredientAnalyzer

# Load test data
TEST_DATA_PATH = Path(__file__).parent / 'test_data' / 'golden_dataset.json'

with open(TEST_DATA_PATH, 'r') as f:
    TEST_CASES = json.load(f)['test_cases']

class TestAIService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", TEST_CASES)
    async def test_ai_analysis(self, test_case: Dict[str, Any]):
        """Test AI analysis against golden dataset."""
        # Get test case data
        test_id = test_case['id']
        ingredients = test_case['ingredients']
        health_profiles = test_case['health_profiles']
        expected = test_case['expected_output']
        
        # Call the AI service
        analyzer = AIIngredientAnalyzer()
        result = await analyzer.analyze_ingredients(ingredients, health_profiles)
        
        # Basic structure validation
        assert 'risk_flags' in result, f"Test {test_id}: Missing 'risk_flags' in result"
        assert 'overall_risk_score' in result, f"Test {test_id}: Missing 'overall_risk_score' in result"
        assert 'recommendations' in result, f"Test {test_id}: Missing 'recommendations' in result"
        
        # Validate risk flags
        self._validate_risk_flags(test_id, result['risk_flags'], ingredients, health_profiles)
        
        # Validate risk score is within expected range
        assert 0 <= result['overall_risk_score'] <= 100, \
            f"Test {test_id}: Risk score out of range"
        
        # If expected output is provided, validate against it
        if expected:
            self._compare_with_expected(test_id, result, expected)
    
    def _validate_risk_flags(self, test_id: str, risk_flags: List[Dict], 
                           ingredients: List[str], health_profiles: List[str]):
        """Validate the structure and content of risk flags."""
        required_fields = {'ingredient', 'risk_level', 'concern', 'affected_profiles'}
        
        for flag in risk_flags:
            # Check required fields
            missing_fields = required_fields - set(flag.keys())
            assert not missing_fields, \
                f"Test {test_id}: Missing fields in risk flag: {missing_fields}"
            
            # Validate risk level
            assert flag['risk_level'] in ['low', 'medium', 'high'], \
                f"Test {test_id}: Invalid risk level: {flag['risk_level']}"
            
            # Validate ingredient exists in the input
            assert flag['ingredient'].lower() in [i.lower() for i in ingredients], \
                f"Test {test_id}: Flagged ingredient not in input: {flag['ingredient']}"
            
            # Validate affected profiles
            for profile in flag['affected_profiles']:
                assert profile in health_profiles, \
                    f"Test {test_id}: Invalid affected profile: {profile}"
    
    def _compare_with_expected(self, test_id: str, actual: Dict, expected: Dict):
        """Compare actual results with expected results."""
        # Compare risk score with tolerance
        assert abs(actual['overall_risk_score'] - expected['overall_risk_score']) <= 10, \
            f"Test {test_id}: Risk score differs significantly from expected"
        
        # Compare number of risk flags
        assert len(actual['risk_flags']) == len(expected['risk_flags']), \
            f"Test {test_id}: Expected {len(expected['risk_flags'])} risk flags, got {len(actual['risk_flags'])}"
        
        # Compare recommendations
        assert len(actual['recommendations']) > 0, \
            f"Test {test_id}: No recommendations provided"

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
