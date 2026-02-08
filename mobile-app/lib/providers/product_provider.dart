import 'package:flutter/foundation.dart';
import '../models/product.dart';
import '../models/analysis_result.dart';
import '../models/family_member.dart';
import '../services/open_food_facts_service.dart';
import '../services/backend_service.dart';

class ProductProvider extends ChangeNotifier {
  Product? _currentProduct;
  AnalysisResult? _currentAnalysis;
  List<HealthyAlternative> _alternatives = [];
  List<Product> _scanHistory = [];
  bool _isLoading = false;
  bool _isAnalyzing = false;
  String? _error;
  
  final OpenFoodFactsService _openFoodFactsService = OpenFoodFactsService();
  final BackendService _backendService = BackendService();
  
  List<FamilyMember> _familyMembers = [];

  Product? get currentProduct => _currentProduct;
  AnalysisResult? get currentAnalysis => _currentAnalysis;
  List<HealthyAlternative> get alternatives => _alternatives;
  List<Product> get scanHistory => _scanHistory;
  bool get isLoading => _isLoading;
  bool get isAnalyzing => _isAnalyzing;
  String? get error => _error;

  void initialize() {
    _backendService.initialize();
  }
  
  void setFamilyMembers(List<FamilyMember> members) {
    _familyMembers = members;
  }

  Future<void> setProductFromBarcode(String barcode) async {
    _isLoading = true;
    _error = null;
    _currentAnalysis = null;
    notifyListeners();

    try {
      // Fetch from Open Food Facts API
      final product = await _openFoodFactsService.getProductByBarcode(barcode);
      
      if (product != null) {
        _currentProduct = product;
      } else {
        // Product not found in Open Food Facts
        _currentProduct = Product(
          id: barcode,
          barcode: barcode,
          name: 'Unknown Product',
          brand: null,
          ingredients: [],
        );
        _error = 'Product not found in database. Try scanning the ingredient label instead.';
      }
      
      _scanHistory.insert(0, _currentProduct!);
      if (_scanHistory.length > 50) {
        _scanHistory = _scanHistory.sublist(0, 50);
      }
    } on OpenFoodFactsException catch (e) {
      _error = e.message;
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
    _currentAnalysis = null;
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
    
    // Skip analysis if no ingredients
    if (_currentProduct!.ingredients.isEmpty) {
      _currentAnalysis = AnalysisResult(
        productId: _currentProduct!.id,
        overallScore: 50.0,
        overallRisk: RiskLevel.low,
        ingredientFlags: [],
        memberRisks: [],
        explanation: 'No ingredients available for analysis. Try scanning the ingredient label.',
      );
      notifyListeners();
      return;
    }

    _isAnalyzing = true;
    _error = null;
    notifyListeners();

    try {
      // Call backend API for AI-powered analysis
      _currentAnalysis = await _backendService.analyzeIngredients(
        productId: _currentProduct!.id,
        ingredients: _currentProduct!.ingredients,
        familyMembers: _familyMembers,
      );
    } on BackendException catch (e) {
      _error = e.message;
      // Provide a fallback analysis
      _currentAnalysis = _createFallbackAnalysis();
    } catch (e) {
      _error = 'Failed to analyze product: $e';
      _currentAnalysis = _createFallbackAnalysis();
    } finally {
      _isAnalyzing = false;
      notifyListeners();
    }
  }
  
  AnalysisResult _createFallbackAnalysis() {
    return AnalysisResult(
      productId: _currentProduct!.id,
      overallScore: 50.0,
      overallRisk: RiskLevel.low,
      ingredientFlags: [],
      memberRisks: [],
      explanation: 'Unable to perform AI analysis. Please check your connection and try again.',
    );
  }

  Future<void> fetchAlternatives() async {
    if (_currentProduct == null) return;

    _isLoading = true;
    notifyListeners();

    try {
      // Fetch alternatives from backend
      _alternatives = await _backendService.getAlternatives(
        productId: _currentProduct!.id,
        ingredients: _currentProduct!.ingredients,
        familyMembers: _familyMembers,
        category: _currentProduct!.category,
      );
      
      // If no alternatives from backend, provide some suggestions
      if (_alternatives.isEmpty) {
        _alternatives = _generateLocalAlternatives();
      }
    } on BackendException catch (e) {
      _error = e.message;
      _alternatives = _generateLocalAlternatives();
    } catch (e) {
      _error = 'Failed to fetch alternatives: $e';
      _alternatives = _generateLocalAlternatives();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  List<HealthyAlternative> _generateLocalAlternatives() {
    // Generate suggestions based on current product analysis
    final suggestions = <HealthyAlternative>[];
    
    if (_currentAnalysis != null) {
      final flags = _currentAnalysis!.ingredientFlags;
      
      // Check for artificial sweeteners
      if (flags.any((f) => f.canonicalName.toLowerCase().contains('aspartame') ||
                          f.canonicalName.toLowerCase().contains('sucralose'))) {
        suggestions.add(HealthyAlternative(
          productId: 'alt-sweetener',
          name: 'Natural sweetener alternative',
          score: 85.0,
          reason: 'Consider products sweetened with stevia or monk fruit',
          benefits: ['No artificial sweeteners', 'Natural ingredients'],
        ));
      }
      
      // Check for artificial dyes
      if (flags.any((f) => f.canonicalName.toLowerCase().contains('red 40') ||
                          f.canonicalName.toLowerCase().contains('yellow'))) {
        suggestions.add(HealthyAlternative(
          productId: 'alt-dye',
          name: 'Natural color alternative',
          score: 80.0,
          reason: 'Look for products with natural colorings from fruits and vegetables',
          benefits: ['No artificial dyes', 'Natural colors'],
        ));
      }
      
      // Check for high sodium
      if (flags.any((f) => f.canonicalName.toLowerCase().contains('sodium'))) {
        suggestions.add(HealthyAlternative(
          productId: 'alt-sodium',
          name: 'Low-sodium alternative',
          score: 82.0,
          reason: 'Choose low-sodium or no-salt-added versions',
          benefits: ['Reduced sodium', 'Heart-healthy'],
        ));
      }
    }
    
    // Add a generic healthy suggestion
    if (suggestions.isEmpty) {
      suggestions.add(HealthyAlternative(
        productId: 'alt-generic',
        name: 'Whole food alternative',
        score: 90.0,
        reason: 'Consider whole, unprocessed foods as an alternative',
        benefits: ['Minimally processed', 'Nutrient-dense', 'No additives'],
      ));
    }
    
    return suggestions;
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
