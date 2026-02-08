import 'package:flutter/foundation.dart';
import '../models/family_member.dart';

class FamilyProvider extends ChangeNotifier {
  List<FamilyMember> _members = [];
  bool _isLoading = false;
  String? _error;

  List<FamilyMember> get members => _members;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasMembers => _members.isNotEmpty;

  FamilyMember? getMemberById(String id) {
    try {
      return _members.firstWhere((m) => m.id == id);
    } catch (_) {
      return null;
    }
  }

  List<FamilyMember> getMembersByType(MemberType type) {
    return _members.where((m) => m.type == type).toList();
  }

  List<FamilyMember> getMembersWithCondition(HealthCondition condition) {
    return _members.where((m) => m.conditions.contains(condition)).toList();
  }

  Future<void> loadMembers() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // TODO: Load from Hive storage
      await Future.delayed(const Duration(milliseconds: 300));
      // For now, keep existing members
    } catch (e) {
      _error = 'Failed to load family members: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> addMember(FamilyMember member) async {
    _isLoading = true;
    notifyListeners();

    try {
      _members.add(member);
      // TODO: Save to Hive storage
      await Future.delayed(const Duration(milliseconds: 100));
    } catch (e) {
      _error = 'Failed to add member: $e';
      _members.remove(member);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> updateMember(FamilyMember updatedMember) async {
    _isLoading = true;
    notifyListeners();

    try {
      final index = _members.indexWhere((m) => m.id == updatedMember.id);
      if (index != -1) {
        _members[index] = updatedMember;
        // TODO: Save to Hive storage
        await Future.delayed(const Duration(milliseconds: 100));
      }
    } catch (e) {
      _error = 'Failed to update member: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> removeMember(String memberId) async {
    _isLoading = true;
    notifyListeners();

    try {
      _members.removeWhere((m) => m.id == memberId);
      // TODO: Remove from Hive storage
      await Future.delayed(const Duration(milliseconds: 100));
    } catch (e) {
      _error = 'Failed to remove member: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
