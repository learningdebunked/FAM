import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../screens/home/home_screen.dart';
import '../screens/profile/family_profile_screen.dart';
import '../screens/profile/add_member_screen.dart';
import '../screens/scanner/scanner_screen.dart';
import '../screens/analysis/product_analysis_screen.dart';
import '../screens/alternatives/alternatives_screen.dart';
import '../screens/onboarding/onboarding_screen.dart';
import '../screens/settings/settings_screen.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
    GoRoute(
      path: '/onboarding',
      builder: (context, state) => const OnboardingScreen(),
    ),
    GoRoute(
      path: '/family-profile',
      builder: (context, state) => const FamilyProfileScreen(),
    ),
    GoRoute(
      path: '/add-member',
      builder: (context, state) => const AddMemberScreen(),
    ),
    GoRoute(
      path: '/edit-member/:id',
      builder: (context, state) {
        final memberId = state.pathParameters['id']!;
        return AddMemberScreen(memberId: memberId);
      },
    ),
    GoRoute(
      path: '/scanner',
      builder: (context, state) => const ScannerScreen(),
    ),
    GoRoute(
      path: '/analysis/:productId',
      builder: (context, state) {
        final productId = state.pathParameters['productId']!;
        return ProductAnalysisScreen(productId: productId);
      },
    ),
    GoRoute(
      path: '/alternatives/:productId',
      builder: (context, state) {
        final productId = state.pathParameters['productId']!;
        return AlternativesScreen(productId: productId);
      },
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
  ],
);
