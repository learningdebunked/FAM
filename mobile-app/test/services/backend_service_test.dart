import 'package:flutter_test/flutter_test.dart';
import 'package:fam_app/models/family_member.dart';
import 'package:fam_app/models/analysis_result.dart';

void main() {
  group('Health Profile Building Tests', () {
    List<String> buildHealthProfiles(List<FamilyMember> members) {
      final profiles = <String>{};
      
      for (final member in members) {
        switch (member.type) {
          case MemberType.toddler:
            profiles.add('toddler');
            profiles.add('child');
            break;
          case MemberType.child:
            profiles.add('child');
            break;
          case MemberType.adult:
            profiles.add('adult');
            break;
          case MemberType.senior:
            profiles.add('senior');
            break;
          case MemberType.pregnant:
            profiles.add('pregnant');
            profiles.add('adult');
            break;
        }
        
        for (final condition in member.conditions) {
          switch (condition) {
            case HealthCondition.diabetic:
              profiles.add('diabetic');
              break;
            case HealthCondition.cardiac:
              profiles.add('cardiac');
              profiles.add('hypertensive');
              break;
            case HealthCondition.hypertensive:
              profiles.add('hypertensive');
              break;
            case HealthCondition.obesity:
              profiles.add('obesity');
              break;
            case HealthCondition.celiac:
              profiles.add('celiac');
              break;
            case HealthCondition.lactoseIntolerant:
              profiles.add('lactose_intolerant');
              break;
            default:
              break;
          }
        }
        
        for (final allergy in member.allergies) {
          profiles.add(allergy.toLowerCase());
        }
      }
      
      return profiles.toList();
    }

    test('builds profile for child member', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Emma',
          type: MemberType.child,
          age: 6,
          conditions: [],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('child'));
    });

    test('builds profile for toddler with child flag', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Baby',
          type: MemberType.toddler,
          age: 2,
          conditions: [],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('toddler'));
      expect(profiles, contains('child'));
    });

    test('builds profile for pregnant member', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Mom',
          type: MemberType.pregnant,
          age: 30,
          conditions: [],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('pregnant'));
      expect(profiles, contains('adult'));
    });

    test('builds profile for senior member', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Grandpa',
          type: MemberType.senior,
          age: 70,
          conditions: [],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('senior'));
    });

    test('includes diabetic condition', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Dad',
          type: MemberType.adult,
          age: 45,
          conditions: [HealthCondition.diabetic],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('adult'));
      expect(profiles, contains('diabetic'));
    });

    test('includes cardiac condition', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Dad',
          type: MemberType.adult,
          age: 55,
          conditions: [HealthCondition.cardiac],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('cardiac'));
      expect(profiles, contains('hypertensive'));
    });

    test('includes allergies in profile', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Emma',
          type: MemberType.child,
          age: 6,
          conditions: [],
          allergies: ['Peanuts', 'Tree Nuts'],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('peanuts'));
      expect(profiles, contains('tree nuts'));
    });

    test('combines multiple family members profiles', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Emma',
          type: MemberType.child,
          age: 6,
          conditions: [],
          allergies: ['Peanuts'],
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
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('child'));
      expect(profiles, contains('adult'));
      expect(profiles, contains('pregnant'));
      expect(profiles, contains('diabetic'));
      expect(profiles, contains('peanuts'));
    });

    test('deduplicates profiles', () {
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
          name: 'Liam',
          type: MemberType.child,
          age: 8,
          conditions: [],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles.where((p) => p == 'child').length, equals(1));
    });

    test('handles empty family members list', () {
      final profiles = buildHealthProfiles([]);
      expect(profiles, isEmpty);
    });

    test('handles member with multiple conditions', () {
      final members = [
        FamilyMember(
          id: '1',
          name: 'Dad',
          type: MemberType.adult,
          age: 55,
          conditions: [
            HealthCondition.diabetic,
            HealthCondition.hypertensive,
            HealthCondition.obesity,
          ],
          allergies: [],
        ),
      ];
      
      final profiles = buildHealthProfiles(members);
      expect(profiles, contains('diabetic'));
      expect(profiles, contains('hypertensive'));
      expect(profiles, contains('obesity'));
    });
  });

  group('RiskLevel Tests', () {
    test('RiskLevel has expected values', () {
      expect(RiskLevel.values, contains(RiskLevel.safe));
      expect(RiskLevel.values, contains(RiskLevel.low));
      expect(RiskLevel.values, contains(RiskLevel.medium));
      expect(RiskLevel.values, contains(RiskLevel.high));
      expect(RiskLevel.values, contains(RiskLevel.critical));
    });
  });

  group('FAM Score Interpretation Tests', () {
    String interpretScore(int score) {
      if (score >= 80) return 'safe';
      if (score >= 60) return 'low';
      if (score >= 40) return 'medium';
      if (score >= 20) return 'high';
      return 'critical';
    }

    test('score 85 is safe', () {
      expect(interpretScore(85), equals('safe'));
    });

    test('score 70 is low risk', () {
      expect(interpretScore(70), equals('low'));
    });

    test('score 50 is medium risk', () {
      expect(interpretScore(50), equals('medium'));
    });

    test('score 30 is high risk', () {
      expect(interpretScore(30), equals('high'));
    });

    test('score 15 is critical', () {
      expect(interpretScore(15), equals('critical'));
    });

    test('boundary score 80 is safe', () {
      expect(interpretScore(80), equals('safe'));
    });

    test('boundary score 60 is low', () {
      expect(interpretScore(60), equals('low'));
    });

    test('boundary score 40 is medium', () {
      expect(interpretScore(40), equals('medium'));
    });

    test('boundary score 20 is high', () {
      expect(interpretScore(20), equals('high'));
    });
  });

  group('Nutri-Score Interpretation Tests', () {
    String getNutriScoreDescription(String grade) {
      switch (grade) {
        case 'A':
          return 'Excellent nutritional quality';
        case 'B':
          return 'Good nutritional quality';
        case 'C':
          return 'Average nutritional quality';
        case 'D':
          return 'Poor nutritional quality';
        case 'E':
          return 'Very poor nutritional quality';
        default:
          return 'Unknown';
      }
    }

    test('Nutri-Score A description', () {
      expect(getNutriScoreDescription('A'), contains('Excellent'));
    });

    test('Nutri-Score B description', () {
      expect(getNutriScoreDescription('B'), contains('Good'));
    });

    test('Nutri-Score C description', () {
      expect(getNutriScoreDescription('C'), contains('Average'));
    });

    test('Nutri-Score D description', () {
      expect(getNutriScoreDescription('D'), contains('Poor'));
    });

    test('Nutri-Score E description', () {
      expect(getNutriScoreDescription('E'), contains('Very poor'));
    });
  });

  group('NOVA Group Interpretation Tests', () {
    String getNovaDescription(int group) {
      switch (group) {
        case 1:
          return 'Unprocessed or minimally processed foods';
        case 2:
          return 'Processed culinary ingredients';
        case 3:
          return 'Processed foods';
        case 4:
          return 'Ultra-processed food and drink products';
        default:
          return 'Unknown';
      }
    }

    test('NOVA Group 1 description', () {
      expect(getNovaDescription(1), contains('minimally processed'));
    });

    test('NOVA Group 2 description', () {
      expect(getNovaDescription(2), contains('culinary ingredients'));
    });

    test('NOVA Group 3 description', () {
      expect(getNovaDescription(3), contains('Processed foods'));
    });

    test('NOVA Group 4 description', () {
      expect(getNovaDescription(4), contains('Ultra-processed'));
    });
  });
}
