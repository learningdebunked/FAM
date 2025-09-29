"""
Ingredient Classifier Evaluation Script

This script evaluates the performance of the ingredient classifier against a golden dataset
and generates a formatted report showing precision, recall, and F1 scores for each risk flag.
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

# Import the mock service
from services.mock_ai_service import MockAIIngredientAnalyzer

class IngredientEvaluator:
    """Evaluates the performance of the ingredient classifier."""
    
    def __init__(self):
        self.risk_flags = {
            'Aspartame': {'tp': 0, 'fp': 0, 'fn': 0},
            'Red 40': {'tp': 0, 'fp': 0, 'fn': 0},
            'HFCS': {'tp': 0, 'fp': 0, 'fn': 0},
            'Sucralose': {'tp': 0, 'fp': 0, 'fn': 0},
            'Sodium nitrate': {'tp': 0, 'fp': 0, 'fn': 0},
            'Caffeine': {'tp': 0, 'fp': 0, 'fn': 0}
        }
        
        # Map ingredients to their standard risk flag names
        self.ingredient_to_flag = {
            'aspartame': 'Aspartame',
            'red 40': 'Red 40',
            'high fructose corn syrup': 'HFCS',
            'sucralose': 'Sucralose',
            'sodium nitrate': 'Sodium nitrate',
            'caffeine': 'Caffeine'
        }
    
    def _normalize_ingredient(self, ingredient: str) -> str:
        """Normalize ingredient name for matching."""
        return ingredient.lower().strip()
    
    def _extract_expected_flags(self, test_case: dict) -> Set[str]:
        """Extract expected risk flags from test case."""
        expected = set()
        for flag in test_case['expected_output'].get('risk_flags', []):
            ingredient = self._normalize_ingredient(flag['ingredient'])
            if ingredient in self.ingredient_to_flag:
                expected.add(self.ingredient_to_flag[ingredient])
        return expected
    
    def _extract_predicted_flags(self, result: dict) -> Set[str]:
        """Extract predicted risk flags from analysis result."""
        predicted = set()
        for flag in result.get('risk_flags', []):
            ingredient = self._normalize_ingredient(flag['ingredient'])
            if ingredient in self.ingredient_to_flag:
                predicted.add(self.ingredient_to_flag[ingredient])
        return predicted
    
    def update_metrics(self, test_case: dict, result: dict):
        """Update evaluation metrics based on test case and prediction result."""
        expected = self._extract_expected_flags(test_case)
        predicted = self._extract_predicted_flags(result)
        
        # Update metrics for each risk flag
        for flag in self.risk_flags:
            if flag in expected and flag in predicted:
                self.risk_flags[flag]['tp'] += 1  # True positive
            elif flag in expected and flag not in predicted:
                self.risk_flags[flag]['fn'] += 1  # False negative
            elif flag not in expected and flag in predicted:
                self.risk_flags[flag]['fp'] += 1  # False positive
    
    def calculate_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate precision, recall, and F1 score for each risk flag."""
        metrics = {}
        
        for flag, counts in self.risk_flags.items():
            tp = counts['tp']
            fp = counts['fp']
            fn = counts['fn']
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics[flag] = {
                'precision': round(precision, 3),
                'recall': round(recall, 3),
                'f1': round(f1, 3)
            }
        
        return metrics
    
    def print_report(self, dataset_size: int):
        """Print the evaluation report in the requested format."""
        metrics = self.calculate_metrics()
        
        # Calculate macro-averages
        avg_precision = sum(m['precision'] for m in metrics.values()) / len(metrics)
        avg_recall = sum(m['recall'] for m in metrics.values()) / len(metrics)
        avg_f1 = sum(m['f1'] for m in metrics.values()) / len(metrics)
        
        # Format the report
        header = "=" * 40 + " INGREDIENT CLASSIFIER EVALUATION RESULTS " + "=" * 40
        print(header)
        print(f"Dataset size: {dataset_size} items")
        print("Risk Flag          Precision  Recall     F1")
        print("-" * 80)
        
        for flag in sorted(metrics.keys()):
            print(f"{flag:<18} {metrics[flag]['precision']:>8.3f}  {metrics[flag]['recall']:>6.3f}  {metrics[flag]['f1']:>7.3f}")
        
        print("-" * 80)
        print(f"{'Macro-average':<18} {avg_precision:>8.3f}  {avg_recall:>6.3f}  {avg_f1:>7.3f}")
        print("=" * len(header))

async def main():
    """Main function to run the evaluation."""
    # Load the expanded golden dataset
    dataset_path = Path(__file__).parent / 'test_data' / 'expanded_golden_dataset.json'
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Initialize evaluator and mock service
    evaluator = IngredientEvaluator()
    mock_service = MockAIIngredientAnalyzer()
    
    # Evaluate each test case
    for test_case in dataset['test_cases']:
        try:
            # Get prediction from mock service
            ingredients = ", ".join(test_case['ingredients'])
            health_profiles = test_case['health_profiles']
            result = await mock_service.analyze_ingredients(ingredients, health_profiles)
            
            # Update evaluation metrics
            evaluator.update_metrics(test_case, result)
            
        except Exception as e:
            print(f"Error evaluating test case {test_case.get('id', 'unknown')}: {str(e)}")
    
    # Print the evaluation report
    evaluator.print_report(len(dataset['test_cases']))

if __name__ == "__main__":
    asyncio.run(main())
