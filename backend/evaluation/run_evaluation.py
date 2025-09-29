import json
import asyncio
from pathlib import Path
from collections import defaultdict
import sys

# Add parent directory to path to import ai_service
sys.path.append(str(Path(__file__).parent.parent))

from services.ai_service import AIIngredientAnalyzer

class IngredientClassifierEvaluator:
    # The six risk flags from your paper
    RISK_FLAGS = ["Aspartame", "Red 40", "HFCS", "Sucralose", "Sodium nitrate", "Caffeine"]
    
    def __init__(self, test_data_path):
        """Load test dataset"""
        with open(test_data_path, 'r') as f:
            data = json.load(f)
            self.test_cases = data['test_cases']
        
        # Initialize confusion matrix counters for each flag
        self.metrics = {flag: {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0} for flag in self.RISK_FLAGS}
    
    def normalize_flag(self, flag):
        """Normalize flag names to match canonical list"""
        flag_lower = str(flag).lower()
        
        # Map variations to canonical names
        mappings = {
            'high fructose corn syrup': 'HFCS',
            'hfcs': 'HFCS',
            'corn syrup': 'HFCS',
            'red 40': 'Red 40',
            'red 40 lake': 'Red 40',
            'red dye 40': 'Red 40',
            'aspartame': 'Aspartame',
            'sucralose': 'Sucralose',
            'sodium nitrate': 'Sodium nitrate',
            'sodium nitrite': 'Sodium nitrate',  # Group nitrite with nitrate
            'caffeine': 'Caffeine'
        }
        
        for key, value in mappings.items():
            if key in flag_lower:
                return value
        
        return None  # Unknown flag
    
    async def evaluate_single_case(self, test_case):
        """Evaluate one test case and update metrics"""
        try:
            # Get prediction from your AI service
            result = await AIIngredientAnalyzer.analyze_ingredients(
                test_case['ingredients_raw'],
                health_profiles=[]
            )
            
            # Extract and normalize predicted flags from risk_flags
            predicted_flags = set()
            for risk in result.get('risk_flags', []):
                normalized = self.normalize_flag(risk.get('ingredient', ''))
                if normalized:
                    predicted_flags.add(normalized)
            
            # Get ground truth
            ground_truth_flags = set(test_case['ground_truth']['risk_flags'])
            
            # Update metrics for each flag
            for flag in self.RISK_FLAGS:
                is_predicted = flag in predicted_flags
                is_actual = flag in ground_truth_flags
                
                if is_actual and is_predicted:
                    self.metrics[flag]['tp'] += 1  # True Positive
                elif not is_actual and is_predicted:
                    self.metrics[flag]['fp'] += 1  # False Positive
                elif is_actual and not is_predicted:
                    self.metrics[flag]['fn'] += 1  # False Negative
                elif not is_actual and not is_predicted:
                    self.metrics[flag]['tn'] += 1  # True Negative
            
            return {
                'id': test_case['id'],
                'product_name': test_case['product_name'],
                'predicted': sorted(predicted_flags),
                'actual': sorted(ground_truth_flags),
                'correct': predicted_flags == ground_truth_flags
            }
            
        except Exception as e:
            print(f"Error evaluating {test_case['id']}: {str(e)}")
            return None
    
    async def run_evaluation(self):
        """Run evaluation on all test cases"""
        print(f"Evaluating {len(self.test_cases)} test cases...")
        
        results = []
        for i, test_case in enumerate(self.test_cases):
            print(f"Processing {i+1}/{len(self.test_cases)}: {test_case['id']}")
            result = await self.evaluate_single_case(test_case)
            if result:
                results.append(result)
        
        return results
    
    def calculate_metrics(self):
        """Calculate precision, recall, F1 for each flag"""
        flag_metrics = {}
        
        for flag in self.RISK_FLAGS:
            tp = self.metrics[flag]['tp']
            fp = self.metrics[flag]['fp']
            fn = self.metrics[flag]['fn']
            
            # Calculate metrics
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            flag_metrics[flag] = {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'tp': tp,
                'fp': fp,
                'fn': fn,
                'support': tp + fn  # Number of actual positives
            }
        
        # Calculate macro and weighted averages
        total_support = sum(m['support'] for m in flag_metrics.values())
        macro_precision = sum(m['precision'] for m in flag_metrics.values()) / len(self.RISK_FLAGS)
        macro_recall = sum(m['recall'] for m in flag_metrics.values()) / len(self.RISK_FLAGS)
        macro_f1 = sum(m['f1'] for m in flag_metrics.values()) / len(self.RISK_FLAGS)
        
        # Calculate weighted averages
        weighted_precision = sum(m['precision'] * m['support'] for m in flag_metrics.values()) / total_support if total_support > 0 else 0
        weighted_recall = sum(m['recall'] * m['support'] for m in flag_metrics.values()) / total_support if total_support > 0 else 0
        weighted_f1 = sum(m['f1'] * m['support'] for m in flag_metrics.values()) / total_support if total_support > 0 else 0
        
        return {
            'per_flag': flag_metrics,
            'macro_avg': {
                'precision': macro_precision,
                'recall': macro_recall,
                'f1': macro_f1,
                'support': total_support
            },
            'weighted_avg': {
                'precision': weighted_precision,
                'recall': weighted_recall,
                'f1': weighted_f1,
                'support': total_support
            }
        }
    
    def print_results(self, metrics):
        """Print formatted results table"""
        print("\n" + "="*80)
        print("INGREDIENT CLASSIFIER EVALUATION RESULTS")
        print("="*80)
        print(f"\nDataset size: {len(self.test_cases)} items\n")
        
        # Per-flag table
        print(f"{'Risk Flag':<20} {'Precision':<10} {'Recall':<10} {'F1':<10} {'Support':<10}")
        print("-"*60)
        for flag, scores in metrics['per_flag'].items():
            print(f"{flag:<20} {scores['precision']:<10.3f} {scores['recall']:<10.3f} "
                  f"{scores['f1']:<10.3f} {scores['support']:<10}")
        
        # Averages
        print("\nAverages:")
        print(f"{'Macro':<20} {metrics['macro_avg']['precision']:<10.3f} "
              f"{metrics['macro_avg']['recall']:<10.3f} {metrics['macro_avg']['f1']:<10.3f} {metrics['macro_avg']['support']:<10}")
        print(f"{'Weighted':<20} {metrics['weighted_avg']['precision']:<10.3f} "
              f"{metrics['weighted_avg']['recall']:<10.3f} {metrics['weighted_avg']['f1']:<10.3f} {metrics['weighted_avg']['support']:<10}")
        
        # Detailed confusion matrix
        print("\nDetailed Confusion Matrix (TP/FP/FN):")
        print(f"{'Flag':<20} {'TP':<6} {'FP':<6} {'FN':<6}")
        print("-"*45)
        for flag, scores in metrics['per_flag'].items():
            print(f"{flag:<20} {scores['tp']:<6} {scores['fp']:<6} {scores['fn']:<6}")
        
        print("="*80)


async def main():
    # Path to your test dataset
    test_data_path = Path(__file__).parent / '../tests/test_data/ingredient_test_cases.json'
    
    if not test_data_path.exists():
        print(f"Error: Test dataset not found at {test_data_path}")
        print("Please make sure the test data file exists.")
        return
    
    # Run evaluation
    evaluator = IngredientClassifierEvaluator(test_data_path)
    results = await evaluator.run_evaluation()
    
    # Calculate and print metrics
    metrics = evaluator.calculate_metrics()
    evaluator.print_results(metrics)
    
    # Save detailed results
    output_dir = Path(__file__).parent / 'results'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'evaluation_results.json'
    
    with open(output_path, 'w') as f:
        json.dump({
            'metrics': metrics,
            'individual_results': results,
            'total_cases': len(evaluator.test_cases),
            'test_data_path': str(test_data_path)
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
