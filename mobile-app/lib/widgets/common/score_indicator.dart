import 'package:flutter/material.dart';
import 'dart:math' as math;

import '../../config/theme.dart';
import '../../models/analysis_result.dart';

class ScoreIndicator extends StatelessWidget {
  final double score;
  final double size;
  final double strokeWidth;

  const ScoreIndicator({
    super.key,
    required this.score,
    this.size = 80,
    this.strokeWidth = 8,
  });

  @override
  Widget build(BuildContext context) {
    final color = _getColorForScore(score);

    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size),
            painter: _ScoreRingPainter(
              progress: score / 100,
              color: color,
              strokeWidth: strokeWidth,
            ),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '${score.toInt()}',
                style: TextStyle(
                  fontSize: size * 0.3,
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
              Text(
                'score',
                style: TextStyle(
                  fontSize: size * 0.12,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Color _getColorForScore(double score) {
    if (score >= 80) return AppColors.safe;
    if (score >= 60) return AppColors.riskLow;
    if (score >= 40) return AppColors.riskMedium;
    return AppColors.riskHigh;
  }
}

class _ScoreRingPainter extends CustomPainter {
  final double progress;
  final Color color;
  final double strokeWidth;

  _ScoreRingPainter({
    required this.progress,
    required this.color,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Background circle
    final bgPaint = Paint()
      ..color = Colors.grey[200]!
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawCircle(center, radius, bgPaint);

    // Progress arc
    final progressPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      -math.pi / 2,
      2 * math.pi * progress,
      false,
      progressPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _ScoreRingPainter oldDelegate) {
    return oldDelegate.progress != progress || oldDelegate.color != color;
  }
}

class RiskBadge extends StatelessWidget {
  final RiskLevel riskLevel;
  final bool showIcon;
  final bool compact;

  const RiskBadge({
    super.key,
    required this.riskLevel,
    this.showIcon = true,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = Color(riskLevel.colorValue);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 8 : 12,
        vertical: compact ? 4 : 6,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(compact ? 8 : 16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (showIcon) ...[
            Icon(
              _getIcon(),
              color: color,
              size: compact ? 14 : 18,
            ),
            SizedBox(width: compact ? 4 : 6),
          ],
          Text(
            riskLevel.displayName,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w600,
              fontSize: compact ? 11 : 13,
            ),
          ),
        ],
      ),
    );
  }

  IconData _getIcon() {
    switch (riskLevel) {
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
