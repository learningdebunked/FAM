import { OpenAI } from "openai";
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function classifyIngredientLLM(ingredient) {
  const prompt = `Classify the following food ingredient for health impact:

Ingredient: ${ingredient}

Return JSON like:
{
  "category": "added_sugar" | "preservative" | "artificial_color" | "positive" | "unknown",
  "risk_tags": ["child", "pregnant", "diabetic"],
  "reasoning": "High fructose corn syrup raises glycemic load..."
}`;

  const completion = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [
      { role: "system", content: "You are a nutrition and food safety expert." },
      { role: "user", content: prompt }
    ],
    temperature: 0.3
  });

  const responseText = completion.choices[0]?.message?.content || "";

  try {
    return JSON.parse(responseText);
  } catch {
    return { category: "unknown", risk_tags: [], reasoning: "Unparsable" };
  }
}