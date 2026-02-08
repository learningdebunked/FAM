import 'dart:io';
import 'package:dio/dio.dart';
import '../config/app_config.dart';
import '../models/product.dart';
import '../models/analysis_result.dart';
import '../models/family_member.dart';
import '../models/feedback.dart';

class BackendService {
  static final BackendService _instance = BackendService._internal();
  factory BackendService() => _instance;
  BackendService._internal();

  late final Dio _dio;
  bool _initialized = false;

  void initialize() {
    if (_initialized) return;
    
    final baseUrl = Platform.isAndroid 
        ? AppConfig.backendBaseUrl 
        : AppConfig.backendBaseUrlIOS;
    
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
      headers: {
        'Content-Type': 'application/json',
      },
    ));

    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (obj) => print('[Backend] $obj'),
    ));
    
    _initialized = true;
  }

  Future<List<Product>> getProducts({
    String category = 'beverages,snacks,cereals',
    int pageSize = 50,
  }) async {
    try {
      final response = await _dio.get('/api/products', queryParameters: {
        'category': category,
        'page_size': pageSize,
        'use_ai': false,
      });

      if (response.statusCode == 200) {
        final products = response.data['products'] as List<dynamic>? ?? [];
        return products.map((p) => Product(
          id: p['name']?.hashCode.toString() ?? '',
          barcode: '',
          name: p['name'] ?? 'Unknown',
          ingredients: List<String>.from(p['ingredients'] ?? []),
          imageUrl: p['image_url'],
        )).toList();
      }
      return [];
    } catch (e) {
      throw BackendException('Failed to fetch products: $e');
    }
  }

  Future<AnalysisResult> analyzeIngredients({
    required String productId,
    required List<String> ingredients,
    required List<FamilyMember> familyMembers,
  }) async {
    try {
      // Convert family members to health profiles for the backend
      final healthProfiles = _buildHealthProfiles(familyMembers);
      
      // Use the database-backed analysis endpoint for better performance
      final response = await _dio.post('/api/db/analyze', data: {
        'ingredients': ingredients,
        'health_profiles': healthProfiles,
        'use_ai': false,  // Use local database analysis (faster, no API costs)
      });

      if (response.statusCode == 200) {
        return _parseAnalysisResponse(productId, response.data, familyMembers);
      }
      
      throw BackendException('Analysis failed with status: ${response.statusCode}');
    } catch (e) {
      if (e is BackendException) rethrow;
      throw BackendException('Failed to analyze ingredients: $e');
    }
  }
  
  Future<Map<String, dynamic>?> searchProductsInDatabase(String query, {String? retailer}) async {
    try {
      final response = await _dio.get('/api/db/search', queryParameters: {
        'query': query,
        if (retailer != null) 'retailer': retailer,
        'limit': 20,
      });
      
      if (response.statusCode == 200) {
        return response.data;
      }
      return null;
    } catch (e) {
      print('Database search error: $e');
      return null;
    }
  }
  
  Future<Map<String, dynamic>?> getProductFromDatabase(String barcode) async {
    try {
      final response = await _dio.get('/api/db/product/$barcode');
      
      if (response.statusCode == 200) {
        return response.data;
      }
      return null;
    } catch (e) {
      print('Database product lookup error: $e');
      return null;
    }
  }
  
  /// Unified tiered lookup - the optimal way to get product + analysis
  /// 
  /// Flow:
  /// 1. Check local database first (fastest, <50ms)
  /// 2. Fall back to OpenFoodFacts if not found (~200ms)
  /// 3. Analyze using local risk database (fast)
  /// 4. Fall back to AI analysis only if needed (~2-5s)
  /// 
  /// Returns complete product info with FAM analysis in one call.
  Future<TieredLookupResult> tieredLookup({
    String? barcode,
    List<String>? ingredients,
    required List<FamilyMember> familyMembers,
    String? productName,
    bool useAiFallback = true,
  }) async {
    try {
      final healthProfiles = _buildHealthProfiles(familyMembers);
      
      final response = await _dio.post('/api/lookup', data: {
        'barcode': barcode,
        'ingredients': ingredients,
        'health_profiles': healthProfiles,
        'product_name': productName,
        'use_ai_fallback': useAiFallback,
      });
      
      if (response.statusCode == 200) {
        return TieredLookupResult.fromJson(response.data, familyMembers);
      }
      
      throw BackendException('Lookup failed with status: ${response.statusCode}');
    } catch (e) {
      if (e is BackendException) rethrow;
      throw BackendException('Tiered lookup failed: $e');
    }
  }
  
  Future<Map<String, dynamic>> getDatabaseStats() async {
    try {
      final response = await _dio.get('/api/db/stats');
      
      if (response.statusCode == 200) {
        return response.data;
      }
      return {};
    } catch (e) {
      print('Database stats error: $e');
      return {};
    }
  }

  Future<List<HealthyAlternative>> getAlternatives({
    required String productId,
    required List<String> ingredients,
    required List<FamilyMember> familyMembers,
    String? category,
  }) async {
    try {
      final healthProfiles = _buildHealthProfiles(familyMembers);
      
      // Use database-backed alternatives endpoint
      final response = await _dio.post('/api/db/alternatives', data: {
        'product_id': productId,
        'ingredients': ingredients,
        'health_profiles': healthProfiles,
        'category': category,
      });

      if (response.statusCode == 200) {
        final alternatives = response.data['alternatives'] as List<dynamic>? ?? [];
        return alternatives.map((a) => HealthyAlternative(
          productId: a['product_id'] ?? '',
          name: a['name'] ?? 'Unknown',
          brand: a['brand'],
          imageUrl: a['image_url'],
          score: (a['score'] as num?)?.toDouble() ?? 0.0,
          reason: a['reason'] ?? '',
          benefits: List<String>.from(a['benefits'] ?? []),
          priceDifference: (a['price_difference'] as num?)?.toDouble(),
        )).toList();
      }
      return [];
    } catch (e) {
      // Return empty list if endpoint not available yet
      print('Alternatives endpoint error: $e');
      return [];
    }
  }

  Future<void> submitFeedback({
    required String productId,
    required FeedbackType type,
    String? comment,
    List<String>? issues,
  }) async {
    try {
      await _dio.post('/api/feedback', data: {
        'product_id': productId,
        'feedback_type': type == FeedbackType.thumbsUp ? 'positive' : 'negative',
        'comment': comment,
        'issues': issues,
        'timestamp': DateTime.now().toIso8601String(),
      });
    } catch (e) {
      // Log but don't throw - feedback is non-critical
      print('Failed to submit feedback: $e');
    }
  }

  List<String> _buildHealthProfiles(List<FamilyMember> members) {
    final profiles = <String>{};
    
    // If no family members, use default adult profile
    if (members.isEmpty) {
      return ['adult'];
    }
    
    for (final member in members) {
      // Add member type
      profiles.add(member.type.name);
      
      // Add health conditions
      for (final condition in member.conditions) {
        profiles.add(condition.name);
      }
      
      // Add allergies
      profiles.addAll(member.allergies);
    }
    
    return profiles.toList();
  }

  AnalysisResult _parseAnalysisResponse(
    String productId,
    Map<String, dynamic> data,
    List<FamilyMember> familyMembers,
  ) {
    final riskFlags = data['risk_flags'] as List<dynamic>? ?? [];
    final overallScore = 100 - (data['overall_risk_score'] as num? ?? 50);
    final recommendations = data['recommendations'] as List<dynamic>? ?? [];
    
    // Parse ingredient flags from risk_flags
    final ingredientFlags = riskFlags.map((flag) {
      final riskLevel = _parseRiskLevel(flag['risk_level'] as String?);
      final affectedProfiles = List<String>.from(flag['affected_profiles'] ?? []);
      
      return IngredientFlag(
        ingredientName: flag['ingredient'] ?? '',
        canonicalName: flag['ingredient'] ?? '',
        riskLevel: riskLevel,
        explanation: flag['concern'] ?? '',
        affectedMemberTypes: _parseAffectedMemberTypes(affectedProfiles),
        affectedConditions: _parseAffectedConditions(affectedProfiles),
      );
    }).toList();

    // Calculate member-specific risks
    final memberRisks = familyMembers.map((member) {
      final relevantFlags = ingredientFlags.where((flag) {
        return flag.affectedMemberTypes.contains(member.type) ||
               flag.affectedConditions.any((c) => member.conditions.contains(c));
      }).toList();
      
      RiskLevel memberRisk = RiskLevel.safe;
      if (relevantFlags.isNotEmpty) {
        final maxRisk = relevantFlags
            .map((f) => f.riskLevel.index)
            .reduce((a, b) => a > b ? a : b);
        memberRisk = RiskLevel.values[maxRisk];
      }
      
      return MemberRisk(
        memberId: member.id,
        memberName: member.name,
        memberType: member.type,
        overallRisk: memberRisk,
        flags: relevantFlags,
        summary: _generateMemberSummary(member, relevantFlags),
      );
    }).toList();

    return AnalysisResult(
      productId: productId,
      overallScore: overallScore.toDouble().clamp(0, 100),
      overallRisk: _scoreToRiskLevel(overallScore.toDouble()),
      ingredientFlags: ingredientFlags,
      memberRisks: memberRisks,
      explanation: recommendations.isNotEmpty 
          ? recommendations.join(' ') 
          : 'Analysis complete. ${ingredientFlags.length} ingredients flagged.',
    );
  }

  RiskLevel _parseRiskLevel(String? level) {
    switch (level?.toLowerCase()) {
      case 'low':
        return RiskLevel.low;
      case 'medium':
        return RiskLevel.medium;
      case 'high':
        return RiskLevel.high;
      default:
        return RiskLevel.low;
    }
  }

  RiskLevel _scoreToRiskLevel(double score) {
    if (score >= 80) return RiskLevel.safe;
    if (score >= 60) return RiskLevel.low;
    if (score >= 40) return RiskLevel.medium;
    if (score >= 20) return RiskLevel.high;
    return RiskLevel.critical;
  }

  List<MemberType> _parseAffectedMemberTypes(List<String> profiles) {
    final types = <MemberType>[];
    for (final profile in profiles) {
      final lower = profile.toLowerCase();
      if (lower.contains('child')) types.add(MemberType.child);
      if (lower.contains('toddler')) types.add(MemberType.toddler);
      if (lower.contains('pregnant')) types.add(MemberType.pregnant);
      if (lower.contains('senior') || lower.contains('elderly')) types.add(MemberType.senior);
      if (lower.contains('adult')) types.add(MemberType.adult);
    }
    return types;
  }

  List<HealthCondition> _parseAffectedConditions(List<String> profiles) {
    final conditions = <HealthCondition>[];
    for (final profile in profiles) {
      final lower = profile.toLowerCase();
      if (lower.contains('diabetic') || lower.contains('diabetes')) {
        conditions.add(HealthCondition.diabetic);
      }
      if (lower.contains('hypertensive') || lower.contains('blood pressure')) {
        conditions.add(HealthCondition.hypertensive);
      }
      if (lower.contains('cardiac') || lower.contains('heart')) {
        conditions.add(HealthCondition.cardiac);
      }
      if (lower.contains('celiac')) conditions.add(HealthCondition.celiac);
      if (lower.contains('lactose')) conditions.add(HealthCondition.lactoseIntolerant);
      if (lower.contains('gluten')) conditions.add(HealthCondition.glutenSensitive);
      if (lower.contains('kidney')) conditions.add(HealthCondition.kidneyDisease);
      if (lower.contains('liver')) conditions.add(HealthCondition.liverDisease);
      if (lower.contains('thyroid')) conditions.add(HealthCondition.thyroid);
      if (lower.contains('gout')) conditions.add(HealthCondition.gout);
      if (lower.contains('obesity') || lower.contains('obese')) {
        conditions.add(HealthCondition.obesity);
      }
    }
    return conditions;
  }

  String _generateMemberSummary(FamilyMember member, List<IngredientFlag> flags) {
    if (flags.isEmpty) {
      return 'No specific concerns for ${member.name}.';
    }
    
    final highRisk = flags.where((f) => f.riskLevel == RiskLevel.high || f.riskLevel == RiskLevel.critical);
    if (highRisk.isNotEmpty) {
      return '${highRisk.length} high-risk ingredient(s) detected for ${member.name}. Consider alternatives.';
    }
    
    return '${flags.length} ingredient(s) may require attention for ${member.name}.';
  }
}

