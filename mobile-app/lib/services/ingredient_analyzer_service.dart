import 'dart:convert';
import 'package:dio/dio.dart';

import '../models/family_member.dart';
import '../models/analysis_result.dart';

class IngredientAnalyzerService {
  static const String _openAiBaseUrl = 'https://api.openai.com/v1';
  
  final Dio _dio = Dio(BaseOptions(
    baseUrl: _openAiBaseUrl,
    connectTimeout: const Duration(seconds: 60),
    receiveTimeout: const Duration(seconds: 60),
  ));

  String? _apiKey;

  void initialize(String apiKey) {
    _apiKey = apiKey;
    _dio.options.headers['Authorization'] = 'Bearer $apiKey';
    _dio.options.headers['Content-Type'] = 'application/json';
  }

  Future<AnalysisResult> analyzeIngredients({
    required String productId,
    required List<String> ingredients,
    required List<FamilyMember> familyMembers,
  }) async {
    if (_apiKey == null) {
      throw AnalyzerException('API key not configured');
    }

    final prompt = _buildPrompt(ingredients, familyMembers);
    
    try {
      final response = await _dio.post('/chat/completions', data: {
        'model': 'gpt-4o',
        'messages': [
          {
            'role': 'system',
            'content': _systemPrompt,
          },
          {
            'role': 'user',
            'content': prompt,
          },
        ],
        'temperature': 0.3,
        'response_format': {'type': 'json_object'},
      });

      final content = response.data['choices'][0]['message']['content'];
      final analysisData = jsonDecode(content) as Map<String, dynamic>;
      
      return _parseAnalysisResult(productId, analysisData, familyMembers);
    } catch (e) {
      throw AnalyzerException('Failed to analyze ingredients: $e');
    }
  }

  static const String _systemPrompt = '''
You are a nutrition classification assistant for the Food-as-Medicine app. 
Analyze ingredient lists and identify health risks for different family member profiles.

For each ingredient, identify:
1. Canonical name (standardized name)
2. Risk level: safe, low, medium, high, critical
3. Which family member types are affected (adult, child, toddler, senior, pregnant)
4. Which health conditions are affected (cardiac, diabetic, hypertensive, etc.)
5. Brief explanation of the risk

Output JSON with this structure:
{
  "overallScore": 0-100 (higher is healthier),
  "overallRisk": "safe|low|medium|high|critical",
  "explanation": "Brief summary of the product",
  "ingredientFlags": [
    {
      "ingredientName": "original name",
      "canonicalName": "Standardized Name",
      "riskLevel": "safe|low|medium|high|critical",
      "explanation": "Why this is flagged",
      "affectedMemberTypes": ["child", "pregnant"],
      "affectedConditions": ["diabetic", "cardiac"],
      "evidenceLink": null
    }
  ],
  "memberRisks": [
    {
      "memberId": "id",
      "memberName": "name",
      "memberType": "child",
      "overallRisk": "medium",
      "summary": "Brief risk summary for this member"
    }
  ]
}

Key risk ingredients to flag:
- Aspartame, Sucralose (artificial sweeteners) - affects children, pregnant
- Red 40, Yellow 5, Blue 1 (artificial dyes) - affects children
- High Fructose Corn Syrup - affects diabetics, obesity
- Sodium Nitrate/Nitrite - affects pregnant, cardiac
- Trans fats, Partially Hydrogenated Oils - affects cardiac
- High sodium content - affects hypertensive, cardiac, seniors
- Caffeine - affects pregnant, children, hypertensive
- MSG - general sensitivity
- BHA/BHT preservatives - general concern

Be conservative - only flag ingredients with documented health concerns.
''';

  String _buildPrompt(List<String> ingredients, List<FamilyMember> familyMembers) {
    final memberDescriptions = familyMembers.map((m) {
      final conditions = m.conditions.map((c) => c.name).join(', ');
      final allergies = m.allergies.join(', ');
      return '- ${m.name} (${m.type.name}): conditions=[${conditions}], allergies=[${allergies}]';
    }).join('\n');

    return '''
Analyze these ingredients for health risks:

INGREDIENTS:
${ingredients.join(', ')}

FAMILY MEMBERS:
$memberDescriptions

Provide a detailed analysis in JSON format.
''';
  }

