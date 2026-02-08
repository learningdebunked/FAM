import 'package:flutter/material.dart';
import 'analysis_result.dart';

/// NOVA Classification (1-4) - Food Processing Level
enum NovaGroup {
  group1, // Unprocessed or minimally processed foods
  group2, // Processed culinary ingredients
  group3, // Processed foods
  group4, // Ultra-processed foods
  unknown,
}

extension NovaGroupExtension on NovaGroup {
  int get value {
    switch (this) {
      case NovaGroup.group1:
        return 1;
      case NovaGroup.group2:
        return 2;
      case NovaGroup.group3:
        return 3;
      case NovaGroup.group4:
        return 4;
      case NovaGroup.unknown:
        return 0;
    }
  }

  String get title {
    switch (this) {
      case NovaGroup.group1:
        return 'Unprocessed';
      case NovaGroup.group2:
        return 'Culinary Ingredients';
      case NovaGroup.group3:
        return 'Processed';
      case NovaGroup.group4:
        return 'Ultra-processed';
      case NovaGroup.unknown:
        return 'Unknown';
    }
  }

  String get description {
    switch (this) {
      case NovaGroup.group1:
        return 'Unprocessed or minimally processed foods';
      case NovaGroup.group2:
        return 'Processed culinary ingredients';
      case NovaGroup.group3:
        return 'Processed foods';
      case NovaGroup.group4:
        return 'Ultra-processed food and drink products';
      case NovaGroup.unknown:
        return 'Processing level unknown';
    }
  }

  Color get color {
    switch (this) {
      case NovaGroup.group1:
        return const Color(0xFF388E3C); // Green
      case NovaGroup.group2:
        return const Color(0xFFFBC02D); // Yellow
      case NovaGroup.group3:
        return const Color(0xFFF57C00); // Orange
      case NovaGroup.group4:
        return const Color(0xFFD32F2F); // Red
      case NovaGroup.unknown:
        return const Color(0xFF9E9E9E); // Grey
    }
  }
}

/// Nutri-Score (A-E) - Nutritional Quality
enum NutriScore {
  a,
  b,
  c,
  d,
  e,
  unknown,
}

extension NutriScoreExtension on NutriScore {
  String get letter {
    switch (this) {
      case NutriScore.a:
        return 'A';
      case NutriScore.b:
        return 'B';
      case NutriScore.c:
        return 'C';
      case NutriScore.d:
        return 'D';
      case NutriScore.e:
        return 'E';
      case NutriScore.unknown:
        return '?';
    }
  }

  String get description {
    switch (this) {
      case NutriScore.a:
        return 'Excellent nutritional quality';
      case NutriScore.b:
        return 'Good nutritional quality';
      case NutriScore.c:
        return 'Average nutritional quality';
      case NutriScore.d:
        return 'Poor nutritional quality';
      case NutriScore.e:
        return 'Bad nutritional quality';
      case NutriScore.unknown:
        return 'Nutritional quality unknown';
    }
  }

  Color get color {
    switch (this) {
      case NutriScore.a:
        return const Color(0xFF038141); // Dark green
      case NutriScore.b:
        return const Color(0xFF85BB2F); // Light green
      case NutriScore.c:
        return const Color(0xFFFECB02); // Yellow
      case NutriScore.d:
        return const Color(0xFFEE8100); // Orange
      case NutriScore.e:
        return const Color(0xFFE63E11); // Red
      case NutriScore.unknown:
        return const Color(0xFF9E9E9E); // Grey
    }
  }

  int get numericValue {
    switch (this) {
      case NutriScore.a:
        return 100;
      case NutriScore.b:
        return 80;
      case NutriScore.c:
        return 60;
      case NutriScore.d:
        return 40;
      case NutriScore.e:
        return 20;
      case NutriScore.unknown:
        return 50;
    }
  }
}

/// Ingredient concern category (like EWG)
enum IngredientConcern {
  none,
  low,
  moderate,
  high,
}

