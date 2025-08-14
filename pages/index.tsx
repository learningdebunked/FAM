import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import axios from "axios";

const healthQuestions = [
  { 
    key: "hypertensive", 
    text: "Any household member has high blood pressure?",
    icon: "💓",
    description: "Watching sodium and saturated fats"
  },
  { 
    key: "diabetic", 
    text: "Any diabetic or pre-diabetic family members?",
    icon: "🩸",
    description: "Monitoring sugar and carb intake"
  },
  { 
    key: "child", 
    text: "Do you shop for children under 12?",
    icon: "👶",
    description: "Avoiding artificial additives"
  },
  { 
    key: "pregnant", 
    text: "Is anyone currently pregnant?",
    icon: "🤰",
    description: "Special nutritional needs"
  },
  { 
    key: "fiber_focused", 
    text: "Prefer high-fiber or whole grain foods?",
    icon: "🌾",
    description: "Looking for whole grain options"
  }
];

const riskMap = {
  "high fructose corn syrup": ["diabetic"],
  "sugar": ["diabetic"],
  "corn syrup": ["diabetic"],
  "aspartame": ["child", "pregnant"],
  "sucralose": ["child", "pregnant"],
  "caffeine": ["child", "pregnant"],
  "sodium": ["hypertensive"],
  "salt": ["hypertensive"],
  "monosodium glutamate": ["child"],
  "msg": ["child"],
  "red 40 lake": ["child"],
  "yellow 6": ["child"],
  "caramel color": ["general"],
  "whole grain": ["fiber_focused", "positive"],
  "whole wheat": ["fiber_focused", "positive"],
  "oats": ["fiber_focused", "positive"],
  "fiber": ["fiber_focused", "positive"],
  "flaxseed": ["fiber_focused", "positive"]
};

const getRecommendationReason = (product, profileTags) => {
  const reasons = [];
  
  product.ingredients.forEach(ing => {
    const lowerIng = ing.toLowerCase();
    Object.entries(riskMap).forEach(([ingredient, tags]) => {
      if (lowerIng.includes(ingredient)) {
        const matchedTags = tags.filter(tag => profileTags.includes(tag));
        if (matchedTags.length > 0) {
          matchedTags.forEach(tag => {
            if (tag === 'positive') {
              reasons.push(`Contains beneficial ${ingredient}`);
            } else {
              reasons.push(`Contains ${ingredient} (${tag})`);
            }
          });
        }
      }
    });
  });
  
  return reasons.length > 0 ? [...new Set(reasons)] : ["No specific concerns detected"];
};

const evaluateProduct = (product, profileTags) => {
  let score = 50;
  let flagged = [];
  let benefits = [];
  
  product.ingredients.forEach((ing) => {
    const lowerIng = ing.toLowerCase();
    Object.entries(riskMap).forEach(([ingredient, tags]) => {
      if (lowerIng.includes(ingredient)) {
        tags.forEach((t) => {
          if (profileTags.includes(t)) {
            if (t === "positive") {
              score += 10;
              benefits.push(ingredient);
            } else {
              score -= 15;
              flagged.push(ing);
            }
          }
        });
      }
    });
  });
  
  score = Math.max(0, Math.min(100, score));
  const light = score >= 75 ? "🟢 Good" : score >= 50 ? "🟡 Okay" : "🔴 Risky";
  return { score, light, flagged, benefits };
};

