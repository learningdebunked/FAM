import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:fam_app/providers/product_provider.dart';
import 'package:fam_app/config/theme.dart';

void main() {
  group('AlternativesScreen Widget Tests', () {
    late ProductProvider productProvider;

    setUp(() {
      productProvider = ProductProvider();
    });

    Widget createAlternativesMock({bool hasAlternatives = true}) {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: productProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: Scaffold(
            appBar: AppBar(
              title: const Text('Healthy Alternatives'),
            ),
            body: hasAlternatives
                ? ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      // Current product card
                      Card(
                        color: Colors.orange.withOpacity(0.05),
                        child: const ListTile(
                          leading: Icon(Icons.fastfood),
                          title: Text('Current Selection'),
                          subtitle: Text('Gummy Bears'),
                        ),
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'Healthier Alternatives',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      // Alternative card
                      Card(
                        child: InkWell(
                          onTap: () {},
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      width: 64,
                                      height: 64,
                                      decoration: BoxDecoration(
                                        color: Colors.grey[200],
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: const Icon(Icons.eco, color: Colors.green),
                                    ),
                                    const SizedBox(width: 16),
                                    const Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text('Organic Fruit Snacks', style: TextStyle(fontWeight: FontWeight.bold)),
                                          Text('Nature\'s Best'),
                                        ],
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.all(8),
                                      decoration: BoxDecoration(
                                        color: Colors.green.withOpacity(0.1),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: const Column(
                                        children: [
                                          Text('85', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.green)),
                                          Text('score', style: TextStyle(fontSize: 10, color: Colors.green)),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Container(
                                  padding: const EdgeInsets.all(12),
                                  decoration: BoxDecoration(
                                    color: Colors.green.withOpacity(0.05),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Row(
                                    children: [
                                      Icon(Icons.lightbulb_outline, color: Colors.green, size: 18),
                                      SizedBox(width: 8),
                                      Expanded(child: Text('No artificial dyes, made with real fruit')),
                                    ],
                                  ),
                                ),
                                const SizedBox(height: 12),
                                Wrap(
                                  spacing: 8,
                                  children: [
                                    Chip(
                                      label: const Text('No Dyes'),
                                      backgroundColor: Colors.green.withOpacity(0.1),
                                    ),
                                    Chip(
                                      label: const Text('Low Sugar'),
                                      backgroundColor: Colors.green.withOpacity(0.1),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.end,
                                  children: [
                                    TextButton.icon(
                                      onPressed: () {},
                                      icon: const Icon(Icons.analytics_outlined, size: 18),
                                      label: const Text('View Analysis'),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  )
                : Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.check_circle, size: 64, color: Colors.green),
                        const SizedBox(height: 24),
                        const Text('Great Choice!', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 12),
                        const Text('This product is already healthy'),
                        const SizedBox(height: 32),
                        OutlinedButton(
                          onPressed: () {},
                          child: const Text('Back to Analysis'),
                        ),
                      ],
                    ),
                  ),
          ),
        ),
      );
    }

    testWidgets('Screen has app bar with title', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('Healthy Alternatives'), findsOneWidget);
    });

    testWidgets('Current product card is displayed', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('Current Selection'), findsOneWidget);
      expect(find.text('Gummy Bears'), findsOneWidget);
    });

    testWidgets('Healthier Alternatives section header is present', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('Healthier Alternatives'), findsOneWidget);
    });

    testWidgets('Alternative card shows product name', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('Organic Fruit Snacks'), findsOneWidget);
    });

    testWidgets('Alternative card shows brand', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('Nature\'s Best'), findsOneWidget);
    });

    testWidgets('Alternative card shows score', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('85'), findsOneWidget);
      expect(find.text('score'), findsOneWidget);
    });

    testWidgets('Alternative card shows reason', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('No artificial dyes, made with real fruit'), findsOneWidget);
    });

    testWidgets('Alternative card shows benefits chips', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      expect(find.text('No Dyes'), findsOneWidget);
      expect(find.text('Low Sugar'), findsOneWidget);
    });

    testWidgets('View Analysis button is present and tappable', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      final button = find.text('View Analysis');
      expect(button, findsOneWidget);
      
      await tester.tap(button);
      await tester.pumpAndSettle();
    });

    testWidgets('Alternative card is tappable', (tester) async {
      await tester.pumpWidget(createAlternativesMock());
      await tester.pumpAndSettle();

      final card = find.text('Organic Fruit Snacks');
      expect(card, findsOneWidget);
      
      await tester.tap(card);
      await tester.pumpAndSettle();
    });

    testWidgets('Empty state shows Great Choice message', (tester) async {
      await tester.pumpWidget(createAlternativesMock(hasAlternatives: false));
      await tester.pumpAndSettle();

      expect(find.text('Great Choice!'), findsOneWidget);
      expect(find.text('This product is already healthy'), findsOneWidget);
    });

    testWidgets('Empty state has Back to Analysis button', (tester) async {
      await tester.pumpWidget(createAlternativesMock(hasAlternatives: false));
      await tester.pumpAndSettle();

      final button = find.text('Back to Analysis');
      expect(button, findsOneWidget);
      
      await tester.tap(button);
      await tester.pumpAndSettle();
    });
  });
}
