-- FAM Product Database Schema
-- Stores scraped product data from major grocery retailers

-- Retailers table
CREATE TABLE IF NOT EXISTS retailers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL,
    region TEXT,  -- US, EU, UK, Asia, Middle East, Americas, Australia
    website_url TEXT NOT NULL,
    scraper_enabled BOOLEAN DEFAULT TRUE,
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product categories
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    is_processed_food BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table - main product information
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    retailer_id INTEGER NOT NULL REFERENCES retailers(id),
    external_id TEXT,  -- Retailer's product ID
    barcode TEXT,  -- UPC/EAN/GTIN
    name TEXT NOT NULL,
    brand TEXT,
    category_id INTEGER REFERENCES categories(id),
    description TEXT,
    image_url TEXT,
    price REAL,
    currency TEXT DEFAULT 'USD',
    serving_size TEXT,
    servings_per_container REAL,
    product_url TEXT,
    is_processed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(retailer_id, external_id)
);

-- Ingredients table - raw ingredient list
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    raw_text TEXT,  -- Full ingredient text as scraped
    parsed_ingredients TEXT,  -- JSON array of parsed ingredients
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nutrition facts table
CREATE TABLE IF NOT EXISTS nutrition_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    calories REAL,
    total_fat REAL,
    saturated_fat REAL,
    trans_fat REAL,
    cholesterol REAL,
    sodium REAL,
    total_carbohydrates REAL,
    dietary_fiber REAL,
    total_sugars REAL,
    added_sugars REAL,
    protein REAL,
    vitamin_d REAL,
    calcium REAL,
    iron REAL,
    potassium REAL,
    -- Additional nutrients
    vitamin_a REAL,
    vitamin_c REAL,
    vitamin_b6 REAL,
    vitamin_b12 REAL,
    magnesium REAL,
    zinc REAL,
    -- Units are per serving unless noted
    unit_basis TEXT DEFAULT 'per_serving',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk ingredients lookup table (canonical list from paper)
CREATE TABLE IF NOT EXISTS risk_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,  -- artificial_sweetener, artificial_dye, preservative, etc.
    risk_level TEXT NOT NULL,  -- low, medium, high, critical
    description TEXT,
    affected_profiles TEXT,  -- JSON array: ["child", "pregnant", "diabetic"]
    evidence_links TEXT,  -- JSON array of URLs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product risk analysis cache
CREATE TABLE IF NOT EXISTS product_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    overall_score REAL,
    risk_level TEXT,
    flagged_ingredients TEXT,  -- JSON array of flagged ingredients
    analysis_json TEXT,  -- Full analysis result
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id)
);

-- Healthy alternatives mapping
CREATE TABLE IF NOT EXISTS product_alternatives (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    alternative_product_id INTEGER NOT NULL REFERENCES products(id),
    reason TEXT,
    score_improvement REAL,
    health_profiles TEXT,  -- JSON array of profiles this alternative is good for
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, alternative_product_id)
);