export default function FAMNudger() {
  const [profile, setProfile] = useState({});
  const [results, setResults] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [showOnlyGreen, setShowOnlyGreen] = useState(false);

  const handleToggle = (key, value) => {
    setProfile({ ...profile, [key]: value });
    setShowRecommendations(false);
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
    if (profileTags.length === 0) {
      alert("Please select at least one health consideration");
      return;
    }
    
    let result = products
      .map((p) => {
        const evalResult = evaluateProduct(p, profileTags);
        const reasons = getRecommendationReason(p, profileTags);
        return { 
          ...p, 
          ...evalResult, 
          reasons,
          matchCount: reasons.filter(r => !r.includes("No specific")).length,
          isGreen: evalResult.flagged.length === 0 && evalResult.benefits.length > 0
        };
      })
      .sort((a, b) => {
        // Sort by score descending, then by number of matches
        if (a.score !== b.score) return b.score - a.score;
        return b.matchCount - a.matchCount;
      });

    // Filter for green products if the toggle is on
    if (showOnlyGreen) {
      result = result.filter(p => p.isGreen);
    }
      
    setResults(result);
    setShowRecommendations(true);
  };

  const getActiveProfileTags = () => {
    return Object.entries(profile)
      .filter(([_, value]) => value)
      .map(([key]) => key);
  };

  const activeTags = getActiveProfileTags();
  const hasSelections = activeTags.length > 0;

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Food-as-Medicine Recommender</h1>
        <p className="text-muted-foreground">
          Select your health considerations to get personalized food recommendations
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Your Health Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {healthQuestions.map((q) => (
            <div key={q.key} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-xl">{q.icon}</span>
                  <Label className="text-base" htmlFor={q.key}>
                    {q.text}
                  </Label>
                </div>
                <p className="text-sm text-muted-foreground">{q.description}</p>
              </div>
              <Switch
                id={q.key}
                checked={!!profile[q.key]}
                onCheckedChange={(val) => handleToggle(q.key, val)}
              />
            </div>
          ))}
          
          <div className="flex items-center justify-between p-3 rounded-lg">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="text-xl">🌿</span>
                <Label className="text-base" htmlFor="show-only-green">
                  Show only green (safe) products
                </Label>
              </div>
              <p className="text-sm text-muted-foreground">Display only products with no concerning ingredients</p>
            </div>
            <Switch
              id="show-only-green"
              checked={showOnlyGreen}
              onCheckedChange={setShowOnlyGreen}
            />
          </div>
          
          <Button 
            className="w-full mt-6 py-6 text-lg" 
            onClick={runNudge}
            disabled={loading || !hasSelections}
          >
            {loading ? (
              "Loading recommendations..."
            ) : (
              `Generate ${hasSelections ? activeTags.length : ''} ${hasSelections ? 'Personalized ' : ''}Recommendations`
            )}
          </Button>
        </CardContent>
      </Card>

      {showRecommendations && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Your Recommendations</h2>
            <div className="flex flex-wrap gap-2">
              {activeTags.map(tag => (
                <Badge key={tag} variant="secondary" className="text-sm">
                  {healthQuestions.find(q => q.key === tag)?.icon} {tag}
                </Badge>
              ))}
            </div>
          </div>
          
          {results.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground">No products match your current filters.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {results.map((r) => (
                <Card key={r.name} className="h-full flex flex-col">
                  <CardContent className="p-4 flex-grow flex flex-col">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-semibold line-clamp-2">{r.name}</h3>
                      <span className={`text-sm px-2 py-1 rounded-full ${
                        r.light.includes("Good") ? 'bg-green-100 text-green-800' :
                        r.light.includes("Okay") ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {r.light} ({r.score}%)
                      </span>
                    </div>
                    
                    <div className="mt-2 space-y-2 text-sm">
                      <div className="space-y-1">
                        {r.reasons.map((reason, i) => (
                          <div key={i} className="flex items-start">
                            <span className="mr-1">•</span>
                            <span className={reason.includes("beneficial") ? "text-green-600" : ""}>
                              {reason}
                            </span>
                          </div>
                        ))}
                      </div>
                      
                      {r.flagged.length > 0 && (
                        <div className="mt-2 p-2 bg-red-50 rounded-md">
                          <p className="text-xs font-medium text-red-800 mb-1">Considerations:</p>
                          <ul className="text-xs text-red-700 space-y-1">
                            {r.flagged.map((ing, i) => (
                              <li key={i} className="flex items-start">
                                <span className="mr-1">•</span>
                                <span>Contains {ing}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    
                    <div className="mt-4 pt-3 border-t text-xs text-muted-foreground">
                      <p className="font-medium">Ingredients:</p>
                      <p className="line-clamp-2">
                        {r.ingredients?.join(", ")}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
