"""
Load missing data to PostgreSQL database
Only loads: transactions, donors, e-bike logistics, carbon credits
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import json
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../logs/etl_pipeline.log'),
        logging.StreamHandler()
    ]
)

class MissingDataLoader:
    def __init__(self):
        """Initialize database connection"""
        self.connection_string = (
            f"{os.getenv('DB_TYPE')}://{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:"
            f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        self.engine = create_engine(self.connection_string)
        print(f"Connected to database: {os.getenv('DB_NAME')}")
        
    # def load_transactions(self):
    #     """Load financial transactions"""
    #     logging.info("\n[1/4] Loading financial transactions...")
        
    #     df = pd.read_csv('../../data/raw/financial_transactions.csv')
    #     print(f"  Read {len(df)} records from CSV")
        
    #     # Get dimension keys
    #     with self.engine.connect() as conn:
    #         households = pd.read_sql(
    #             "SELECT household_key, household_id FROM kiota.dim_household", 
    #             conn
    #         )
    #         products = pd.read_sql(
    #             "SELECT product_key, product_type FROM kiota.dim_product", 
    #             conn
    #         )
        
    #     # Merge to get keys
    #     transactions = df.merge(households, on='household_id', how='left')
    #     print(f"  After household merge: {len(transactions)} records")
        
    #     # Map product types to keys
    #     product_mapping = products.groupby('product_type').first().reset_index()
    #     transactions = transactions.merge(
    #         product_mapping, 
    #         on='product_type', 
    #         how='left'
    #     )
        
    #     # Create date keys
    #     transactions['transaction_date_key'] = pd.to_datetime(
    #         transactions['date']
    #     ).dt.strftime('%Y%m%d').astype(int)
        
    #     # Prepare fact table data
    #     fact_data = transactions[[
    #         'transaction_id', 'household_key', 'product_key', 
    #         'transaction_date_key', 'amount_ksh', 'type', 
    #         'payment_method', 'status'
    #     ]].copy()

    #     # Rename 'type' to match database column name
    #     fact_data.rename(columns={'type': 'transaction_type'}, inplace=True)
        
    #     # Drop rows with missing keys
    #     before_drop = len(fact_data)
    #     fact_data = fact_data.dropna(subset=['household_key', 'transaction_date_key'])
    #     print(f"  Dropped {before_drop - len(fact_data)} rows with missing keys")
        
    #     # Load to database
    #     fact_data.to_sql('fact_transactions', self.engine, schema='kiota',
    #                     if_exists='append', index=False, method='multi')
    #     print(f"  ✓ Loaded {len(fact_data)} transaction records")
        
    def load_donors(self):
        """Load donor dimension"""
        logging.info("\n[2/4] Loading donor data...")
        
        # Read JSON file
        with open('../../data/raw/donor_segmentation_matrix.json', 'r') as f:
            donors_data = json.load(f)
        
        # Convert to DataFrame
        df = pd.DataFrame(donors_data)
        logging.info(f"  Read {len(df)} donor records from JSON")
        
        # Select only columns that exist in database schema
        db_columns = [
            'donor_id',
            'donor_name', 
            'donor_type',
            'focus_area',
            'funding_available_usd',
            'reporting_frequency',
            'cost_per_impact_target'
        ]
        
        df_load = df[db_columns].copy()
        logging.info(f"  Selected {len(db_columns)} columns matching database schema")
        
        df_load.to_sql('dim_donor', self.engine, schema='kiota',
                    if_exists='append', index=False)
        logging.info(f"  ✓ Loaded {len(df_load)} donors")
        
    def load_ebike_logistics(self):
        """Load e-bike logistics data"""
        logging.info("\n[3/4] Loading e-bike logistics data...")
        
        df = pd.read_csv('../../data/raw/ebike_logistics_data.csv')
        print(f"  Read {len(df)} routes from CSV")
        
        # Get geography keys
        with self.engine.connect() as conn:
            geography = pd.read_sql(
                "SELECT geography_key, county FROM kiota.dim_geography", 
                conn
            )
        
        # Merge to get keys
        logistics = df.merge(geography, on='county', how='left')
        
        # Prepare data
        fact_data = logistics[[
            'route_id', 'geography_key', 'distribution_center', 'route_name',
            'distance_km', 'households_covered', 'terrain_type',
            'avg_delivery_time_hours', 'ebike_required',
            'traditional_cost_per_delivery_ksh', 'ebike_cost_per_delivery_ksh',
            'deliveries_per_month', 'route_efficiency_score'
        ]].copy()
        
        before_drop = len(fact_data)
        fact_data = fact_data.dropna(subset=['geography_key'])
        print(f"  Dropped {before_drop - len(fact_data)} rows with missing geography keys")
        
        fact_data.to_sql('fact_ebike_logistics', self.engine, schema='kiota',
                        if_exists='append', index=False, method='multi')
        print(f"  ✓ Loaded {len(fact_data)} e-bike routes")
        
    def load_carbon_credits(self):
        """Load carbon credit price data"""
        logging.info("\n[4/4] Loading carbon credit prices...")
        
        df = pd.read_csv('../../data/raw/carbon_credit_prices.csv')
        print(f"  Read {len(df)} records from CSV")
        
        # Create date keys
        df['date_key'] = pd.to_datetime(df['date']).dt.strftime('%Y%m%d').astype(int)
        
        # Prepare data
        fact_data = df[[
            'date_key', 'price_per_ton_usd', 'market_type', 'standard',
            'verification_status', 'volume_traded_tons', 'kenya_premium_pct'
        ]].copy()
        
        fact_data.to_sql('fact_carbon_credits', self.engine, schema='kiota',
                        if_exists='append', index=False, method='multi')
        print(f"  ✓ Loaded {len(fact_data)} carbon credit records")


    # This needs the sql requirement on text, as in
    # verify_load = text (""" SQL QUERY, YES THAT'S REDUNDANT""")   
    # with self.engine.connect() as conn:
    # conn.execute(verify_load)
    # conn.commit()

    # Not the way below, the way above, but I decided to do this on SQL instead
    # Kept it for the print statements, didn't wanna re-type

    # def verify_load(self):
    #     """Verify all data was loaded successfully"""
    #     print("\n" + "="*60)
    #     print("VERIFICATION: Checking record counts...")
    #     print("="*60)
        
    #     with self.engine.connect() as conn:
    #         counts = pd.read_sql("""
    #             SELECT 'fact_transactions' as table_name, COUNT(*) as count FROM kiota.fact_transactions
    #             UNION ALL
    #             SELECT 'dim_donor', COUNT(*) FROM kiota.dim_donor
    #             UNION ALL
    #             SELECT 'fact_ebike_logistics', COUNT(*) FROM kiota.fact_ebike_logistics
    #             UNION ALL
    #             SELECT 'fact_carbon_credits', COUNT(*) FROM kiota.fact_carbon_credits
    #         """, conn)
            
    #     print(counts.to_string(index=False))
    #     print()
        
    def run(self):
        """Execute missing data load"""
        logging.info("\n" + "="*60)
        logging.info("LOADING MISSING DATA TO KIOTA DATABASE")
        logging.info("="*60)
        
        try:
            logging.info("Starting Load of Missing Data...")
            # self.load_transactions()
            self.load_donors()
            self.load_ebike_logistics()
            self.load_carbon_credits()
            # self.verify_load()
            
            logging.info("="*60)
            logging.info("ALL MISSING DATA LOADED SUCCESSFULLY")
            logging.info("="*60 + "\n")
            logging.info("Loading complete!")
            
        except Exception as e:
            logging.error(f"Pipeline failed: {str(e)}")
            raise

if __name__ == "__main__":
    loader = MissingDataLoader()
    loader.run()