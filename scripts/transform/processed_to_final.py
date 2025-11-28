"""
Transforming the data in the DB from Processed to Final (Silver to Gold)
Creates business-ready aggregations for Power BI
"""
import pandas as pd
from sqlalchemy import create_engine, text 
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../logs/etl_pipeline.log'),
        logging.StreamHandler()
    ]
)

class SilverToGold:
    def __init__(self):
        self.engine = self._create_connection()
        
    def _create_connection(self):
        connection_string = (
            f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:"
            f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        return create_engine(connection_string)
    
    def create_executive_summary(self):
        """Create executive summary table for Power BI"""
        logging.info("Creating executive summary...")
        
        
        exec_summary_sql = text("""
        CREATE OR REPLACE VIEW kiota.gold_executive_summary AS
        SELECT 
            -- Key Metrics
            COUNT(DISTINCT f.household_key) as total_households_reached,
            SUM(i.co2_avoided_annual) as total_co2_avoided_tons,
            SUM(i.carbon_credit_value_usd) as total_carbon_credit_value,
            SUM(i.dalys_avoided) as total_dalys_avoided,
            SUM(i.annual_fuel_savings_ksh) as total_fuel_savings_ksh,
            
            -- Adoption Metrics
            AVG(f.usage_intensity) as avg_usage_intensity,
            COUNT(DISTINCT CASE WHEN f.usage_intensity >= 0.8 THEN f.household_key END) as full_adopters,
            COUNT(DISTINCT CASE WHEN f.usage_intensity < 0.5 THEN f.household_key END) as low_adopters,
            
            -- Financial Metrics
            SUM(f.subsidy_amount) as total_subsidies,
            AVG(f.subsidy_amount) as avg_subsidy_per_household,
            
            -- Progress to Goal
            COUNT(DISTINCT f.household_key)::float / 975000 * 100 as pct_of_goal_achieved
            
        FROM kiota.fact_adoptions f
        JOIN kiota.silver_impact_calculations i 
            ON f.household_key = i.household_key;
        """)
        
        with self.engine.connect() as conn:
            conn.execute(exec_summary_sql)
            conn.commit()
    
    def create_county_performance(self):
        """Create county performance aggregations"""
        logging.info("Creating county performance view...")
        
        
        county_sql = text("""
        CREATE OR REPLACE VIEW kiota.gold_county_performance AS
        SELECT 
            g.county,
            g.poverty_rate,
            g.electrification_rate,
            COUNT(DISTINCT f.household_key) as households_reached,
            
            -- Penetration
            COUNT(DISTINCT f.household_key)::float / g.population * 4.5 * 100 as penetration_rate,
            
            -- Impact Metrics
            SUM(i.co2_avoided_annual) as co2_avoided,
            SUM(i.dalys_avoided) as dalys_avoided,
            SUM(i.annual_fuel_savings_ksh) as fuel_savings,
            
            -- Efficiency Metrics
            SUM(i.carbon_credit_value_usd) / NULLIF(SUM(f.subsidy_amount), 0) as roi_ratio,
            AVG(f.usage_intensity) as avg_usage_intensity,
            
            -- Product Mix
            COUNT(DISTINCT CASE WHEN p.product_type = 'charcoal_stove' THEN f.household_key END) as charcoal_stoves,
            COUNT(DISTINCT CASE WHEN p.product_type = 'firewood_stove' THEN f.household_key END) as firewood_stoves,
            COUNT(DISTINCT CASE WHEN p.product_type = 'pellet_stove' THEN f.household_key END) as pellet_stoves,
            COUNT(DISTINCT CASE WHEN p.product_type = 'solar_lantern' THEN f.household_key END) as solar_lanterns
            
        FROM kiota.fact_adoptions f
        JOIN kiota.dim_geography g ON f.geography_key = g.geography_key
        JOIN kiota.dim_product p ON f.product_key = p.product_key
        JOIN kiota.silver_impact_calculations i ON f.household_key = i.household_key
        GROUP BY g.county, g.poverty_rate, g.electrification_rate, g.population;
        """)
        
        with self.engine.connect() as conn:
            conn.execute(county_sql)
            conn.commit()
    
    def create_donor_impact_views(self):
        """Create donor-specific impact views"""
        logging.info("Creating donor-specific views...")
        
        
        health_donor_sql = text("""
        CREATE OR REPLACE VIEW kiota.gold_donor_health_impact AS
        SELECT 
            g.county,
            COUNT(DISTINCT f.household_key) as households,
            SUM(i.mortality_reduction) as lives_saved,
            SUM(i.dalys_avoided) as dalys_avoided,
            SUM(i.healthcare_savings_annual_ksh) as healthcare_cost_avoided,
            SUM(CASE WHEN h.vulnerability_factors LIKE '%Elderly%' THEN 1 ELSE 0 END) as elderly_reached,
            SUM(CASE WHEN h.children_under_18 > 0 THEN h.children_under_18 ELSE 0 END) as children_impacted
        FROM kiota.fact_adoptions f
        JOIN kiota.dim_household h ON f.household_key = h.household_key
        JOIN kiota.dim_geography g ON f.geography_key = g.geography_key
        JOIN kiota.silver_impact_calculations i ON f.household_key = i.household_key
        GROUP BY g.county;
        """)
        
        env_donor_sql = text("""
        CREATE OR REPLACE VIEW kiota.gold_donor_environment_impact AS
        SELECT 
            g.county,
            COUNT(DISTINCT f.household_key) as households,
            SUM(i.co2_avoided_annual) as co2_avoided_tons,
            SUM(i.carbon_credit_value_usd) as carbon_credit_value,
            SUM(i.co2_avoided_annual * 0.17) as trees_equivalent,
            SUM(p.pm25_emissions_mg_m3 * f.usage_intensity) as pm25_reduced
        FROM kiota.fact_adoptions f
        JOIN kiota.dim_product p ON f.product_key = p.product_key
        JOIN kiota.dim_geography g ON f.geography_key = g.geography_key
        JOIN kiota.silver_impact_calculations i ON f.household_key = i.household_key
        GROUP BY g.county;
        """)
        
        gender_donor_sql = text("""
        CREATE OR REPLACE VIEW kiota.gold_donor_gender_impact AS
        SELECT 
            g.county,
            COUNT(DISTINCT CASE WHEN h.head_gender = 'Female' THEN f.household_key END) as female_headed_households,
            SUM(i.time_saved_hours_annual) as total_time_saved_hours,
            SUM(i.time_saved_hours_annual * 0.7) as women_time_saved_hours,
            SUM(CASE WHEN h.vulnerability_factors LIKE '%Single Parent%' THEN 1 ELSE 0 END) as single_parents_reached
        FROM kiota.fact_adoptions f
        JOIN kiota.dim_household h ON f.household_key = h.household_key
        JOIN kiota.dim_geography g ON f.geography_key = g.geography_key
        JOIN kiota.silver_impact_calculations i ON f.household_key = i.household_key
        GROUP BY g.county;
        """)
        
        with self.engine.connect() as conn:
            conn.execute(health_donor_sql)
            conn.execute(env_donor_sql) 
            conn.execute(gender_donor_sql)
            conn.commit()
    
    def run_pipeline(self):
        """Execute complete Silver to Gold pipeline"""
        try:
            logging.info("Starting Silver to Gold transformation...")
            
            self.create_executive_summary()
            self.create_county_performance()
            self.create_donor_impact_views()
            
            logging.info("Silver to Gold transformation complete!")
            
        except Exception as e:
            logging.error(f"Pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    pipeline = SilverToGold()
    pipeline.run_pipeline()