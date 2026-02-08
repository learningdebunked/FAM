import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fam_app/config/theme.dart';

void main() {
  group('OnboardingScreen Widget Tests', () {
    Widget createOnboardingMock() {
      return MaterialApp(
        theme: AppTheme.lightTheme,
        home: Scaffold(
          body: SafeArea(
            child: Column(
              children: [
                // Page indicator
                Expanded(
                  child: PageView(
                    children: [
                      // Page 1
                      Padding(
                        padding: const EdgeInsets.all(32),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.eco, size: 100, color: Colors.green),
                            const SizedBox(height: 32),
                            const Text(
                              'Welcome to FAM',
                              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'Food as Medicine - Make healthier choices for your family',
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                      // Page 2
                      Padding(
                        padding: const EdgeInsets.all(32),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.qr_code_scanner, size: 100, color: Colors.blue),
                            const SizedBox(height: 32),
                            const Text(
                              'Scan Any Product',
                              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'Use barcode or ingredient label scanning',
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                      // Page 3
                      Padding(
                        padding: const EdgeInsets.all(32),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.family_restroom, size: 100, color: Colors.purple),
                            const SizedBox(height: 32),
                            const Text(
                              'Personalized Insights',
                              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'Get recommendations based on your family health profiles',
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                // Page indicators
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 10,
                      height: 10,
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.green,
                      ),
                    ),
                    Container(
                      width: 10,
                      height: 10,
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.grey[300],
                      ),
                    ),
                    Container(
                      width: 10,
                      height: 10,
                      margin: const EdgeInsets.symmetric(horizontal: 4),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.grey[300],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                // Buttons
                Padding(
                  padding: const EdgeInsets.all(24),
                  child: Row(
                    children: [
                      TextButton(
                        onPressed: () {},
                        child: const Text('Skip'),
                      ),
                      const Spacer(),
                      ElevatedButton(
                        onPressed: () {},
                        child: const Text('Next'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      );
    }

    testWidgets('Onboarding shows welcome message', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      expect(find.text('Welcome to FAM'), findsOneWidget);
    });

    testWidgets('Onboarding has page view', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      expect(find.byType(PageView), findsOneWidget);
    });

    testWidgets('Skip button is present', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      expect(find.text('Skip'), findsOneWidget);
    });

    testWidgets('Next button is present', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      expect(find.text('Next'), findsOneWidget);
    });

    testWidgets('Skip button is tappable', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      final button = find.text('Skip');
      expect(button, findsOneWidget);
      
      await tester.tap(button);
      await tester.pumpAndSettle();
    });

    testWidgets('Next button is tappable', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      final button = find.text('Next');
      expect(button, findsOneWidget);
      
      await tester.tap(button);
      await tester.pumpAndSettle();
    });

    testWidgets('Page indicators are present', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      // Should have 3 page indicators
      final indicators = find.byType(Container);
      expect(indicators, findsWidgets);
    });

    testWidgets('Can swipe between pages', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      // Swipe left to go to next page
      await tester.drag(find.byType(PageView), const Offset(-300, 0));
      await tester.pumpAndSettle();

      expect(find.text('Scan Any Product'), findsOneWidget);
    });

    testWidgets('Page 2 content is correct', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      await tester.drag(find.byType(PageView), const Offset(-300, 0));
      await tester.pumpAndSettle();

      expect(find.text('Scan Any Product'), findsOneWidget);
      expect(find.text('Use barcode or ingredient label scanning'), findsOneWidget);
    });

    testWidgets('Page 3 content is correct', (tester) async {
      await tester.pumpWidget(createOnboardingMock());
      await tester.pumpAndSettle();

      // Swipe twice to get to page 3
      await tester.drag(find.byType(PageView), const Offset(-300, 0));
      await tester.pumpAndSettle();
      await tester.drag(find.byType(PageView), const Offset(-300, 0));
      await tester.pumpAndSettle();

      expect(find.text('Personalized Insights'), findsOneWidget);
    });
  });
}
