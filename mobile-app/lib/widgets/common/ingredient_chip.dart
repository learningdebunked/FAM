import 'package:flutter/material.dart';

import '../../config/theme.dart';
import '../../models/analysis_result.dart';

class IngredientChip extends StatelessWidget {
  final String name;
  final RiskLevel? riskLevel;
  final VoidCallback? onTap;
  final bool showTooltip;

  const IngredientChip({
    super.key,
    required this.name,
    this.riskLevel,
    this.onTap,
    this.showTooltip = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = riskLevel != null
        ? Color(riskLevel!.colorValue)
        : AppColors.textSecondary;

    final chip = GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: riskLevel != null
              ? color.withOpacity(0.1)
              : AppColors.background,
          borderRadius: BorderRadius.circular(8),
          border: riskLevel != null
              ? Border.all(color: color.withOpacity(0.3))
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (riskLevel != null) ...[
              Icon(
                _getIcon(),
                size: 14,
                color: color,
              ),
              const SizedBox(width: 4),
            ],
            Text(
              name,
              style: TextStyle(
                fontSize: 13,
                color: riskLevel != null ? color : AppColors.textPrimary,
                fontWeight:
                    riskLevel != null ? FontWeight.w500 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );

    if (showTooltip && riskLevel != null) {
      return Tooltip(
        message: riskLevel!.displayName,
        child: chip,
      );
    }

    return chip;
  }

  IconData _getIcon() {
    switch (riskLevel) {
      case RiskLevel.safe:
        return Icons.check_circle_outline;
      case RiskLevel.low:
        return Icons.info_outline;
      case RiskLevel.medium:
        return Icons.warning_amber;
      case RiskLevel.high:
        return Icons.error_outline;
      case RiskLevel.critical:
        return Icons.dangerous;
      case null:
        return Icons.circle;
    }
  }
}

class IngredientFlagCard extends StatelessWidget {
  final IngredientFlag flag;
  final VoidCallback? onLearnMore;

  const IngredientFlagCard({
    super.key,
    required this.flag,
    this.onLearnMore,
  });

  @override
  Widget build(BuildContext context) {
    final color = Color(flag.riskLevel.colorValue);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
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
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(_getIcon(), size: 16, color: color),
                    const SizedBox(width: 6),
                    Text(
                      flag.canonicalName,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: color,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  flag.riskLevel.displayName,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: color,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            flag.explanation,
            style: const TextStyle(
              fontSize: 13,
              height: 1.4,
            ),
          ),
          if (flag.affectedMemberTypes.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                const Text(
                  'Affects:',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                  ),
                ),
                ...flag.affectedMemberTypes.map((type) => Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '${type.icon} ${type.displayName.split(' ').first}',
                        style: const TextStyle(fontSize: 11),
                      ),
                    )),
              ],
            ),
          ],
          if (onLearnMore != null || flag.evidenceLink != null) ...[
            const SizedBox(height: 10),
            GestureDetector(
              onTap: onLearnMore,
              child: Text(
                'Learn more →',
                style: TextStyle(
                  color: color,
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

  IconData _getIcon() {
    switch (flag.riskLevel) {
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
}