class BackendException implements Exception {
  final String message;
  BackendException(this.message);
  
  @override
  String toString() => message;
}

/// Result from the unified tiered lookup endpoint
class TieredLookupResult {
  final Product? product;
  final AnalysisResult? analysis;
  final List<HealthyAlternative> alternatives;
  final String source; // 'local_database', 'openfoodfacts', 'manual_entry'
  final bool cached;
  final int lookupTimeMs;
  
  TieredLookupResult({
    this.product,
    this.analysis,
    this.alternatives = const [],
    required this.source,
    this.cached = false,
    this.lookupTimeMs = 0,
  });
  
  factory TieredLookupResult.fromJson(
    Map<String, dynamic> json,
    List<FamilyMember> familyMembers,
  ) {
    // Parse product
    Product? product;
    final productData = json['product'] as Map<String, dynamic>?;
    if (productData != null) {
      product = Product(
        id: productData['id']?.toString() ?? '',
        barcode: productData['barcode'] ?? '',
        name: productData['name'] ?? 'Unknown Product',
        brand: productData['brand'],
        ingredients: List<String>.from(productData['ingredients'] ?? []),
        imageUrl: productData['image_url'],
      );
    }
    
    // Parse analysis
    AnalysisResult? analysis;
    final analysisData = json['analysis'] as Map<String, dynamic>?;
    if (analysisData != null && product != null) {
      analysis = _parseAnalysisFromLookup(product.id, analysisData, familyMembers);
    }
    
    // Parse alternatives
    final alternativesData = json['alternatives'] as List<dynamic>? ?? [];
    final alternatives = alternativesData.map((a) => HealthyAlternative(
      productId: a['product_id']?.toString() ?? '',
      name: a['name'] ?? 'Unknown',
      brand: a['brand'],
      imageUrl: a['image_url'],
      score: (a['score'] as num?)?.toDouble() ?? 0.0,
      reason: a['reason'] ?? '',
      benefits: List<String>.from(a['benefits'] ?? []),
      priceDifference: (a['price_difference'] as num?)?.toDouble(),
    )).toList();
    
    return TieredLookupResult(
      product: product,
      analysis: analysis,
      alternatives: alternatives,
      source: json['source'] ?? 'unknown',
      cached: json['cached'] ?? false,
      lookupTimeMs: json['lookup_time_ms'] ?? 0,
    );
  }
  
