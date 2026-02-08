import 'package:dio/dio.dart';
import '../models/product.dart';

class OpenFoodFactsService {
  static const String _baseUrl = 'https://world.openfoodfacts.org/api/v2';
  
  final Dio _dio = Dio(BaseOptions(
    baseUrl: _baseUrl,
    connectTimeout: const Duration(seconds: 15),
    receiveTimeout: const Duration(seconds: 15),
  ));

  Future<Product?> getProductByBarcode(String barcode) async {
    try {
      final response = await _dio.get('/product/$barcode.json');
      
      if (response.statusCode == 200 && response.data['status'] == 1) {
        final productData = response.data['product'];
        return _parseProduct(barcode, productData);
      }
      
      return null;
    } catch (e) {
      throw OpenFoodFactsException('Failed to fetch product: $e');
    }
  }

  Future<List<Product>> searchProducts(String query, {int page = 1, int pageSize = 20}) async {
    try {
      final response = await _dio.get('/search', queryParameters: {
        'search_terms': query,
        'page': page,
        'page_size': pageSize,
        'json': 1,
      });

      if (response.statusCode == 200) {
        final products = response.data['products'] as List<dynamic>? ?? [];
        return products
            .map((p) => _parseProduct(p['code'] ?? '', p))
            .whereType<Product>()
            .toList();
      }

      return [];
    } catch (e) {
      throw OpenFoodFactsException('Failed to search products: $e');
    }
  }

  Product? _parseProduct(String barcode, Map<String, dynamic> data) {
    try {
      final name = data['product_name'] ?? 
                   data['product_name_en'] ?? 
                   'Unknown Product';
      
      final brand = data['brands'];
      final imageUrl = data['image_front_url'] ?? data['image_url'];
      
      // Parse ingredients
      final ingredientsText = data['ingredients_text'] ?? 
                              data['ingredients_text_en'] ?? '';
      final ingredients = _parseIngredients(ingredientsText);
      
      // Parse nutrition
      final nutriments = data['nutriments'] as Map<String, dynamic>?;
      final nutrition = nutriments != null ? _parseNutrition(nutriments) : null;
      
      final category = data['categories_tags']?.isNotEmpty == true
          ? (data['categories_tags'] as List).first.toString().replaceAll('en:', '')
          : null;

      return Product(
        id: barcode,
        barcode: barcode,
        name: name,
        brand: brand,
        imageUrl: imageUrl,
        ingredients: ingredients,
        nutrition: nutrition,
        category: category,
      );
    } catch (e) {
      return null;
    }
  }

  List<String> _parseIngredients(String ingredientsText) {
    if (ingredientsText.isEmpty) return [];
    
    // Split by common delimiters and clean up
    return ingredientsText
        .replaceAll(RegExp(r'\([^)]*\)'), '') // Remove parenthetical content
        .split(RegExp(r'[,;•]'))
        .map((i) => i.trim())
        .where((i) => i.isNotEmpty && i.length > 1)
        .map((i) => i.replaceAll(RegExp(r'^\d+\.?\d*%?\s*'), '')) // Remove percentages
        .where((i) => i.isNotEmpty)
        .toList();
  }

  NutritionInfo _parseNutrition(Map<String, dynamic> nutriments) {
    return NutritionInfo(
      calories: _getDouble(nutriments, 'energy-kcal_100g'),
      fat: _getDouble(nutriments, 'fat_100g'),
      saturatedFat: _getDouble(nutriments, 'saturated-fat_100g'),
      transFat: _getDouble(nutriments, 'trans-fat_100g'),
      cholesterol: _getDouble(nutriments, 'cholesterol_100g'),
      sodium: _getDouble(nutriments, 'sodium_100g'),
      carbohydrates: _getDouble(nutriments, 'carbohydrates_100g'),
      fiber: _getDouble(nutriments, 'fiber_100g'),
      sugars: _getDouble(nutriments, 'sugars_100g'),
      protein: _getDouble(nutriments, 'proteins_100g'),
      calcium: _getDouble(nutriments, 'calcium_100g'),
      iron: _getDouble(nutriments, 'iron_100g'),
      potassium: _getDouble(nutriments, 'potassium_100g'),
      servingSize: nutriments['serving_size'] as String?,
    );
  }

  double? _getDouble(Map<String, dynamic> map, String key) {
    final value = map[key];
    if (value == null) return null;
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value);
    return null;
  }
}

class OpenFoodFactsException implements Exception {
  final String message;
  OpenFoodFactsException(this.message);
  
  @override
  String toString() => message;
}
