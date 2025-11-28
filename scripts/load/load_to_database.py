"""
Load data from CSV files to PostgreSQL database
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import psycopg2
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()


class Org XDataLoader:
    def __init__(self):
        """Initialize database connection"""
        self.connection_string = (
            f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:"
            f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        self.engine = create_engine(self.connection_string)
        print(f"Connected to database: {os.getenv('DB_NAME')}")
        
    def populate_date_dimension(self, start_date='2023-01-01', end_date='2026-12-31'):
        """Populate date dimension table"""
        print("Populating date dimension...")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        date_data = []
        
        for date in dates:
            date_data.append({
                'date_key': int(date.strftime('%Y%m%d')),
                'full_date': date.date(),
                'year': date.year,
                'quarter': date.quarter,
                'month': date.month,
                'month_name': date.strftime('%B'),
                'week': date.isocalendar()[1],
                'day_of_month': date.day,
                'day_of_week': date.dayofweek,
                'day_name': date.strftime('%A'),
                'is_weekend': date.dayofweek >= 5,
                'fiscal_year': date.year if date.month >= 7 else date.year - 1,
                'fiscal_quarter': ((date.month - 7) % 12) // 3 + 1
            })
        
        df_date = pd.DataFrame(date_data)
        df_date.to_sql('dim_date', self.engine, schema='Org X', 
                      if_exists='append', index=False, method='multi')
        print(f"Loaded {len(df_date)} dates")
        
    def load_households(self):
        """Load household dimension"""
        print("Loading household data...")
        
        df = pd.read_csv('../../data/raw/Org X_households_200k.csv')
        
        # Select relevant columns for dim_household
        household_cols = [
            'household_id', 'county', 'sub_county', 'ward', 'village',
            'urban_rural', 'gps_latitude', 'gps_longitude', 'head_name',
            'head_gender', 'head_age', 'marital_status', 'education_level',
            'household_size', 'children_under_18', 'youth_18_35', 'elderly_over_60',
            'primary_economic_activity', 'monthly_income_ksh', 'owns_land',
            'land_size_acres', 'livestock_owned', 'electricity_access',
            'mobile_phone_ownership', 'water_source', 'toilet_type',
            'control_group', 'vulnerability_factors'
        ]
        
        df_household = df[household_cols].copy()
        df_household.to_sql('dim_household', self.engine, schema='Org X',
                           if_exists='append', index=False, method='multi')
        print(f"Loaded {len(df_household)} households")
        
        return df
        
    def load_products(self):
        """Load product dimension"""
        print("Loading product data...")
        
        df = pd.read_csv('../../data/raw/product_performance_metrics.csv')
        df.to_sql('dim_product', self.engine, schema='Org X',
                 if_exists='append', index=False, method='multi')
        print(f"Loaded {len(df)} products")
        
    def load_geography(self):
        """Load geography dimension with Kenya county data"""
        print("Loading geography data...")
        
        # Kenya county data (simplified - you can enhance with real data)
        counties = [
            {'county': 'Nairobi', 'region': 'Central', 'population': 4397073, 
             'area_sq_km': 696.1, 'poverty_rate': 16.7, 'electrification_rate': 77.6},
            {'county': 'Kiambu', 'region': 'Central', 'population': 2417735,
             'area_sq_km': 2543.5, 'poverty_rate': 21.8, 'electrification_rate': 71.2},
            {'county': 'Nakuru', 'region': 'Rift Valley', 'population': 2162202,
             'area_sq_km': 7495.1, 'poverty_rate': 29.9, 'electrification_rate': 51.3},
            {'county': 'Kakamega', 'region': 'Western', 'population': 1867579,
             'area_sq_km': 3033.8, 'poverty_rate': 36.4, 'electrification_rate': 38.1},
            {'county': 'Bungoma', 'region': 'Western', 'population': 1670570,
             'area_sq_km': 2069.0, 'poverty_rate': 52.2, 'electrification_rate': 31.5},
            {'county': 'Meru', 'region': 'Eastern', 'population': 1545714,
             'area_sq_km': 6936.0, 'poverty_rate': 28.3, 'electrification_rate': 42.7},
            {'county': 'Kisumu', 'region': 'Nyanza', 'population': 1155574,
             'area_sq_km': 2085.9, 'poverty_rate': 35.0, 'electrification_rate': 48.2},
            {'county': 'Machakos', 'region': 'Eastern', 'population': 1421932,
             'area_sq_km': 6208.0, 'poverty_rate': 32.7, 'electrification_rate': 54.8},
            {'county': 'Mombasa', 'region': 'Coast', 'population': 1208333,
             'area_sq_km': 229.9, 'poverty_rate': 34.8, 'electrification_rate': 65.1},
            {'county': 'Kilifi', 'region': 'Coast', 'population': 1453787,
             'area_sq_km': 12245.9, 'poverty_rate': 48.8, 'electrification_rate': 37.4},
            {'county': 'Uasin Gishu', 'region': 'Rift Valley', 'population': 1163186,
             'area_sq_km': 3345.2, 'poverty_rate': 30.3, 'electrification_rate': 56.9},
            {'county': 'Nyeri', 'region': 'Central', 'population': 759164,
             'area_sq_km': 3337.1, 'poverty_rate': 20.7, 'electrification_rate': 68.3},
            {'county': 'Kisii', 'region': 'Nyanza', 'population': 1266860,
             'area_sq_km': 1317.5, 'poverty_rate': 44.2, 'electrification_rate': 29.4},
            {'county': 'Turkana', 'region': 'Rift Valley', 'population': 926976,
             'area_sq_km': 68680.0, 'poverty_rate': 79.4, 'electrification_rate': 15.2}
        ]
        
        df_geo = pd.DataFrame(counties)
        df_geo.to_sql('dim_geography', self.engine, schema='Org X',
                     if_exists='append', index=False)
        print(f"Loaded {len(df_geo)} counties")
        
    def load_adoptions(self, households_df):
        """Load adoption facts"""
        print("Loading adoption facts...")
        
        # Filter for adopted households
        adopted = households_df[households_df['product_type'].notna() & 
                               (households_df['product_type'] != 'none')].copy()
        
        # Get dimension keys
        with self.engine.connect() as conn:
            # Get household keys
            households = pd.read_sql(
                "SELECT household_key, household_id FROM Org X.dim_household", 
                conn
            )
            
            # Get product keys
            products = pd.read_sql(
                "SELECT product_key, product_type FROM Org X.dim_product", 
                conn
            )
            
            # Get geography keys
            geography = pd.read_sql(
                "SELECT geography_key, county FROM Org X.dim_geography", 
                conn
            )
        
        # Merge to get keys
        adoptions = adopted.merge(households, on='household_id')
        
        # Map product types to product keys (using first product of each type)
        product_mapping = products.groupby('product_type').first().reset_index()
        adoptions = adoptions.merge(product_mapping, on='product_type', how='left')
        
        # Map geography
        adoptions = adoptions.merge(geography, on='county')
        
        # Create date keys
        adoptions['adoption_date_key'] = pd.to_datetime(
            adoptions['adoption_date']
        ).dt.strftime('%Y%m%d').astype(int)
        
        # Prepare fact table data
        fact_data = adoptions[[
            'household_key', 'product_key', 'adoption_date_key', 'geography_key',
            'payment_method', 'subsidy_amount', 'usage_intensity',
            'baseline_cooking_method', 'baseline_fuel_type', 'weekly_fuel_cost_ksh',
            'cooking_hours_per_day'
        ]].copy()
        
        fact_data.rename(columns={
            'weekly_fuel_cost_ksh': 'baseline_weekly_fuel_cost_ksh',
            'cooking_hours_per_day': 'baseline_cooking_hours_per_day'
        }, inplace=True)
        
        fact_data['actual_price_paid'] = 500  # KSH 500 = $5
        
        fact_data.to_sql('fact_adoptions', self.engine, schema='Org X',
                        if_exists='append', index=False, method='multi')
        print(f"Loaded {len(fact_data)} adoption records")
        
    def run_full_load(self):
        """Execute complete data loading process"""
        print("\n" + "="*50)
        print("STARTING Org X DATA LOAD")
        print("="*50 + "\n")
        
        # Load dimensions first
        self.populate_date_dimension()
        households_df = self.load_households()
        self.load_products()
        self.load_geography()
        
        # Load facts
        self.load_adoptions(households_df)
        
        print("\n" + "="*50)
        print("DATA LOAD COMPLETE")
        print("="*50)
        
if __name__ == "__main__":
    loader = Org XDataLoader()
    loader.run_full_load()