  static AnalysisResult _parseAnalysisFromLookup(
    String productId,
    Map<String, dynamic> data,
    List<FamilyMember> familyMembers,
  ) {
    final riskFlags = data['risk_flags'] as List<dynamic>? ?? [];
    final overallScore = (data['overall_score'] as num?)?.toDouble() ?? 
                         (data['fam_score'] as num?)?.toDouble() ?? 50.0;
    final recommendations = data['recommendations'] as List<dynamic>? ?? [];
    
    // Parse ingredient flags
    final ingredientFlags = riskFlags.map((flag) {
      final riskLevelStr = flag['risk_level'] as String? ?? 'low';
      RiskLevel riskLevel;
      switch (riskLevelStr.toLowerCase()) {
        case 'high':
          riskLevel = RiskLevel.high;
          break;
        case 'medium':
          riskLevel = RiskLevel.medium;
          break;
        case 'critical':
          riskLevel = RiskLevel.critical;
          break;
        default:
          riskLevel = RiskLevel.low;
      }
      
      final affectedProfiles = List<String>.from(flag['affected_profiles'] ?? []);
      
      return IngredientFlag(
        ingredientName: flag['ingredient'] ?? '',
        canonicalName: flag['canonical_name'] ?? flag['ingredient'] ?? '',
        riskLevel: riskLevel,
        explanation: flag['description'] ?? flag['concern'] ?? '',
        affectedMemberTypes: _parseAffectedTypes(affectedProfiles),
        affectedConditions: _parseAffectedConds(affectedProfiles),
        evidenceLink: flag['evidence_url'],
      );
    }).toList();
    
    // Calculate member-specific risks
    final memberRisks = familyMembers.map((member) {
      final relevantFlags = ingredientFlags.where((flag) {
        return flag.affectedMemberTypes.contains(member.type) ||
               flag.affectedConditions.any((c) => member.conditions.contains(c));
      }).toList();
      
      RiskLevel memberRisk = RiskLevel.safe;
      if (relevantFlags.isNotEmpty) {
        final maxRisk = relevantFlags
            .map((f) => f.riskLevel.index)
            .reduce((a, b) => a > b ? a : b);
        memberRisk = RiskLevel.values[maxRisk];
      }
      
      return MemberRisk(
        memberId: member.id,
        memberName: member.name,
        memberType: member.type,
        overallRisk: memberRisk,
        flags: relevantFlags,
        summary: relevantFlags.isEmpty 
            ? 'No specific concerns for ${member.name}.'
            : '${relevantFlags.length} ingredient(s) may require attention for ${member.name}.',
      );
    }).toList();
    
    // Determine overall risk level
    RiskLevel overallRisk;
    if (overallScore >= 80) {
      overallRisk = RiskLevel.safe;
    } else if (overallScore >= 60) {
      overallRisk = RiskLevel.low;
    } else if (overallScore >= 40) {
      overallRisk = RiskLevel.medium;
    } else if (overallScore >= 20) {
      overallRisk = RiskLevel.high;
    } else {
      overallRisk = RiskLevel.critical;
    }
    
    return AnalysisResult(
      productId: productId,
      overallScore: overallScore,
      overallRisk: overallRisk,
      ingredientFlags: ingredientFlags,
      memberRisks: memberRisks,
      explanation: recommendations.isNotEmpty 
          ? recommendations.join(' ') 
          : 'Analysis complete. ${ingredientFlags.length} ingredients flagged.',
    );
  }
  
