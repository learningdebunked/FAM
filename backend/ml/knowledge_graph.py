"""
Food-Health Knowledge Graph
Captures relationships between ingredients, health conditions, and outcomes

This enables:
1. Reasoning about WHY an ingredient is bad for a condition
2. Finding alternatives that avoid specific risks
3. Explaining recommendations with evidence chains
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RelationType(Enum):
    """Types of relationships in the knowledge graph"""
    CONTAINS = "contains"  # Product -> Ingredient
    CAUSES = "causes"  # Ingredient -> Health Effect
    AFFECTS = "affects"  # Health Effect -> Health Condition
    ALTERNATIVE_TO = "alternative_to"  # Ingredient -> Ingredient
    SIMILAR_TO = "similar_to"  # Product -> Product
    CATEGORY_OF = "category_of"  # Category -> Product
    SAFE_FOR = "safe_for"  # Ingredient -> Health Profile
    RISKY_FOR = "risky_for"  # Ingredient -> Health Profile


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph"""
    id: str
    node_type: str  # ingredient, product, condition, effect, profile
    name: str
    properties: Dict = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return self.id == other.id


@dataclass
class KnowledgeEdge:
    """An edge in the knowledge graph"""
    source_id: str
    target_id: str
    relation: RelationType
    properties: Dict = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)  # URLs or citations
    confidence: float = 1.0


