import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:fam_app/providers/family_provider.dart';
import 'package:fam_app/providers/product_provider.dart';
import 'package:fam_app/config/theme.dart';

void main() {
  group('FAMAnalysisScreen Widget Tests', () {
    late FamilyProvider familyProvider;
    late ProductProvider productProvider;

    setUp(() {
      familyProvider = FamilyProvider();
      productProvider = ProductProvider();
    });

    Widget createAnalysisMock() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: familyProvider),
          ChangeNotifierProvider.value(value: productProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: Scaffold(
            appBar: AppBar(
              title: const Text('Product Analysis'),
              actions: [
                IconButton(
                  icon: const Icon(Icons.share),
                  onPressed: () {},
                ),
              ],
            ),
            body: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // FAM Score Card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        children: [
                          const Text('FAM Score', style: TextStyle(fontSize: 16)),
                          const SizedBox(height: 8),
                          const Text('72', style: TextStyle(fontSize: 48, fontWeight: FontWeight.bold)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                            decoration: BoxDecoration(
                              color: Colors.orange.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Text('Medium Risk'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Nutri-Score
                  const Text('Nutri-Score', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Row(
                    children: ['A', 'B', 'C', 'D', 'E'].map((grade) {
                      final isSelected = grade == 'C';
                      return Container(
                        width: 40,
                        height: 40,
                        margin: const EdgeInsets.only(right: 4),
                        decoration: BoxDecoration(
                          color: isSelected ? Colors.orange : Colors.grey[200],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Center(
                          child: Text(
                            grade,
                            style: TextStyle(
                              color: isSelected ? Colors.white : Colors.grey,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 16),
                  // NOVA Group
                  const Text('NOVA Classification', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text('Group 4 - Ultra-processed'),
                  const SizedBox(height: 16),
                  // Flagged Ingredients
                  const Text('Flagged Ingredients', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.warning, color: Colors.red),
                      title: const Text('Red 40'),
                      subtitle: const Text('Artificial dye - High risk for children'),
                      trailing: IconButton(
                        icon: const Icon(Icons.info_outline),
                        onPressed: () {},
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Family Risks
                  const Text('Family Risk Assessment', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Card(
                    child: ListTile(
                      leading: const CircleAvatar(child: Text('👶')),
                      title: const Text('Emma (Child)'),
                      subtitle: const Text('2 concerns found'),
                      trailing: const Icon(Icons.chevron_right),
                    ),
                  ),
                  const SizedBox(height: 24),
                  // Action Buttons
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.swap_horiz),
                      label: const Text('Find Alternatives'),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () {},
                      icon: const Icon(Icons.feedback_outlined),
                      label: const Text('Give Feedback'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    testWidgets('Analysis screen has app bar with title', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.text('Product Analysis'), findsOneWidget);
    });

    testWidgets('Share button is present', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.share), findsOneWidget);
    });

    testWidgets('FAM Score is displayed', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.text('FAM Score'), findsOneWidget);
      expect(find.text('72'), findsOneWidget);
    });

    testWidgets('Risk level is displayed', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.text('Medium Risk'), findsOneWidget);
    });

    testWidgets('Nutri-Score section is present', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.text('Nutri-Score'), findsOneWidget);
    });

    testWidgets('NOVA Classification is displayed', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.text('NOVA Classification'), findsOneWidget);
      expect(find.text('Group 4 - Ultra-processed'), findsOneWidget);
    });

    testWidgets('Flagged Ingredients section is present', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.text('Flagged Ingredients'), findsOneWidget);
      expect(find.text('Red 40'), findsOneWidget);
    });

    testWidgets('Family Risk Assessment is present', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      expect(find.text('Family Risk Assessment'), findsOneWidget);
    });

    testWidgets('Find Alternatives button is present and tappable', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      final button = find.text('Find Alternatives');
      expect(button, findsOneWidget);
      
      await tester.tap(button);
      await tester.pumpAndSettle();
    });

    testWidgets('Give Feedback button is present and tappable', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      final button = find.text('Give Feedback');
      expect(button, findsOneWidget);
      
      await tester.tap(button);
      await tester.pumpAndSettle();
    });

    testWidgets('Ingredient info button is tappable', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      final infoButton = find.byIcon(Icons.info_outline);
      expect(infoButton, findsOneWidget);
      
      await tester.tap(infoButton);
      await tester.pumpAndSettle();
    });

    testWidgets('Family member card is tappable', (tester) async {
      await tester.pumpWidget(createAnalysisMock());
      await tester.pumpAndSettle();

      final memberCard = find.text('Emma (Child)');
      expect(memberCard, findsOneWidget);
    });
  });
}
