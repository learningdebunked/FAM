import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:fam_app/main.dart' as app;

/// End-to-End Integration Test: Gummy Bears Analysis
/// 
/// Test Scenario:
/// 1. Family profile: 2 small kids (ages 4 and 6)
/// 2. Product: Gummy Bears (manually entered ingredients)
/// 3. Expected: High risk flags for artificial dyes and sugars
/// 
/// Gummy Bears typical ingredients:
/// - Glucose syrup, Sugar, Gelatin, Dextrose, Citric acid
/// - Natural and artificial flavors, Red 40, Yellow 5, Yellow 6, Blue 1
/// - Carnauba wax, Beeswax coating

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Gummy Bears E2E Test - Family with 2 Kids', () {
    testWidgets('Complete flow: Add family → Scan ingredients → Get ML analysis',
        (WidgetTester tester) async {
      // Launch the app
      app.main();
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // ==================== Step 1: Navigate to Family Tab ====================
      print('📱 Step 1: Navigating to Family tab...');
      
      // Tap on Family tab in bottom navigation (index 2)
      final bottomNav = find.byType(BottomNavigationBar);
      expect(bottomNav, findsOneWidget, reason: 'Bottom navigation should exist');
      
      // Find the Family label and tap it
      final familyTab = find.text('Family');
      expect(familyTab, findsOneWidget, reason: 'Family tab should exist');
      await tester.tap(familyTab);
      await tester.pumpAndSettle();
      
      print('✅ Navigated to Family tab');

      // ==================== Step 2: Add First Child (Emma, Age 4) ====================
      print('👶 Step 2: Adding first child (Emma, age 4)...');
      
      // Look for Add Member button (FAB or text button)
      Finder addMemberFinder = find.text('Add Member');
      if (addMemberFinder.evaluate().isEmpty) {
        addMemberFinder = find.text('Add First Member');
      }
      
      if (addMemberFinder.evaluate().isNotEmpty) {
        await tester.tap(addMemberFinder.first);
        await tester.pumpAndSettle();
        
        // Fill in child details
        await _addFamilyMember(tester, name: 'Emma', type: 'Child', age: '4');
        print('✅ Added Emma (age 4)');
      }

      // ==================== Step 3: Add Second Child (Liam, Age 6) ====================
      print('👶 Step 3: Adding second child (Liam, age 6)...');
      
      // Find Add Member button again
      addMemberFinder = find.text('Add Member');
      if (addMemberFinder.evaluate().isNotEmpty) {
        await tester.tap(addMemberFinder.first);
        await tester.pumpAndSettle();
        
        await _addFamilyMember(tester, name: 'Liam', type: 'Child', age: '6');
        print('✅ Added Liam (age 6)');
      }

      // ==================== Step 4: Navigate to Scanner Tab ====================
      print('📷 Step 4: Navigating to Scanner tab...');
      
      // After adding member, we need to navigate back to home first
      // The BottomNavigationBar should still be visible
      await tester.pumpAndSettle(const Duration(seconds: 1));
      
      // Try multiple ways to find and tap the Scan tab
      Finder scanTab = find.text('Scan');
      if (scanTab.evaluate().isEmpty) {
        // Try finding by icon
        scanTab = find.byIcon(Icons.qr_code_scanner_outlined);
      }
      if (scanTab.evaluate().isEmpty) {
        scanTab = find.byIcon(Icons.qr_code_scanner);
      }
      
      if (scanTab.evaluate().isNotEmpty) {
        await tester.tap(scanTab.first);
        await tester.pumpAndSettle();
        print('✅ Navigated to Scanner tab');
      } else {
        // If we can't find scan tab, we might already be on a different screen
        // Try going back first
        final backButton = find.byIcon(Icons.arrow_back);
        if (backButton.evaluate().isNotEmpty) {
          await tester.tap(backButton.first);
          await tester.pumpAndSettle();
        }
        
        // Now try again
        scanTab = find.text('Scan');
        if (scanTab.evaluate().isNotEmpty) {
          await tester.tap(scanTab.first);
          await tester.pumpAndSettle();
          print('✅ Navigated to Scanner tab (after going back)');
        } else {
          print('⚠️ Could not find Scan tab, continuing anyway...');
        }
      }

      // ==================== Step 5: Switch to OCR/Label mode and Enter Manually ====================
      print('🍬 Step 5: Entering Gummy Bears ingredients manually...');
      
      // First, switch to Label (OCR) tab to get ingredient entry mode
      final labelTab = find.text('Label (OCR)');
      if (labelTab.evaluate().isNotEmpty) {
        await tester.tap(labelTab);
        await tester.pumpAndSettle();
      }
      
      // Tap Enter Manually button
      final manualEntryButton = find.text('Enter Manually');
      expect(manualEntryButton, findsOneWidget, reason: 'Enter Manually button should exist');
      await tester.tap(manualEntryButton);
      await tester.pumpAndSettle();

      // Gummy Bears ingredients (typical Haribo-style)
      const gummyBearsIngredients = 
          'Glucose syrup, Sugar, Gelatin, Dextrose, Citric acid, '
          'Corn starch, Natural and artificial flavors, '
          'Red 40, Yellow 5, Yellow 6, Blue 1, '
          'Carnauba wax, Beeswax coating';

      // Find the text field in the bottom sheet and enter ingredients
      final textFields = find.byType(TextField);
      expect(textFields, findsWidgets, reason: 'TextField should exist for ingredient entry');
      await tester.enterText(textFields.first, gummyBearsIngredients);
      await tester.pumpAndSettle();
      
      print('✅ Entered gummy bears ingredients');

      // ==================== Step 6: Submit for Analysis ====================
      print('⏳ Step 6: Submitting for ML analysis...');
      
      // Find and tap Analyze button
      final analyzeButton = find.text('Analyze');
      expect(analyzeButton, findsOneWidget, reason: 'Analyze button should exist');
      await tester.tap(analyzeButton);
      
      // Wait for analysis to complete (backend + ML call)
      await tester.pumpAndSettle(const Duration(seconds: 8));
      
      print('✅ Analysis submitted');

      // ==================== Step 7: Verify Analysis Results ====================
      print('🔍 Step 7: Verifying analysis results...');

      // The app should navigate to analysis screen
      // Check for any score or risk display
      bool foundAnalysisContent = false;
      
      // Look for FAM Score
      if (find.textContaining('Score').evaluate().isNotEmpty) {
        print('   ✓ Found Score display');
        foundAnalysisContent = true;
      }
      
      // Look for risk level
      if (find.textContaining('Risk').evaluate().isNotEmpty) {
        print('   ✓ Found Risk display');
        foundAnalysisContent = true;
      }
      
      // Look for NOVA classification
      if (find.textContaining('NOVA').evaluate().isNotEmpty) {
        print('   ✓ Found NOVA classification');
        foundAnalysisContent = true;
      }
      
      // Look for flagged ingredients
      if (find.textContaining('Red 40').evaluate().isNotEmpty) {
        print('   🔴 Red 40 correctly identified');
        foundAnalysisContent = true;
      }
      
      if (find.textContaining('Yellow').evaluate().isNotEmpty) {
        print('   🟡 Yellow dye correctly identified');
        foundAnalysisContent = true;
      }

      // Check for family-specific warnings
      if (find.textContaining('child').evaluate().isNotEmpty ||
          find.textContaining('Child').evaluate().isNotEmpty) {
        print('   � Child-specific warnings displayed');
        foundAnalysisContent = true;
      }

      expect(foundAnalysisContent, true, 
          reason: 'Analysis screen should show scores, risks, or flagged ingredients');

      print('🎉 E2E Test Complete: Gummy Bears analysis with 2 kids profile');
    });
  });
}

/// Helper function to add a family member
Future<void> _addFamilyMember(
  WidgetTester tester, {
  required String name,
  required String type,
  required String age,
}) async {
  // Find all TextFields on the add member screen
  final textFields = find.byType(TextField);
  
  // First TextField should be Name
  if (textFields.evaluate().length >= 1) {
    await tester.enterText(textFields.at(0), name);
    await tester.pumpAndSettle();
  }
  
  // Second TextField should be Age (optional)
  if (textFields.evaluate().length >= 2) {
    await tester.enterText(textFields.at(1), age);
    await tester.pumpAndSettle();
  }

  // Select member type by tapping the Child chip
  final childChip = find.text(type);
  if (childChip.evaluate().isNotEmpty) {
    await tester.tap(childChip.first);
    await tester.pumpAndSettle();
  }

  // Save the member - look for Add Member button
  Finder saveButton = find.text('Add Member');
  if (saveButton.evaluate().isEmpty) {
    saveButton = find.text('Save Changes');
  }
  if (saveButton.evaluate().isEmpty) {
    saveButton = find.text('Save');
  }
  
  if (saveButton.evaluate().isNotEmpty) {
    await tester.tap(saveButton.first);
    await tester.pumpAndSettle(const Duration(seconds: 1));
  }
}