  static List<MemberType> _parseAffectedTypes(List<String> profiles) {
    final types = <MemberType>[];
    for (final profile in profiles) {
      final lower = profile.toLowerCase();
      if (lower.contains('child')) types.add(MemberType.child);
      if (lower.contains('toddler')) types.add(MemberType.toddler);
      if (lower.contains('pregnant')) types.add(MemberType.pregnant);
      if (lower.contains('senior') || lower.contains('elderly')) types.add(MemberType.senior);
      if (lower.contains('adult')) types.add(MemberType.adult);
    }
    return types;
  }
  
  static List<HealthCondition> _parseAffectedConds(List<String> profiles) {
    final conditions = <HealthCondition>[];
    for (final profile in profiles) {
      final lower = profile.toLowerCase();
      if (lower.contains('diabetic') || lower.contains('diabetes')) {
        conditions.add(HealthCondition.diabetic);
      }
      if (lower.contains('hypertensive') || lower.contains('blood pressure')) {
        conditions.add(HealthCondition.hypertensive);
      }
      if (lower.contains('cardiac') || lower.contains('heart')) {
        conditions.add(HealthCondition.cardiac);
      }
      if (lower.contains('celiac')) conditions.add(HealthCondition.celiac);
      if (lower.contains('lactose')) conditions.add(HealthCondition.lactoseIntolerant);
      if (lower.contains('gluten')) conditions.add(HealthCondition.glutenSensitive);
      if (lower.contains('kidney')) conditions.add(HealthCondition.kidneyDisease);
    }
    return conditions;
  }
}
