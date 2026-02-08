import 'family_member.dart';

enum RiskLevel {
  safe,
  low,
  medium,
  high,
  critical,
}

extension RiskLevelExtension on RiskLevel {
  String get displayName {
    switch (this) {
      case RiskLevel.safe:
        return 'Safe';
      case RiskLevel.low:
        return 'Low Risk';
      case RiskLevel.medium:
        return 'Medium Risk';
      case RiskLevel.high:
        return 'High Risk';
      case RiskLevel.critical:
        return 'Critical';
    }
  }

  int get colorValue {
    switch (this) {
      case RiskLevel.safe:
        return 0xFF388E3C;
      case RiskLevel.low:
        return 0xFFFBC02D;
      case RiskLevel.medium:
        return 0xFFF57C00;
      case RiskLevel.high:
        return 0xFFD32F2F;
      case RiskLevel.critical:
        return 0xFF880E4F;
    }
  }
}

class IngredientFlag {
  final String ingredientName;
  final String canonicalName;
  final RiskLevel riskLevel;
  final String explanation;
  final List<MemberType> affectedMemberTypes;
  final List<HealthCondition> affectedConditions;
  final String? evidenceLink;

  IngredientFlag({
    required this.ingredientName,
    required this.canonicalName,
    required this.riskLevel,
    required this.explanation,
    this.affectedMemberTypes = const [],
    this.affectedConditions = const [],
    this.evidenceLink,
  });

  Map<String, dynamic> toJson() {
    return {
      'ingredientName': ingredientName,
      'canonicalName': canonicalName,
      'riskLevel': riskLevel.index,
      'explanation': explanation,
      'affectedMemberTypes': affectedMemberTypes.map((t) => t.index).toList(),
      'affectedConditions': affectedConditions.map((c) => c.index).toList(),
      'evidenceLink': evidenceLink,
    };
  }

  factory IngredientFlag.fromJson(Map<String, dynamic> json) {
    return IngredientFlag(
      ingredientName: json['ingredientName'] as String,
      canonicalName: json['canonicalName'] as String,
      riskLevel: RiskLevel.values[json['riskLevel'] as int],
      explanation: json['explanation'] as String,
      affectedMemberTypes: (json['affectedMemberTypes'] as List<dynamic>?)
              ?.map((t) => MemberType.values[t as int])
              .toList() ??
          [],
      affectedConditions: (json['affectedConditions'] as List<dynamic>?)
              ?.map((c) => HealthCondition.values[c as int])
              .toList() ??
          [],
      evidenceLink: json['evidenceLink'] as String?,
    );
  }
}

class MemberRisk {
  final String memberId;
  final String memberName;
  final MemberType memberType;
  final RiskLevel overallRisk;
  final List<IngredientFlag> flags;
  final String summary;

  MemberRisk({
    required this.memberId,
    required this.memberName,
    required this.memberType,
    required this.overallRisk,
    required this.flags,
    required this.summary,
  });

  Map<String, dynamic> toJson() {
    return {
      'memberId': memberId,
      'memberName': memberName,
      'memberType': memberType.index,
      'overallRisk': overallRisk.index,
      'flags': flags.map((f) => f.toJson()).toList(),
      'summary': summary,
    };
  }

  factory MemberRisk.fromJson(Map<String, dynamic> json) {
    return MemberRisk(
      memberId: json['memberId'] as String,
      memberName: json['memberName'] as String,
      memberType: MemberType.values[json['memberType'] as int],
      overallRisk: RiskLevel.values[json['overallRisk'] as int],
      flags: (json['flags'] as List<dynamic>)
          .map((f) => IngredientFlag.fromJson(f as Map<String, dynamic>))
          .toList(),
      summary: json['summary'] as String,
    );
  }
}

class AnalysisResult {
  final String productId;
  final double overallScore;
  final RiskLevel overallRisk;
  final List<IngredientFlag> ingredientFlags;
  final List<MemberRisk> memberRisks;
  final String explanation;
  final DateTime analyzedAt;

  AnalysisResult({
    required this.productId,
    required this.overallScore,
    required this.overallRisk,
    required this.ingredientFlags,
    required this.memberRisks,
    required this.explanation,
    DateTime? analyzedAt,
  }) : analyzedAt = analyzedAt ?? DateTime.now();

  Map<String, dynamic> toJson() {
    return {
      'productId': productId,
      'overallScore': overallScore,
      'overallRisk': overallRisk.index,
      'ingredientFlags': ingredientFlags.map((f) => f.toJson()).toList(),
      'memberRisks': memberRisks.map((r) => r.toJson()).toList(),
      'explanation': explanation,
      'analyzedAt': analyzedAt.toIso8601String(),
    };
  }

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      productId: json['productId'] as String,
      overallScore: (json['overallScore'] as num).toDouble(),
      overallRisk: RiskLevel.values[json['overallRisk'] as int],
      ingredientFlags: (json['ingredientFlags'] as List<dynamic>)
          .map((f) => IngredientFlag.fromJson(f as Map<String, dynamic>))
          .toList(),
      memberRisks: (json['memberRisks'] as List<dynamic>)
          .map((r) => MemberRisk.fromJson(r as Map<String, dynamic>))
          .toList(),
      explanation: json['explanation'] as String,
      analyzedAt: DateTime.parse(json['analyzedAt'] as String),
    );
  }
}

class HealthyAlternative {
  final String productId;
  final String name;
  final String? brand;
  final String? imageUrl;
  final double score;
  final String reason;
  final List<String> benefits;
  final double? priceDifference;

  HealthyAlternative({
    required this.productId,
    required this.name,
    this.brand,
    this.imageUrl,
    required this.score,
    required this.reason,
    this.benefits = const [],
    this.priceDifference,
  });

  Map<String, dynamic> toJson() {
    return {
      'productId': productId,
      'name': name,
      'brand': brand,
      'imageUrl': imageUrl,
      'score': score,
      'reason': reason,
      'benefits': benefits,
      'priceDifference': priceDifference,
    };
  }

  factory HealthyAlternative.fromJson(Map<String, dynamic> json) {
    return HealthyAlternative(
      productId: json['productId'] as String,
      name: json['name'] as String,
      brand: json['brand'] as String?,
      imageUrl: json['imageUrl'] as String?,
      score: (json['score'] as num).toDouble(),
      reason: json['reason'] as String,
      benefits: List<String>.from(json['benefits'] as List? ?? []),
      priceDifference: (json['priceDifference'] as num?)?.toDouble(),
    );
  }
}
