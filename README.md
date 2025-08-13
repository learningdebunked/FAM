# Food-as-Medicine Nudger (FAM)

A GenAI-powered React + Next.js prototype to nudge users toward healthier grocery choices based on family health profiles and ingredient classification.

## 💡 Features
- ✅ Lifestyle question toggles (hypertension, diabetes, child safety, pregnancy)
- ✅ Live FAM scoring based on flagged ingredients
- ✅ Data sourced from OpenFoodFacts (beverages, snacks, cereals)
- ✅ Easily extendable with LLM-based classification

## 🛠 Technologies
- React + Next.js
- shadcn/ui (Tailwind UI system)
- OpenFoodFacts API
- Ingredient normalizer (rule-based + LLM-ready)

## 📦 Setup
```bash
git clone https://github.com/your-username/fam-nudger.git
cd fam-nudger
npm install
npm run dev
```

## 📁 Structure
```
/pages
  index.tsx               ← UI & logic
  /api/openfoodfacts.ts   ← Fetches real-world product data
/utils
  normalize.ts            ← Ingredient → risk classification
  classifyWithLLM.ts      ← Optional LLM fallback
```
