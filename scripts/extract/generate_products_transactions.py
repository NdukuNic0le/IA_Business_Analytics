"""
Generate Product Performance Metrics based on EPA/ISO standards
"""

import pandas as pd
import numpy as np
import random

# Set seed
np.random.seed(42)

# Product specifications based on EPA Tier ratings
products_data = []

# Charcoal stoves
for i in range(1, 4):
    products_data.append({
        'product_id': f'CS00{i}',
        'product_type': 'charcoal_stove',
        'product_model': f'Jiko Smart {i}',
        'thermal_efficiency_pct': round(np.random.uniform(30, 38), 1),
        'pm25_emissions_mg_m3': round(np.random.uniform(200, 300), 0),
        'co_emissions_ppm': round(np.random.uniform(15, 25), 1),
        'fuel_consumption_kg_hour': round(np.random.uniform(0.3, 0.5), 2),
        'lifespan_years': random.choice([3, 4, 5]),
        'maintenance_frequency_months': random.choice([3, 6]),
        'tier_rating': random.choice([2, 3]),
        'unit_cost_usd': 5.0,
        'carbon_reduction_tons_year': round(np.random.uniform(1.2, 1.8), 2)
    })

# Firewood stoves
for i in range(1, 4):
    products_data.append({
        'product_id': f'FS00{i}',
        'product_type': 'firewood_stove',
        'product_model': f'EcoFire {i}',
        'thermal_efficiency_pct': round(np.random.uniform(25, 35), 1),
        'pm25_emissions_mg_m3': round(np.random.uniform(250, 350), 0),
        'co_emissions_ppm': round(np.random.uniform(20, 30), 1),
        'fuel_consumption_kg_hour': round(np.random.uniform(0.5, 0.8), 2),
        'lifespan_years': random.choice([3, 4]),
        'maintenance_frequency_months': random.choice([3, 4, 6]),
        'tier_rating': random.choice([2, 3]),
        'unit_cost_usd': 5.0,
        'carbon_reduction_tons_year': round(np.random.uniform(1.5, 2.2), 2)
    })

# Pellet stoves (under evaluation)
for i in range(1, 3):
    products_data.append({
        'product_id': f'PS00{i}',
        'product_type': 'pellet_stove',
        'product_model': f'PelletPro {i}',
        'thermal_efficiency_pct': round(np.random.uniform(40, 50), 1),
        'pm25_emissions_mg_m3': round(np.random.uniform(100, 150), 0),
        'co_emissions_ppm': round(np.random.uniform(8, 15), 1),
        'fuel_consumption_kg_hour': round(np.random.uniform(0.2, 0.4), 2),
        'lifespan_years': random.choice([5, 6, 7]),
        'maintenance_frequency_months': random.choice([6, 12]),
        'tier_rating': random.choice([3, 4]),
        'unit_cost_usd': 5.0,
        'carbon_reduction_tons_year': round(np.random.uniform(2.0, 2.5), 2)
    })

# Solar lanterns
for i in range(1, 4):
    products_data.append({
        'product_id': f'SL00{i}',
        'product_type': 'solar_lantern',
        'product_model': f'SunLight {i}',
        'thermal_efficiency_pct': 100.0,  # No thermal process
        'pm25_emissions_mg_m3': 0,
        'co_emissions_ppm': 0,
        'fuel_consumption_kg_hour': 0,
        'lifespan_years': random.choice([2, 3]),
        'maintenance_frequency_months': 12,
        'tier_rating': 5,  # Clean energy
        'unit_cost_usd': 5.0,
        'carbon_reduction_tons_year': round(np.random.uniform(0.3, 0.5), 2)  # From kerosene replacement
    })

# Create dataframe
products_df = pd.DataFrame(products_data)

# Save to CSV
products_df.to_csv('/home/claude/product_performance_metrics.csv', index=False)
print(f"Generated {len(products_df)} product specifications")
print("\n=== PRODUCT SUMMARY ===")
print(products_df.groupby('product_type').agg({
    'thermal_efficiency_pct': 'mean',
    'pm25_emissions_mg_m3': 'mean',
    'carbon_reduction_tons_year': 'mean'
}).round(1))

# Generate Financial Transactions
print("\n\nGenerating 400,000 financial transactions...")

transactions = []
transaction_id = 1000000

# Load household data to link transactions
households_df = pd.read_csv('/home/claude/kiota_households_200k.csv')
adopted_households = households_df[households_df['product_type'] != 'none']

for idx, household in adopted_households.iterrows():
    # Initial purchase transaction
    transactions.append({
        'transaction_id': f'TRX{transaction_id}',
        'household_id': household['household_id'],
        'date': household['adoption_date'],
        'amount_ksh': 500,  # ~$5 at 100 KSH/USD
        'type': 'purchase',
        'payment_method': household['payment_method'],
        'status': 'completed',
        'product_type': household['product_type']
    })
    transaction_id += 1
    
    # Subsidy transaction
    if household['payment_method'] != 'Full Subsidy':
        transactions.append({
            'transaction_id': f'TRX{transaction_id}',
            'household_id': household['household_id'],
            'date': household['adoption_date'],
            'amount_ksh': 300,  # Partial subsidy
            'type': 'subsidy',
            'payment_method': 'donor_fund',
            'status': 'completed',
            'product_type': household['product_type']
        })
        transaction_id += 1
    
    # Monthly payments for credit purchases
    if household['payment_method'] == 'Credit':
        payment_date = pd.to_datetime(household['adoption_date'])
        for month in range(1, random.randint(3, 6)):
            payment_date += pd.DateOffset(months=1)
            transactions.append({
                'transaction_id': f'TRX{transaction_id}',
                'household_id': household['household_id'],
                'date': payment_date.strftime('%Y-%m-%d'),
                'amount_ksh': 100,
                'type': 'payment',
                'payment_method': 'mobile_money',
                'status': random.choices(['completed', 'pending', 'failed'], weights=[0.85, 0.10, 0.05])[0],
                'product_type': household['product_type']
            })
            transaction_id += 1
    
    # Maintenance transactions
    if random.random() < 0.3:  # 30% need maintenance
        maint_date = pd.to_datetime(household['adoption_date']) + pd.DateOffset(months=random.randint(3, 12))
        transactions.append({
            'transaction_id': f'TRX{transaction_id}',
            'household_id': household['household_id'],
            'date': maint_date.strftime('%Y-%m-%d'),
            'amount_ksh': random.randint(50, 200),
            'type': 'maintenance',
            'payment_method': random.choice(['cash', 'mobile_money']),
            'status': 'completed',
            'product_type': household['product_type']
        })
        transaction_id += 1

transactions_df = pd.DataFrame(transactions)
transactions_df.to_csv('/home/claude/financial_transactions.csv', index=False)

print(f"Generated {len(transactions_df)} transactions")
print("\n=== TRANSACTION SUMMARY ===")
print(transactions_df['type'].value_counts())
print(f"\nTotal transaction value: KSH {transactions_df['amount_ksh'].sum():,.0f}")