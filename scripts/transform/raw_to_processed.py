"""
Transforming the data in the DB from Raw to Processed (Bronze to Silver)
Cleans and validates raw data
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text 
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
os.makedirs('../../logs', exist_ok=True) 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../logs/etl_pipeline.log'),
        logging.StreamHandler()
    ]
)

class BronzeToSilver:
    def __init__(self):
        self.engine = self._create_connection()
        self.quality_metrics = {}
        
    def _create_connection(self):
        """Create database connection"""
        connection_string = (
            f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:"
            f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        return create_engine(connection_string)
    
    def validate_households(self):
        """Validate and clean household data"""
        logging.info("Validating household data...")
        
        with self.engine.connect() as conn:
            # Check for data quality issues
            quality_checks = {
                'missing_counties': """
                    SELECT COUNT(*) FROM Org X.dim_household 
                    WHERE county IS NULL
                """,
                'invalid_ages': """
                    SELECT COUNT(*) FROM Org X.dim_household 
                    WHERE head_age < 18 OR head_age > 100
                """,
                'negative_income': """
                    SELECT COUNT(*) FROM Org X.dim_household 
                    WHERE monthly_income_ksh < 0
                """,
                'household_size_anomalies': """
                    SELECT COUNT(*) FROM Org X.dim_household 
                    WHERE household_size < 1 OR household_size > 20
                """
            }
            
            for check_name, query in quality_checks.items():
                result = pd.read_sql(query, conn).iloc[0, 0]
                self.quality_metrics[f'household_{check_name}'] = result
                logging.info(f"  {check_name}: {result} records")
        
        # Create cleaned view 
        create_view_sql = text("""
        CREATE OR REPLACE VIEW Org X.silver_households AS
        SELECT 
            *,
            CASE 
                WHEN monthly_income_ksh < 10000 THEN 'Low'
                WHEN monthly_income_ksh < 30000 THEN 'Medium'
                ELSE 'High'
            END as income_bracket,
            CASE
                WHEN children_under_18 > 3 THEN 'Large Family'
                WHEN children_under_18 > 0 THEN 'Family with Children'
                ELSE 'No Children'
            END as family_type,
            CASE
                WHEN head_age < 30 THEN 'Youth'
                WHEN head_age < 60 THEN 'Adult'
                ELSE 'Senior'
            END as age_group
        FROM Org X.dim_household
        WHERE household_size BETWEEN 1 AND 20
          AND head_age BETWEEN 18 AND 100
          AND monthly_income_ksh >= 0;
        """)
        
        with self.engine.connect() as conn:
            conn.execute(create_view_sql)
            conn.commit()
            
        logging.info("Created silver_households view with data quality filters")
        
    def calculate_adoption_metrics(self):
        """Calculate adoption metrics with counterfactual analysis"""
        logging.info("Calculating adoption metrics...")
        
        # Simplified version without control group fuel costs
        adoption_metrics_sql = text("""
        CREATE OR REPLACE VIEW Org X.silver_adoption_metrics AS
        WITH treatment_group AS (
            SELECT 
                g.county,
                h.urban_rural,
                COUNT(DISTINCT f.household_key) as adopted_households,
                AVG(f.usage_intensity) as avg_usage_intensity,
                AVG(f.baseline_weekly_fuel_cost_ksh) as avg_baseline_cost,
                MIN(f.baseline_weekly_fuel_cost_ksh) as min_baseline_cost,
                MAX(f.baseline_weekly_fuel_cost_ksh) as max_baseline_cost
            FROM Org X.fact_adoptions f
            JOIN Org X.dim_household h ON f.household_key = h.household_key
            JOIN Org X.dim_geography g ON f.geography_key = g.geography_key
            GROUP BY g.county, h.urban_rural
        ),
        control_counts AS (
            SELECT 
                county,
                urban_rural,
                COUNT(*) as control_households
            FROM Org X.dim_household
            WHERE control_group = true
            GROUP BY county, urban_rural
        )
        SELECT 
            t.*,
            c.control_households,
            -- Calculate adoption penetration
            CASE 
                WHEN c.control_households > 0 
                THEN (t.adopted_households::float / (t.adopted_households + c.control_households)) * 100
                ELSE NULL 
            END as adoption_penetration_pct,
            -- Estimate savings based on usage intensity
            t.avg_baseline_cost * t.avg_usage_intensity * 0.3 as estimated_weekly_savings,
            t.avg_baseline_cost * t.avg_usage_intensity * 0.3 * 52 as estimated_annual_savings
        FROM treatment_group t
        LEFT JOIN control_counts c 
            ON t.county = c.county 
            AND t.urban_rural = c.urban_rural;
        """)
        
        with self.engine.connect() as conn:
            conn.execute(adoption_metrics_sql)
            conn.commit()
            
        logging.info("Created silver_adoption_metrics view with counterfactual analysis")
            
    def create_impact_calculations(self):
        """Create impact calculation tables"""
        logging.info("Creating impact calculations...")
        
        
        impact_sql = text("""
        CREATE OR REPLACE VIEW Org X.silver_impact_calculations AS
        SELECT 
            f.household_key,
            f.product_key,
            g.county,
            p.product_type,
            
            -- Environmental Impact
            p.carbon_reduction_tons_year * f.usage_intensity as co2_avoided_annual,
            p.carbon_reduction_tons_year * f.usage_intensity * 12.50 as carbon_credit_value_usd,
            
            -- Health Impact (using coefficients)
            (p.pm25_emissions_mg_m3 / 1000) * 0.00082 * f.usage_intensity as mortality_reduction,
            (p.pm25_emissions_mg_m3 / 1000) * 24.5 * f.usage_intensity as dalys_avoided,
            
            -- Economic Impact
            f.baseline_weekly_fuel_cost_ksh * 52 * f.usage_intensity as annual_fuel_savings_ksh,
            2.5 * 365 * f.usage_intensity as time_saved_hours_annual,
            5000 * f.usage_intensity as healthcare_savings_annual_ksh,
            
            -- Stove Stacking Behavior
            f.usage_intensity as stacking_ratio,
            CASE 
                WHEN f.usage_intensity >= 0.8 THEN 'Full Adoption'
                WHEN f.usage_intensity >= 0.5 THEN 'Partial Adoption'
                ELSE 'Minimal Use'
            END as adoption_category
            
        FROM Org X.fact_adoptions f
        JOIN Org X.dim_product p ON f.product_key = p.product_key
        JOIN Org X.dim_geography g ON f.geography_key = g.geography_key;
        """)
        
        with self.engine.connect() as conn:
            conn.execute(impact_sql)
            conn.commit()
            
        logging.info("Created silver_impact_calculations view")
        
    def generate_quality_report(self):
        """Generate data quality report"""
        logging.info("\n=== DATA QUALITY REPORT ===")
        
        with self.engine.connect() as conn:
            # Completeness check
            completeness = pd.read_sql("""
                SELECT 
                    'Households' as dataset,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN county IS NOT NULL THEN 1 END) as complete_county,
                    COUNT(CASE WHEN monthly_income_ksh IS NOT NULL THEN 1 END) as complete_income
                FROM Org X.dim_household
                UNION ALL
                SELECT 
                    'Adoptions',
                    COUNT(*),
                    COUNT(CASE WHEN usage_intensity IS NOT NULL THEN 1 END),
                    COUNT(CASE WHEN subsidy_amount IS NOT NULL THEN 1 END)
                FROM Org X.fact_adoptions
            """, conn)
            
            print("\nCompleteness Metrics:")
            print(completeness.to_string(index=False))
            
            # Anomaly detection
            anomalies = pd.read_sql("""
                SELECT 
                    'High Usage Intensity' as anomaly_type,
                    COUNT(*) as count
                FROM Org X.fact_adoptions
                WHERE usage_intensity > 0.95
                UNION ALL
                SELECT 
                    'Low Income High Adoption',
                    COUNT(*)
                FROM Org X.fact_adoptions f
                JOIN Org X.dim_household h ON f.household_key = h.household_key
                WHERE h.monthly_income_ksh < 10000 AND f.usage_intensity > 0.8
            """, conn)
            
            print("\nAnomaly Detection:")
            print(anomalies.to_string(index=False))
        
        return self.quality_metrics
    
    def run_pipeline(self):
        """Execute complete Bronze to Silver pipeline"""
        try:
            logging.info("Starting Bronze to Silver transformation...")
            
            self.validate_households()
            self.calculate_adoption_metrics()
            self.create_impact_calculations()
            quality_metrics = self.generate_quality_report()
            
            logging.info("Bronze to Silver transformation complete!")
            return quality_metrics
            
        except Exception as e:
            logging.error(f"Pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    pipeline = BronzeToSilver()
    pipeline.run_pipeline()
