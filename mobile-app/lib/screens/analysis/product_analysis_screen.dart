import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../models/analysis_result.dart';
import '../../models/family_member.dart';
import '../../providers/family_provider.dart';
import '../../providers/product_provider.dart';
import '../../providers/feedback_provider.dart';
import '../../models/feedback.dart';
import '../feedback/feedback_dialog.dart';

class ProductAnalysisScreen extends StatefulWidget {
  final String productId;

  const ProductAnalysisScreen({super.key, required this.productId});

  @override
  State<ProductAnalysisScreen> createState() => _ProductAnalysisScreenState();
}

class _ProductAnalysisScreenState extends State<ProductAnalysisScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadAnalysis();
    });
  }

  Future<void> _loadAnalysis() async {
    final provider = context.read<ProductProvider>();
    await provider.analyzeProduct();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            onPressed: () {
              // TODO: Share functionality
            },
          ),
        ],
      ),
      body: Consumer<ProductProvider>(
        builder: (context, provider, child) {
          if (provider.isAnalyzing) {
            return _buildLoadingState();
          }

          if (provider.error != null) {
            return _buildErrorState(provider.error!);
          }

          final product = provider.currentProduct;
          final analysis = provider.currentAnalysis;

          if (product == null) {
            return _buildErrorState('Product not found');
          }

          return _buildAnalysisContent(product, analysis);
        },
      ),
      bottomNavigationBar: _buildBottomBar(),
    );
  }

  Widget _buildLoadingState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 24),
          const Text(
            'Analyzing ingredients...',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Checking against your family profile',
            style: TextStyle(
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.grey[400],
            ),
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
    );
  }

  Widget _buildAnalysisContent(product, AnalysisResult? analysis) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildProductHeader(product),
          const SizedBox(height: 20),
          if (analysis != null) ...[
            _buildScoreCard(analysis),
            const SizedBox(height: 20),
            _buildFamilyRisks(analysis),
            const SizedBox(height: 20),
            _buildIngredientFlags(analysis),
            const SizedBox(height: 20),
            _buildExplanation(analysis),
          ],
          const SizedBox(height: 20),
          _buildIngredientsList(product),
          const SizedBox(height: 100),
        ],
      ),
    );
  }

  Widget _buildProductHeader(product) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: AppColors.background,
                borderRadius: BorderRadius.circular(12),
              ),
              child: product.imageUrl != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.network(
                        product.imageUrl,
                        fit: BoxFit.cover,
                      ),
                    )
                  : const Icon(
                      Icons.fastfood,
                      size: 40,
                      color: AppColors.textSecondary,
                    ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (product.brand != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      product.brand,
                      style: TextStyle(
                        color: Colors.grey[600],
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
                      color: AppColors.background,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      product.barcode,
                      style: const TextStyle(
                        fontSize: 12,
                        fontFamily: 'monospace',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildScoreCard(AnalysisResult analysis) {
    final color = Color(analysis.overallRisk.colorValue);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Health Score',
                        style: TextStyle(
                          fontSize: 14,
                          color: AppColors.textSecondary,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            '${analysis.overallScore.toInt()}',
                            style: TextStyle(
                              fontSize: 48,
                              fontWeight: FontWeight.bold,
                              color: color,
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Text(
                              '/100',
                              style: TextStyle(
                                fontSize: 20,
                                color: Colors.grey[400],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: color.withOpacity(0.3)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _getRiskIcon(analysis.overallRisk),
                        color: color,
                        size: 20,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        analysis.overallRisk.displayName,
                        style: TextStyle(
                          color: color,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: analysis.overallScore / 100,
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation<Color>(color),
                minHeight: 8,
              ),
            ),
          ],
        ),
      ),
    );
  }

  IconData _getRiskIcon(RiskLevel risk) {
    switch (risk) {
      case RiskLevel.safe:
        return Icons.check_circle;
      case RiskLevel.low:
        return Icons.info;
      case RiskLevel.medium:
        return Icons.warning_amber;
      case RiskLevel.high:
        return Icons.error;
      case RiskLevel.critical:
        return Icons.dangerous;
    }
  }

  Widget _buildFamilyRisks(AnalysisResult analysis) {
    return Consumer<FamilyProvider>(
      builder: (context, familyProvider, child) {
        final members = familyProvider.members;

        if (members.isEmpty) {
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(
                      Icons.family_restroom,
                      color: AppColors.primary,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Add Family Members',
                          style: TextStyle(fontWeight: FontWeight.w600),
                        ),
                        Text(
                          'Get personalized risk analysis',
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                  TextButton(
                    onPressed: () => context.push('/add-member'),
                    child: const Text('Add'),
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
                const Row(
                  children: [
                    Icon(Icons.family_restroom, size: 20),
                    SizedBox(width: 8),
                    Text(
                      'Family Risk Assessment',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                ...members.map((member) => _buildMemberRiskItem(member, analysis)),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildMemberRiskItem(FamilyMember member, AnalysisResult analysis) {
    // Determine risk based on member type and conditions
    final risk = _calculateMemberRisk(member, analysis);
    final color = Color(risk.colorValue);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Text(member.type.icon, style: const TextStyle(fontSize: 24)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  member.name,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                if (member.conditions.isNotEmpty)
                  Text(
                    member.conditions.map((c) => c.displayName.split(' ').first).join(', '),
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              risk.displayName,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }

  RiskLevel _calculateMemberRisk(FamilyMember member, AnalysisResult analysis) {
    // Simple risk calculation based on member type and flags
    var riskScore = analysis.overallScore;

    // Adjust for member type
    if (member.type == MemberType.pregnant || member.type == MemberType.toddler) {
      riskScore -= 15;
    } else if (member.type == MemberType.child || member.type == MemberType.senior) {
      riskScore -= 10;
    }

    // Adjust for conditions
    riskScore -= member.conditions.length * 5;

    if (riskScore >= 80) return RiskLevel.safe;
    if (riskScore >= 60) return RiskLevel.low;
    if (riskScore >= 40) return RiskLevel.medium;
    if (riskScore >= 20) return RiskLevel.high;
    return RiskLevel.critical;
  }

  Widget _buildIngredientFlags(AnalysisResult analysis) {
    if (analysis.ingredientFlags.isEmpty) {
      return const SizedBox.shrink();
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.flag, size: 20, color: AppColors.riskMedium),
                SizedBox(width: 8),
                Text(
                  'Flagged Ingredients',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...analysis.ingredientFlags.map((flag) => _buildFlagItem(flag)),
          ],
        ),
      ),
    );
  }

  Widget _buildFlagItem(IngredientFlag flag) {
    final color = Color(flag.riskLevel.colorValue);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  flag.canonicalName,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: color,
                  ),
                ),
              ),
              const Spacer(),
              Icon(
                _getRiskIcon(flag.riskLevel),
                color: color,
                size: 20,
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            flag.explanation,
            style: const TextStyle(fontSize: 13),
          ),
          if (flag.evidenceLink != null) ...[
            const SizedBox(height: 8),
            GestureDetector(
              onTap: () {
                // TODO: Open evidence link
              },
              child: const Text(
                'Learn more →',
                style: TextStyle(
                  color: AppColors.primary,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildExplanation(AnalysisResult analysis) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.lightbulb_outline, size: 20, color: AppColors.secondary),
                SizedBox(width: 8),
                Text(
                  'Summary',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              analysis.explanation,
              style: const TextStyle(
                fontSize: 14,
                height: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIngredientsList(product) {
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
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Text(
                  '${product.ingredients.length} items',
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 13,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: product.ingredients.map<Widget>((ingredient) {
                return Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    ingredient,
                    style: const TextStyle(fontSize: 13),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            _buildFeedbackButtons(),
            const SizedBox(width: 16),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () {
                  context.push('/alternatives/${widget.productId}');
                },
                icon: const Icon(Icons.swap_horiz),
                label: const Text('Find Alternatives'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeedbackButtons() {
    return Consumer<FeedbackProvider>(
      builder: (context, feedbackProvider, child) {
        final existingFeedback = feedbackProvider.getUserFeedbackType(widget.productId);

        return Row(
          children: [
            _FeedbackButton(
              icon: Icons.thumb_up_outlined,
              activeIcon: Icons.thumb_up,
              isActive: existingFeedback == FeedbackType.thumbsUp,
              color: AppColors.safe,
              onTap: () => _submitFeedback(FeedbackType.thumbsUp),
            ),
            const SizedBox(width: 8),
            _FeedbackButton(
              icon: Icons.thumb_down_outlined,
              activeIcon: Icons.thumb_down,
              isActive: existingFeedback == FeedbackType.thumbsDown,
              color: AppColors.riskHigh,
              onTap: () => _submitFeedback(FeedbackType.thumbsDown),
            ),
          ],
        );
      },
    );
  }

  Future<void> _submitFeedback(FeedbackType type) async {
    final feedbackProvider = context.read<FeedbackProvider>();
    final feedback = await feedbackProvider.submitQuickFeedback(
      productId: widget.productId,
      type: type,
    );

    if (type == FeedbackType.thumbsDown && mounted) {
      // Show detailed feedback dialog for negative feedback
      showDialog(
        context: context,
        builder: (context) => FeedbackDialog(
          feedbackId: feedback.id,
          productId: widget.productId,
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Thanks for your feedback!'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
    }
  }
}

class _FeedbackButton extends StatelessWidget {
  final IconData icon;
  final IconData activeIcon;
  final bool isActive;
  final Color color;
  final VoidCallback onTap;

  const _FeedbackButton({
    required this.icon,
    required this.activeIcon,
    required this.isActive,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: isActive ? color.withOpacity(0.1) : AppColors.background,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(12),
          child: Icon(
            isActive ? activeIcon : icon,
            color: isActive ? color : AppColors.textSecondary,
          ),
        ),
      ),
    );
  }
}
