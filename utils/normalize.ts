export const classifyIngredient = (ingredient: string) => {
  const lower = ingredient.toLowerCase();

  const riskMap: Record<string, string[]> = {
    "high fructose corn syrup": ["diabetic"],
    "aspartame": ["child", "pregnant"],
    "caffeine": ["child", "pregnant"],
    "salt": ["hypertensive"],
    "monosodium glutamate": ["child"],
    "red 40 lake": ["child"],
    "yellow 6": ["child"],
    "caramel color": ["general"],
    "whole grain oats": ["positive"]
  };

  for (const key in riskMap) {
    if (lower.includes(key)) {
      return riskMap[key];
    }
  }

  return [];
};