import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fam_app/config/theme.dart';

void main() {
  group('SettingsScreen Widget Tests', () {
    Widget createSettingsMock() {
      return MaterialApp(
        theme: AppTheme.lightTheme,
        home: Scaffold(
          appBar: AppBar(
            title: const Text('Settings'),
          ),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // API Key Section
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.key, size: 20),
                          SizedBox(width: 8),
                          Text('OpenAI API Key', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        obscureText: true,
                        decoration: InputDecoration(
                          hintText: 'sk-...',
                          prefixIcon: const Icon(Icons.vpn_key_outlined),
                          suffixIcon: IconButton(
                            icon: const Icon(Icons.visibility),
                            onPressed: () {},
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: () {},
                          child: const Text('Save API Key'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              // About Section
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.info_outline, size: 20),
                          SizedBox(width: 8),
                          Text('About', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 16),
                      const Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Version'),
                          Text('1.0.0'),
                        ],
                      ),
                      const Divider(height: 24),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.description_outlined),
                        title: const Text('Privacy Policy'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {},
                      ),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.gavel_outlined),
                        title: const Text('Terms of Service'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {},
                      ),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.code),
                        title: const Text('Open Source Licenses'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {},
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              // Data Section
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.storage, size: 20),
                          SizedBox(width: 8),
                          Text('Data Management', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 16),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.history),
                        title: const Text('Clear Scan History'),
                        subtitle: const Text('Remove all scanned products'),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () {},
                      ),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.delete_forever, color: Colors.red),
                        title: const Text('Delete All Data', style: TextStyle(color: Colors.red)),
                        subtitle: const Text('Remove all app data'),
                        trailing: const Icon(Icons.chevron_right, color: Colors.red),
                        onTap: () {},
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    testWidgets('Screen has app bar with title', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      expect(find.text('Settings'), findsOneWidget);
    });

    testWidgets('API Key section is present', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      expect(find.text('OpenAI API Key'), findsOneWidget);
    });

    testWidgets('API Key text field is present', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('Save API Key button is present', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      expect(find.text('Save API Key'), findsOneWidget);
    });

    testWidgets('Visibility toggle button is present', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.visibility), findsOneWidget);
    });

    testWidgets('About section is present', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      expect(find.text('About'), findsOneWidget);
    });

    testWidgets('Version info is displayed', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      expect(find.text('Version'), findsOneWidget);
      expect(find.text('1.0.0'), findsOneWidget);
    });

    testWidgets('Privacy Policy option is present and tappable', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      final tile = find.text('Privacy Policy');
      expect(tile, findsOneWidget);
      
      await tester.tap(tile);
      await tester.pumpAndSettle();
    });

    testWidgets('Terms of Service option is present and tappable', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      final tile = find.text('Terms of Service');
      expect(tile, findsOneWidget);
      
      await tester.tap(tile);
      await tester.pumpAndSettle();
    });

    testWidgets('Open Source Licenses option is present and tappable', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      final tile = find.text('Open Source Licenses');
      expect(tile, findsOneWidget);
      
      await tester.tap(tile);
      await tester.pumpAndSettle();
    });

    testWidgets('Data Management section is present', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      // Scroll down to find Data Management section
      await tester.scrollUntilVisible(
        find.text('Data Management'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      expect(find.text('Data Management'), findsOneWidget);
    });

    testWidgets('Clear Scan History option is present and tappable', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      // Scroll down to find the option
      await tester.scrollUntilVisible(
        find.text('Clear Scan History'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      final tile = find.text('Clear Scan History');
      expect(tile, findsOneWidget);
      
      await tester.tap(tile);
      await tester.pumpAndSettle();
    });

    testWidgets('Delete All Data option is present and tappable', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      // Scroll down to find the option
      await tester.scrollUntilVisible(
        find.text('Delete All Data'),
        200,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      final tile = find.text('Delete All Data');
      expect(tile, findsOneWidget);
      
      await tester.tap(tile);
      await tester.pumpAndSettle();
    });

    testWidgets('Save API Key button is tappable', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      final button = find.text('Save API Key');
      expect(button, findsOneWidget);
      
      await tester.tap(button);
      await tester.pumpAndSettle();
    });

    testWidgets('Can enter text in API key field', (tester) async {
      await tester.pumpWidget(createSettingsMock());
      await tester.pumpAndSettle();

      final textField = find.byType(TextField);
      await tester.enterText(textField, 'sk-test-key');
      await tester.pumpAndSettle();

      expect(find.text('sk-test-key'), findsOneWidget);
    });
  });
}
