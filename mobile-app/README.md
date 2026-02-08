# Food as Medicine (FAM) App

A native iOS/Android app that transforms grocery shopping into a precision health intervention using AI-powered ingredient analysis and family health profiling.

Based on the research paper: **"Food-as-Medicine Recommender Systems: A Vision for Generative AI–Powered Grocery Guidance"** (AMICT 2025)

## Features

### 🏠 Family Health Profiles
- Add family members with different profiles (Adults, Children, Toddlers, Seniors, Pregnant)
- Track health conditions (Cardiac, Diabetic, Hypertensive, Celiac, etc.)
- Record allergies and dietary preferences
- Personalized risk assessment for each family member

### 📱 Label Scanning
- **Barcode Scanner**: Quick product lookup via barcode
- **OCR Scanner**: Capture ingredient lists from product labels
- **Manual Entry**: Type barcode or paste ingredients directly

### 🔬 AI-Powered Analysis
- LLM-based ingredient classification using OpenAI GPT-4
- Risk scoring per family member based on their health profile
- Flagged ingredients with explanations and evidence links
- Overall product health score (0-100)

### 🔄 Healthy Alternatives
- AI-suggested healthier product swaps
- Benefits comparison between products
- Score-based recommendations

### 👍 Feedback System
- Thumbs up/down on analysis results
- Detailed feedback categories for improvement
- Telemetry for continuous model improvement

## Tech Stack

- **Framework**: Flutter 3.x (Dart)
- **State Management**: Provider
- **Navigation**: go_router
- **Local Storage**: Hive + SharedPreferences
- **Networking**: Dio
- **Barcode Scanning**: mobile_scanner
- **OCR**: google_mlkit_text_recognition
- **Product Data**: Open Food Facts API
- **AI Analysis**: OpenAI GPT-4 API

## Project Structure

```
lib/
├── main.dart                 # App entry point
├── config/
│   ├── routes.dart          # Navigation routes
│   └── theme.dart           # App theming
├── models/
│   ├── family_member.dart   # Family member & health conditions
│   ├── product.dart         # Product & nutrition info
│   ├── analysis_result.dart # Analysis results & risk flags
│   └── feedback.dart        # User feedback model
├── providers/
│   ├── family_provider.dart  # Family state management
│   ├── product_provider.dart # Product & analysis state
│   └── feedback_provider.dart# Feedback state
├── screens/
│   ├── home/                # Home dashboard
│   ├── profile/             # Family profile management
│   ├── scanner/             # Barcode & OCR scanning
│   ├── analysis/            # Product analysis results
│   ├── alternatives/        # Healthy alternatives
│   ├── feedback/            # Feedback dialogs
│   └── onboarding/          # Onboarding flow
├── services/
│   ├── api_service.dart           # Base API client
│   ├── open_food_facts_service.dart # Product data API
│   ├── ingredient_analyzer_service.dart # LLM analysis
│   └── storage_service.dart       # Local storage
└── widgets/
    └── common/              # Reusable UI components
```

## Getting Started

### Prerequisites

- Flutter SDK 3.0+
- Dart SDK 3.0+
- Xcode (for iOS)
- Android Studio (for Android)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/learningdebunked/FAM.git
cd FAM-APP
```

2. Install dependencies:
```bash
flutter pub get
```

3. Configure API key:
   - Add your OpenAI API key in the app settings, or
   - Set environment variable: `OPENAI_API_KEY=your_key`

4. Run the app:
```bash
# iOS
flutter run -d ios

# Android
flutter run -d android
```

### Building for Production

```bash
# iOS
flutter build ios --release

# Android
flutter build apk --release
# or
flutter build appbundle --release
```

## Configuration

### OpenAI API Key

The app requires an OpenAI API key for ingredient analysis. You can:
1. Enter it in Settings within the app
2. Store it securely using the app's storage service

### Open Food Facts

The app uses the [Open Food Facts API](https://world.openfoodfacts.org/) for product data. No API key required.

## Risk Categories

The app flags ingredients based on these risk levels:

| Level | Color | Description |
|-------|-------|-------------|
| Safe | 🟢 Green | No known concerns |
| Low | 🟡 Yellow | Minor considerations |
| Medium | 🟠 Orange | Moderate concern for some groups |
| High | 🔴 Red | Significant concern |
| Critical | 🟣 Purple | Avoid for specific conditions |

## Key Ingredients Monitored

- **Artificial Sweeteners**: Aspartame, Sucralose
- **Artificial Dyes**: Red 40, Yellow 5, Blue 1
- **Sugars**: High Fructose Corn Syrup
- **Preservatives**: Sodium Nitrate/Nitrite, BHA/BHT
- **Fats**: Trans fats, Partially Hydrogenated Oils
- **Stimulants**: Caffeine
- **Additives**: MSG

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

1. Downer, S., et al. "Food is medicine: Actions to integrate food and nutrition into health care." BMJ, 2020.
2. Open Food Facts API Documentation
3. OpenAI API Documentation

## Acknowledgments

- Research paper authors: Kapil Poredy, Ajit Sahu
- Open Food Facts community
- Flutter and Dart teams
