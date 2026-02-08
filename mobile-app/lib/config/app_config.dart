class AppConfig {
  // Backend API URL - use 10.0.2.2 for Android emulator to reach localhost
  static const String backendBaseUrl = 'http://10.0.2.2:8000';
  
  // For iOS simulator, use localhost
  static const String backendBaseUrlIOS = 'http://localhost:8000';
  
  // Open Food Facts API
  static const String openFoodFactsBaseUrl = 'https://world.openfoodfacts.org/api/v2';
  
  // OpenAI API (for direct calls if needed)
  static const String openAiBaseUrl = 'https://api.openai.com/v1';
  
  // Feature flags
  static const bool useBackendForAnalysis = true;
  static const bool enableOfflineMode = false;
  
  // Get the appropriate backend URL based on platform
  static String getBackendUrl() {
    // For Android emulator, 10.0.2.2 maps to host's localhost
    // For iOS simulator, use localhost directly
    // In production, this would be your actual server URL
    return backendBaseUrl;
  }
}