-- Scraping jobs tracking
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    retailer_id INTEGER NOT NULL REFERENCES retailers(id),
    status TEXT DEFAULT 'pending',  -- pending, running, completed, failed
    total_products INTEGER DEFAULT 0,
    scraped_products INTEGER DEFAULT 0,
    failed_products INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User feedback for model improvement
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    feedback_type TEXT NOT NULL,  -- positive, negative
    category TEXT,  -- accuracy, alternatives, missing_info
    comment TEXT,
    health_profiles TEXT,  -- JSON array of user's profiles
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_retailer ON products(retailer_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_ingredients_product ON ingredients(product_id);
CREATE INDEX IF NOT EXISTS idx_nutrition_product ON nutrition_facts(product_id);
CREATE INDEX IF NOT EXISTS idx_analysis_product ON product_analysis(product_id);

-- Insert default retailers
INSERT OR IGNORE INTO retailers (name, country, region, website_url) VALUES
-- United States
('Walmart', 'USA', 'US', 'https://www.walmart.com'),
('Target', 'USA', 'US', 'https://www.target.com'),
('Kroger', 'USA', 'US', 'https://www.kroger.com'),
('Costco', 'USA', 'US', 'https://www.costco.com'),
('Whole Foods', 'USA', 'US', 'https://www.wholefoodsmarket.com'),
('Safeway', 'USA', 'US', 'https://www.safeway.com'),
('Publix', 'USA', 'US', 'https://www.publix.com'),
('Trader Joes', 'USA', 'US', 'https://www.traderjoes.com'),
-- United Kingdom
('Tesco', 'UK', 'UK', 'https://www.tesco.com'),
('Sainsburys', 'UK', 'UK', 'https://www.sainsburys.co.uk'),
('ASDA', 'UK', 'UK', 'https://www.asda.com'),
('Morrisons', 'UK', 'UK', 'https://www.morrisons.com'),
('Waitrose', 'UK', 'UK', 'https://www.waitrose.com'),
('Iceland', 'UK', 'UK', 'https://www.iceland.co.uk'),
-- Europe
('Carrefour', 'France', 'EU', 'https://www.carrefour.fr'),
('Aldi', 'Germany', 'EU', 'https://www.aldi.com'),
('Lidl', 'Germany', 'EU', 'https://www.lidl.com'),
('Albert Heijn', 'Netherlands', 'EU', 'https://www.ah.nl'),
-- Australia
('Woolworths', 'Australia', 'Australia', 'https://www.woolworths.com.au'),
('Coles', 'Australia', 'Australia', 'https://www.coles.com.au'),
('IGA', 'Australia', 'Australia', 'https://www.iga.com.au'),
-- New Zealand
('Countdown', 'New Zealand', 'Australia', 'https://www.countdown.co.nz'),
('PAKnSAVE', 'New Zealand', 'Australia', 'https://www.paknsave.co.nz'),
('New World', 'New Zealand', 'Australia', 'https://www.newworld.co.nz'),
-- Asia
('FairPrice', 'Singapore', 'Asia', 'https://www.fairprice.com.sg'),
('Big Bazaar', 'India', 'Asia', 'https://www.bigbazaar.com'),
('DMart', 'India', 'Asia', 'https://www.dmart.in'),
('Aeon', 'Japan', 'Asia', 'https://www.aeon.com'),
('E-Mart', 'South Korea', 'Asia', 'https://emart.ssg.com'),
('Lotte Mart', 'South Korea', 'Asia', 'https://www.lottemart.com'),
-- China
('Freshippo', 'China', 'China', 'https://www.freshhema.com'),
('RT-Mart', 'China', 'China', 'https://www.rt-mart.com.cn'),
('Yonghui', 'China', 'China', 'https://www.yonghui.com.cn'),
('Wumart', 'China', 'China', 'https://www.wumart.com'),
-- Middle East
('Carrefour UAE', 'UAE', 'Middle East', 'https://www.carrefouruae.com'),
('Lulu Hypermarket', 'UAE', 'Middle East', 'https://www.luluhypermarket.com'),
('Spinneys', 'UAE', 'Middle East', 'https://www.spinneys.com'),
('Choithrams', 'UAE', 'Middle East', 'https://www.choithrams.com'),
-- Turkey
('Migros Turkey', 'Turkey', 'Turkey', 'https://www.migros.com.tr'),
('BIM', 'Turkey', 'Turkey', 'https://www.bim.com.tr'),
('A101', 'Turkey', 'Turkey', 'https://www.a101.com.tr'),
-- Russia
('Magnit', 'Russia', 'Russia', 'https://magnit.ru'),
('Pyaterochka', 'Russia', 'Russia', 'https://5ka.ru'),
('Lenta', 'Russia', 'Russia', 'https://lenta.com'),
('Perekrestok', 'Russia', 'Russia', 'https://www.perekrestok.ru'),
-- Africa
('Shoprite', 'South Africa', 'Africa', 'https://www.shoprite.co.za'),
('Pick n Pay', 'South Africa', 'Africa', 'https://www.pnp.co.za'),
('Checkers', 'South Africa', 'Africa', 'https://www.checkers.co.za'),
('Woolworths SA', 'South Africa', 'Africa', 'https://www.woolworths.co.za'),
-- South America
('Walmart Mexico', 'Mexico', 'Americas', 'https://www.walmart.com.mx'),
('Cencosud', 'Chile', 'Americas', 'https://www.jumbo.cl'),
('Grupo Exito', 'Colombia', 'Americas', 'https://www.exito.com'),
('Pao de Acucar', 'Brazil', 'Americas', 'https://www.paodeacucar.com'),
('Coto', 'Argentina', 'Americas', 'https://www.cotodigital3.com.ar'),
-- Canada
('Loblaws', 'Canada', 'US', 'https://www.loblaws.ca');

-- Insert risk ingredients from the paper
INSERT OR IGNORE INTO risk_ingredients (canonical_name, category, risk_level, description, affected_profiles) VALUES
-- Artificial Sweeteners
('Aspartame', 'artificial_sweetener', 'high', 'Artificial sweetener linked to potential metabolic and neurological concerns', '["child", "pregnant", "toddler"]'),
('Sucralose', 'artificial_sweetener', 'medium', 'Artificial sweetener that may affect gut microbiome', '["child", "pregnant", "diabetic"]'),
('Saccharin', 'artificial_sweetener', 'medium', 'Artificial sweetener with historical safety concerns', '["child", "pregnant"]'),
('Acesulfame Potassium', 'artificial_sweetener', 'medium', 'Artificial sweetener with limited long-term studies', '["child", "pregnant"]'),
-- Artificial Dyes
('Red 40', 'artificial_dye', 'high', 'Artificial dye associated with hyperactivity in children', '["child", "toddler"]'),
('Yellow 5', 'artificial_dye', 'medium', 'Artificial dye that may cause allergic reactions', '["child", "toddler"]'),
('Yellow 6', 'artificial_dye', 'medium', 'Artificial dye linked to hyperactivity', '["child", "toddler"]'),
('Blue 1', 'artificial_dye', 'low', 'Artificial dye with limited safety data', '["child", "toddler"]'),
('Blue 2', 'artificial_dye', 'low', 'Artificial dye derived from petroleum', '["child", "toddler"]'),
-- Preservatives
('Sodium Nitrate', 'preservative', 'high', 'Preservative linked to increased cancer risk', '["pregnant", "cardiac"]'),
('Sodium Nitrite', 'preservative', 'high', 'Preservative that may form carcinogenic compounds', '["pregnant", "cardiac"]'),
('BHA', 'preservative', 'medium', 'Preservative classified as possibly carcinogenic', '["pregnant", "child"]'),
('BHT', 'preservative', 'medium', 'Preservative with potential endocrine disruption', '["pregnant", "child"]'),
('TBHQ', 'preservative', 'medium', 'Preservative that may affect immune function', '["child", "pregnant"]'),
('Sodium Benzoate', 'preservative', 'low', 'Preservative that may form benzene with vitamin C', '["child"]'),
-- Harmful Fats
('Trans Fat', 'harmful_fat', 'high', 'Strongly linked to cardiovascular disease', '["cardiac", "hypertensive"]'),
('Partially Hydrogenated Oil', 'harmful_fat', 'high', 'Contains trans fats linked to heart disease', '["cardiac", "hypertensive", "diabetic"]'),
-- High Sugar
('High Fructose Corn Syrup', 'high_sugar', 'high', 'Associated with obesity, diabetes, and metabolic syndrome', '["diabetic", "obesity", "cardiac"]'),
('Corn Syrup', 'high_sugar', 'medium', 'High glycemic sweetener', '["diabetic", "obesity"]'),
-- Stimulants
('Caffeine', 'stimulant', 'medium', 'Stimulant affecting sleep, blood pressure, fetal development', '["pregnant", "child", "hypertensive", "senior"]'),
-- Flavor Enhancers
('MSG', 'flavor_enhancer', 'low', 'May cause sensitivity reactions in some individuals', '["adult"]'),
('Monosodium Glutamate', 'flavor_enhancer', 'low', 'May cause sensitivity reactions', '["adult"]');

-- Insert default categories
INSERT OR IGNORE INTO categories (name, is_processed_food) VALUES
('Beverages', TRUE),
('Snacks', TRUE),
('Cereals', TRUE),
('Frozen Foods', TRUE),
('Canned Goods', TRUE),
('Condiments', TRUE),
('Dairy', TRUE),
('Bakery', TRUE),
('Deli', TRUE),
('Candy', TRUE),
('Chips', TRUE),
('Cookies', TRUE),
('Crackers', TRUE),
('Energy Drinks', TRUE),
('Soft Drinks', TRUE),
('Juice', TRUE),
('Instant Meals', TRUE),
('Processed Meats', TRUE),
('Fresh Produce', FALSE),
('Fresh Meat', FALSE),
('Fresh Seafood', FALSE);