  AnalysisResult _parseAnalysisResult(
    String productId,
    Map<String, dynamic> data,
    List<FamilyMember> familyMembers,
  ) {
    final ingredientFlags = (data['ingredientFlags'] as List<dynamic>? ?? [])
        .map((f) => IngredientFlag(
              ingredientName: f['ingredientName'] ?? '',
              canonicalName: f['canonicalName'] ?? '',
              riskLevel: _parseRiskLevel(f['riskLevel']),
              explanation: f['explanation'] ?? '',
              affectedMemberTypes: (f['affectedMemberTypes'] as List<dynamic>? ?? [])
                  .map((t) => _parseMemberType(t))
                  .whereType<MemberType>()
                  .toList(),
              affectedConditions: (f['affectedConditions'] as List<dynamic>? ?? [])
                  .map((c) => _parseHealthCondition(c))
                  .whereType<HealthCondition>()
                  .toList(),
              evidenceLink: f['evidenceLink'],
            ))
        .toList();

    final memberRisks = (data['memberRisks'] as List<dynamic>? ?? [])
        .map((r) => MemberRisk(
              memberId: r['memberId'] ?? '',
              memberName: r['memberName'] ?? '',
              memberType: _parseMemberType(r['memberType']) ?? MemberType.adult,
              overallRisk: _parseRiskLevel(r['overallRisk']),
              flags: [],
              summary: r['summary'] ?? '',
            ))
        .toList();

    return AnalysisResult(
      productId: productId,
      overallScore: (data['overallScore'] as num?)?.toDouble() ?? 50.0,
      overallRisk: _parseRiskLevel(data['overallRisk']),
      ingredientFlags: ingredientFlags,
      memberRisks: memberRisks,
      explanation: data['explanation'] ?? 'Analysis complete.',
    );
  }

  RiskLevel _parseRiskLevel(String? level) {
    switch (level?.toLowerCase()) {
      case 'safe':
        return RiskLevel.safe;
      case 'low':
        return RiskLevel.low;
      case 'medium':
        return RiskLevel.medium;
      case 'high':
        return RiskLevel.high;
      case 'critical':
        return RiskLevel.critical;
      default:
        return RiskLevel.low;
    }
  }

  MemberType? _parseMemberType(String? type) {
    switch (type?.toLowerCase()) {
      case 'adult':
        return MemberType.adult;
      case 'child':
        return MemberType.child;
      case 'toddler':
        return MemberType.toddler;
      case 'senior':
        return MemberType.senior;
      case 'pregnant':
        return MemberType.pregnant;
      default:
        return null;
    }
  }

  HealthCondition? _parseHealthCondition(String? condition) {
    switch (condition?.toLowerCase()) {
      case 'cardiac':
        return HealthCondition.cardiac;
      case 'diabetic':
        return HealthCondition.diabetic;
      case 'hypertensive':
        return HealthCondition.hypertensive;
      case 'celiac':
        return HealthCondition.celiac;
      case 'lactoseintolerant':
        return HealthCondition.lactoseIntolerant;
      case 'glutensensitive':
        return HealthCondition.glutenSensitive;
      case 'kidneydisease':
        return HealthCondition.kidneyDisease;
      case 'liverdisease':
        return HealthCondition.liverDisease;
      case 'thyroid':
        return HealthCondition.thyroid;
      case 'gout':
        return HealthCondition.gout;
      case 'obesity':
        return HealthCondition.obesity;
      case 'anemia':
        return HealthCondition.anemia;
      case 'osteoporosis':
        return HealthCondition.osteoporosis;
      default:
        return null;
    }
  }
}

class AnalyzerException implements Exception {
  final String message;
  AnalyzerException(this.message);
  
  @override
  String toString() => message;
}
