import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const category = "beverages,snacks,cereals";
    const response = await fetch(`https://world.openfoodfacts.org/api/v2/search?categories_tags_en=${category}&fields=product_name,ingredients_text&size=50`);
    const json = await response.json();

    const products = (json.products || []).map((p: any) => ({
      name: p.product_name || "Unnamed Product",
      ingredients: (p.ingredients_text || "").split(/,|\./).map((i: string) => i.trim()).filter(Boolean)
    }));

    res.status(200).json({ products });
  } catch (err) {
    console.error("OpenFoodFacts fetch error:", err);
    res.status(500).json({ error: "Failed to fetch products" });
  }
}