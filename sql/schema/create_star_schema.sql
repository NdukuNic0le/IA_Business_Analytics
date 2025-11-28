-- Drop schema if exists for fresh start
DROP SCHEMA IF EXISTS kiota CASCADE;
CREATE SCHEMA kiota;

-- ============================================
-- DIMENSION TABLES
-- ============================================

-- Dimension: Household
CREATE TABLE kiota.dim_household (
    household_key SERIAL PRIMARY KEY,
    household_id VARCHAR(20) UNIQUE NOT NULL,
    county VARCHAR(50),
    sub_county VARCHAR(50),
    ward VARCHAR(50),
    village VARCHAR(100),
    urban_rural VARCHAR(10),
    gps_latitude DECIMAL(10,6),
    gps_longitude DECIMAL(10,6),
    
    -- Demographics
    head_name VARCHAR(100),
    head_gender VARCHAR(10),
    head_age INT,
    marital_status VARCHAR(20),
    education_level VARCHAR(50),
    
    -- Household composition
    household_size INT,
    children_under_18 INT,
    youth_18_35 INT,
    elderly_over_60 INT,
    
    -- Economic
    primary_economic_activity VARCHAR(50),
    monthly_income_ksh DECIMAL(12,2),
    owns_land BOOLEAN,
    land_size_acres DECIMAL(10,2),
    livestock_owned VARCHAR(50),
    
    -- Infrastructure
    electricity_access VARCHAR(20),
    mobile_phone_ownership BOOLEAN,
    water_source VARCHAR(50),
    toilet_type VARCHAR(50),
    
    -- Program flags
    control_group BOOLEAN,
    vulnerability_factors TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Product
CREATE TABLE kiota.dim_product (
    product_key SERIAL PRIMARY KEY,
    product_id VARCHAR(10) UNIQUE NOT NULL,
    product_type VARCHAR(50),
    product_model VARCHAR(50),
    thermal_efficiency_pct DECIMAL(5,2),
    pm25_emissions_mg_m3 DECIMAL(8,2),
    co_emissions_ppm DECIMAL(8,2),
    fuel_consumption_kg_hour DECIMAL(5,3),
    lifespan_years INT,
    maintenance_frequency_months INT,
    tier_rating INT,
    unit_cost_usd DECIMAL(10,2),
    carbon_reduction_tons_year DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Date
CREATE TABLE kiota.dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    week INT,
    day_of_month INT,
    day_of_week INT,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    fiscal_year INT,
    fiscal_quarter INT
);

-- Dimension: Geography (County details)
CREATE TABLE kiota.dim_geography (
    geography_key SERIAL PRIMARY KEY,
    county VARCHAR(50) UNIQUE NOT NULL,
    region VARCHAR(50),
    population INT,
    area_sq_km DECIMAL(10,2),
    poverty_rate DECIMAL(5,2),
    electrification_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Donor
CREATE TABLE kiota.dim_donor (
    donor_key SERIAL PRIMARY KEY,
    donor_id VARCHAR(10) UNIQUE NOT NULL,
    donor_name VARCHAR(100),
    donor_type VARCHAR(50),
    focus_area VARCHAR(50),
    funding_available_usd DECIMAL(12,2),
    reporting_frequency VARCHAR(50),
    cost_per_impact_target DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FACT TABLES
-- ============================================

-- Fact: Adoptions
CREATE TABLE kiota.fact_adoptions (
    adoption_key SERIAL PRIMARY KEY,
    household_key INT REFERENCES kiota.dim_household(household_key),
    product_key INT REFERENCES kiota.dim_product(product_key),
    adoption_date_key INT REFERENCES kiota.dim_date(date_key),
    geography_key INT REFERENCES kiota.dim_geography(geography_key),
    
    -- Measures
    payment_method VARCHAR(50),
    subsidy_amount DECIMAL(10,2),
    actual_price_paid DECIMAL(10,2),
    usage_intensity DECIMAL(3,2),
    
    -- Baseline measures (before adoption)
    baseline_cooking_method VARCHAR(100),
    baseline_fuel_type VARCHAR(50),
    baseline_weekly_fuel_cost_ksh DECIMAL(10,2),
    baseline_cooking_hours_per_day DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Transactions
CREATE TABLE kiota.fact_transactions (
    transaction_key SERIAL PRIMARY KEY,
    transaction_id VARCHAR(20) UNIQUE NOT NULL,
    household_key INT REFERENCES kiota.dim_household(household_key),
    product_key INT REFERENCES kiota.dim_product(product_key),
    transaction_date_key INT REFERENCES kiota.dim_date(date_key),
    
    -- Measures
    amount_ksh DECIMAL(12,2),
    transaction_type VARCHAR(50),
    payment_method VARCHAR(50),
    status VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Impact Metrics (Monthly aggregation)
CREATE TABLE kiota.fact_impact_metrics (
    impact_key SERIAL PRIMARY KEY,
    household_key INT REFERENCES kiota.dim_household(household_key),
    product_key INT REFERENCES kiota.dim_product(product_key),
    month_key INT REFERENCES kiota.dim_date(date_key),
    geography_key INT REFERENCES kiota.dim_geography(geography_key),
    
    -- Health impacts
    dalys_avoided DECIMAL(10,4),
    mortality_reduction DECIMAL(10,6),
    respiratory_illness_reduced DECIMAL(10,4),
    
    -- Environmental impacts
    co2_avoided_tons DECIMAL(10,4),
    pm25_reduced_kg DECIMAL(10,4),
    trees_saved_equivalent DECIMAL(10,2),
    
    -- Economic impacts
    fuel_cost_savings_ksh DECIMAL(12,2),
    time_saved_hours DECIMAL(10,2),
    healthcare_savings_ksh DECIMAL(12,2),
    
    -- Usage metrics
    usage_days_in_month INT,
    stove_stacking_ratio DECIMAL(3,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Added on 20th Nov directly to PostgreSQL - E-bike and Carbon Price Timeseries
-- Fact: E-bike Logistics
CREATE TABLE IF NOT EXISTS kiota.fact_ebike_logistics (
    route_key SERIAL PRIMARY KEY,
    route_id VARCHAR(20) UNIQUE NOT NULL,
    geography_key INT REFERENCES kiota.dim_geography(geography_key),
    
    distribution_center VARCHAR(100),
    route_name VARCHAR(100),
    distance_km DECIMAL(10,2),
    households_covered INT,
    terrain_type VARCHAR(50),
    avg_delivery_time_hours DECIMAL(5,2),
    ebike_required BOOLEAN,
    traditional_cost_per_delivery_ksh DECIMAL(10,2),
    ebike_cost_per_delivery_ksh DECIMAL(10,2),
    deliveries_per_month INT,
    route_efficiency_score DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Carbon Credit Prices (time series data)
CREATE TABLE IF NOT EXISTS kiota.fact_carbon_credits (
    carbon_key SERIAL PRIMARY KEY,
    date_key INT REFERENCES kiota.dim_date(date_key),
    
    price_per_ton_usd DECIMAL(10,2),
    market_type VARCHAR(50),
    standard VARCHAR(50),
    verification_status VARCHAR(50),
    volume_traded_tons INT,
    kenya_premium_pct DECIMAL(5,2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_household_county ON kiota.dim_household(county);
CREATE INDEX idx_household_control ON kiota.dim_household(control_group);
CREATE INDEX idx_adoptions_date ON kiota.fact_adoptions(adoption_date_key);
CREATE INDEX idx_transactions_date ON kiota.fact_transactions(transaction_date_key);
CREATE INDEX idx_impact_month ON kiota.fact_impact_metrics(month_key);

-- Create views for common queries
CREATE OR REPLACE VIEW kiota.v_adoption_summary AS
SELECT 
    h.county,
    h.urban_rural,
    p.product_type,
    COUNT(*) as adoption_count,
    AVG(f.usage_intensity) as avg_usage_intensity,
    SUM(f.subsidy_amount) as total_subsidy
FROM kiota.fact_adoptions f
JOIN kiota.dim_household h ON f.household_key = h.household_key
JOIN kiota.dim_product p ON f.product_key = p.product_key
GROUP BY h.county, h.urban_rural, p.product_type;

COMMENT ON SCHEMA kiota IS 'Kiota SIC Impact Measurement Analytics Schema';