enum FeedbackType {
  thumbsUp,
  thumbsDown,
}

enum FeedbackCategory {
  incorrectIngredient,
  wrongRiskLevel,
  missingIngredient,
  badAlternative,
  helpfulInfo,
  other,
}

extension FeedbackCategoryExtension on FeedbackCategory {
  String get displayName {
    switch (this) {
      case FeedbackCategory.incorrectIngredient:
        return 'Incorrect ingredient identified';
      case FeedbackCategory.wrongRiskLevel:
        return 'Risk level seems wrong';
      case FeedbackCategory.missingIngredient:
        return 'Missing important ingredient';
      case FeedbackCategory.badAlternative:
        return 'Alternative suggestion not helpful';
      case FeedbackCategory.helpfulInfo:
        return 'Information was helpful';
      case FeedbackCategory.other:
        return 'Other feedback';
    }
  }
}

class UserFeedback {
  final String id;
  final String productId;
  final FeedbackType type;
  final FeedbackCategory? category;
  final String? comment;
  final String? ingredientFlagged;
  final DateTime createdAt;
  final bool synced;

  UserFeedback({
    required this.id,
    required this.productId,
    required this.type,
    this.category,
    this.comment,
    this.ingredientFlagged,
    DateTime? createdAt,
    this.synced = false,
  }) : createdAt = createdAt ?? DateTime.now();

  UserFeedback copyWith({
    FeedbackCategory? category,
    String? comment,
    String? ingredientFlagged,
    bool? synced,
  }) {
    return UserFeedback(
      id: id,
      productId: productId,
      type: type,
      category: category ?? this.category,
      comment: comment ?? this.comment,
      ingredientFlagged: ingredientFlagged ?? this.ingredientFlagged,
      createdAt: createdAt,
      synced: synced ?? this.synced,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'productId': productId,
      'type': type.index,
      'category': category?.index,
      'comment': comment,
      'ingredientFlagged': ingredientFlagged,
      'createdAt': createdAt.toIso8601String(),
      'synced': synced,
    };
  }

  factory UserFeedback.fromJson(Map<String, dynamic> json) {
    return UserFeedback(
      id: json['id'] as String,
      productId: json['productId'] as String,
      type: FeedbackType.values[json['type'] as int],
      category: json['category'] != null
          ? FeedbackCategory.values[json['category'] as int]
          : null,
      comment: json['comment'] as String?,
      ingredientFlagged: json['ingredientFlagged'] as String?,
      createdAt: DateTime.parse(json['createdAt'] as String),
      synced: json['synced'] as bool? ?? false,
    );
  }
}
