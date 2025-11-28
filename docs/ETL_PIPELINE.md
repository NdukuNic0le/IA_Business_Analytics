# ETL Pipeline Documentation

This document describes the Extract, Transform, Load (ETL) pipeline for the Kiota SIC Impact Measurement & ROI Analytics System.

## Pipeline Overview
## Layer Transformation Details

### Bronze Layer → Silver Layer

**Script:** `raw_to_processed.py`

#### 1. Household Data Validation

```python
# Quality checks performed
quality_checks = {
    'missing_counties': "SELECT COUNT(*) WHERE county IS NULL",
    'invalid_ages': "SELECT COUNT(*) WHERE head_age < 18 OR head_age > 100",
    'negative_income': "SELECT COUNT(*) WHERE monthly_income_ksh < 0",
    'household_size_anomalies': "SELECT COUNT(*) WHERE household_size < 1 OR household_size > 20"
}
```

**Transformations Applied:**

| Transformation | Logic | Purpose |
|---------------|-------|---------|
| Income bracket | `< 10K = Low, 10-30K = Medium, > 30K = High` | Segmentation |
| Family type | Based on children_under_18 count | Impact targeting |
| Age group | `< 30 = Youth, 30-60 = Adult, > 60 = Senior` | Demographics |
| Data type enforcement | All fields cast to appropriate types | Query performance |

**Output:** `kiota.silver_households` view

#### 2. Adoption Metrics with Counterfactual

```python
# Counterfactual analysis structure
WITH treatment_group AS (
    SELECT 
        county,
        COUNT(DISTINCT household_key) as adopted_households,
        AVG(usage_intensity) as avg_usage_intensity,
        AVG(baseline_weekly_fuel_cost_ksh) as avg_baseline_cost
    FROM fact_adoptions
    JOIN dim_household USING (household_key)
    GROUP BY county
),
control_counts AS (
    SELECT county, COUNT(*) as control_households
    FROM dim_household
    WHERE control_group = true
    GROUP BY county
)
```

**Transformations Applied:**

| Transformation | Logic | Purpose |
|---------------|-------|---------|
| Adoption penetration | `adopted / (adopted + control) × 100` | Market analysis |
| Estimated savings | `baseline_cost × usage_intensity × 0.30` | Impact calculation |
| Control group comparison | Treatment vs Control aggregations | Additionality proof |

**Output:** `kiota.silver_adoption_metrics` view

#### 3. Impact Calculations

```python
# Impact calculation coefficients
coefficients = {
    'pm25_mortality_coefficient': 0.00082,  # WHO standard
    'dalys_per_pm25': 24.5,                 # WHO methodology
    'carbon_price_usd': 14.50,              # Voluntary market
    'fuel_savings_factor': 0.30             # 30% reduction
}
```

**Transformations Applied:**

| Metric | Formula | Unit |
|--------|---------|------|
| CO2 avoided | `carbon_reduction_tons_year × usage_intensity` | tons/year |
| Carbon credit value | `co2_avoided × $14.50` | USD |
| Mortality reduction | `(pm25_emissions / 1000) × 0.00082 × usage_intensity` | lives |
| DALYs avoided | `(pm25_emissions / 1000) × 24.5 × usage_intensity` | DALYs |
| Fuel savings | `baseline_weekly × 52 × usage_intensity × 0.30` | KES/year |
| Time savings | `2.5 hours × 365 × usage_intensity` | hours/year |
| Healthcare savings | `5000 × usage_intensity` | KES/year |

**Output:** `kiota.silver_impact_calculations` view

---

### Silver Layer → Gold Layer

**Script:** `processed_to_final.py`

#### 1. Executive Summary

```sql
CREATE VIEW kiota.gold_executive_summary AS
SELECT 
    COUNT(DISTINCT household_key) as total_households_reached,
    SUM(co2_avoided_annual) as total_co2_avoided_tons,
    SUM(carbon_credit_value_usd) as total_carbon_credit_value,
    SUM(dalys_avoided) as total_dalys_avoided,
    SUM(annual_fuel_savings_ksh) as total_fuel_savings_ksh,
    AVG(usage_intensity) as avg_usage_intensity,
    COUNT(DISTINCT CASE WHEN usage_intensity >= 0.8 THEN household_key END) as full_adopters,
    COUNT(DISTINCT household_key)::float / 975000 * 100 as pct_of_goal_achieved
FROM fact_adoptions
JOIN silver_impact_calculations USING (household_key);
```

#### 2. County Performance

```sql
CREATE VIEW kiota.gold_county_performance AS
SELECT 
    county,
    poverty_rate,
    electrification_rate,
    COUNT(DISTINCT household_key) as households_reached,
    COUNT(DISTINCT household_key)::float / population * 4.5 * 100 as penetration_rate,
    SUM(co2_avoided_annual) as co2_avoided,
    SUM(dalys_avoided) as dalys_avoided,
    SUM(annual_fuel_savings_ksh) as fuel_savings,
    SUM(carbon_credit_value_usd) / NULLIF(SUM(subsidy_amount), 0) as roi_ratio
FROM fact_adoptions
JOIN dim_geography USING (geography_key)
JOIN silver_impact_calculations USING (household_key)
GROUP BY county, poverty_rate, electrification_rate, population;
```

