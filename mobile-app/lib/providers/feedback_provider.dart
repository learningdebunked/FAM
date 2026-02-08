import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';
import '../models/feedback.dart';

class FeedbackProvider extends ChangeNotifier {
  final List<UserFeedback> _feedbackList = [];
  bool _isSubmitting = false;
  String? _error;

  List<UserFeedback> get feedbackList => _feedbackList;
  bool get isSubmitting => _isSubmitting;
  String? get error => _error;

  List<UserFeedback> getFeedbackForProduct(String productId) {
    return _feedbackList.where((f) => f.productId == productId).toList();
  }

  bool hasUserFeedback(String productId) {
    return _feedbackList.any((f) => f.productId == productId);
  }

  FeedbackType? getUserFeedbackType(String productId) {
    try {
      return _feedbackList.firstWhere((f) => f.productId == productId).type;
    } catch (_) {
      return null;
    }
  }

  Future<UserFeedback> submitQuickFeedback({
    required String productId,
    required FeedbackType type,
  }) async {
    final feedback = UserFeedback(
      id: const Uuid().v4(),
      productId: productId,
      type: type,
    );

    _feedbackList.add(feedback);
    notifyListeners();

    return feedback;
  }

  Future<void> submitDetailedFeedback({
    required String feedbackId,
    required FeedbackCategory category,
    String? comment,
    String? ingredientFlagged,
  }) async {
    _isSubmitting = true;
    _error = null;
    notifyListeners();

    try {
      final index = _feedbackList.indexWhere((f) => f.id == feedbackId);
      if (index != -1) {
        _feedbackList[index] = _feedbackList[index].copyWith(
          category: category,
          comment: comment,
          ingredientFlagged: ingredientFlagged,
        );

        // TODO: Sync to backend
        await Future.delayed(const Duration(milliseconds: 500));
        
        _feedbackList[index] = _feedbackList[index].copyWith(synced: true);
      }
    } catch (e) {
      _error = 'Failed to submit feedback: $e';
    } finally {
      _isSubmitting = false;
      notifyListeners();
    }
  }

  Future<void> syncPendingFeedback() async {
    final pending = _feedbackList.where((f) => !f.synced).toList();
    
    for (final feedback in pending) {
      try {
        // TODO: Sync to backend API
        await Future.delayed(const Duration(milliseconds: 200));
        
        final index = _feedbackList.indexWhere((f) => f.id == feedback.id);
        if (index != -1) {
          _feedbackList[index] = _feedbackList[index].copyWith(synced: true);
        }
      } catch (e) {
        debugPrint('Failed to sync feedback ${feedback.id}: $e');
      }
    }
    
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