extension IngredientConcernExtension on IngredientConcern {
  String get label {
    switch (this) {
      case IngredientConcern.none:
        return 'No Concern';
      case IngredientConcern.low:
        return 'Low Concern';
      case IngredientConcern.moderate:
        return 'Moderate Concern';
      case IngredientConcern.high:
        return 'High Concern';
    }
  }

  Color get color {
    switch (this) {
      case IngredientConcern.none:
        return const Color(0xFF388E3C);
      case IngredientConcern.low:
        return const Color(0xFF8BC34A);
      case IngredientConcern.moderate:
        return const Color(0xFFFFC107);
      case IngredientConcern.high:
        return const Color(0xFFD32F2F);
    }
  }
}

/// Detailed ingredient with concern level
class DetailedIngredient {
  final String name;
  final String? canonicalName;
  final IngredientConcern concern;
  final String? category; // e.g., "artificial_sweetener", "preservative"
  final String? description;
  final List<String> affectedProfiles;
  final String? evidenceUrl;
  final bool isRelevantToUser;

  DetailedIngredient({
    required this.name,
    this.canonicalName,
    this.concern = IngredientConcern.none,
    this.category,
    this.description,
    this.affectedProfiles = const [],
    this.evidenceUrl,
    this.isRelevantToUser = false,
  });

  factory DetailedIngredient.fromJson(Map<String, dynamic> json) {
    return DetailedIngredient(
      name: json['name'] ?? json['ingredient'] ?? '',
      canonicalName: json['canonical_name'] ?? json['canonicalName'],
      concern: _parseConcern(json['risk_level'] ?? json['concern']),
      category: json['category'],
      description: json['description'] ?? json['concern'],
      affectedProfiles: List<String>.from(json['affected_profiles'] ?? []),
      evidenceUrl: json['evidence_url'],
      isRelevantToUser: json['is_relevant_to_user'] ?? false,
    );
  }

  static IngredientConcern _parseConcern(String? level) {
    switch (level?.toLowerCase()) {
      case 'high':
      case 'critical':
        return IngredientConcern.high;
      case 'medium':
      case 'moderate':
        return IngredientConcern.moderate;
      case 'low':
        return IngredientConcern.low;
      default:
        return IngredientConcern.none;
    }
  }
}

/// Nutrition level indicator
enum NutritionLevel {
  low,
  moderate,
  high,
}

extension NutritionLevelExtension on NutritionLevel {
  Color get color {
    switch (this) {
      case NutritionLevel.low:
        return const Color(0xFF388E3C); // Green - good for fat/sugar/salt
      case NutritionLevel.moderate:
        return const Color(0xFFFFC107); // Yellow
      case NutritionLevel.high:
        return const Color(0xFFD32F2F); // Red - bad for fat/sugar/salt
    }
  }

  String get label {
    switch (this) {
      case NutritionLevel.low:
        return 'Low';
      case NutritionLevel.moderate:
        return 'Moderate';
      case NutritionLevel.high:
        return 'High';
    }
  }
}

/// Nutrition fact with level
class NutritionFact {
  final String name;
  final double? value;
  final String unit;
  final NutritionLevel level;
  final double? dailyValuePercent;
  final bool isGood; // true for fiber, protein; false for fat, sugar, salt

  NutritionFact({
    required this.name,
    this.value,
    required this.unit,
    this.level = NutritionLevel.moderate,
    this.dailyValuePercent,
    this.isGood = false,
  });

  Color get displayColor {
    if (isGood) {
      // For good nutrients, high is green, low is red
      switch (level) {
        case NutritionLevel.high:
          return const Color(0xFF388E3C);
        case NutritionLevel.moderate:
          return const Color(0xFFFFC107);
        case NutritionLevel.low:
          return const Color(0xFFD32F2F);
      }
    } else {
      // For bad nutrients, low is green, high is red
      return level.color;
    }
  }
}

/// Complete FAM Analysis Result
class FAMAnalysis {
  final String productId;
  
  // Scores
  final double famScore; // 0-100, computed from paper formula
  final NutriScore nutriScore;
  final NovaGroup novaGroup;
  