class FoodHealthKnowledgeGraph:
    """
    Knowledge graph for food-health relationships
    
    Enables:
    - Ingredient → Health Effect → Condition reasoning
    - Evidence-based explanations
    - Alternative ingredient discovery
    """
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        self.adjacency: Dict[str, List[KnowledgeEdge]] = {}  # node_id -> outgoing edges
        self.reverse_adjacency: Dict[str, List[KnowledgeEdge]] = {}  # node_id -> incoming edges
        
        # Initialize with base knowledge
        self._initialize_base_knowledge()
    
    def _initialize_base_knowledge(self):
        """Initialize with curated food-health knowledge"""
        
        # ==================== Health Conditions ====================
        conditions = [
            ("condition:diabetes", "Diabetes", {"type": "metabolic"}),
            ("condition:hypertension", "Hypertension", {"type": "cardiovascular"}),
            ("condition:heart_disease", "Heart Disease", {"type": "cardiovascular"}),
            ("condition:obesity", "Obesity", {"type": "metabolic"}),
            ("condition:adhd", "ADHD/Hyperactivity", {"type": "neurological"}),
            ("condition:cancer_risk", "Cancer Risk", {"type": "oncological"}),
            ("condition:gut_issues", "Gut Microbiome Disruption", {"type": "digestive"}),
            ("condition:allergic_reaction", "Allergic Reaction", {"type": "immune"}),
        ]
        
        for cid, name, props in conditions:
            self.add_node(KnowledgeNode(cid, "condition", name, props))
        
        # ==================== Health Profiles ====================
        profiles = [
            ("profile:child", "Child", {"age_range": "2-12"}),
            ("profile:toddler", "Toddler", {"age_range": "0-2"}),
            ("profile:pregnant", "Pregnant", {"special": True}),
            ("profile:senior", "Senior", {"age_range": "65+"}),
            ("profile:diabetic", "Diabetic", {"condition": "diabetes"}),
            ("profile:hypertensive", "Hypertensive", {"condition": "hypertension"}),
            ("profile:cardiac", "Cardiac Patient", {"condition": "heart_disease"}),
        ]
        
        for pid, name, props in profiles:
            self.add_node(KnowledgeNode(pid, "profile", name, props))
        
        # ==================== Health Effects ====================
        effects = [
            ("effect:blood_sugar_spike", "Blood Sugar Spike", {}),
            ("effect:insulin_resistance", "Insulin Resistance", {}),
            ("effect:blood_pressure_increase", "Blood Pressure Increase", {}),
            ("effect:inflammation", "Inflammation", {}),
            ("effect:hyperactivity", "Hyperactivity", {}),
            ("effect:carcinogenic", "Carcinogenic Potential", {}),
            ("effect:gut_disruption", "Gut Microbiome Disruption", {}),
            ("effect:metabolic_disruption", "Metabolic Disruption", {}),
            ("effect:cardiovascular_stress", "Cardiovascular Stress", {}),
            ("effect:neurotoxicity", "Neurotoxicity", {}),
        ]
        
        for eid, name, props in effects:
            self.add_node(KnowledgeNode(eid, "effect", name, props))
        
        # ==================== Ingredients ====================
        ingredients = [
            # Artificial Sweeteners
            ("ing:aspartame", "Aspartame", {"category": "artificial_sweetener", "e_number": "E951"}),
            ("ing:sucralose", "Sucralose", {"category": "artificial_sweetener", "e_number": "E955"}),
            ("ing:saccharin", "Saccharin", {"category": "artificial_sweetener", "e_number": "E954"}),
            ("ing:acesulfame_k", "Acesulfame Potassium", {"category": "artificial_sweetener", "e_number": "E950"}),
            
            # Artificial Dyes
            ("ing:red_40", "Red 40", {"category": "artificial_dye", "e_number": "E129"}),
            ("ing:yellow_5", "Yellow 5 (Tartrazine)", {"category": "artificial_dye", "e_number": "E102"}),
            ("ing:yellow_6", "Yellow 6", {"category": "artificial_dye", "e_number": "E110"}),
            ("ing:blue_1", "Blue 1", {"category": "artificial_dye", "e_number": "E133"}),
            
            # Preservatives
            ("ing:sodium_nitrate", "Sodium Nitrate", {"category": "preservative", "e_number": "E251"}),
            ("ing:sodium_nitrite", "Sodium Nitrite", {"category": "preservative", "e_number": "E250"}),
            ("ing:bha", "BHA", {"category": "preservative", "e_number": "E320"}),
            ("ing:bht", "BHT", {"category": "preservative", "e_number": "E321"}),
            ("ing:tbhq", "TBHQ", {"category": "preservative", "e_number": "E319"}),
            ("ing:sodium_benzoate", "Sodium Benzoate", {"category": "preservative", "e_number": "E211"}),
            
            # Sugars
            ("ing:hfcs", "High Fructose Corn Syrup", {"category": "high_sugar"}),
            ("ing:corn_syrup", "Corn Syrup", {"category": "high_sugar"}),
            
            # Fats
            ("ing:trans_fat", "Trans Fat", {"category": "harmful_fat"}),
            ("ing:partially_hydrogenated", "Partially Hydrogenated Oil", {"category": "harmful_fat"}),
            
            # Others
            ("ing:msg", "MSG (Monosodium Glutamate)", {"category": "flavor_enhancer", "e_number": "E621"}),
            ("ing:caffeine", "Caffeine", {"category": "stimulant"}),
            
            # Healthy Alternatives
            ("ing:stevia", "Stevia", {"category": "natural_sweetener", "safe": True}),
            ("ing:monk_fruit", "Monk Fruit", {"category": "natural_sweetener", "safe": True}),
            ("ing:olive_oil", "Olive Oil", {"category": "healthy_fat", "safe": True}),
            ("ing:avocado_oil", "Avocado Oil", {"category": "healthy_fat", "safe": True}),
        ]
        
        for iid, name, props in ingredients:
            self.add_node(KnowledgeNode(iid, "ingredient", name, props))
        
        # ==================== Relationships ====================
        
        # Artificial Sweeteners → Effects → Conditions
        self._add_ingredient_risk_chain(
            "ing:aspartame",
            ["effect:metabolic_disruption", "effect:gut_disruption"],
            ["condition:diabetes", "condition:obesity"],
            ["profile:child", "profile:pregnant", "profile:diabetic"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/28198207/"]
        )
        
        self._add_ingredient_risk_chain(
            "ing:sucralose",
            ["effect:gut_disruption", "effect:insulin_resistance"],
            ["condition:diabetes", "condition:gut_issues"],
            ["profile:child", "profile:diabetic"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/31226297/"]
        )
        
        # Artificial Dyes → Effects → Conditions
        self._add_ingredient_risk_chain(
            "ing:red_40",
            ["effect:hyperactivity", "effect:allergic_reaction"],
            ["condition:adhd", "condition:allergic_reaction"],
            ["profile:child", "profile:toddler"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/21933378/"]
        )
        
        self._add_ingredient_risk_chain(
            "ing:yellow_5",
            ["effect:hyperactivity", "effect:allergic_reaction"],
            ["condition:adhd", "condition:allergic_reaction"],
            ["profile:child", "profile:toddler"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/21933378/"]
        )
        
        # Preservatives → Effects → Conditions
        self._add_ingredient_risk_chain(
            "ing:sodium_nitrate",
            ["effect:carcinogenic"],
            ["condition:cancer_risk"],
            ["profile:pregnant", "profile:cardiac"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/28487287/"]
        )
        
        self._add_ingredient_risk_chain(
            "ing:sodium_nitrite",
            ["effect:carcinogenic"],
            ["condition:cancer_risk"],
            ["profile:pregnant", "profile:cardiac"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/28487287/"]
        )
        
        # High Sugar → Effects → Conditions
        self._add_ingredient_risk_chain(
            "ing:hfcs",
            ["effect:blood_sugar_spike", "effect:insulin_resistance", "effect:inflammation"],
            ["condition:diabetes", "condition:obesity", "condition:heart_disease"],
            ["profile:diabetic", "profile:cardiac"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/23594708/"]
        )
        
        # Trans Fat → Effects → Conditions
        self._add_ingredient_risk_chain(
            "ing:trans_fat",
            ["effect:inflammation", "effect:cardiovascular_stress"],
            ["condition:heart_disease", "condition:obesity"],
            ["profile:cardiac", "profile:hypertensive"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/16611951/"]
        )
        
        self._add_ingredient_risk_chain(
            "ing:partially_hydrogenated",
            ["effect:inflammation", "effect:cardiovascular_stress"],
            ["condition:heart_disease"],
            ["profile:cardiac", "profile:hypertensive"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/16611951/"]
        )
        
        # Caffeine → Effects → Conditions
        self._add_ingredient_risk_chain(
            "ing:caffeine",
            ["effect:blood_pressure_increase"],
            ["condition:hypertension"],
            ["profile:pregnant", "profile:hypertensive", "profile:child"],
            evidence=["https://pubmed.ncbi.nlm.nih.gov/28675917/"]
        )
        
        # ==================== Alternatives ====================
        # Sweetener alternatives
        self.add_edge(KnowledgeEdge("ing:aspartame", "ing:stevia", RelationType.ALTERNATIVE_TO))
        self.add_edge(KnowledgeEdge("ing:aspartame", "ing:monk_fruit", RelationType.ALTERNATIVE_TO))
        self.add_edge(KnowledgeEdge("ing:sucralose", "ing:stevia", RelationType.ALTERNATIVE_TO))
        self.add_edge(KnowledgeEdge("ing:hfcs", "ing:stevia", RelationType.ALTERNATIVE_TO))
        
        # Fat alternatives
        self.add_edge(KnowledgeEdge("ing:trans_fat", "ing:olive_oil", RelationType.ALTERNATIVE_TO))
        self.add_edge(KnowledgeEdge("ing:partially_hydrogenated", "ing:olive_oil", RelationType.ALTERNATIVE_TO))
        self.add_edge(KnowledgeEdge("ing:partially_hydrogenated", "ing:avocado_oil", RelationType.ALTERNATIVE_TO))
        
        # Safe ingredients for profiles
        for safe_ing in ["ing:stevia", "ing:monk_fruit", "ing:olive_oil", "ing:avocado_oil"]:
            for profile in ["profile:child", "profile:pregnant", "profile:diabetic", "profile:cardiac"]:
                self.add_edge(KnowledgeEdge(safe_ing, profile, RelationType.SAFE_FOR))
    
    def _add_ingredient_risk_chain(self, ingredient_id: str, effect_ids: List[str],
                                   condition_ids: List[str], profile_ids: List[str],
                                   evidence: List[str] = None):
        """Add a complete risk chain: Ingredient → Effects → Conditions, Ingredient → Profiles"""
        # Ingredient causes effects
        for effect_id in effect_ids:
            self.add_edge(KnowledgeEdge(
                ingredient_id, effect_id, RelationType.CAUSES,
                evidence=evidence or []
            ))
        
        # Effects affect conditions
        for effect_id in effect_ids:
            for condition_id in condition_ids:
                self.add_edge(KnowledgeEdge(
                    effect_id, condition_id, RelationType.AFFECTS
                ))
        
        # Ingredient is risky for profiles
        for profile_id in profile_ids:
            self.add_edge(KnowledgeEdge(
                ingredient_id, profile_id, RelationType.RISKY_FOR,
                evidence=evidence or []
            ))
    
    def add_node(self, node: KnowledgeNode):
        """Add a node to the graph"""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []
        if node.id not in self.reverse_adjacency:
            self.reverse_adjacency[node.id] = []
    
    def add_edge(self, edge: KnowledgeEdge):
        """Add an edge to the graph"""
        self.edges.append(edge)
        
        if edge.source_id not in self.adjacency:
            self.adjacency[edge.source_id] = []
        self.adjacency[edge.source_id].append(edge)
        
        if edge.target_id not in self.reverse_adjacency:
            self.reverse_adjacency[edge.target_id] = []
        self.reverse_adjacency[edge.target_id].append(edge)
    
    def get_ingredient_risks(self, ingredient_name: str) -> Dict:
        """
        Get all risks associated with an ingredient
        
        Returns:
            Dict with effects, conditions, and risky profiles
        """
        # Find ingredient node
        ingredient_id = None
        ingredient_lower = ingredient_name.lower()
        
        for node_id, node in self.nodes.items():
            if node.node_type == "ingredient":
                if ingredient_lower in node.name.lower() or ingredient_lower in node_id:
                    ingredient_id = node_id
                    break
        
        if not ingredient_id:
            return {"found": False, "ingredient": ingredient_name}
        
        node = self.nodes[ingredient_id]
        
        # Get effects (CAUSES edges)
        effects = []
        for edge in self.adjacency.get(ingredient_id, []):
            if edge.relation == RelationType.CAUSES:
                target = self.nodes.get(edge.target_id)
                if target:
                    effects.append({
                        "id": target.id,
                        "name": target.name,
                        "evidence": edge.evidence
                    })
        
        # Get risky profiles (RISKY_FOR edges)
        risky_profiles = []
        for edge in self.adjacency.get(ingredient_id, []):
            if edge.relation == RelationType.RISKY_FOR:
                target = self.nodes.get(edge.target_id)
                if target:
                    risky_profiles.append({
                        "id": target.id,
                        "name": target.name
                    })
        
        # Get conditions (follow effects → conditions)
        conditions = set()
        for effect in effects:
            for edge in self.adjacency.get(effect["id"], []):
                if edge.relation == RelationType.AFFECTS:
                    target = self.nodes.get(edge.target_id)
                    if target:
                        conditions.add((target.id, target.name))
        
        # Get alternatives
        alternatives = []
        for edge in self.adjacency.get(ingredient_id, []):
            if edge.relation == RelationType.ALTERNATIVE_TO:
                target = self.nodes.get(edge.target_id)
                if target:
                    alternatives.append({
                        "id": target.id,
                        "name": target.name
                    })
        
        return {
            "found": True,
            "ingredient": node.name,
            "category": node.properties.get("category"),
            "e_number": node.properties.get("e_number"),
            "effects": effects,
            "conditions": [{"id": c[0], "name": c[1]} for c in conditions],
            "risky_for_profiles": risky_profiles,
            "alternatives": alternatives
        }
    
    def explain_risk(self, ingredient_name: str, profile: str) -> Dict:
        """
        Explain why an ingredient is risky for a profile
        
        Returns a reasoning chain with evidence
        """
        risks = self.get_ingredient_risks(ingredient_name)
        
        if not risks.get("found"):
            return {"explanation": f"No risk data found for {ingredient_name}"}
        
        # Check if profile is in risky profiles
        profile_lower = profile.lower()
        is_risky = any(
            profile_lower in p["name"].lower() or profile_lower in p["id"]
            for p in risks.get("risky_for_profiles", [])
        )
        
        if not is_risky:
            return {
                "is_risky": False,
                "explanation": f"{risks['ingredient']} is not specifically flagged for {profile}"
            }
        
        # Build explanation chain
        effects = risks.get("effects", [])
        conditions = risks.get("conditions", [])
        
        chain = []
        chain.append(f"{risks['ingredient']} is a {risks.get('category', 'food additive')}")
        
        if effects:
            effect_names = [e["name"] for e in effects]
            chain.append(f"It can cause: {', '.join(effect_names)}")
        
        if conditions:
            condition_names = [c["name"] for c in conditions]
            chain.append(f"This may lead to or worsen: {', '.join(condition_names)}")
        
        chain.append(f"This is particularly concerning for {profile} profiles")
        
        # Get evidence
        evidence = []
        for effect in effects:
            evidence.extend(effect.get("evidence", []))
        
        return {
            "is_risky": True,
            "ingredient": risks["ingredient"],
            "profile": profile,
            "explanation_chain": chain,
            "evidence_urls": list(set(evidence)),
            "alternatives": risks.get("alternatives", [])
        }
    
    def get_safe_alternatives(self, ingredient_name: str) -> List[Dict]:
        """Get safe alternatives for an ingredient"""
        risks = self.get_ingredient_risks(ingredient_name)
        return risks.get("alternatives", [])
    
    def query_by_profile(self, profile: str) -> Dict:
        """Get all ingredients risky for a profile"""
        profile_id = None
        profile_lower = profile.lower()
        
        for node_id, node in self.nodes.items():
            if node.node_type == "profile":
                if profile_lower in node.name.lower() or profile_lower in node_id:
                    profile_id = node_id
                    break
        
        if not profile_id:
            return {"found": False, "profile": profile}
        
        # Find all ingredients risky for this profile
        risky_ingredients = []
        for edge in self.reverse_adjacency.get(profile_id, []):
            if edge.relation == RelationType.RISKY_FOR:
                source = self.nodes.get(edge.source_id)
                if source and source.node_type == "ingredient":
                    risky_ingredients.append({
                        "id": source.id,
                        "name": source.name,
                        "category": source.properties.get("category")
                    })
        
        return {
            "found": True,
            "profile": self.nodes[profile_id].name,
            "risky_ingredients": risky_ingredients,
            "count": len(risky_ingredients)
        }
    
    def save(self, path: str):
        """Save knowledge graph to JSON"""
        data = {
            "nodes": [
                {
                    "id": n.id,
                    "node_type": n.node_type,
                    "name": n.name,
                    "properties": n.properties
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation.value,
                    "properties": e.properties,
                    "evidence": e.evidence,
                    "confidence": e.confidence
                }
                for e in self.edges
            ]
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: str):
        """Load knowledge graph from JSON"""
        with open(path, 'r') as f:
            data = json.load(f)
        
        self.nodes = {}
        self.edges = []
        self.adjacency = {}
        self.reverse_adjacency = {}
        
        for n in data["nodes"]:
            node = KnowledgeNode(n["id"], n["node_type"], n["name"], n.get("properties", {}))
            self.add_node(node)
        
        for e in data["edges"]:
            edge = KnowledgeEdge(
                e["source_id"],
                e["target_id"],
                RelationType(e["relation"]),
                e.get("properties", {}),
                e.get("evidence", []),
                e.get("confidence", 1.0)
            )
            self.add_edge(edge)
    
    def get_stats(self) -> Dict:
        """Get statistics about the knowledge graph"""
        node_types = {}
        for node in self.nodes.values():
            node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        relation_types = {}
        for edge in self.edges:
            rel = edge.relation.value
            relation_types[rel] = relation_types.get(rel, 0) + 1
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": node_types,
            "relation_types": relation_types
        }
