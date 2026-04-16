-- FreshRoute PostgreSQL Schema

-- ProductSKU: master data, rarely changes
CREATE TABLE product_sku (
    sku_id          VARCHAR(50) PRIMARY KEY,
    ingredient_id   VARCHAR(50) NOT NULL,
    product_name    VARCHAR(200) NOT NULL,
    category_l1     VARCHAR(50) NOT NULL,
    category_l2     VARCHAR(50),
    unit_type       VARCHAR(20) NOT NULL,
    pack_size_g     DECIMAL(10,2),
    retail_price    DECIMAL(12,2) NOT NULL,
    cost_price      DECIMAL(12,2) NOT NULL,
    typical_shelf_life_days INTEGER,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- RecipeDB: all recipes with ingredients
CREATE TABLE recipe (
    recipe_id       VARCHAR(50) PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    servings        INTEGER DEFAULT 2,
    category        VARCHAR(100),
    cuisine         VARCHAR(50) DEFAULT 'vietnamese',
    source_url      VARCHAR(500),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- RecipeRequirement: ingredients per recipe
CREATE TABLE recipe_requirement (
    id              SERIAL PRIMARY KEY,
    recipe_id       VARCHAR(50) NOT NULL REFERENCES recipe(recipe_id),
    ingredient_id   VARCHAR(50) NOT NULL,
    required_qty_g  DECIMAL(10,2) NOT NULL,
    is_optional     BOOLEAN DEFAULT FALSE,
    role            VARCHAR(50),
    UNIQUE(recipe_id, ingredient_id)
);

-- BundleEvents: append-only tracking log
CREATE TABLE bundle_events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_id       VARCHAR(200) NOT NULL,
    recipe_id       VARCHAR(50) NOT NULL,
    store_id        VARCHAR(50) NOT NULL,
    event_type      VARCHAR(20) NOT NULL,
    timestamp       TIMESTAMP DEFAULT NOW(),
    user_id         VARCHAR(100),
    rank_at_time    INTEGER,
    final_score     DECIMAL(8,4),
    urgency_coverage_score DECIMAL(8,4),
    completeness_score     DECIMAL(8,4),
    waste_score_normalized DECIMAL(8,4)
);

-- Indexes
CREATE INDEX idx_product_sku_ingredient ON product_sku(ingredient_id);
CREATE INDEX idx_bundle_events_store_date ON bundle_events(store_id, DATE(timestamp));
CREATE INDEX idx_bundle_events_bundle_id ON bundle_events(bundle_id);
CREATE INDEX idx_recipe_requirement_ingredient ON recipe_requirement(ingredient_id);
CREATE INDEX idx_recipe_requirement_recipe ON recipe_requirement(recipe_id);
