# Food-as-Medicine Nudger (FAM)

A GenAI-powered web application that helps users make healthier grocery choices based on family health profiles and ingredient classification.

## 💡 Features
- ✅ Lifestyle question toggles (hypertension, diabetes, child safety, pregnancy)
- ✅ Live FAM scoring based on flagged ingredients
- ✅ Data sourced from OpenFoodFacts (beverages, snacks, cereals)
- ✅ Rule-based ingredient classification
- 🧠 Optional LLM-based classification for advanced analysis

## 🏗️ Architecture
- **Frontend**: React + Next.js
- **Backend**: Python FastAPI
- **UI**: shadcn/ui with Tailwind CSS
- **Data**: OpenFoodFacts API

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ (for frontend)
- Python 3.8+ (for backend)
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys if needed
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the project root:
   ```bash
   cd ..
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   The app will be available at `http://localhost:3000`

## 🔍 Classification Methods

### 1. Rule-based Classification
- Fast and free (no API costs)
- Works offline
- Limited to predefined list of ingredients
- Easy to maintain for common ingredients

### 2. LLM-based Classification (Optional)
- Uses OpenAI's GPT-4 model
- Can classify any ingredient, including novel or complex ones
- Provides detailed reasoning for classifications
- **Considerations**:
  - Requires an OpenAI API key
  - Incurs API costs (based on token usage)
  - Adds latency (API call to OpenAI's servers)
  - Recommended for fallback use when rule-based classification is insufficient

## 📁 Project Structure
```
/
├── backend/                  # Python FastAPI backend
│   ├── main.py              # Main FastAPI application
│   ├── requirements.txt      # Python dependencies
│   └── .env.example         # Environment variables template
├── pages/                   # Next.js pages
│   ├── index.tsx            # Main application page
│   └── _app.tsx             # Next.js app wrapper
├── public/                  # Static files
├── styles/                  # Global styles
├── utils/                   # Utility functions
│   ├── normalize.ts         # Rule-based classification
│   └── classifyWithLLM.ts   # LLM-based classification
└── README.md                # This file
```

## 📚 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation powered by Swagger UI.

### Available Endpoints
- `GET /api/products` - Fetch products from OpenFoodFacts
  - Query Parameters:
    - `category`: Comma-separated list of categories (default: "beverages,snacks,cereals")
    - `page_size`: Number of products to return (default: 50)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
