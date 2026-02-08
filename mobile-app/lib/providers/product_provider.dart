import 'package:flutter/foundation.dart';
import '../models/product.dart';
import '../models/analysis_result.dart';

class ProductProvider extends ChangeNotifier {
  Product? _currentProduct;
  AnalysisResult? _currentAnalysis;
  List<HealthyAlternative> _alternatives = [];
  List<Product> _scanHistory = [];
  bool _isLoading = false;
  bool _isAnalyzing = false;
  String? _error;

  Product? get currentProduct => _currentProduct;
  AnalysisResult? get currentAnalysis => _currentAnalysis;
  List<HealthyAlternative> get alternatives => _alternatives;
  List<Product> get scanHistory => _scanHistory;
  bool get isLoading => _isLoading;
  bool get isAnalyzing => _isAnalyzing;
  String? get error => _error;

  Future<void> setProductFromBarcode(String barcode) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // TODO: Fetch from Open Food Facts API
      await Future.delayed(const Duration(seconds: 1));
      
      // Mock product for now
      _currentProduct = Product(
        id: barcode,
        barcode: barcode,
        name: 'Sample Product',
        brand: 'Sample Brand',
        ingredients: ['Sugar', 'Wheat flour', 'Palm oil', 'Salt'],
      );
      
      _scanHistory.insert(0, _currentProduct!);
      if (_scanHistory.length > 50) {
        _scanHistory = _scanHistory.sublist(0, 50);
      }
    } catch (e) {
      _error = 'Failed to fetch product: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> setProductFromOCR(String ingredientText) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Parse ingredients from OCR text
      final ingredients = ingredientText
          .split(RegExp(r'[,;]'))
          .map((i) => i.trim())
          .where((i) => i.isNotEmpty)
          .toList();

      _currentProduct = Product(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        barcode: 'OCR-${DateTime.now().millisecondsSinceEpoch}',
        name: 'Scanned Product',
        ingredients: ingredients,
      );
      
      _scanHistory.insert(0, _currentProduct!);
    } catch (e) {
      _error = 'Failed to parse ingredients: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> analyzeProduct() async {
    if (_currentProduct == null) return;

    _isAnalyzing = true;
    _error = null;
    notifyListeners();

    try {
      // TODO: Call LLM API for analysis
      await Future.delayed(const Duration(seconds: 2));

      // Mock analysis result
      _currentAnalysis = AnalysisResult(
        productId: _currentProduct!.id,
        overallScore: 65.0,
        overallRisk: RiskLevel.medium,
        ingredientFlags: [
          IngredientFlag(
            ingredientName: 'Palm oil',
            canonicalName: 'Palm Oil',
            riskLevel: RiskLevel.medium,
            explanation: 'High in saturated fats, may increase cardiovascular risk.',
          ),
        ],
        memberRisks: [],
        explanation: 'This product contains moderate levels of saturated fat and sodium.',
      );
    } catch (e) {
      _error = 'Failed to analyze product: $e';
    } finally {
      _isAnalyzing = false;
      notifyListeners();
    }
  }

  Future<void> fetchAlternatives() async {
    if (_currentProduct == null) return;

    _isLoading = true;
    notifyListeners();

    try {
      // TODO: Fetch from API
      await Future.delayed(const Duration(seconds: 1));

      _alternatives = [
        HealthyAlternative(
          productId: 'alt-1',
          name: 'Organic Alternative',
          brand: 'Health Brand',
          score: 85.0,
          reason: 'Lower in saturated fat, no palm oil',
          benefits: ['No palm oil', 'Organic ingredients', 'Lower sodium'],
        ),
      ];
    } catch (e) {
      _error = 'Failed to fetch alternatives: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearCurrentProduct() {
    _currentProduct = null;
    _currentAnalysis = null;
    _alternatives = [];
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
