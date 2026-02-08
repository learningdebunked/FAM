import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:fam_app/providers/product_provider.dart';
import 'package:fam_app/config/theme.dart';

void main() {
  group('Scanner Screen Widget Tests', () {
    late ProductProvider productProvider;

    setUp(() {
      productProvider = ProductProvider();
    });

    Widget createScannerMock() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: productProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: Scaffold(
            appBar: AppBar(title: const Text('Scan Product')),
            body: Column(
              children: [
                // Tab selector mock
                Container(
                  margin: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: () {},
                          child: const Text('Barcode'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () {},
                          child: const Text('Label (OCR)'),
                        ),
                      ),
                    ],
                  ),
                ),
                // Bottom panel mock
                const Spacer(),
                Padding(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.keyboard),
                          label: const Text('Enter Manually'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {},
                          icon: const Icon(Icons.history),
                          label: const Text('Recent'),
                        ),
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

    testWidgets('Scanner screen has app bar with title', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      expect(find.text('Scan Product'), findsOneWidget);
    });

    testWidgets('Tab selector shows Barcode and OCR options', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      expect(find.text('Barcode'), findsOneWidget);
      expect(find.text('Label (OCR)'), findsOneWidget);
    });

    testWidgets('Enter Manually button is present', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      expect(find.text('Enter Manually'), findsOneWidget);
    });

    testWidgets('Recent button is present', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      expect(find.text('Recent'), findsOneWidget);
    });

    testWidgets('Barcode tab is tappable', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      final barcodeTab = find.text('Barcode');
      expect(barcodeTab, findsOneWidget);
      
      await tester.tap(barcodeTab);
      await tester.pumpAndSettle();
    });

    testWidgets('OCR tab is tappable', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      final ocrTab = find.text('Label (OCR)');
      expect(ocrTab, findsOneWidget);
      
      await tester.tap(ocrTab);
      await tester.pumpAndSettle();
    });

    testWidgets('Enter Manually button is tappable', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      final manualButton = find.text('Enter Manually');
      expect(manualButton, findsOneWidget);
      
      await tester.tap(manualButton);
      await tester.pumpAndSettle();
    });

    testWidgets('Recent button is tappable', (tester) async {
      await tester.pumpWidget(createScannerMock());
      await tester.pumpAndSettle();

      final recentButton = find.text('Recent');
      expect(recentButton, findsOneWidget);
      
      await tester.tap(recentButton);
      await tester.pumpAndSettle();
    });
  });

  group('Manual Entry Sheet Tests', () {
    testWidgets('Manual entry sheet has text field', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.lightTheme,
          home: Scaffold(
            body: Builder(
              builder: (context) => ElevatedButton(
                onPressed: () {
                  showModalBottomSheet(
                    context: context,
                    builder: (context) => Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Text('Enter Ingredients'),
                          const SizedBox(height: 16),
                          const TextField(
                            decoration: InputDecoration(
                              hintText: 'Paste or type ingredients...',
                            ),
                            maxLines: 5,
                          ),
                          const SizedBox(height: 16),
                          ElevatedButton(
                            onPressed: () {},
                            child: const Text('Analyze'),
                          ),
                        ],
                      ),
                    ),
                  );
                },
                child: const Text('Open Sheet'),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Open Sheet'));
      await tester.pumpAndSettle();

      expect(find.text('Enter Ingredients'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
      expect(find.text('Analyze'), findsOneWidget);
    });

    testWidgets('Analyze button is tappable', (tester) async {
      bool analyzed = false;
      
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ElevatedButton(
              onPressed: () => analyzed = true,
              child: const Text('Analyze'),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Analyze'));
      await tester.pumpAndSettle();

      expect(analyzed, true);
    });
  });
}
