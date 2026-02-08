import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../models/family_member.dart';
import '../../providers/family_provider.dart';

class AddMemberScreen extends StatefulWidget {
  final String? memberId;

  const AddMemberScreen({super.key, this.memberId});

  @override
  State<AddMemberScreen> createState() => _AddMemberScreenState();
}

class _AddMemberScreenState extends State<AddMemberScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _ageController = TextEditingController();
  final _allergyController = TextEditingController();

  MemberType _selectedType = MemberType.adult;
  List<HealthCondition> _selectedConditions = [];
  List<String> _allergies = [];

  bool get isEditing => widget.memberId != null;

  @override
  void initState() {
    super.initState();
    if (isEditing) {
      _loadMember();
    }
  }

  void _loadMember() {
    final provider = context.read<FamilyProvider>();
    final member = provider.getMemberById(widget.memberId!);
    if (member != null) {
      _nameController.text = member.name;
      _ageController.text = member.age?.toString() ?? '';
      _selectedType = member.type;
      _selectedConditions = List.from(member.conditions);
      _allergies = List.from(member.allergies);
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _ageController.dispose();
    _allergyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(isEditing ? 'Edit Member' : 'Add Family Member'),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          physics: const AlwaysScrollableScrollPhysics(
            parent: BouncingScrollPhysics(),
          ),
          children: [
            _buildBasicInfoSection(),
            const SizedBox(height: 24),
            _buildMemberTypeSection(),
            const SizedBox(height: 24),
            _buildHealthConditionsSection(),
            const SizedBox(height: 24),
            _buildAllergiesSection(),
            const SizedBox(height: 32),
            _buildSaveButton(),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildBasicInfoSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Basic Information',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Name',
                hintText: 'Enter name',
                prefixIcon: Icon(Icons.person_outline),
              ),
              textCapitalization: TextCapitalization.words,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter a name';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _ageController,
              decoration: const InputDecoration(
                labelText: 'Age (optional)',
                hintText: 'Enter age',
                prefixIcon: Icon(Icons.cake_outlined),
              ),
              keyboardType: TextInputType.number,
              validator: (value) {
                if (value != null && value.isNotEmpty) {
                  final age = int.tryParse(value);
                  if (age == null || age < 0 || age > 120) {
                    return 'Please enter a valid age';
                  }
                }
                return null;
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMemberTypeSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Member Type',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Select the category that best describes this family member',
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: MemberType.values.map((type) {
                final isSelected = _selectedType == type;
                return ChoiceChip(
                  label: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(type.icon),
                      const SizedBox(width: 6),
                      Text(
                        type.displayName,
                        style: TextStyle(
                          color: isSelected ? AppColors.primary : Colors.black87,
                          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                    ],
                  ),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) {
                      setState(() {
                        _selectedType = type;
                      });
                    }
                  },
                  backgroundColor: Colors.grey[100],
                  selectedColor: AppColors.primaryLight.withOpacity(0.3),
                  checkmarkColor: AppColors.primary,
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHealthConditionsSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Health Conditions',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (_selectedConditions.isNotEmpty)
                  TextButton(
                    onPressed: () {
                      setState(() {
                        _selectedConditions.clear();
                      });
                    },
                    child: const Text('Clear All'),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Select any health conditions to get personalized food recommendations',
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: HealthCondition.values.map((condition) {
                final isSelected = _selectedConditions.contains(condition);
                return FilterChip(
                  label: Text(
                    condition.displayName,
                    style: TextStyle(
                      color: isSelected ? AppColors.riskMedium : Colors.black87,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                  selected: isSelected,
                  onSelected: (selected) {
                    setState(() {
                      if (selected) {
                        _selectedConditions.add(condition);
                      } else {
                        _selectedConditions.remove(condition);
                      }
                    });
                  },
                  backgroundColor: Colors.grey[100],
                  selectedColor: AppColors.riskMedium.withOpacity(0.2),
                  checkmarkColor: AppColors.riskMedium,
                );
              }).toList(),
            ),
            if (_selectedConditions.isNotEmpty) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.05),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: AppColors.primary.withOpacity(0.2),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(
                          Icons.info_outline,
                          size: 16,
                          color: AppColors.primary,
                        ),
                        SizedBox(width: 8),
                        Text(
                          'Dietary Considerations',
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ..._selectedConditions.map((c) => Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Text(
                            '• ${c.description}',
                            style: const TextStyle(fontSize: 13),
                          ),
                        )),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAllergiesSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Allergies & Intolerances',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Add any food allergies or intolerances',
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _allergyController,
                    decoration: const InputDecoration(
                      hintText: 'e.g., Peanuts, Shellfish',
                      prefixIcon: Icon(Icons.warning_amber_outlined),
                    ),
                    textCapitalization: TextCapitalization.words,
                    onSubmitted: (_) => _addAllergy(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _addAllergy,
                  icon: const Icon(Icons.add),
                  style: IconButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                  ),
                ),
              ],
            ),
            if (_allergies.isNotEmpty) ...[
              const SizedBox(height: 16),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _allergies.map((allergy) {
                  return Chip(
                    label: Text(
                      allergy,
                      style: TextStyle(
                        color: AppColors.riskHigh,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    deleteIcon: const Icon(Icons.close, size: 18),
                    onDeleted: () {
                      setState(() {
                        _allergies.remove(allergy);
                      });
                    },
                    backgroundColor: AppColors.riskHigh.withOpacity(0.1),
                    deleteIconColor: AppColors.riskHigh,
                    side: BorderSide(color: AppColors.riskHigh.withOpacity(0.3)),
                  );
                }).toList(),
              ),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                'Peanuts',
                'Tree Nuts',
                'Milk',
                'Eggs',
                'Wheat',
                'Soy',
                'Fish',
                'Shellfish',
              ].where((a) => !_allergies.contains(a)).map((suggestion) {
                return ActionChip(
                  label: Text(
                    suggestion,
                    style: const TextStyle(
                      color: Colors.black87,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  avatar: Icon(Icons.add, size: 16, color: AppColors.primary),
                  backgroundColor: Colors.grey[100],
                  side: BorderSide(color: Colors.grey[300]!),
                  onPressed: () {
                    setState(() {
                      _allergies.add(suggestion);
                    });
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  void _addAllergy() {
    final allergy = _allergyController.text.trim();
    if (allergy.isNotEmpty && !_allergies.contains(allergy)) {
      setState(() {
        _allergies.add(allergy);
        _allergyController.clear();
      });
    }
  }

  Widget _buildSaveButton() {
    return Consumer<FamilyProvider>(
      builder: (context, provider, child) {
        return ElevatedButton(
          onPressed: provider.isLoading ? null : _saveMember,
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: provider.isLoading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  )
                : Text(isEditing ? 'Save Changes' : 'Add Member'),
          ),
        );
      },
    );
  }

  void _saveMember() {
    if (!_formKey.currentState!.validate()) return;

    final provider = context.read<FamilyProvider>();
    final member = FamilyMember(
      id: widget.memberId,
      name: _nameController.text.trim(),
      type: _selectedType,
      age: int.tryParse(_ageController.text),
      conditions: _selectedConditions,
      allergies: _allergies,
    );

    if (isEditing) {
      provider.updateMember(member);
    } else {
      provider.addMember(member);
    }

    context.pop();

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          isEditing
              ? '${member.name} updated successfully'
              : '${member.name} added to family',
        ),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }
}
