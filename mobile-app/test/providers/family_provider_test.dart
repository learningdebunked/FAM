import 'package:flutter_test/flutter_test.dart';
import 'package:fam_app/providers/family_provider.dart';
import 'package:fam_app/models/family_member.dart';

void main() {
  group('FamilyProvider Tests', () {
    late FamilyProvider provider;

    setUp(() {
      provider = FamilyProvider();
    });

    test('initial state has empty members list', () {
      expect(provider.members, isEmpty);
    });

    test('initial state is not loading', () {
      expect(provider.isLoading, isFalse);
    });

    test('addMember adds a member to the list', () async {
      final member = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: [],
      );

      await provider.addMember(member);

      expect(provider.members, hasLength(1));
      expect(provider.members.first.name, equals('Emma'));
    });

    test('addMember notifies listeners', () async {
      bool notified = false;
      provider.addListener(() => notified = true);

      final member = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: [],
      );

      await provider.addMember(member);

      expect(notified, isTrue);
    });

    test('updateMember updates existing member', () async {
      final member = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: [],
      );

      await provider.addMember(member);

      final updatedMember = FamilyMember(
        id: '1',
        name: 'Emma Updated',
        type: MemberType.child,
        age: 7,
        conditions: [HealthCondition.diabetic],
        allergies: ['Peanuts'],
      );

      await provider.updateMember(updatedMember);

      expect(provider.members.first.name, equals('Emma Updated'));
      expect(provider.members.first.age, equals(7));
      expect(provider.members.first.conditions, contains(HealthCondition.diabetic));
      expect(provider.members.first.allergies, contains('Peanuts'));
    });

    test('removeMember removes member from list', () async {
      final member = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: [],
      );

      await provider.addMember(member);
      expect(provider.members, hasLength(1));

      await provider.removeMember('1');
      expect(provider.members, isEmpty);
    });

    test('getMemberById returns correct member', () async {
      final member1 = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: [],
      );

      final member2 = FamilyMember(
        id: '2',
        name: 'Liam',
        type: MemberType.child,
        age: 8,
        conditions: [],
        allergies: [],
      );

      await provider.addMember(member1);
      await provider.addMember(member2);

      final found = provider.getMemberById('2');
      expect(found?.name, equals('Liam'));
    });

    test('getMemberById returns null for non-existent id', () {
      final found = provider.getMemberById('non-existent');
      expect(found, isNull);
    });

    test('can add multiple members', () async {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Emma',
          type: MemberType.child,
          age: 6,
          conditions: [],
          allergies: [],
        ),
        FamilyMember(
          id: '2',
          name: 'Dad',
          type: MemberType.adult,
          age: 40,
          conditions: [HealthCondition.diabetic],
          allergies: [],
        ),
        FamilyMember(
          id: '3',
          name: 'Mom',
          type: MemberType.pregnant,
          age: 35,
          conditions: [],
          allergies: [],
        ),
      ];

      for (final member in members) {
        await provider.addMember(member);
      }

      expect(provider.members, hasLength(3));
    });

    test('members list can be accessed', () async {
      final member = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: [],
      );

      await provider.addMember(member);

      // Verify members list is accessible and contains the added member
      expect(provider.members, isNotEmpty);
      expect(provider.members.first.id, equals('1'));
    });
  });

  group('FamilyMember Model Tests', () {
    test('FamilyMember can be created with all fields', () {
      final member = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [HealthCondition.diabetic],
        allergies: ['Peanuts', 'Tree Nuts'],
        dietaryPreferences: ['Vegetarian'],
      );

      expect(member.id, equals('1'));
      expect(member.name, equals('Emma'));
      expect(member.type, equals(MemberType.child));
      expect(member.age, equals(6));
      expect(member.conditions, contains(HealthCondition.diabetic));
      expect(member.allergies, hasLength(2));
    });

    test('FamilyMember toJson serializes correctly', () {
      final member = FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [HealthCondition.diabetic],
        allergies: ['Peanuts'],
      );

      final json = member.toJson();

      expect(json['id'], equals('1'));
      expect(json['name'], equals('Emma'));
      // Type is serialized as index
      expect(json['type'], equals(MemberType.child.index));
      expect(json['age'], equals(6));
      expect(json['allergies'], contains('Peanuts'));
    });

    test('FamilyMember fromJson deserializes correctly', () {
      final now = DateTime.now();
      final json = {
        'id': '1',
        'name': 'Emma',
        'type': MemberType.child.index,  // Index value
        'age': 6,
        'conditions': [HealthCondition.diabetic.index],  // Index values
        'allergies': ['Peanuts'],
        'dietaryPreferences': <String>[],
        'createdAt': now.toIso8601String(),
        'updatedAt': now.toIso8601String(),
      };

      final member = FamilyMember.fromJson(json);

      expect(member.id, equals('1'));
      expect(member.name, equals('Emma'));
      expect(member.type, equals(MemberType.child));
      expect(member.age, equals(6));
      expect(member.conditions, contains(HealthCondition.diabetic));
    });
  });

  group('MemberType Tests', () {
    test('MemberType has all expected values', () {
      expect(MemberType.values, contains(MemberType.toddler));
      expect(MemberType.values, contains(MemberType.child));
      expect(MemberType.values, contains(MemberType.adult));
      expect(MemberType.values, contains(MemberType.senior));
      expect(MemberType.values, contains(MemberType.pregnant));
    });

    test('MemberType displayName returns correct values', () {
      expect(MemberType.toddler.displayName, contains('Toddler'));
      expect(MemberType.child.displayName, contains('Child'));
      expect(MemberType.adult.displayName, equals('Adult'));
      expect(MemberType.senior.displayName, contains('Senior'));
      expect(MemberType.pregnant.displayName, contains('Pregnant'));
    });
  });

  group('HealthCondition Tests', () {
    test('HealthCondition has all expected values', () {
      expect(HealthCondition.values, contains(HealthCondition.diabetic));
      expect(HealthCondition.values, contains(HealthCondition.cardiac));
      expect(HealthCondition.values, contains(HealthCondition.hypertensive));
      expect(HealthCondition.values, contains(HealthCondition.obesity));
      expect(HealthCondition.values, contains(HealthCondition.celiac));
      expect(HealthCondition.values, contains(HealthCondition.lactoseIntolerant));
    });

    test('HealthCondition displayName returns correct values', () {
      expect(HealthCondition.diabetic.displayName, equals('Diabetic'));
      expect(HealthCondition.cardiac.displayName, contains('Cardiac'));
      expect(HealthCondition.hypertensive.displayName, contains('Hypertensive'));
      expect(HealthCondition.obesity.displayName, equals('Obesity'));
      expect(HealthCondition.celiac.displayName, contains('Celiac'));
      expect(HealthCondition.lactoseIntolerant.displayName, contains('Lactose'));
    });
  });

  group('Family Profile Statistics Tests', () {
    late FamilyProvider provider;

    setUp(() {
      provider = FamilyProvider();
    });

    test('counts members by type', () async {
      await provider.addMember(FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: [],
      ));
      await provider.addMember(FamilyMember(
        id: '2',
        name: 'Liam',
        type: MemberType.child,
        age: 8,
        conditions: [],
        allergies: [],
      ));
      await provider.addMember(FamilyMember(
        id: '3',
        name: 'Dad',
        type: MemberType.adult,
        age: 40,
        conditions: [],
        allergies: [],
      ));

      final childCount = provider.members
          .where((m) => m.type == MemberType.child)
          .length;
      final adultCount = provider.members
          .where((m) => m.type == MemberType.adult)
          .length;

      expect(childCount, equals(2));
      expect(adultCount, equals(1));
    });

    test('identifies members with health conditions', () async {
      await provider.addMember(FamilyMember(
        id: '1',
        name: 'Dad',
        type: MemberType.adult,
        age: 45,
        conditions: [HealthCondition.diabetic],
        allergies: [],
      ));
      await provider.addMember(FamilyMember(
        id: '2',
        name: 'Mom',
        type: MemberType.adult,
        age: 42,
        conditions: [],
        allergies: [],
      ));

      final membersWithConditions = provider.members
          .where((m) => m.conditions.isNotEmpty)
          .toList();

      expect(membersWithConditions, hasLength(1));
      expect(membersWithConditions.first.name, equals('Dad'));
    });

    test('identifies members with allergies', () async {
      await provider.addMember(FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: ['Peanuts', 'Tree Nuts'],
      ));
      await provider.addMember(FamilyMember(
        id: '2',
        name: 'Liam',
        type: MemberType.child,
        age: 8,
        conditions: [],
        allergies: [],
      ));

      final membersWithAllergies = provider.members
          .where((m) => m.allergies.isNotEmpty)
          .toList();

      expect(membersWithAllergies, hasLength(1));
      expect(membersWithAllergies.first.allergies, hasLength(2));
    });

    test('collects all unique allergies', () async {
      await provider.addMember(FamilyMember(
        id: '1',
        name: 'Emma',
        type: MemberType.child,
        age: 6,
        conditions: [],
        allergies: ['Peanuts', 'Tree Nuts'],
      ));
      await provider.addMember(FamilyMember(
        id: '2',
        name: 'Liam',
        type: MemberType.child,
        age: 8,
        conditions: [],
        allergies: ['Peanuts', 'Milk'],
      ));

      final allAllergies = provider.members
          .expand((m) => m.allergies)
          .toSet()
          .toList();

      expect(allAllergies, hasLength(3));
      expect(allAllergies, contains('Peanuts'));
      expect(allAllergies, contains('Tree Nuts'));
      expect(allAllergies, contains('Milk'));
    });
  });
}
