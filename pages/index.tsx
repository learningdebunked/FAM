import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import axios from "axios";

const healthQuestions = [
  { key: "hypertensive", text: "Any household member has high blood pressure?" },
  { key: "diabetic", text: "Any diabetic or pre-diabetic family members?" },
  { key: "child", text: "Do you shop for children under 12?" },
  { key: "pregnant", text: "Is anyone currently pregnant?" },
  { key: "fiber_focused", text: "Prefer high-fiber or whole grain foods?" }
];

const riskMap = {
  "high fructose corn syrup": ["diabetic"],
  aspartame: ["child", "pregnant"],
  caffeine: ["child", "pregnant"],
  salt: ["hypertensive"],
  "monosodium glutamate": ["child"],
  "red 40 lake": ["child"],
  "yellow 6": ["child"],
  "caramel color": ["general"],
  "whole grain oats": ["positive"]
};

const evaluateProduct = (product, profileTags) => {
  let score = 50;
  let flagged = [];
  product.ingredients.forEach((ing) => {
    const tags = riskMap[ing.toLowerCase()] || [];
    tags.forEach((t) => {
      if (profileTags.includes(t)) {
        if (t === "positive") score += 25;
        else {
          score -= 10;
          flagged.push(ing);
        }
      }
    });
  });
  score = Math.max(0, Math.min(100, score));
  const light = score >= 75 ? "🟢 Good" : score >= 50 ? "🟡 Okay" : "🔴 Risky";
  return { score, light, flagged };
};

export default function FAMNudger() {
  const [profile, setProfile] = useState({});
  const [results, setResults] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleToggle = (key, value) => {
    setProfile({ ...profile, [key]: value });
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get("http://localhost:8000/api/products");
      setProducts(response.data.products);
    } catch (err) {
      console.error("Error fetching product data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const runNudge = () => {
    const profileTags = Object.keys(profile).filter((k) => profile[k]);
    const result = products.map((p) => {
      const evalResult = evaluateProduct(p, profileTags);
      return { ...p, ...evalResult };
    });
    setResults(result);
  };

  return (
    <div className="p-6 space-y-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold">Food-as-Medicine Recommender</h2>
      <Card>
        <CardContent className="space-y-4 py-4">
          {healthQuestions.map((q) => (
            <div key={q.key} className="flex items-center justify-between">
              <Label>{q.text}</Label>
              <Switch
                checked={!!profile[q.key]}
                onCheckedChange={(val) => handleToggle(q.key, val)}
              />
            </div>
          ))}
          <Button disabled={loading} onClick={runNudge}>
            {loading ? "Loading products..." : "Generate Recommendations"}
          </Button>
        </CardContent>
      </Card>
      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((r) => (
            <Card key={r.name}>
              <CardContent className="py-4">
                <h3 className="text-lg font-semibold">{r.name}</h3>
                <p className="text-sm text-muted-foreground">
                  Ingredients: {r.ingredients?.join(", ")}
                </p>
                <p className="mt-1">FAM Score: {r.score} ({r.light})</p>
                {r.flagged.length > 0 && (
                  <p className="text-sm text-red-600">
                    ⚠ Flagged for: {r.flagged.join(", ")}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
