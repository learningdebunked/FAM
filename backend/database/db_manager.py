"""
Database Manager for FAM Product Database
Handles SQLite database operations for storing scraped product data
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

class DatabaseManager:
    """Manages SQLite database for FAM product data"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_dir = Path(__file__).parent
            db_path = str(db_dir / "fam_products.db")
        
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Initialize database with schema if it doesn't exist"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not os.path.exists(self.db_path) or os.path.getsize(self.db_path) == 0:
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            with self.get_connection() as conn:
                conn.executescript(schema)
                print(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # ==================== Retailer Operations ====================
    
    def get_retailers(self, region: str = None) -> List[Dict]:
        """Get all retailers, optionally filtered by region"""
        with self.get_connection() as conn:
            if region:
                cursor = conn.execute(
                    "SELECT * FROM retailers WHERE region = ? AND scraper_enabled = TRUE",
                    (region,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM retailers WHERE scraper_enabled = TRUE"
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_retailer_by_name(self, name: str) -> Optional[Dict]:
        """Get retailer by name"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM retailers WHERE name = ?", (name,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_retailer_last_scraped(self, retailer_id: int):
        """Update last scraped timestamp for retailer"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE retailers SET last_scraped_at = ? WHERE id = ?",
                (datetime.now().isoformat(), retailer_id)
            )
    
    # ==================== Product Operations ====================
    
    def insert_product(self, product_data: Dict) -> int:
        """Insert or update a product"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO products (
                    retailer_id, external_id, barcode, name, brand,
                    category_id, description, image_url, price, currency,
                    serving_size, servings_per_container, product_url, is_processed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(retailer_id, external_id) DO UPDATE SET
                    name = excluded.name,
                    brand = excluded.brand,
                    price = excluded.price,
                    image_url = excluded.image_url,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                product_data.get('retailer_id'),
                product_data.get('external_id'),
                product_data.get('barcode'),
                product_data.get('name'),
                product_data.get('brand'),
                product_data.get('category_id'),
                product_data.get('description'),
                product_data.get('image_url'),
                product_data.get('price'),
                product_data.get('currency', 'USD'),
                product_data.get('serving_size'),
                product_data.get('servings_per_container'),
                product_data.get('product_url'),
                product_data.get('is_processed', True)
            ))
            return cursor.lastrowid
    
    def get_product_by_barcode(self, barcode: str) -> Optional[Dict]:
        """Get product by barcode"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, r.name as retailer_name, i.raw_text as ingredients_text,
                       i.parsed_ingredients, n.*
                FROM products p
                LEFT JOIN retailers r ON p.retailer_id = r.id
                LEFT JOIN ingredients i ON p.id = i.product_id
                LEFT JOIN nutrition_facts n ON p.id = n.product_id
                WHERE p.barcode = ?
            """, (barcode,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def search_products(self, query: str, retailer_id: int = None, 
                       category_id: int = None, limit: int = 50) -> List[Dict]:
        """Search products by name or brand"""
        with self.get_connection() as conn:
            sql = """
                SELECT p.*, r.name as retailer_name
                FROM products p
                LEFT JOIN retailers r ON p.retailer_id = r.id
                WHERE (p.name LIKE ? OR p.brand LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]
            
            if retailer_id:
                sql += " AND p.retailer_id = ?"
                params.append(retailer_id)
            
            if category_id:
                sql += " AND p.category_id = ?"
                params.append(category_id)
            
            sql += f" LIMIT {limit}"
            
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_products_by_category(self, category_id: int, limit: int = 100) -> List[Dict]:
        """Get products by category"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT p.*, r.name as retailer_name
                FROM products p
                LEFT JOIN retailers r ON p.retailer_id = r.id
                WHERE p.category_id = ?
                LIMIT ?
            """, (category_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Ingredients Operations ====================
    
    def insert_ingredients(self, product_id: int, raw_text: str, 
                          parsed_ingredients: List[str] = None):
        """Insert ingredients for a product"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ingredients (product_id, raw_text, parsed_ingredients)
                VALUES (?, ?, ?)
            """, (
                product_id,
                raw_text,
                json.dumps(parsed_ingredients) if parsed_ingredients else None
            ))
    
    def get_ingredients(self, product_id: int) -> Optional[Dict]:
        """Get ingredients for a product"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM ingredients WHERE product_id = ?", (product_id,)
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('parsed_ingredients'):
                    result['parsed_ingredients'] = json.loads(result['parsed_ingredients'])
                return result
            return None
    
    # ==================== Nutrition Operations ====================
    
    def insert_nutrition(self, product_id: int, nutrition_data: Dict):
        """Insert nutrition facts for a product"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO nutrition_facts (
                    product_id, calories, total_fat, saturated_fat, trans_fat,
                    cholesterol, sodium, total_carbohydrates, dietary_fiber,
                    total_sugars, added_sugars, protein, vitamin_d, calcium,
                    iron, potassium, vitamin_a, vitamin_c, vitamin_b6,
                    vitamin_b12, magnesium, zinc, unit_basis
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                nutrition_data.get('calories'),
                nutrition_data.get('total_fat'),
                nutrition_data.get('saturated_fat'),
                nutrition_data.get('trans_fat'),
                nutrition_data.get('cholesterol'),
                nutrition_data.get('sodium'),
                nutrition_data.get('total_carbohydrates'),
                nutrition_data.get('dietary_fiber'),
                nutrition_data.get('total_sugars'),
                nutrition_data.get('added_sugars'),
                nutrition_data.get('protein'),
                nutrition_data.get('vitamin_d'),
                nutrition_data.get('calcium'),
                nutrition_data.get('iron'),
                nutrition_data.get('potassium'),
                nutrition_data.get('vitamin_a'),
                nutrition_data.get('vitamin_c'),
                nutrition_data.get('vitamin_b6'),
                nutrition_data.get('vitamin_b12'),
                nutrition_data.get('magnesium'),
                nutrition_data.get('zinc'),
                nutrition_data.get('unit_basis', 'per_serving')
            ))
    
    # ==================== Risk Ingredients Operations ====================
    
    def get_risk_ingredients(self) -> List[Dict]:
        """Get all risk ingredients"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM risk_ingredients")
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('affected_profiles'):
                    result['affected_profiles'] = json.loads(result['affected_profiles'])
                results.append(result)
            return results
    
    def find_risk_ingredient(self, ingredient_name: str) -> Optional[Dict]:
        """Find a risk ingredient by name (partial match)"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM risk_ingredients 
                WHERE LOWER(canonical_name) LIKE LOWER(?)
            """, (f"%{ingredient_name}%",))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('affected_profiles'):
                    result['affected_profiles'] = json.loads(result['affected_profiles'])
                return result
            return None
    
    # ==================== Analysis Operations ====================
    
    def save_product_analysis(self, product_id: int, analysis: Dict):
        """Save product analysis results"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO product_analysis (
                    product_id, overall_score, risk_level, 
                    flagged_ingredients, analysis_json, analyzed_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                analysis.get('overall_score'),
                analysis.get('risk_level'),
                json.dumps(analysis.get('flagged_ingredients', [])),
                json.dumps(analysis),
                datetime.now().isoformat()
            ))
    
    def get_product_analysis(self, product_id: int) -> Optional[Dict]:
        """Get cached analysis for a product"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM product_analysis WHERE product_id = ?",
                (product_id,)
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('analysis_json'):
                    result['analysis'] = json.loads(result['analysis_json'])
                return result
            return None
    
    # ==================== Alternatives Operations ====================
    
    def save_alternative(self, product_id: int, alternative_id: int, 
                        reason: str, score_improvement: float,
                        health_profiles: List[str] = None):
        """Save a product alternative mapping"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO product_alternatives (
                    product_id, alternative_product_id, reason,
                    score_improvement, health_profiles
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                product_id,
                alternative_id,
                reason,
                score_improvement,
                json.dumps(health_profiles) if health_profiles else None
            ))
    
    def get_alternatives(self, product_id: int, health_profiles: List[str] = None,
                        limit: int = 5) -> List[Dict]:
        """Get alternatives for a product"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT pa.*, p.name, p.brand, p.image_url, p.price,
                       pa2.overall_score as alternative_score
                FROM product_alternatives pa
                JOIN products p ON pa.alternative_product_id = p.id
                LEFT JOIN product_analysis pa2 ON p.id = pa2.product_id
                WHERE pa.product_id = ?
                ORDER BY pa.score_improvement DESC
                LIMIT ?
            """, (product_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Scrape Job Operations ====================
    
    def create_scrape_job(self, retailer_id: int) -> int:
        """Create a new scrape job"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO scrape_jobs (retailer_id, status, started_at)
                VALUES (?, 'running', ?)
            """, (retailer_id, datetime.now().isoformat()))
            return cursor.lastrowid
    
    def update_scrape_job(self, job_id: int, **kwargs):
        """Update scrape job status"""
        with self.get_connection() as conn:
            updates = []
            params = []
            for key, value in kwargs.items():
                updates.append(f"{key} = ?")
                params.append(value)
            
            if 'status' in kwargs and kwargs['status'] in ['completed', 'failed']:
                updates.append("completed_at = ?")
                params.append(datetime.now().isoformat())
            
            params.append(job_id)
            conn.execute(
                f"UPDATE scrape_jobs SET {', '.join(updates)} WHERE id = ?",
                params
            )
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            stats = {}
            
            cursor = conn.execute("SELECT COUNT(*) FROM products")
            stats['total_products'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM retailers")
            stats['total_retailers'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM ingredients")
            stats['products_with_ingredients'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM nutrition_facts")
            stats['products_with_nutrition'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM product_analysis")
            stats['analyzed_products'] = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT r.name, COUNT(p.id) as product_count
                FROM retailers r
                LEFT JOIN products p ON r.id = p.retailer_id
                GROUP BY r.id
            """)
            stats['products_by_retailer'] = {
                row['name']: row['product_count'] 
                for row in cursor.fetchall()
            }
            
            return stats


# Singleton instance
_db_manager = None

def get_db() -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
