import 'dart:convert';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/family_member.dart';
import '../models/product.dart';
import '../models/feedback.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  static const String _familyMembersBox = 'family_members';
  static const String _scanHistoryBox = 'scan_history';
  static const String _feedbackBox = 'feedback';
  static const String _settingsKey = 'app_settings';

  late Box<String> _familyBox;
  late Box<String> _historyBox;
  late Box<String> _feedbackBoxInstance;
  late SharedPreferences _prefs;

  Future<void> initialize() async {
    await Hive.initFlutter();
    _familyBox = await Hive.openBox<String>(_familyMembersBox);
    _historyBox = await Hive.openBox<String>(_scanHistoryBox);
    _feedbackBoxInstance = await Hive.openBox<String>(_feedbackBox);
    _prefs = await SharedPreferences.getInstance();
  }

  // Family Members
  Future<List<FamilyMember>> getFamilyMembers() async {
    final members = <FamilyMember>[];
    for (final key in _familyBox.keys) {
      final json = _familyBox.get(key);
      if (json != null) {
        try {
          members.add(FamilyMember.fromJson(jsonDecode(json)));
        } catch (_) {}
      }
    }
    return members;
  }

  Future<void> saveFamilyMember(FamilyMember member) async {
    await _familyBox.put(member.id, jsonEncode(member.toJson()));
  }

  Future<void> deleteFamilyMember(String memberId) async {
    await _familyBox.delete(memberId);
  }

  // Scan History
  Future<List<Product>> getScanHistory({int limit = 50}) async {
    final products = <Product>[];
    final keys = _historyBox.keys.toList().reversed.take(limit);
    for (final key in keys) {
      final json = _historyBox.get(key);
      if (json != null) {
        try {
          products.add(Product.fromJson(jsonDecode(json)));
        } catch (_) {}
      }
    }
    return products;
  }

  Future<void> addToScanHistory(Product product) async {
    await _historyBox.put(
      '${product.scannedAt.millisecondsSinceEpoch}_${product.id}',
      jsonEncode(product.toJson()),
    );

    // Keep only last 100 items
    if (_historyBox.length > 100) {
      final keysToDelete = _historyBox.keys.toList()
        ..sort()
        ..take(_historyBox.length - 100);
      for (final key in keysToDelete) {
        await _historyBox.delete(key);
      }
    }
  }

  Future<void> clearScanHistory() async {
    await _historyBox.clear();
  }

  // Feedback
  Future<List<UserFeedback>> getPendingFeedback() async {
    final feedbackList = <UserFeedback>[];
    for (final key in _feedbackBoxInstance.keys) {
      final json = _feedbackBoxInstance.get(key);
      if (json != null) {
        try {
          final feedback = UserFeedback.fromJson(jsonDecode(json));
          if (!feedback.synced) {
            feedbackList.add(feedback);
          }
        } catch (_) {}
      }
    }
    return feedbackList;
  }

  Future<void> saveFeedback(UserFeedback feedback) async {
    await _feedbackBoxInstance.put(feedback.id, jsonEncode(feedback.toJson()));
  }

  Future<void> markFeedbackSynced(String feedbackId) async {
    final json = _feedbackBoxInstance.get(feedbackId);
    if (json != null) {
      final feedback = UserFeedback.fromJson(jsonDecode(json));
      final updated = feedback.copyWith(synced: true);
      await _feedbackBoxInstance.put(feedbackId, jsonEncode(updated.toJson()));
    }
  }

  // Settings
  Future<bool> isOnboardingComplete() async {
    return _prefs.getBool('onboarding_complete') ?? false;
  }

  Future<void> setOnboardingComplete(bool complete) async {
    await _prefs.setBool('onboarding_complete', complete);
  }

  Future<String?> getApiKey() async {
    return _prefs.getString('openai_api_key');
  }

  Future<void> setApiKey(String apiKey) async {
    await _prefs.setString('openai_api_key', apiKey);
  }

  Future<bool> isDarkMode() async {
    return _prefs.getBool('dark_mode') ?? false;
  }

  Future<void> setDarkMode(bool darkMode) async {
    await _prefs.setBool('dark_mode', darkMode);
  }

  Future<void> clearAllData() async {
    await _familyBox.clear();
    await _historyBox.clear();
    await _feedbackBoxInstance.clear();
    await _prefs.clear();
  }
}