---

## Data Quality Checks

### At Bronze Layer (Load)

| Check | Rule | Action if Failed |
|-------|------|------------------|
| File exists | CSV file present | Abort load |
| Schema match | Columns match expected | Abort load |
| Row count | > 0 rows | Warning |

### At Silver Layer (Transform)

| Check | Rule | Action if Failed |
|-------|------|------------------|
| County values | In list of 14 counties | Flag record |
| Age range | 18-100 | Flag record |
| Income non-negative | >= 0 | Set to NULL |
| Household size | 1-20 | Flag record |
| GPS coordinates | Within Kenya bounds | Flag record |
| Usage intensity | 0-1 | Cap at boundaries |

### At Gold Layer (Aggregate)

| Check | Rule | Action if Failed |
|-------|------|------------------|
| Sum consistency | Totals match detail | Investigate |
| Penetration rate | <= 100% | Investigate |
| ROI ratio | Positive | Investigate |

### Quality Metrics Dashboard

The following metrics are tracked in the data quality dashboard:

```python
quality_metrics = {
    'completeness_pct': 98.5,      # % of required fields populated
    'validation_pass_rate': 97.2,  # % of records passing all rules
    'anomalies_detected': 142,     # Records flagged for review
    'last_updated': '2024-11-28',  # Most recent refresh
    'records_count': 200000        # Total records processed
}
```

---

## Business Rules Applied

### Income Classification

```python
def classify_income(monthly_income_ksh):
    if monthly_income_ksh < 10000:
        return 'Low'
    elif monthly_income_ksh < 30000:
        return 'Medium'
    else:
        return 'High'
```

### Adoption Category

```python
def classify_adoption(usage_intensity):
    if usage_intensity >= 0.80:
        return 'Full Adoption'
    elif usage_intensity >= 0.50:
        return 'Partial Adoption'
    else:
        return 'Minimal Use'
```

### Vulnerability Score

```python
def calculate_vulnerability(household):
    score = 0
    if household['head_gender'] == 'Female':
        score += 1
    if household['monthly_income_ksh'] < 10000:
        score += 2
    if household['children_under_18'] > 3:
        score += 1
    if household['elderly_over_60'] > 0:
        score += 1
    if 'Disability' in household['vulnerability_factors']:
        score += 2
    return score
```

### Impact Calculations

```python
# WHO-based health impact coefficients
MORTALITY_PER_1000_BASELINE = 2.3
MORTALITY_REDUCTION_FACTOR = 0.35
DALYS_PER_1000_BASELINE = 19.4
DALYS_REDUCTION_FACTOR = 0.40

# Environmental coefficients
CARBON_PRICE_USD = 14.50
LEAKAGE_DISCOUNT = 0.05
UNCERTAINTY_DISCOUNT = 0.10

# Economic coefficients
FUEL_SAVINGS_FACTOR = 0.30
TIME_SAVINGS_HOURS_PER_DAY = 2.5
HEALTHCARE_SAVINGS_ANNUAL_KES = 5000
```

---

## Refresh Schedule Recommendations

### Demo/Development

| Layer | Frequency | Method |
|-------|-----------|--------|
| Bronze | On-demand | Full refresh |
| Silver | After Bronze | Full refresh |
| Gold | After Silver | Full refresh |

### Production

| Layer | Frequency | Method | Window |
|-------|-----------|--------|--------|
| Bronze | Daily | Incremental (new records only) | 2:00-3:00 AM |
| Silver | Daily | Incremental + affected records | 3:00-4:00 AM |
| Gold | Daily | Full refresh (aggregations) | 4:00-5:00 AM |
| Power BI | Daily | Scheduled refresh | 5:30 AM |

### Incremental Load Strategy

```python
# For production: Only process new/changed records
def get_incremental_records(last_run_timestamp):
    query = """
    SELECT * FROM salesforce_export
    WHERE modified_date > %s
    OR created_date > %s
    """
    return execute_query(query, [last_run_timestamp, last_run_timestamp])
```

---

## Error Handling

### Logging Configuration

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
```

### Exception Handling Pattern

```python
def run_pipeline():
    try:
        logging.info("Starting ETL pipeline...")
        
        # Step 1: Validate
        validate_households()
        
        # Step 2: Calculate
        calculate_adoption_metrics()
        create_impact_calculations()
        
        # Step 3: Report
        generate_quality_report()
        
        logging.info("ETL pipeline complete!")
        
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        send_alert(f"ETL Pipeline Failed: {str(e)}")
        raise
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Pipeline duration | > 30 minutes | Warning |
| Records processed | < 90% of expected | Error |
| Validation failures | > 5% | Warning |
| Null values in required fields | > 2% | Warning |

### Audit Trail

Each pipeline run logs:

- Start/end timestamps
- Records processed per layer
- Quality check results
- Errors and warnings
- User/process that triggered run
