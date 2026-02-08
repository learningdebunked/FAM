import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../config/theme.dart';
import '../../providers/family_provider.dart';
import '../../providers/product_provider.dart';
import '../profile/family_profile_screen.dart';
import '../scanner/scanner_screen.dart';
import 'widgets/home_dashboard.dart';
import 'widgets/scan_history_list.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const HomeDashboard(),
    const ScannerScreen(),
    const FamilyProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() {
              _currentIndex = index;
            });
          },
          items: [
            BottomNavigationBarItem(
              icon: Icon(Icons.home_outlined, key: const Key('nav_home_icon')),
              activeIcon: Icon(Icons.home, key: const Key('nav_home_active_icon')),
              label: 'Home',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.qr_code_scanner_outlined, key: const Key('nav_scan_icon')),
              activeIcon: Icon(Icons.qr_code_scanner, key: const Key('nav_scan_active_icon')),
              label: 'Scan',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.family_restroom_outlined, key: const Key('nav_family_icon')),
              activeIcon: Icon(Icons.family_restroom, key: const Key('nav_family_active_icon')),
              label: 'Family',
            ),
          ],
        ),
      ),
      floatingActionButton: _currentIndex == 0
          ? FloatingActionButton.extended(
              onPressed: () {
                setState(() {
                  _currentIndex = 1;
                });
              },
              icon: const Icon(Icons.camera_alt),
              label: const Text('Scan Food'),
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
            )
          : null,
    );
  }
}
