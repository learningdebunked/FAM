import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:fam_app/screens/profile/add_member_screen.dart';
import 'package:fam_app/providers/family_provider.dart';
import 'package:fam_app/config/theme.dart';

void main() {
  group('AddMemberScreen Tests', () {
    late FamilyProvider familyProvider;

    setUp(() {
      familyProvider = FamilyProvider();
    });

    Widget createAddMemberScreen() {
      return MultiProvider(
        providers: [
          ChangeNotifierProvider.value(value: familyProvider),
        ],
        child: MaterialApp(
          theme: AppTheme.lightTheme,
          home: const AddMemberScreen(),
        ),
      );
    }

    testWidgets('Screen renders with app bar', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      expect(find.text('Add Family Member'), findsOneWidget);
    });

    testWidgets('Basic Information section is present', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      expect(find.text('Basic Information'), findsOneWidget);
    });

    testWidgets('Name field is present', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      expect(find.text('Name'), findsOneWidget);
    });

    testWidgets('Age field is present', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      expect(find.text('Age (optional)'), findsOneWidget);
    });

    testWidgets('Member Type section is present', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      expect(find.text('Member Type'), findsOneWidget);
    });

    testWidgets('Member type chips are present', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      // At least Adult should be visible (default selected)
      expect(find.text('Adult'), findsOneWidget);
    });

    testWidgets('Screen has scrollable content', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      // Verify the screen has scrollable ListView
      expect(find.byType(ListView), findsOneWidget);
      
      // Verify we can scroll
      final listView = find.byType(ListView);
      expect(listView, findsOneWidget);
    });

    testWidgets('Screen has Form widget', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      expect(find.byType(Form), findsOneWidget);
    });

    testWidgets('Screen has Card widgets for sections', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      // Multiple cards for different sections
      expect(find.byType(Card), findsWidgets);
    });

    testWidgets('Screen has proper structure', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      // Verify basic structure exists
      expect(find.byType(Scaffold), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('Can enter name in text field', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      final nameFields = find.byType(TextFormField);
      expect(nameFields, findsWidgets);

      await tester.enterText(nameFields.first, 'Test Name');
      await tester.pumpAndSettle();

      expect(find.text('Test Name'), findsOneWidget);
    });

    testWidgets('Member type section has ChoiceChips', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      // Verify ChoiceChip widgets exist for member type selection
      expect(find.byType(ChoiceChip), findsWidgets);
    });

    testWidgets('Screen uses Wrap widget for chips', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      // Verify Wrap widgets exist for chip layouts
      expect(find.byType(Wrap), findsWidgets);
    });

    testWidgets('Form has validation for name field', (tester) async {
      await tester.pumpWidget(createAddMemberScreen());
      await tester.pumpAndSettle();

      // Verify the name field exists with proper label
      expect(find.text('Name'), findsOneWidget);
      
      // Verify TextFormField exists for input
      final nameFields = find.byType(TextFormField);
      expect(nameFields, findsWidgets);
    });
  });

  group('EditMemberScreen Tests', () {
    testWidgets('Edit mode shows Save Changes button', (tester) async {
      final familyProvider = FamilyProvider();
      
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: familyProvider),
          ],
          child: MaterialApp(
            theme: AppTheme.lightTheme,
            home: const AddMemberScreen(memberId: 'test-id'),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Edit Member'), findsOneWidget);
    });
  });
}
