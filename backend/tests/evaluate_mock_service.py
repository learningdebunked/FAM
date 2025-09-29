"""Evaluation script for the mock AI service using the golden dataset."""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import the mock service
from services.mock_ai_service import MockAIIngredientAnalyzer

def load_golden_dataset(file_path: Path) -> Dict[str, Any]:
    """Load the golden dataset from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_metrics(
    predicted_flags: List[Dict[str, Any]],
    expected_flags: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Calculate evaluation metrics (precision, recall, f1)."""
    # Extract ingredient names from flags for comparison
    predicted_ingredients = {flag['ingredient'].lower() for flag in predicted_flags}
    expected_ingredients = {flag['ingredient'].lower() for flag in expected_flags}
    
    # Calculate true positives, false positives, and false negatives
    true_positives = len(predicted_ingredients & expected_ingredients)
    false_positives = len(predicted_ingredients - expected_ingredients)
    false_negatives = len(expected_ingredients - predicted_ingredients)
    
    # Calculate metrics
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'precision': precision,
        'recall': recall,
        'f1_score': f1
    }

async def evaluate_test_case(
    test_case: Dict[str, Any],
    mock_service: Any
) -> Tuple[bool, Dict[str, Any]]:
    """Evaluate a single test case using the mock service."""
    test_id = test_case.get('id', 'unknown')
    print(f"\nEvaluating test case {test_id}...")
    
    # Prepare input for the mock service
    ingredients = ", ".join(test_case['ingredients'])
    health_profiles = test_case['health_profiles']
    expected = test_case['expected_output']
    
    try:
        # Call the mock service
        result = await mock_service.analyze_ingredients(ingredients, health_profiles)
        
        # Calculate metrics
        metrics = calculate_metrics(
            result.get('risk_flags', []),
            expected.get('risk_flags', [])
        )
        
        # Check if overall risk score is within 20 points of expected
        score_diff = abs(result.get('overall_risk_score', 0) - expected.get('overall_risk_score', 0))
        score_match = score_diff <= 20
        
        return True, {
            'test_id': test_id,
            'success': True,
            'metrics': metrics,
            'score_match': score_match,
            'score_diff': score_diff,
            'result': result
        }
    except Exception as e:
        return False, {
            'test_id': test_id,
            'success': False,
            'error': str(e)
        }

async def main():
    """Main evaluation function."""
    # Load the golden dataset
    dataset_path = Path(__file__).parent / 'test_data' / 'golden_dataset.json'
    dataset = load_golden_dataset(dataset_path)
    
    # Initialize the mock service
    mock_service = MockAIIngredientAnalyzer()
    
    # Evaluate each test case
    results = []
    for test_case in dataset['test_cases']:
        success, result = await evaluate_test_case(test_case, mock_service)
        results.append(result)
    
    # Calculate overall metrics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get('success', False))
    avg_precision = sum(r.get('metrics', {}).get('precision', 0) for r in results) / total_tests
    avg_recall = sum(r.get('metrics', {}).get('recall', 0) for r in results) / total_tests
    avg_f1 = sum(r.get('metrics', {}).get('f1_score', 0) for r in results) / total_tests
    
    # Print summary
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Total test cases: {total_tests}")
    print(f"Passed test cases: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Average Precision: {avg_precision:.4f}")
    print(f"Average Recall:    {avg_recall:.4f}")
    print(f"Average F1 Score:  {avg_f1:.4f}")
    
    # Print detailed results
    print("\nDETAILED RESULTS:")
    for result in results:
        if result['success']:
            print(f"\nTest {result['test_id']}:")
            print(f"  - Precision: {result['metrics']['precision']:.4f}")
            print(f"  - Recall:    {result['metrics']['recall']:.4f}")
            print(f"  - F1 Score:  {result['metrics']['f1_score']:.4f}")
            print(f"  - Score Diff: {result['score_diff']} (within threshold: {result['score_match']})")
        else:
            print(f"\nTest {result['test_id']} FAILED: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
