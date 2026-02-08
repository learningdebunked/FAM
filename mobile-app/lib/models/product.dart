class Product {
  final String id;
  final String barcode;
  final String name;
  final String? brand;
  final String? imageUrl;
  final List<String> ingredients;
  final NutritionInfo? nutrition;
  final String? category;
  final DateTime scannedAt;

  Product({
    required this.id,
    required this.barcode,
    required this.name,
    this.brand,
    this.imageUrl,
    this.ingredients = const [],
    this.nutrition,
    this.category,
    DateTime? scannedAt,
  }) : scannedAt = scannedAt ?? DateTime.now();

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'barcode': barcode,
      'name': name,
      'brand': brand,
      'imageUrl': imageUrl,
      'ingredients': ingredients,
      'nutrition': nutrition?.toJson(),
      'category': category,
      'scannedAt': scannedAt.toIso8601String(),
    };
  }

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'] as String,
      barcode: json['barcode'] as String,
      name: json['name'] as String,
      brand: json['brand'] as String?,
      imageUrl: json['imageUrl'] as String?,
      ingredients: List<String>.from(json['ingredients'] as List? ?? []),
      nutrition: json['nutrition'] != null
          ? NutritionInfo.fromJson(json['nutrition'] as Map<String, dynamic>)
          : null,
      category: json['category'] as String?,
      scannedAt: json['scannedAt'] != null
          ? DateTime.parse(json['scannedAt'] as String)
          : DateTime.now(),
    );
  }
}

class NutritionInfo {
  final double? calories;
  final double? fat;
  final double? saturatedFat;
  final double? transFat;
  final double? cholesterol;
  final double? sodium;
  final double? carbohydrates;
  final double? fiber;
  final double? sugars;
  final double? addedSugars;
  final double? protein;
  final double? vitaminD;
  final double? calcium;
  final double? iron;
  final double? potassium;
  final String? servingSize;

  NutritionInfo({
    this.calories,
    this.fat,
    this.saturatedFat,
    this.transFat,
    this.cholesterol,
    this.sodium,
    this.carbohydrates,
    this.fiber,
    this.sugars,
    this.addedSugars,
    this.protein,
    this.vitaminD,
    this.calcium,
    this.iron,
    this.potassium,
    this.servingSize,
  });

  Map<String, dynamic> toJson() {
    return {
      'calories': calories,
      'fat': fat,
      'saturatedFat': saturatedFat,
      'transFat': transFat,
      'cholesterol': cholesterol,
      'sodium': sodium,
      'carbohydrates': carbohydrates,
      'fiber': fiber,
      'sugars': sugars,
      'addedSugars': addedSugars,
      'protein': protein,
      'vitaminD': vitaminD,
      'calcium': calcium,
      'iron': iron,
      'potassium': potassium,
      'servingSize': servingSize,
    };
  }

  factory NutritionInfo.fromJson(Map<String, dynamic> json) {
    return NutritionInfo(
      calories: (json['calories'] as num?)?.toDouble(),
      fat: (json['fat'] as num?)?.toDouble(),
      saturatedFat: (json['saturatedFat'] as num?)?.toDouble(),
      transFat: (json['transFat'] as num?)?.toDouble(),
      cholesterol: (json['cholesterol'] as num?)?.toDouble(),
      sodium: (json['sodium'] as num?)?.toDouble(),
      carbohydrates: (json['carbohydrates'] as num?)?.toDouble(),
      fiber: (json['fiber'] as num?)?.toDouble(),
      sugars: (json['sugars'] as num?)?.toDouble(),
      addedSugars: (json['addedSugars'] as num?)?.toDouble(),
      protein: (json['protein'] as num?)?.toDouble(),
      vitaminD: (json['vitaminD'] as num?)?.toDouble(),
      calcium: (json['calcium'] as num?)?.toDouble(),
      iron: (json['iron'] as num?)?.toDouble(),
      potassium: (json['potassium'] as num?)?.toDouble(),
      servingSize: json['servingSize'] as String?,
    );
  }
}
