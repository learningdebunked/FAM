import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../models/family_member.dart';
import '../../providers/family_provider.dart';

class FamilyProfileScreen extends StatelessWidget {
  const FamilyProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Family Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              _showInfoDialog(context);
            },
          ),
        ],
      ),
      body: Consumer<FamilyProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.members.isEmpty) {
            return _buildEmptyState(context);
          }

          return _buildMembersList(context, provider.members);
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          context.push('/add-member');
        },
        icon: const Icon(Icons.person_add),
        label: const Text('Add Member'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.family_restroom,
                size: 64,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'No Family Members Yet',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              'Add your family members to get personalized health insights when scanning food products.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 15,
                color: Colors.grey[600],
                height: 1.5,
              ),
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () {
                context.push('/add-member');
              },
              icon: const Icon(Icons.person_add),
              label: const Text('Add First Member'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMembersList(BuildContext context, List<FamilyMember> members) {
    // Group members by type
    final grouped = <MemberType, List<FamilyMember>>{};
    for (final member in members) {
      grouped.putIfAbsent(member.type, () => []).add(member);
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      physics: const AlwaysScrollableScrollPhysics(
        parent: BouncingScrollPhysics(),
      ),
      children: [
        _buildSummaryCard(members),
        const SizedBox(height: 20),
        ...grouped.entries.map((entry) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8),
                child: Row(
                  children: [
                    Text(
                      entry.key.icon,
                      style: const TextStyle(fontSize: 20),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      _getGroupTitle(entry.key),
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 2,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${entry.value.length}',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppColors.primary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              ...entry.value.map((member) => _MemberCard(member: member)),
              const SizedBox(height: 16),
            ],
          );
        }),
        const SizedBox(height: 80), // Space for FAB
      ],
    );
  }

  Widget _buildSummaryCard(List<FamilyMember> members) {
    final conditionsCount = members.fold<int>(
      0,
      (sum, m) => sum + m.conditions.length,
    );
    final allergiesCount = members.fold<int>(
      0,
      (sum, m) => sum + m.allergies.length,
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Family Overview',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _SummaryItem(
                    icon: Icons.people,
                    value: '${members.length}',
                    label: 'Members',
                    color: AppColors.primary,
                  ),
                ),
                Expanded(
                  child: _SummaryItem(
                    icon: Icons.medical_services,
                    value: '$conditionsCount',
                    label: 'Conditions',
                    color: AppColors.riskMedium,
                  ),
                ),
                Expanded(
                  child: _SummaryItem(
                    icon: Icons.warning_amber,
                    value: '$allergiesCount',
                    label: 'Allergies',
                    color: AppColors.riskHigh,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _getGroupTitle(MemberType type) {
    switch (type) {
      case MemberType.adult:
        return 'Adults';
      case MemberType.child:
        return 'Children';
      case MemberType.toddler:
        return 'Toddlers';
      case MemberType.senior:
        return 'Seniors';
      case MemberType.pregnant:
        return 'Pregnant';
    }
  }

  void _showInfoDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('About Family Profiles'),
        content: const Text(
          'Family profiles help us provide personalized health insights when you scan food products.\n\n'
          'Each member\'s age group, health conditions, and allergies are considered when analyzing ingredients.\n\n'
          'Your data is stored securely on your device and is never shared without your consent.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }
}

class _SummaryItem extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;

  const _SummaryItem({
    required this.icon,
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 20),
        ),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }
}

class _MemberCard extends StatelessWidget {
  final FamilyMember member;

  const _MemberCard({required this.member});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: () {
          context.push('/edit-member/${member.id}');
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: _getTypeColor(member.type).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    member.type.icon,
                    style: const TextStyle(fontSize: 24),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      member.name,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    if (member.conditions.isNotEmpty)
                      Wrap(
                        spacing: 4,
                        runSpacing: 4,
                        children: member.conditions.take(3).map((c) {
                          return Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.riskMedium.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              c.displayName.split(' ').first,
                              style: const TextStyle(
                                fontSize: 11,
                                color: AppColors.riskMedium,
                              ),
                            ),
                          );
                        }).toList(),
                      )
                    else
                      Text(
                        'No health conditions',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.grey[500],
                        ),
                      ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                onSelected: (value) {
                  if (value == 'edit') {
                    context.push('/edit-member/${member.id}');
                  } else if (value == 'delete') {
                    _confirmDelete(context, member);
                  }
                },
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'edit',
                    child: Row(
                      children: [
                        Icon(Icons.edit, size: 20),
                        SizedBox(width: 8),
                        Text('Edit'),
                      ],
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'delete',
                    child: Row(
                      children: [
                        Icon(Icons.delete, size: 20, color: Colors.red),
                        SizedBox(width: 8),
                        Text('Delete', style: TextStyle(color: Colors.red)),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getTypeColor(MemberType type) {
    switch (type) {
      case MemberType.adult:
        return AppColors.primary;
      case MemberType.child:
        return AppColors.child;
      case MemberType.toddler:
        return AppColors.child;
      case MemberType.senior:
        return AppColors.senior;
      case MemberType.pregnant:
        return AppColors.pregnant;
    }
  }

  void _confirmDelete(BuildContext context, FamilyMember member) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remove Member'),
        content: Text('Are you sure you want to remove ${member.name} from your family profile?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              context.read<FamilyProvider>().removeMember(member.id);
              Navigator.pop(context);
            },
            child: const Text(
              'Remove',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }
}
