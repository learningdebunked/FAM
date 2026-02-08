class AppConstants {
  // App Info
  static const String appName = 'Food as Medicine';
  static const String appVersion = '1.0.0';
  
  // API Endpoints
  static const String openFoodFactsBaseUrl = 'https://world.openfoodfacts.org/api/v2';
  static const String openAiBaseUrl = 'https://api.openai.com/v1';
  
  // Storage Keys
  static const String familyMembersBox = 'family_members';
  static const String scanHistoryBox = 'scan_history';
  static const String feedbackBox = 'feedback';
  static const String onboardingCompleteKey = 'onboarding_complete';
  static const String apiKeyKey = 'openai_api_key';
  static const String darkModeKey = 'dark_mode';
  
  // Limits
  static const int maxScanHistoryItems = 100;
  static const int maxFamilyMembers = 20;
  static const int maxAllergies = 50;
  
  // Timeouts
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration llmTimeout = Duration(seconds: 60);
  
  // Cache
  static const Duration productCacheDuration = Duration(days: 7);
  static const Duration analysisCacheDuration = Duration(hours: 24);
  
  // Risk Thresholds
  static const double safeScoreThreshold = 80.0;
  static const double lowRiskScoreThreshold = 60.0;
  static const double mediumRiskScoreThreshold = 40.0;
  static const double highRiskScoreThreshold = 20.0;
  
  // Scoring Weights (from paper)
  static const double nutriScoreWeight = 0.3;      // α
  static const double riskFlagsWeight = 0.35;      // β
  static const double fitToGoalsWeight = 0.25;     // γ
  static const double budgetPenaltyWeight = 0.1;   // δ
}

class RiskIngredients {
  static const List<String> artificialSweeteners = [
    'aspartame',
    'sucralose',
    'saccharin',
    'acesulfame potassium',
    'acesulfame k',
    'neotame',
    'advantame',
  ];
  
  static const List<String> artificialDyes = [
    'red 40',
    'red 40 lake',
    'yellow 5',
    'yellow 6',
    'blue 1',
    'blue 2',
    'green 3',
    'fd&c red',
    'fd&c yellow',
    'fd&c blue',
    'e129',
    'e102',
    'e110',
    'e133',
  ];
  
  static const List<String> harmfulPreservatives = [
    'sodium nitrate',
    'sodium nitrite',
    'potassium nitrate',
    'potassium nitrite',
    'bha',
    'bht',
    'tbhq',
    'propyl gallate',
  ];
  
  static const List<String> harmfulFats = [
    'partially hydrogenated',
    'trans fat',
    'hydrogenated oil',
    'shortening',
  ];
  
  static const List<String> highSodiumIndicators = [
    'sodium',
    'salt',
    'msg',
    'monosodium glutamate',
    'sodium benzoate',
    'sodium phosphate',
  ];
  
  static const List<String> highSugarIndicators = [
    'high fructose corn syrup',
    'hfcs',
    'corn syrup',
    'dextrose',
    'maltose',
    'sucrose',
    'glucose syrup',
    'invert sugar',
  ];
  
  static const List<String> caffeineContaining = [
    'caffeine',
    'coffee',
    'guarana',
    'yerba mate',
    'green tea extract',
    'black tea extract',
  ];
}
