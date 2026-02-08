import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';

import 'package:fam_app/screens/profile/family_profile_screen.dart';
import 'package:fam_app/screens/profile/add_member_screen.dart';
import 'package:fam_app/providers/family_provider.dart';
import 'package:fam_app/config/theme.dart';

void main() {
  group('FamilyProfileScreen Tests', () {
    late FamilyProvider familyProvider;

    setUp(() {
      familyProvider = FamilyProvider();
    });

    Widget createFamilyProfileScreen() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: familyProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const FamilyProfileScreen(),
        ),
      );
    }

    testWidgets('Screen renders with app bar', (tester) async {
      await tester.pumpWidget(createFamilyProfileScreen());
      await tester.pumpAndSettle();

      expect(find.text('Family Profile'), findsOneWidget);
    });

    testWidgets('Info button is present in app bar', (tester) async {
      await tester.pumpWidget(createFamilyProfileScreen());
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.info_outline), findsOneWidget);
    });

    testWidgets('Info button shows dialog when tapped', (tester) async {
      await tester.pumpWidget(createFamilyProfileScreen());
      await tester.pumpAndSettle();

      await tester.tap(find.byIcon(Icons.info_outline));
      await tester.pumpAndSettle();

      expect(find.text('About Family Profiles'), findsOneWidget);
      expect(find.text('Got it'), findsOneWidget);
    });

    testWidgets('Add Member FAB is present', (tester) async {
      await tester.pumpWidget(createFamilyProfileScreen());
      await tester.pumpAndSettle();

      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.text('Add Member'), findsWidgets);
    });

    testWidgets('Empty state shows setup prompt', (tester) async {
      await tester.pumpWidget(createFamilyProfileScreen());
      await tester.pumpAndSettle();

      expect(find.text('No Family Members Yet'), findsOneWidget);
      expect(find.text('Add First Member'), findsOneWidget);
    });

    testWidgets('Add First Member button is tappable', (tester) async {
      bool navigated = false;
      
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: familyProvider),
          ],
          child: MaterialApp.router(
            routerConfig: GoRouter(
              routes: [
                GoRoute(
                  path: '/',
                  builder: (context, state) => const FamilyProfileScreen(),
                ),
                GoRoute(
                  path: '/add-member',
                  builder: (context, state) {
                    navigated = true;
                    return const AddMemberScreen();
                  },
                ),
              ],
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Add First Member'));
      await tester.pumpAndSettle();

      expect(navigated, true);
    });

    testWidgets('FAB navigates to add member screen', (tester) async {
      bool navigated = false;
      
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: familyProvider),
          ],
          child: MaterialApp.router(
            routerConfig: GoRouter(
              routes: [
                GoRoute(
                  path: '/',
                  builder: (context, state) => const FamilyProfileScreen(),
                ),
                GoRoute(
                  path: '/add-member',
                  builder: (context, state) {
                    navigated = true;
                    return const AddMemberScreen();
                  },
                ),
              ],
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Find and tap the FAB
      final fab = find.byType(FloatingActionButton);
      await tester.tap(fab);
      await tester.pumpAndSettle();

      expect(navigated, true);
    });
  });
}
