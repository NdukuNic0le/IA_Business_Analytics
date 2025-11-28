"""
Stage 1: EXTRACT - Synthetic Household Data Generation
For Kiota SIC Impact Measurement Project
Generates 200,000 household records across 14 Kenya counties
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Kenya counties configuration (14 counties as specified)
COUNTIES = {
    'Nairobi': {'urban_pct': 0.95, 'population_weight': 0.15},
    'Kiambu': {'urban_pct': 0.60, 'population_weight': 0.08},
    'Nakuru': {'urban_pct': 0.45, 'population_weight': 0.07},
    'Kakamega': {'urban_pct': 0.20, 'population_weight': 0.06},
    'Bungoma': {'urban_pct': 0.25, 'population_weight': 0.05},
    'Meru': {'urban_pct': 0.30, 'population_weight': 0.05},
    'Kisumu': {'urban_pct': 0.40, 'population_weight': 0.06},
    'Machakos': {'urban_pct': 0.35, 'population_weight': 0.05},
    'Mombasa': {'urban_pct': 0.85, 'population_weight': 0.08},
    'Kilifi': {'urban_pct': 0.25, 'population_weight': 0.06},
    'Uasin Gishu': {'urban_pct': 0.50, 'population_weight': 0.07},
    'Nyeri': {'urban_pct': 0.35, 'population_weight': 0.04},
    'Kisii': {'urban_pct': 0.20, 'population_weight': 0.05},
    'Turkana': {'urban_pct': 0.15, 'population_weight': 0.13}
}

# Product types aligned with Kiota's actual products
PRODUCTS = {
    'charcoal_stove': {'base_price': 5, 'efficiency': 0.35, 'emissions_reduction': 0.40},
    'firewood_stove': {'base_price': 5, 'efficiency': 0.30, 'emissions_reduction': 0.35},
    'pellet_stove': {'base_price': 5, 'efficiency': 0.45, 'emissions_reduction': 0.50},
    'solar_lantern': {'base_price': 5, 'efficiency': 1.0, 'emissions_reduction': 0.10},
    'none': {'base_price': 0, 'efficiency': 0, 'emissions_reduction': 0}  # Control group
}

def generate_households(num_households=200000):
    """Generate synthetic household data"""
    
    households = []
    
    # Calculate households per county based on weights
    county_distribution = {}
    for county, config in COUNTIES.items():
        county_count = int(num_households * config['population_weight'])
        county_distribution[county] = county_count
    
    # Adjust for rounding
    total_assigned = sum(county_distribution.values())
    if total_assigned < num_households:
        county_distribution['Nairobi'] += num_households - total_assigned
    
    household_id = 1000000  # Start from a meaningful number
    
    for county, count in county_distribution.items():
        for i in range(count):
            # Determine urban/rural
            is_urban = random.random() < COUNTIES[county]['urban_pct']
            
            # Generate household characteristics
            household = {
                'household_id': f'HH{household_id}',
                'county': county,
                'sub_county': f"{county}_Sub_{random.randint(1, 5)}",
                'ward': f"Ward_{random.randint(1, 20)}",
                'village': f"Village_{random.randint(1, 50)}",
                'urban_rural': 'Urban' if is_urban else 'Rural',
                
                # GPS coordinates (approximate for each county)
                'gps_latitude': np.random.normal(-0.5 if county == 'Nairobi' else -1.0, 0.5),
                'gps_longitude': np.random.normal(37.0 if county == 'Nairobi' else 36.5, 0.5),
                
                # Demographics
                'head_name': f"Person_{household_id}",
                'head_id': f"ID{random.randint(10000000, 99999999)}",
                'head_gender': random.choice(['Male', 'Female']),
                'head_age': int(np.random.normal(45, 12)),
                'marital_status': random.choices(
                    ['Married', 'Single', 'Widowed', 'Divorced'],
                    weights=[0.60, 0.20, 0.10, 0.10]
                )[0],
                'education_level': random.choices(
                    ['None', 'Primary', 'Secondary', 'Tertiary'],
                    weights=[0.10, 0.35, 0.40, 0.15] if is_urban else [0.20, 0.45, 0.30, 0.05]
                )[0],
                
                # Household composition
                'household_size': int(np.random.normal(4.5, 1.5)) if not is_urban else int(np.random.normal(3.5, 1.2)),
                'children_under_18': int(np.random.normal(2, 1)) if not is_urban else int(np.random.normal(1.5, 0.8)),
                'youth_18_35': random.randint(0, 2),
                'elderly_over_60': random.randint(0, 1),
                
                # Economic indicators
                'primary_economic_activity': random.choices(
                    ['Farming', 'Business', 'Employment', 'Casual Labor', 'Other'],
                    weights=[0.10, 0.25, 0.45, 0.15, 0.05] if is_urban else [0.60, 0.15, 0.10, 0.10, 0.05]
                )[0],
                'monthly_income_ksh': int(np.random.lognormal(
                    np.log(25000 if is_urban else 15000), 0.5
                )),
                
                # Land and assets
                'owns_land': random.random() < (0.30 if is_urban else 0.75),
                'land_size_acres': round(np.random.exponential(2), 1) if random.random() < 0.75 else 0,
                'livestock_owned': random.choices(
                    ['None', 'Chickens', 'Goats', 'Cattle', 'Mixed'],
                    weights=[0.60, 0.20, 0.10, 0.05, 0.05] if is_urban else [0.20, 0.25, 0.20, 0.20, 0.15]
                )[0],
                
                # Current cooking methods (before intervention)
                'baseline_cooking_method': random.choices(
                    ['Three-stone fire', 'Charcoal stove', 'Kerosene', 'LPG', 'Electric'],
                    weights=[0.05, 0.40, 0.30, 0.15, 0.10] if is_urban else [0.45, 0.35, 0.15, 0.03, 0.02]
                )[0],
                'cooking_hours_per_day': round(np.random.normal(3 if is_urban else 4, 1), 1),
                'meals_per_day': random.choices([2, 3], weights=[0.3, 0.7])[0],
                
                # Fuel consumption and costs (baseline)
                'baseline_fuel_type': random.choices(
                    ['Charcoal', 'Firewood', 'Kerosene', 'LPG', 'Mixed'],
                    weights=[0.40, 0.10, 0.25, 0.15, 0.10] if is_urban else [0.20, 0.50, 0.15, 0.05, 0.10]
                )[0],
                'weekly_fuel_cost_ksh': int(np.random.normal(
                    800 if is_urban else 600, 200
                )),
                
                # Health indicators
                'respiratory_issues_reported': random.random() < 0.35,
                'cooking_smoke_problems': random.random() < 0.45,
                
                # Infrastructure
                'electricity_access': random.choices(
                    ['Grid', 'Solar', 'None'],
                    weights=[0.85, 0.10, 0.05] if is_urban else [0.25, 0.15, 0.60]
                )[0],
                'mobile_phone_ownership': random.random() < (0.95 if is_urban else 0.75),
                'water_source': random.choices(
                    ['Piped', 'Borehole', 'Well', 'River', 'Other'],
                    weights=[0.70, 0.15, 0.10, 0.03, 0.02] if is_urban else [0.15, 0.30, 0.30, 0.20, 0.05]
                )[0],
                'toilet_type': random.choices(
                    ['Flush', 'VIP latrine', 'Pit latrine', 'None'],
                    weights=[0.60, 0.25, 0.14, 0.01] if is_urban else [0.10, 0.20, 0.65, 0.05]
                )[0],
                
                # Program participation
                'control_group': random.random() < 0.20,  # 20% control group for counterfactual
                'adoption_date': None,
                'product_type': None,
                'payment_method': None,
                'subsidy_amount': None,
                'usage_intensity': None,
                
                # Data quality
                'data_collection_date': datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365)),
                'data_collector_id': f"DC{random.randint(100, 150)}",
                'data_validated': random.random() < 0.95,
                'consent_obtained': True
            }
            
            # For treatment group, assign products
            if not household['control_group']:
                # S-curve adoption pattern
                days_since_start = random.randint(0, 365)
                adoption_probability = 1 / (1 + np.exp(-0.02 * (days_since_start - 180)))
                
                if random.random() < adoption_probability:
                    # Assign product based on location and income
                    if household['electricity_access'] == 'None':
                        product_weights = [0.40, 0.50, 0.05, 0.05]  # Less solar lanterns
                    else:
                        product_weights = [0.35, 0.30, 0.15, 0.20]  # More balanced
                    
                    household['product_type'] = random.choices(
                        ['charcoal_stove', 'firewood_stove', 'pellet_stove', 'solar_lantern'],
                        weights=product_weights
                    )[0]
                    
                    household['adoption_date'] = datetime(2024, 1, 1) + timedelta(days=days_since_start)
                    household['payment_method'] = random.choices(
                        ['Cash', 'Mobile Money', 'Credit', 'Full Subsidy'],
                        weights=[0.20, 0.45, 0.25, 0.10]
                    )[0]
                    household['subsidy_amount'] = 5.0  # Fixed $5 subsidy
                    household['usage_intensity'] = round(random.uniform(0.3, 1.0), 2)  # Stove stacking behavior
                else:
                    household['product_type'] = 'none'
            else:
                household['product_type'] = 'none'
            
            # Generate unique vulnerability factors
            vulnerability_factors = []
            if household['head_age'] > 60:
                vulnerability_factors.append('Elderly')
            if household['marital_status'] in ['Widowed', 'Divorced'] and household['children_under_18'] > 0:
                vulnerability_factors.append('Single Parent')
            if household['monthly_income_ksh'] < 10000:
                vulnerability_factors.append('Low Income')
            if random.random() < 0.05:
                vulnerability_factors.append('Disability')
            
            household['vulnerability_factors'] = ','.join(vulnerability_factors) if vulnerability_factors else 'None'
            
            households.append(household)
            household_id += 1
    
    return pd.DataFrame(households)

def generate_summary_statistics(df):
    """Generate summary statistics for validation"""
    stats = {
        'total_households': len(df),
        'control_group_pct': (df['control_group'].sum() / len(df)) * 100,
        'adoption_rate': (df['product_type'] != 'none').sum() / len(df) * 100,
        'avg_household_size': df['household_size'].mean(),
        'avg_monthly_income': df['monthly_income_ksh'].mean(),
        'urban_pct': (df['urban_rural'] == 'Urban').sum() / len(df) * 100,
        'product_distribution': df['product_type'].value_counts().to_dict(),
        'county_distribution': df['county'].value_counts().to_dict()
    }
    return stats

# Generate the data
print("Generating 200,000 household records...")
households_df = generate_households(200000)

# Save to CSV
households_df.to_csv('/home/claude/kiota_households_200k.csv', index=False)
print(f"Saved {len(households_df)} records to kiota_households_200k.csv")

# Generate and save summary statistics
stats = generate_summary_statistics(households_df)
with open('/home/claude/kiota_data_summary.json', 'w') as f:
    json.dump(stats, f, indent=2, default=str)
print("\nSummary statistics saved to kiota_data_summary.json")

# Display summary
print("\n=== DATA GENERATION SUMMARY ===")
print(f"Total Households: {stats['total_households']:,}")
print(f"Control Group: {stats['control_group_pct']:.1f}%")
print(f"Adoption Rate: {stats['adoption_rate']:.1f}%")
print(f"Average Household Size: {stats['avg_household_size']:.1f}")
print(f"Average Monthly Income: KSH {stats['avg_monthly_income']:,.0f}")
print(f"Urban Percentage: {stats['urban_pct']:.1f}%")

print("\n=== PRODUCT DISTRIBUTION ===")
for product, count in stats['product_distribution'].items():
    print(f"{product}: {count:,} ({count/stats['total_households']*100:.1f}%)")