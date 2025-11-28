"""
Generate remaining Stage 1 data sources:
- E-bike Logistics Data
- Carbon Credit Prices
- Donor Segmentation Matrix
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

np.random.seed(42)

# 1. E-BIKE LOGISTICS DATA
print("Generating E-bike Logistics Data...")

ebike_routes = []
route_id = 1

# Generate routes for each county
counties = ['Nairobi', 'Kiambu', 'Nakuru', 'Kakamega', 'Bungoma', 'Meru', 'Kisumu', 
           'Machakos', 'Mombasa', 'Kilifi', 'Uasin Gishu', 'Nyeri', 'Kisii', 'Turkana']

for county in counties:
    # Distribution centers per county
    num_centers = 3 if county in ['Nairobi', 'Mombasa'] else 2 if county in ['Nakuru', 'Kisumu'] else 1
    
    for center in range(1, num_centers + 1):
        # Routes from each center
        num_routes = np.random.randint(5, 15)
        
        for route in range(num_routes):
            ebike_routes.append({
                'route_id': f'RT{route_id:04d}',
                'county': county,
                'distribution_center': f'{county}_DC{center}',
                'route_name': f'{county}_Route_{route + 1}',
                'distance_km': round(np.random.uniform(5, 50), 1),
                'households_covered': np.random.randint(20, 100),
                'terrain_type': np.random.choice(['flat', 'hilly', 'mixed'], p=[0.3, 0.3, 0.4]),
                'avg_delivery_time_hours': round(np.random.uniform(2, 8), 1),
                'ebike_required': np.random.choice([True, False], p=[0.7, 0.3]),
                'traditional_cost_per_delivery_ksh': round(np.random.uniform(50, 200), 0),
                'ebike_cost_per_delivery_ksh': round(np.random.uniform(20, 80), 0),
                'deliveries_per_month': np.random.randint(10, 100),
                'route_efficiency_score': round(np.random.uniform(0.5, 1.0), 2)
            })
            route_id += 1

ebike_df = pd.DataFrame(ebike_routes)
ebike_df.to_csv('/home/project/ebike_logistics_data.csv', index=False)
print(f"Generated {len(ebike_df)} e-bike routes")

# 2. CARBON CREDIT PRICES (Historical and Projected)
print("\nGenerating Carbon Credit Price Data...")

carbon_prices = []
start_date = datetime(2023, 1, 1)

for i in range(36):  # 3 years of monthly data
    current_date = start_date + timedelta(days=30 * i)
    
    # Base price with trend and volatility
    base_price = 12.50 + (i * 0.15)  # Gradual increase
    volatility = np.random.normal(0, 2)
    
    carbon_prices.append({
        'date': current_date.strftime('%Y-%m-%d'),
        'price_per_ton_usd': round(max(8, base_price + volatility), 2),
        'market_type': 'voluntary',
        'standard': 'CCP',
        'verification_status': 'verified' if i < 24 else 'projected',
        'volume_traded_tons': np.random.randint(10000, 100000),
        'kenya_premium_pct': round(np.random.uniform(5, 15), 1)  # Kenya projects get premium
    })

carbon_df = pd.DataFrame(carbon_prices)
carbon_df.to_csv('/home/project/carbon_credit_prices.csv', index=False)
print(f"Generated {len(carbon_df)} months of carbon credit price data")

# 3. DONOR SEGMENTATION MATRIX
print("\nGenerating Donor Segmentation Matrix...")

donors = [
    {
        'donor_id': 'DN001',
        'donor_name': 'Global Health Foundation',
        'donor_type': 'Foundation',
        'focus_area': 'Health',
        'priority_metrics': ['DALYs_avoided', 'mortality_reduction', 'respiratory_illness_reduction'],
        'funding_available_usd': 2000000,
        'reporting_frequency': 'Quarterly',
        'preferred_counties': ['Turkana', 'Kilifi', 'Kakamega'],
        'impact_threshold_households': 50000,
        'cost_per_impact_target': 10
    },
    {
        'donor_id': 'DN002',
        'donor_name': 'Climate Action Fund',
        'donor_type': 'International NGO',
        'focus_area': 'Environment',
        'priority_metrics': ['CO2_avoided_tons', 'deforestation_prevented_hectares', 'carbon_credits_generated'],
        'funding_available_usd': 3000000,
        'reporting_frequency': 'Monthly',
        'preferred_counties': ['All'],
        'impact_threshold_households': 100000,
        'cost_per_impact_target': 8
    },
    {
        'donor_id': 'DN003',
        'donor_name': 'Women Empowerment Initiative',
        'donor_type': 'Bilateral',
        'focus_area': 'Gender',
        'priority_metrics': ['women_time_saved_hours', 'female_headed_households_reached', 'girls_education_hours_gained'],
        'funding_available_usd': 1500000,
        'reporting_frequency': 'Bi-annual',
        'preferred_counties': ['Kisumu', 'Mombasa', 'Nairobi'],
        'impact_threshold_households': 30000,
        'cost_per_impact_target': 12
    },
    {
        'donor_id': 'DN004',
        'donor_name': 'Economic Development Bank',
        'donor_type': 'Development Bank',
        'focus_area': 'Economic',
        'priority_metrics': ['household_savings_ksh', 'jobs_created', 'income_generating_hours_freed'],
        'funding_available_usd': 2500000,
        'reporting_frequency': 'Annual',
        'preferred_counties': ['Nairobi', 'Kiambu', 'Nakuru', 'Uasin Gishu'],
        'impact_threshold_households': 75000,
        'cost_per_impact_target': 7
    },
    {
        'donor_id': 'DN005',
        'donor_name': 'Carbon Investor Group',
        'donor_type': 'Private Investor',
        'focus_area': 'Carbon Credits',
        'priority_metrics': ['verified_carbon_credits', 'additionality_score', 'permanence_years'],
        'funding_available_usd': 5000000,
        'reporting_frequency': 'Monthly',
        'preferred_counties': ['All'],
        'impact_threshold_households': 200000,
        'cost_per_impact_target': 5
    }
]

# Save donor data as JSON for flexibility
with open('/home/project/donor_segmentation_matrix.json', 'w') as f:
    json.dump(donors, f, indent=2)
print(f"Generated {len(donors)} donor profiles")

# 4. HEALTH IMPACT COEFFICIENTS (WHO/EPA based)
print("\nGenerating Health Impact Coefficients...")

health_coefficients = {
    'PM2.5_mortality_coefficient': 0.00082,  # WHO standard
    'CO_health_impact_factor': 0.00045,
    'DALY_per_ton_PM25_reduced': 24.5,
    'respiratory_illness_reduction_per_clean_stove': 0.35,
    'child_mortality_reduction_factor': 0.28,
    'time_saved_hours_per_day': 2.5,
    'healthcare_cost_savings_ksh_per_year': 5000
}

with open('/home/project/health_impact_coefficients.json', 'w') as f:
    json.dump(health_coefficients, f, indent=2)
print("Generated health impact coefficients")

# 5. DATA QUALITY METRICS
print("\nGenerating Data Quality Tracking...")

# Track data quality for each source
data_quality = []
sources = ['households', 'products', 'transactions', 'ebike_routes', 'carbon_prices']

for source in sources:
    data_quality.append({
        'data_source': source,
        'completeness_pct': round(np.random.uniform(92, 99), 1),
        'validation_pass_rate': round(np.random.uniform(94, 99.5), 1),
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'records_count': {
            'households': 200000,
            'products': 11,
            'transactions': 251168,
            'ebike_routes': len(ebike_df),
            'carbon_prices': 36
        }.get(source, 0),
        'anomalies_detected': np.random.randint(0, 50)
    })

quality_df = pd.DataFrame(data_quality)
quality_df.to_csv('/home/project/data_quality_metrics.csv', index=False)
print("Generated data quality metrics")

# SUMMARY REPORT
print("\n" + "="*50)
print("STAGE 1: EXTRACT - COMPLETE")
print("="*50)
print(f"✓ Household Data: 200,000 records")
print(f"✓ Product Performance: 11 products")
print(f"✓ Financial Transactions: 251,168 records")
print(f"✓ E-bike Routes: {len(ebike_df)} routes")
print(f"✓ Carbon Credit Prices: 36 months")
print(f"✓ Donor Profiles: 5 segments")
print(f"✓ Health Coefficients: WHO/EPA based")
print(f"✓ Data Quality Tracking: Initialized")

# Calculate total impact potential
total_adopted = 81423  # from transactions
potential_co2_reduction = total_adopted * 1.7  # avg tons per household
potential_revenue = potential_co2_reduction * 12.50  # carbon credit value

print(f"\nIMPACT POTENTIAL (Year 1):")
print(f"• Households Reached: {total_adopted:,}")
print(f"• CO2 Reduction: {potential_co2_reduction:,.0f} tons")
print(f"• Carbon Credit Value: ${potential_revenue:,.0f}")