  // Score components (from paper)
  final double nutriScoreComponent; // α·NutriScore
  final double riskFlagsComponent;  // β·RiskFlags
  final double fitToGoalsComponent; // γ·FitToGoals
  final double budgetPenaltyComponent; // δ·BudgetPenalty
  
  // Ingredients analysis
  final List<DetailedIngredient> ingredients;
  final int totalIngredients;
  final int flaggedIngredients;
  
  // Nutrition
  final List<NutritionFact> nutritionFacts;
  
  // Family-specific
  final Map<String, double> memberScores; // memberId -> score
  final List<String> recommendations;
  final List<String> warnings;
  
  // Alternatives
  final List<HealthyAlternative> alternatives;
  
  // Meta
  final DateTime analyzedAt;
  final String? analysisSource; // 'ai' or 'local_database'

  FAMAnalysis({
    required this.productId,
    required this.famScore,
    this.nutriScore = NutriScore.unknown,
    this.novaGroup = NovaGroup.unknown,
    this.nutriScoreComponent = 0,
    this.riskFlagsComponent = 0,
    this.fitToGoalsComponent = 0,
    this.budgetPenaltyComponent = 0,
    this.ingredients = const [],
    this.totalIngredients = 0,
    this.flaggedIngredients = 0,
    this.nutritionFacts = const [],
    this.memberScores = const {},
    this.recommendations = const [],
    this.warnings = const [],
    this.alternatives = const [],
    DateTime? analyzedAt,
    this.analysisSource,
  }) : analyzedAt = analyzedAt ?? DateTime.now();

  RiskLevel get overallRisk {
    if (famScore >= 80) return RiskLevel.safe;
    if (famScore >= 60) return RiskLevel.low;
    if (famScore >= 40) return RiskLevel.medium;
    if (famScore >= 20) return RiskLevel.high;
    return RiskLevel.critical;
  }

  String get famScoreLabel {
    if (famScore >= 80) return 'Excellent';
    if (famScore >= 60) return 'Good';
    if (famScore >= 40) return 'Fair';
    if (famScore >= 20) return 'Poor';
    return 'Avoid';
  }

  Color get famScoreColor {
    if (famScore >= 80) return const Color(0xFF388E3C);
    if (famScore >= 60) return const Color(0xFF8BC34A);
    if (famScore >= 40) return const Color(0xFFFFC107);
    if (famScore >= 20) return const Color(0xFFF57C00);
    return const Color(0xFFD32F2F);
  }

  factory FAMAnalysis.fromApiResponse(Map<String, dynamic> json, String productId) {
    // Parse risk flags into detailed ingredients
    final riskFlags = json['risk_flags'] as List<dynamic>? ?? [];
    final ingredients = riskFlags.map((f) => DetailedIngredient.fromJson(f as Map<String, dynamic>)).toList();
    
    // Parse recommendations
    final recommendations = List<String>.from(json['recommendations'] ?? []);
    
    // Separate warnings from recommendations
    final warnings = recommendations.where((r) => 
      r.toLowerCase().contains('avoid') || 
      r.toLowerCase().contains('high-risk') ||
      r.toLowerCase().contains('critical')
    ).toList();
    
    final tips = recommendations.where((r) => !warnings.contains(r)).toList();

    return FAMAnalysis(
      productId: productId,
      famScore: (json['overall_score'] as num?)?.toDouble() ?? 50,
      nutriScoreComponent: (json['nutri_score_component'] as num?)?.toDouble() ?? 0,
      riskFlagsComponent: (json['risk_flags_component'] as num?)?.toDouble() ?? 0,
      fitToGoalsComponent: (json['fit_to_goals_component'] as num?)?.toDouble() ?? 0,
      budgetPenaltyComponent: (json['budget_penalty_component'] as num?)?.toDouble() ?? 0,
      ingredients: ingredients,
      totalIngredients: json['total_ingredients'] as int? ?? ingredients.length,
      flaggedIngredients: json['flagged_count'] as int? ?? ingredients.where((i) => i.concern != IngredientConcern.none).length,
      recommendations: tips,
      warnings: warnings,
      analysisSource: json['analysis_source'] as String?,
    );
  }
}
