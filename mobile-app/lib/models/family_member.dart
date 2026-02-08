import 'package:uuid/uuid.dart';

enum MemberType {
  adult,
  child,
  toddler,
  senior,
  pregnant,
}

enum HealthCondition {
  cardiac,
  diabetic,
  hypertensive,
  celiac,
  lactoseIntolerant,
  glutenSensitive,
  kidneyDisease,
  liverDisease,
  thyroid,
  gout,
  obesity,
  anemia,
  osteoporosis,
}

extension MemberTypeExtension on MemberType {
  String get displayName {
    switch (this) {
      case MemberType.adult:
        return 'Adult';
      case MemberType.child:
        return 'Child (6-12 years)';
      case MemberType.toddler:
        return 'Toddler (0-5 years)';
      case MemberType.senior:
        return 'Senior (50+ years)';
      case MemberType.pregnant:
        return 'Pregnant Woman';
    }
  }

  String get icon {
    switch (this) {
      case MemberType.adult:
        return '👤';
      case MemberType.child:
        return '🧒';
      case MemberType.toddler:
        return '👶';
      case MemberType.senior:
        return '👴';
      case MemberType.pregnant:
        return '🤰';
    }
  }
}

extension HealthConditionExtension on HealthCondition {
  String get displayName {
    switch (this) {
      case HealthCondition.cardiac:
        return 'Cardiac/Heart Disease';
      case HealthCondition.diabetic:
        return 'Diabetic';
      case HealthCondition.hypertensive:
        return 'Hypertensive (High BP)';
      case HealthCondition.celiac:
        return 'Celiac Disease';
      case HealthCondition.lactoseIntolerant:
        return 'Lactose Intolerant';
      case HealthCondition.glutenSensitive:
        return 'Gluten Sensitive';
      case HealthCondition.kidneyDisease:
        return 'Kidney Disease';
      case HealthCondition.liverDisease:
        return 'Liver Disease';
      case HealthCondition.thyroid:
        return 'Thyroid Disorder';
      case HealthCondition.gout:
        return 'Gout';
      case HealthCondition.obesity:
        return 'Obesity';
      case HealthCondition.anemia:
        return 'Anemia';
      case HealthCondition.osteoporosis:
        return 'Osteoporosis';
    }
  }

  String get description {
    switch (this) {
      case HealthCondition.cardiac:
        return 'Avoid high sodium, saturated fats, trans fats';
      case HealthCondition.diabetic:
        return 'Monitor sugar, carbs, glycemic index';
      case HealthCondition.hypertensive:
        return 'Limit sodium, caffeine, processed foods';
      case HealthCondition.celiac:
        return 'Strictly avoid gluten';
      case HealthCondition.lactoseIntolerant:
        return 'Avoid dairy products';
      case HealthCondition.glutenSensitive:
        return 'Reduce gluten intake';
      case HealthCondition.kidneyDisease:
        return 'Limit potassium, phosphorus, sodium';
      case HealthCondition.liverDisease:
        return 'Avoid alcohol, limit sodium';
      case HealthCondition.thyroid:
        return 'Monitor iodine, soy intake';
      case HealthCondition.gout:
        return 'Avoid high-purine foods';
      case HealthCondition.obesity:
        return 'Focus on calorie control, fiber';
      case HealthCondition.anemia:
        return 'Increase iron, vitamin B12, folate';
      case HealthCondition.osteoporosis:
        return 'Increase calcium, vitamin D';
    }
  }
}

class FamilyMember {
  final String id;
  final String name;
  final MemberType type;
  final int? age;
  final List<HealthCondition> conditions;
  final List<String> allergies;
  final List<String> dietaryPreferences;
  final DateTime createdAt;
  final DateTime updatedAt;

  FamilyMember({
    String? id,
    required this.name,
    required this.type,
    this.age,
    this.conditions = const [],
    this.allergies = const [],
    this.dietaryPreferences = const [],
    DateTime? createdAt,
    DateTime? updatedAt,
  })  : id = id ?? const Uuid().v4(),
        createdAt = createdAt ?? DateTime.now(),
        updatedAt = updatedAt ?? DateTime.now();

  FamilyMember copyWith({
    String? name,
    MemberType? type,
    int? age,
    List<HealthCondition>? conditions,
    List<String>? allergies,
    List<String>? dietaryPreferences,
  }) {
    return FamilyMember(
      id: id,
      name: name ?? this.name,
      type: type ?? this.type,
      age: age ?? this.age,
      conditions: conditions ?? this.conditions,
      allergies: allergies ?? this.allergies,
      dietaryPreferences: dietaryPreferences ?? this.dietaryPreferences,
      createdAt: createdAt,
      updatedAt: DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'type': type.index,
      'age': age,
      'conditions': conditions.map((c) => c.index).toList(),
      'allergies': allergies,
      'dietaryPreferences': dietaryPreferences,
      'createdAt': createdAt.toIso8601String(),
      'updatedAt': updatedAt.toIso8601String(),
    };
  }

  factory FamilyMember.fromJson(Map<String, dynamic> json) {
    return FamilyMember(
      id: json['id'] as String,
      name: json['name'] as String,
      type: MemberType.values[json['type'] as int],
      age: json['age'] as int?,
      conditions: (json['conditions'] as List<dynamic>)
          .map((c) => HealthCondition.values[c as int])
          .toList(),
      allergies: List<String>.from(json['allergies'] as List),
      dietaryPreferences: List<String>.from(json['dietaryPreferences'] as List),
      createdAt: DateTime.parse(json['createdAt'] as String),
      updatedAt: DateTime.parse(json['updatedAt'] as String),
    );
  }
}
