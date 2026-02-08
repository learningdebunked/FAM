import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../config/theme.dart';
import '../../models/analysis_result.dart';
import '../../models/product_analysis.dart';
import '../../models/family_member.dart';
import '../../providers/family_provider.dart';
import '../../providers/product_provider.dart';

/// Comprehensive FAM Analysis Screen
/// Inspired by Open Food Facts and EWG Food Scores
class FAMAnalysisScreen extends StatefulWidget {
  final String productId;

  const FAMAnalysisScreen({super.key, required this.productId});

  @override
  State<FAMAnalysisScreen> createState() => _FAMAnalysisScreenState();
}

class _FAMAnalysisScreenState extends State<FAMAnalysisScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  FAMAnalysis? _famAnalysis;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadAnalysis();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadAnalysis() async {
    final productProvider = context.read<ProductProvider>();
    final familyProvider = context.read<FamilyProvider>();

    productProvider.setFamilyMembers(familyProvider.members);
    await productProvider.analyzeProduct();

    // Convert to FAM Analysis
    if (productProvider.currentAnalysis != null && mounted) {
      setState(() {
        _famAnalysis = _convertToFAMAnalysis(
          productProvider.currentAnalysis!,
          productProvider.currentProduct,
        );
      });
    }
  }

  FAMAnalysis _convertToFAMAnalysis(AnalysisResult analysis, dynamic product) {
    // Convert ingredient flags to detailed ingredients
    final ingredients = analysis.ingredientFlags.map((flag) {
      return DetailedIngredient(
        name: flag.ingredientName,
        canonicalName: flag.canonicalName,
        concern: _riskToConcern(flag.riskLevel),
        description: flag.explanation,
        affectedProfiles: [
          ...flag.affectedMemberTypes.map((t) => t.name),
          ...flag.affectedConditions.map((c) => c.name),
        ],
        evidenceUrl: flag.evidenceLink,
        isRelevantToUser: true,
      );
    }).toList();

    // Calculate NOVA group based on flagged ingredients
    NovaGroup novaGroup = NovaGroup.group1;
    if (ingredients.any((i) => i.concern == IngredientConcern.high)) {
      novaGroup = NovaGroup.group4;
    } else if (ingredients.any((i) => i.concern == IngredientConcern.moderate)) {
      novaGroup = NovaGroup.group3;
    } else if (ingredients.isNotEmpty) {
      novaGroup = NovaGroup.group2;
    }

    // Calculate Nutri-Score based on overall score
    NutriScore nutriScore = NutriScore.c;
    if (analysis.overallScore >= 80) {
      nutriScore = NutriScore.a;
    } else if (analysis.overallScore >= 60) {
      nutriScore = NutriScore.b;
    } else if (analysis.overallScore >= 40) {
      nutriScore = NutriScore.c;
    } else if (analysis.overallScore >= 20) {
      nutriScore = NutriScore.d;
    } else {
      nutriScore = NutriScore.e;
    }

    // Build nutrition facts from product
    List<NutritionFact> nutritionFacts = [];
    if (product?.nutrition != null) {
      final n = product.nutrition;
      nutritionFacts = [
        if (n.calories != null)
          NutritionFact(
            name: 'Energy',
            value: n.calories,
            unit: 'kcal',
            level: _getCalorieLevel(n.calories),
          ),
        if (n.fat != null)
          NutritionFact(
            name: 'Fat',
            value: n.fat,
            unit: 'g',
            level: _getFatLevel(n.fat),
          ),
        if (n.saturatedFat != null)
          NutritionFact(
            name: 'Saturated Fat',
            value: n.saturatedFat,
            unit: 'g',
            level: _getSaturatedFatLevel(n.saturatedFat),
          ),
        if (n.sugars != null)
          NutritionFact(
            name: 'Sugars',
            value: n.sugars,
            unit: 'g',
            level: _getSugarLevel(n.sugars),
          ),
        if (n.sodium != null)
          NutritionFact(
            name: 'Salt',
            value: (n.sodium ?? 0) * 2.5, // Convert sodium to salt
            unit: 'g',
            level: _getSaltLevel((n.sodium ?? 0) * 2.5),
          ),
        if (n.fiber != null)
          NutritionFact(
            name: 'Fiber',
            value: n.fiber,
            unit: 'g',
            level: _getFiberLevel(n.fiber),
            isGood: true,
          ),
        if (n.protein != null)
          NutritionFact(
            name: 'Protein',
            value: n.protein,
            unit: 'g',
            level: _getProteinLevel(n.protein),
            isGood: true,
          ),
      ];
    }

    // Generate recommendations
    List<String> recommendations = [];
    List<String> warnings = [];

    for (final ing in ingredients) {
      if (ing.concern == IngredientConcern.high) {
        warnings.add(
            'Contains ${ing.canonicalName ?? ing.name} - ${ing.description ?? "may pose health concerns"}');
      }
    }

    if (novaGroup == NovaGroup.group4) {
      recommendations.add(
          'This is an ultra-processed food. Consider whole food alternatives.');
    }
    if (nutriScore == NutriScore.d || nutriScore == NutriScore.e) {
      recommendations.add(
          'Low nutritional quality. Look for products with better Nutri-Score.');
    }

    return FAMAnalysis(
      productId: analysis.productId,
      famScore: analysis.overallScore,
      nutriScore: nutriScore,
      novaGroup: novaGroup,
      ingredients: ingredients,
      totalIngredients: product?.ingredients?.length ?? 0,
      flaggedIngredients: ingredients.length,
      nutritionFacts: nutritionFacts,
      recommendations: recommendations,
      warnings: warnings,
    );
  }

  IngredientConcern _riskToConcern(RiskLevel risk) {
    switch (risk) {
      case RiskLevel.safe:
        return IngredientConcern.none;
      case RiskLevel.low:
        return IngredientConcern.low;
      case RiskLevel.medium:
        return IngredientConcern.moderate;
      case RiskLevel.high:
      case RiskLevel.critical:
        return IngredientConcern.high;
    }
  }

  NutritionLevel _getCalorieLevel(double? value) {
    if (value == null) return NutritionLevel.moderate;
    if (value < 100) return NutritionLevel.low;
    if (value < 250) return NutritionLevel.moderate;
    return NutritionLevel.high;
  }

  NutritionLevel _getFatLevel(double? value) {
    if (value == null) return NutritionLevel.moderate;
    if (value < 3) return NutritionLevel.low;
    if (value < 17.5) return NutritionLevel.moderate;
    return NutritionLevel.high;
  }

  NutritionLevel _getSaturatedFatLevel(double? value) {
    if (value == null) return NutritionLevel.moderate;
    if (value < 1.5) return NutritionLevel.low;
    if (value < 5) return NutritionLevel.moderate;
    return NutritionLevel.high;
  }

  NutritionLevel _getSugarLevel(double? value) {
    if (value == null) return NutritionLevel.moderate;
    if (value < 5) return NutritionLevel.low;
    if (value < 22.5) return NutritionLevel.moderate;
    return NutritionLevel.high;
  }

  NutritionLevel _getSaltLevel(double? value) {
    if (value == null) return NutritionLevel.moderate;
    if (value < 0.3) return NutritionLevel.low;
    if (value < 1.5) return NutritionLevel.moderate;
    return NutritionLevel.high;
  }

  NutritionLevel _getFiberLevel(double? value) {
    if (value == null) return NutritionLevel.moderate;
    if (value < 1.5) return NutritionLevel.low;
    if (value < 3) return NutritionLevel.moderate;
    return NutritionLevel.high;
  }

  NutritionLevel _getProteinLevel(double? value) {
    if (value == null) return NutritionLevel.moderate;
    if (value < 4) return NutritionLevel.low;
    if (value < 8) return NutritionLevel.moderate;
    return NutritionLevel.high;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<ProductProvider>(
        builder: (context, provider, child) {
          if (provider.isAnalyzing) {
            return _buildLoadingState();
          }

          if (provider.error != null) {
            return _buildErrorState(provider.error!);
          }

          final product = provider.currentProduct;
          if (product == null) {
            return _buildErrorState('Product not found');
          }

          return _buildContent(product, _famAnalysis);
        },
      ),
    );
  }

  Widget _buildLoadingState() {
    return Scaffold(
      appBar: AppBar(title: const Text('Analyzing...')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 24),
            const Text(
              'Analyzing ingredients...',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            Text(
              'Checking against your family health profile',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Scaffold(
      appBar: AppBar(title: const Text('Analysis')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.error_outline, size: 64, color: Colors.grey[400]),
              const SizedBox(height: 16),
              Text(
                'Analysis Failed',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.grey[700],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                error,
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey[600]),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _loadAnalysis,
                child: const Text('Try Again'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContent(dynamic product, FAMAnalysis? analysis) {
    return NestedScrollView(
      headerSliverBuilder: (context, innerBoxIsScrolled) {
        return [
          _buildSliverAppBar(product, analysis),
        ];
      },
      body: Column(
        children: [
          _buildTabBar(),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildOverviewTab(product, analysis),
                _buildIngredientsTab(product, analysis),
                _buildNutritionTab(product, analysis),
                _buildFamilyTab(product, analysis),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSliverAppBar(dynamic product, FAMAnalysis? analysis) {
    return SliverAppBar(
      expandedHeight: 320,
      pinned: true,
      backgroundColor: analysis?.famScoreColor ?? AppColors.primary,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                analysis?.famScoreColor.withOpacity(0.8) ??
                    AppColors.primary.withOpacity(0.8),
                analysis?.famScoreColor ?? AppColors.primary,
              ],
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 60, 16, 16),
              child: Column(
                children: [
                  // Product info row
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Product image
                      Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withOpacity(0.2),
                              blurRadius: 8,
                            ),
                          ],
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: product.imageUrl != null
                              ? Image.network(
                                  product.imageUrl,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) => const Icon(
                                    Icons.fastfood,
                                    size: 40,
                                    color: Colors.grey,
                                  ),
                                )
                              : const Icon(
                                  Icons.fastfood,
                                  size: 40,
                                  color: Colors.grey,
                                ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      // Product details
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              product.name,
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            if (product.brand != null) ...[
                              const SizedBox(height: 4),
                              Text(
                                product.brand,
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.9),
                                  fontSize: 14,
                                ),
                              ),
                            ],
                            const SizedBox(height: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                product.barcode,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.white,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  // Score cards row
                  Row(
                    children: [
                      // FAM Score (main)
                      Expanded(
                        flex: 2,
                        child: _buildFAMScoreCard(analysis),
                      ),
                      const SizedBox(width: 12),
                      // Nutri-Score
                      Expanded(
                        child: _buildNutriScoreCard(analysis),
                      ),
                      const SizedBox(width: 12),
                      // NOVA
                      Expanded(
                        child: _buildNovaCard(analysis),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.share, color: Colors.white),
          onPressed: () {
            // Share functionality
          },
        ),
      ],
    );
  }

  Widget _buildFAMScoreCard(FAMAnalysis? analysis) {
    final score = analysis?.famScore ?? 50;
    final label = analysis?.famScoreLabel ?? 'Analyzing';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        children: [
          const Text(
            'FAM Score',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${score.toInt()}',
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                  color: analysis?.famScoreColor ?? Colors.grey,
                ),
              ),
              Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Text(
                  '/100',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[400],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
            decoration: BoxDecoration(
              color: analysis?.famScoreColor.withOpacity(0.1) ??
                  Colors.grey.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: analysis?.famScoreColor ?? Colors.grey,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNutriScoreCard(FAMAnalysis? analysis) {
    final nutriScore = analysis?.nutriScore ?? NutriScore.unknown;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        children: [
          const Text(
            'Nutri-Score',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w500,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: nutriScore.color,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Center(
              child: Text(
                nutriScore.letter,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNovaCard(FAMAnalysis? analysis) {
    final nova = analysis?.novaGroup ?? NovaGroup.unknown;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        children: [
          const Text(
            'NOVA',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w500,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: nova.color,
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(
                '${nova.value}',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      color: Colors.white,
      child: TabBar(
        controller: _tabController,
        labelColor: AppColors.primary,
        unselectedLabelColor: Colors.grey,
        indicatorColor: AppColors.primary,
        tabs: const [
          Tab(icon: Icon(Icons.dashboard), text: 'Overview'),
          Tab(icon: Icon(Icons.science), text: 'Ingredients'),
          Tab(icon: Icon(Icons.restaurant_menu), text: 'Nutrition'),
          Tab(icon: Icon(Icons.family_restroom), text: 'Family'),
        ],
      ),
    );
  }

  Widget _buildOverviewTab(dynamic product, FAMAnalysis? analysis) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Warnings section
          if (analysis != null && analysis.warnings.isNotEmpty)
            _buildWarningsSection(analysis.warnings),

          // Score breakdown
          _buildScoreBreakdown(analysis),
          const SizedBox(height: 16),

          // Quick stats
          _buildQuickStats(analysis),
          const SizedBox(height: 16),

          // Recommendations
          if (analysis != null && analysis.recommendations.isNotEmpty)
            _buildRecommendationsSection(analysis.recommendations),

          // Find alternatives button
          const SizedBox(height: 24),
          _buildAlternativesButton(),
          const SizedBox(height: 100),
        ],
      ),
    );
  }

  Widget _buildWarningsSection(List<String> warnings) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.red.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.warning_amber, color: Colors.red.shade700),
              const SizedBox(width: 8),
              Text(
                'Health Warnings',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.red.shade700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ...warnings.map((w) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.circle, size: 8, color: Colors.red.shade700),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        w,
                        style: TextStyle(color: Colors.red.shade900),
                      ),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildScoreBreakdown(FAMAnalysis? analysis) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.analytics, size: 20),
                SizedBox(width: 8),
                Text(
                  'Score Breakdown',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Based on FAM formula: Score = α·NutriScore − β·RiskFlags + γ·FitToGoals − δ·BudgetPenalty',
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
            const SizedBox(height: 16),
            _buildScoreRow(
              'Nutritional Quality',
              analysis?.nutriScore.numericValue.toDouble() ?? 50,
              Colors.green,
              '+',
            ),
            _buildScoreRow(
              'Risk Ingredients',
              (analysis?.flaggedIngredients ?? 0) * 10.0,
              Colors.red,
              '-',
            ),
            _buildScoreRow(
              'Fit to Goals',
              50, // Placeholder
              Colors.blue,
              '+',
            ),
            const Divider(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Final FAM Score',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(
                  '${analysis?.famScore.toInt() ?? 50}/100',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                    color: analysis?.famScoreColor ?? Colors.grey,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildScoreRow(String label, double value, Color color, String sign) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(label),
          ),
          Expanded(
            flex: 3,
            child: LinearProgressIndicator(
              value: value / 100,
              backgroundColor: Colors.grey[200],
              valueColor: AlwaysStoppedAnimation(color),
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '$sign${value.toInt()}',
            style: TextStyle(
              fontWeight: FontWeight.w500,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickStats(FAMAnalysis? analysis) {
    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            'Ingredients',
            '${analysis?.totalIngredients ?? 0}',
            Icons.list,
            Colors.blue,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            'Flagged',
            '${analysis?.flaggedIngredients ?? 0}',
            Icons.flag,
            Colors.orange,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            'Processing',
            'NOVA ${analysis?.novaGroup.value ?? "?"}',
            Icons.factory,
            analysis?.novaGroup.color ?? Colors.grey,
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard(
      String label, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              label,
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendationsSection(List<String> recommendations) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.lightbulb_outline, size: 20, color: Colors.amber),
                SizedBox(width: 8),
                Text(
                  'Recommendations',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...recommendations.map((r) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.arrow_right, size: 20, color: Colors.amber),
                      const SizedBox(width: 4),
                      Expanded(child: Text(r)),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildAlternativesButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: () {
          context.push('/alternatives/${widget.productId}');
        },
        icon: const Icon(Icons.swap_horiz),
        label: const Text('Find Healthier Alternatives'),
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }

  Widget _buildIngredientsTab(dynamic product, FAMAnalysis? analysis) {
    final allIngredients = product?.ingredients as List<String>? ?? [];
    final flaggedIngredients = analysis?.ingredients ?? [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Ingredient concerns summary
          _buildIngredientConcernsSummary(flaggedIngredients),
          const SizedBox(height: 16),

          // Flagged ingredients
          if (flaggedIngredients.isNotEmpty) ...[
            _buildFlaggedIngredientsSection(flaggedIngredients),
            const SizedBox(height: 16),
          ],

          // All ingredients
          _buildAllIngredientsSection(allIngredients, flaggedIngredients),
          const SizedBox(height: 100),
        ],
      ),
    );
  }

  Widget _buildIngredientConcernsSummary(List<DetailedIngredient> ingredients) {
    final highConcern =
        ingredients.where((i) => i.concern == IngredientConcern.high).length;
    final moderateConcern =
        ingredients.where((i) => i.concern == IngredientConcern.moderate).length;
    final lowConcern =
        ingredients.where((i) => i.concern == IngredientConcern.low).length;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Ingredient Concerns',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildConcernBadge(
                    'High',
                    highConcern,
                    IngredientConcern.high.color,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildConcernBadge(
                    'Moderate',
                    moderateConcern,
                    IngredientConcern.moderate.color,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildConcernBadge(
                    'Low',
                    lowConcern,
                    IngredientConcern.low.color,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConcernBadge(String label, int count, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(
            '$count',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: TextStyle(fontSize: 12, color: color),
          ),
        ],
      ),
    );
  }

  Widget _buildFlaggedIngredientsSection(List<DetailedIngredient> ingredients) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.flag, size: 20, color: Colors.orange.shade700),
                const SizedBox(width: 8),
                const Text(
                  'Flagged Ingredients',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...ingredients.map((ing) => _buildFlaggedIngredientCard(ing)),
          ],
        ),
      ),
    );
  }

  Widget _buildFlaggedIngredientCard(DetailedIngredient ingredient) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: ingredient.concern.color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ingredient.concern.color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: ingredient.concern.color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  ingredient.canonicalName ?? ingredient.name,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: ingredient.concern.color,
                  ),
                ),
              ),
              const Spacer(),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: ingredient.concern.color,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  ingredient.concern.label,
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: Colors.white,
                  ),
                ),
              ),
            ],
          ),
          if (ingredient.description != null) ...[
            const SizedBox(height: 8),
            Text(
              ingredient.description!,
              style: const TextStyle(fontSize: 13),
            ),
          ],
          if (ingredient.affectedProfiles.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 4,
              runSpacing: 4,
              children: ingredient.affectedProfiles.map((p) {
                return Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    p,
                    style: const TextStyle(fontSize: 11),
                  ),
                );
              }).toList(),
            ),
          ],
          if (ingredient.evidenceUrl != null) ...[
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () async {
                final url = Uri.parse(ingredient.evidenceUrl!);
                if (await canLaunchUrl(url)) {
                  await launchUrl(url);
                }
              },
              child: const Text(
                'View evidence →',
                style: TextStyle(
                  color: AppColors.primary,
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAllIngredientsSection(
      List<String> allIngredients, List<DetailedIngredient> flagged) {
    final flaggedNames =
        flagged.map((f) => f.name.toLowerCase()).toSet();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.list, size: 20),
                    SizedBox(width: 8),
                    Text(
                      'All Ingredients',
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
                Text(
                  '${allIngredients.length} items',
                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: allIngredients.map((ingredient) {
                final isFlagged =
                    flaggedNames.contains(ingredient.toLowerCase());
                return Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: isFlagged
                        ? Colors.orange.withOpacity(0.1)
                        : AppColors.background,
                    borderRadius: BorderRadius.circular(8),
                    border: isFlagged
                        ? Border.all(color: Colors.orange.withOpacity(0.3))
                        : null,
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (isFlagged) ...[
                        const Icon(Icons.flag, size: 14, color: Colors.orange),
                        const SizedBox(width: 4),
                      ],
                      Text(
                        ingredient,
                        style: TextStyle(
                          fontSize: 13,
                          color: isFlagged ? Colors.orange.shade800 : null,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNutritionTab(dynamic product, FAMAnalysis? analysis) {
    final nutritionFacts = analysis?.nutritionFacts ?? [];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Nutri-Score explanation
          _buildNutriScoreExplanation(analysis),
          const SizedBox(height: 16),

          // Nutrition facts table
          _buildNutritionFactsTable(nutritionFacts),
          const SizedBox(height: 16),

          // Nutrition levels
          _buildNutritionLevels(nutritionFacts),
          const SizedBox(height: 100),
        ],
      ),
    );
  }

  Widget _buildNutriScoreExplanation(FAMAnalysis? analysis) {
    final nutriScore = analysis?.nutriScore ?? NutriScore.unknown;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Nutri-Score',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Row(
              children: NutriScore.values
                  .where((s) => s != NutriScore.unknown)
                  .map((score) {
                final isSelected = score == nutriScore;
                return Expanded(
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(
                      color: score.color,
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: isSelected
                          ? [
                              BoxShadow(
                                color: score.color.withOpacity(0.5),
                                blurRadius: 8,
                                spreadRadius: 2,
                              )
                            ]
                          : null,
                    ),
                    child: Center(
                      child: Text(
                        score.letter,
                        style: TextStyle(
                          fontSize: isSelected ? 24 : 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 12),
            Text(
              nutriScore.description,
              style: TextStyle(color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNutritionFactsTable(List<NutritionFact> facts) {
    if (facts.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Icon(Icons.info_outline, size: 48, color: Colors.grey[400]),
              const SizedBox(height: 8),
              Text(
                'Nutrition information not available',
                style: TextStyle(color: Colors.grey[600]),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Nutrition Facts (per 100g)',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            ...facts.map((fact) => _buildNutritionRow(fact)),
          ],
        ),
      ),
    );
  }

  Widget _buildNutritionRow(NutritionFact fact) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: fact.displayColor,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(fact.name),
          ),
          Text(
            fact.value != null
                ? '${fact.value!.toStringAsFixed(1)} ${fact.unit}'
                : '-',
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          const SizedBox(width: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: fact.displayColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              fact.level.label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: fact.displayColor,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNutritionLevels(List<NutritionFact> facts) {
    final badNutrients = facts.where((f) => !f.isGood).toList();
    final goodNutrients = facts.where((f) => f.isGood).toList();

    return Column(
      children: [
        if (badNutrients.isNotEmpty)
          _buildNutrientLevelCard(
            'Nutrients to limit',
            badNutrients,
            Icons.remove_circle_outline,
            Colors.orange,
          ),
        if (goodNutrients.isNotEmpty) ...[
          const SizedBox(height: 12),
          _buildNutrientLevelCard(
            'Beneficial nutrients',
            goodNutrients,
            Icons.add_circle_outline,
            Colors.green,
          ),
        ],
      ],
    );
  }

  Widget _buildNutrientLevelCard(
    String title,
    List<NutritionFact> facts,
    IconData icon,
    Color color,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 20, color: color),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...facts.map((f) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: f.displayColor,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(f.name),
                      const Spacer(),
                      Text(
                        f.level.label,
                        style: TextStyle(
                          color: f.displayColor,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildFamilyTab(dynamic product, FAMAnalysis? analysis) {
    return Consumer<FamilyProvider>(
      builder: (context, familyProvider, child) {
        final members = familyProvider.members;

        if (members.isEmpty) {
          return _buildNoFamilyState();
        }

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildFamilyOverview(members, analysis),
              const SizedBox(height: 16),
              ...members.map((member) =>
                  _buildMemberAnalysisCard(member, analysis)),
              const SizedBox(height: 100),
            ],
          ),
        );
      },
    );
  }

  Widget _buildNoFamilyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.family_restroom, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            const Text(
              'No Family Profile',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 8),
            Text(
              'Add family members to get personalized health analysis',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () => context.push('/add-member'),
              icon: const Icon(Icons.add),
              label: const Text('Add Family Member'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFamilyOverview(
      List<FamilyMember> members, FAMAnalysis? analysis) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.family_restroom, size: 20),
                SizedBox(width: 8),
                Text(
                  'Family Risk Assessment',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Analysis based on ${members.length} family member${members.length > 1 ? "s" : ""}',
              style: TextStyle(color: Colors.grey[600], fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMemberAnalysisCard(FamilyMember member, FAMAnalysis? analysis) {
    final memberRisk = _calculateMemberRisk(member, analysis);
    final color = Color(memberRisk.colorValue);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(member.type.icon, style: const TextStyle(fontSize: 32)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        member.name,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        member.type.displayName,
                        style: TextStyle(color: Colors.grey[600], fontSize: 13),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: color.withOpacity(0.3)),
                  ),
                  child: Text(
                    memberRisk.displayName,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: color,
                    ),
                  ),
                ),
              ],
            ),
            if (member.conditions.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: member.conditions.map((c) {
                  return Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.blue.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      c.displayName,
                      style: const TextStyle(fontSize: 12, color: Colors.blue),
                    ),
                  );
                }).toList(),
              ),
            ],
            // Show relevant warnings for this member
            if (analysis != null) ...[
              const SizedBox(height: 12),
              ...analysis.ingredients
                  .where((i) =>
                      i.affectedProfiles.any((p) =>
                          p.toLowerCase() == member.type.name.toLowerCase() ||
                          member.conditions
                              .any((c) => p.toLowerCase() == c.name.toLowerCase())))
                  .take(3)
                  .map((i) => Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Row(
                          children: [
                            Icon(Icons.warning_amber,
                                size: 16, color: i.concern.color),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                '${i.canonicalName ?? i.name}: ${i.description ?? "May affect ${member.name}"}',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[700],
                                ),
                              ),
                            ),
                          ],
                        ),
                      )),
            ],
          ],
        ),
      ),
    );
  }

  RiskLevel _calculateMemberRisk(FamilyMember member, FAMAnalysis? analysis) {
    if (analysis == null) return RiskLevel.low;

    var riskScore = analysis.famScore;

    // Adjust for member type
    if (member.type == MemberType.pregnant ||
        member.type == MemberType.toddler) {
      riskScore -= 15;
    } else if (member.type == MemberType.child ||
        member.type == MemberType.senior) {
      riskScore -= 10;
    }

    // Adjust for conditions
    riskScore -= member.conditions.length * 5;

    // Check for relevant flagged ingredients
    for (final ing in analysis.ingredients) {
      if (ing.affectedProfiles.any((p) =>
          p.toLowerCase() == member.type.name.toLowerCase() ||
          member.conditions.any((c) => p.toLowerCase() == c.name.toLowerCase()))) {
        if (ing.concern == IngredientConcern.high) {
          riskScore -= 20;
        } else if (ing.concern == IngredientConcern.moderate) {
          riskScore -= 10;
        }
      }
    }

    if (riskScore >= 80) return RiskLevel.safe;
    if (riskScore >= 60) return RiskLevel.low;
    if (riskScore >= 40) return RiskLevel.medium;
    if (riskScore >= 20) return RiskLevel.high;
    return RiskLevel.critical;
  }
}
