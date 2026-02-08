import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';

import 'package:fam_app/screens/home/home_screen.dart';
import 'package:fam_app/screens/home/widgets/home_dashboard.dart';
import 'package:fam_app/providers/family_provider.dart';
import 'package:fam_app/providers/product_provider.dart';
import 'package:fam_app/config/theme.dart';

void main() {
  group('HomeScreen Tests', () {
    late FamilyProvider familyProvider;
    late ProductProvider productProvider;

    setUp(() {
      familyProvider = FamilyProvider();
      productProvider = ProductProvider();
    });

    Widget createHomeScreen() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: familyProvider),
          ChangeNotifierProvider.value(value: productProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const HomeScreen(),
        ),
      );
    }

    testWidgets('HomeScreen renders correctly', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      // Bottom navigation should be present
      expect(find.byType(BottomNavigationBar), findsOneWidget);
    });

    testWidgets('Bottom navigation has 3 tabs', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Scan'), findsOneWidget);
      expect(find.text('Family'), findsOneWidget);
    });

    testWidgets('Home tab is selected by default', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      // Home dashboard content should be visible
      expect(find.text('Food as Medicine'), findsOneWidget);
    });

    testWidgets('Tapping Scan tab switches view', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Scan'));
      await tester.pumpAndSettle();

      expect(find.text('Scan Product'), findsOneWidget);
    });

    testWidgets('Tapping Family tab switches view', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Family'));
      await tester.pumpAndSettle();

      expect(find.text('Family Profile'), findsOneWidget);
    });

    testWidgets('Scan Food FAB is visible on Home tab', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      expect(find.text('Scan Food'), findsOneWidget);
      expect(find.byType(FloatingActionButton), findsOneWidget);
    });

    testWidgets('FAB tapping switches to Scan tab', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Scan Food'));
      await tester.pumpAndSettle();

      expect(find.text('Scan Product'), findsOneWidget);
    });

    testWidgets('FAB is hidden on non-Home tabs', (tester) async {
      await tester.pumpWidget(createHomeScreen());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Family'));
      await tester.pumpAndSettle();

      // FAB should not be visible on Family tab
      expect(find.text('Scan Food'), findsNothing);
    });
  });

  group('HomeDashboard Tests', () {
    late FamilyProvider familyProvider;
    late ProductProvider productProvider;

    setUp(() {
      familyProvider = FamilyProvider();
      productProvider = ProductProvider();
    });

    Widget createDashboard() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: familyProvider),
          ChangeNotifierProvider.value(value: productProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const HomeDashboard(),
        ),
      );
    }

    testWidgets('Dashboard renders welcome card', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      expect(find.text('Make Healthier Choices'), findsOneWidget);
    });

    testWidgets('Quick Actions section is present', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      expect(find.text('Quick Actions'), findsOneWidget);
      expect(find.text('Scan Barcode'), findsOneWidget);
      expect(find.text('Scan Label'), findsOneWidget);
      expect(find.text('Search'), findsOneWidget);
      expect(find.text('History'), findsOneWidget);
    });

    testWidgets('Family Profile section is present', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      expect(find.text('Family Profile'), findsOneWidget);
      expect(find.text('Manage'), findsOneWidget);
    });

    testWidgets('Recent Scans section is present', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      expect(find.text('Recent Scans'), findsOneWidget);
    });

    testWidgets('Search button opens dialog', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      await tester.tap(find.text('Search'));
      await tester.pumpAndSettle();

      expect(find.text('Search Products'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('History button opens bottom sheet', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      await tester.tap(find.text('History'));
      await tester.pumpAndSettle();

      expect(find.text('Scan History'), findsOneWidget);
    });

    testWidgets('Settings button is present in app bar', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.settings_outlined), findsOneWidget);
    });

    testWidgets('Empty family state shows setup prompt', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      expect(find.text('Set up your family profile'), findsOneWidget);
    });

    testWidgets('Empty history state shows prompt', (tester) async {
      await tester.pumpWidget(createDashboard());
      await tester.pumpAndSettle();

      expect(find.text('No scans yet'), findsOneWidget);
    });
  });
}
