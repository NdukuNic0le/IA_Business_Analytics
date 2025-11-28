# Data Dictionary

This document defines all fields in the Org X SIC Impact Measurement & ROI Analytics System, including data types, valid ranges, business meanings, and usage in calculations.

## Table of Contents

- [Dimension Tables](#dimension-tables)
  - [dim_household](#dim_household)
  - [dim_product](#dim_product)
  - [dim_date](#dim_date)
  - [dim_geography](#dim_geography)
  - [dim_donor](#dim_donor)
- [Fact Tables](#fact-tables)
  - [fact_adoptions](#fact_adoptions)
  - [fact_transactions](#fact_transactions)
  - [fact_impact_metrics](#fact_impact_metrics)
- [Business Rules](#business-rules)
- [Calculated Fields](#calculated-fields)

---

## Dimension Tables

### dim_household

Household demographics and baseline characteristics from the 80-question baseline survey.

| Field | Data Type | Valid Range | Business Meaning | Survey Q# | Used In |
|-------|-----------|-------------|------------------|-----------|---------|
| `household_key` | SERIAL | Auto-increment | Surrogate key for star schema | N/A | All joins |
| `household_id` | VARCHAR(20) | HH-XXXXX-XXXXX | Unique identifier from Salesforce | Q12 | Linking, deduplication |
| `county` | VARCHAR(50) | 14 Kenya counties | Geographic location (Level 1) | Q19 | Geographic analysis, allocation |
| `sub_county` | VARCHAR(50) | Valid sub-counties | Geographic location (Level 2) | Q20 | Drill-down analysis |
| `ward` | VARCHAR(50) | Valid wards | Geographic location (Level 3) | Q21 | Field operations |
| `village` | VARCHAR(100) | Free text | Specific location | Q22 | Field operations |
| `urban_rural` | VARCHAR(10) | Urban, Rural | Settlement type | Derived | Segmentation, fuel type analysis |
| `gps_latitude` | DECIMAL(10,6) | -4.5 to 4.5 | GPS coordinate | Q26 | Mapping, distance calculations |
| `gps_longitude` | DECIMAL(10,6) | 33.5 to 42.0 | GPS coordinate | Q26 | Mapping, distance calculations |
| `head_name` | VARCHAR(100) | Free text | Name of household head | Q13 | PII - not in analytics |
| `head_gender` | VARCHAR(10) | Male, Female | Gender of household head | Q15 | Gender impact analysis |
| `head_age` | INT | 18-100 | Age of household head | Q17 | Demographic segmentation |
| `marital_status` | VARCHAR(20) | Single, Married, Divorced, Widowed | Marital status | Q18 | Vulnerability assessment |
| `education_level` | VARCHAR(50) | None, Primary, Secondary, Tertiary | Highest education | Q28 | Socioeconomic analysis |
| `household_size` | INT | 1-20 | Number of people in household | Q29 | Fuel consumption, impact scaling |
| `children_under_18` | INT | 0-15 | Children under 18 | Q31 | Health impact (vulnerable population) |
| `youth_18_35` | INT | 0-10 | Youth 18-35 years | Q32 | Economic activity analysis |
| `elderly_over_60` | INT | 0-5 | People over 60 | Derived | Vulnerability assessment |
| `primary_economic_activity` | VARCHAR(50) | Farming, Business, Employment, etc. | Main income source | Q34 | Segmentation |
| `monthly_income_ksh` | DECIMAL(12,2) | 0-500,000 | Monthly household income (KES) | Q35 | Affordability, segmentation |
| `owns_land` | BOOLEAN | True, False | Land ownership | Q36 | Asset ownership |
| `land_size_acres` | DECIMAL(10,2) | 0-1000 | Land size if owned | Q37 | Agricultural context |
| `livestock_owned` | VARCHAR(50) | None, Cattle, Goats, etc. | Livestock categories | Q38 | Rural livelihood context |
| `electricity_access` | VARCHAR(20) | Grid, Solar, None | Electricity source | Q60 | Energy poverty assessment |
| `mobile_phone_ownership` | BOOLEAN | True, False | Has mobile phone | Q64 | Payment method eligibility |
| `water_source` | VARCHAR(50) | Piped, Borehole, River, etc. | Primary water source | Q57 | Infrastructure context |
| `toilet_type` | VARCHAR(50) | Flush, Pit latrine, None | Sanitation facility | Q58 | Infrastructure context |
| `control_group` | BOOLEAN | True, False | Is control group member | Q9 | Counterfactual analysis |
| `vulnerability_factors` | TEXT | Comma-separated list | Disability, Elderly, Single Parent, Low Income | Q56 | Vulnerability scoring |
| `created_at` | TIMESTAMP | Valid timestamp | Record creation time | N/A | Audit trail |
| `updated_at` | TIMESTAMP | Valid timestamp | Last update time | N/A | Audit trail |

### dim_product

Product specifications and performance characteristics based on EPA/ISO standards.

| Field | Data Type | Valid Range | Business Meaning | Source | Used In |
|-------|-----------|-------------|------------------|--------|---------|
| `product_key` | SERIAL | Auto-increment | Surrogate key | N/A | All joins |
| `product_id` | VARCHAR(10) | CS001, FS001, PS001, SL001 | Product identifier | Product catalog | Linking |
| `product_type` | VARCHAR(50) | charcoal_stove, firewood_stove, pellet_stove, solar_lantern | Product category | Product catalog | Product mix analysis |
| `product_model` | VARCHAR(50) | Jiko Smart, EcoFire, PelletPro, SunLight | Model name | Product catalog | Reporting |
| `thermal_efficiency_pct` | DECIMAL(5,2) | 25-100 | Thermal efficiency (%) | EPA testing | Fuel savings calculation |
| `pm25_emissions_mg_m3` | DECIMAL(8,2) | 0-500 | PM2.5 emissions (mg/m³) | EPA testing | Health impact calculation |
| `co_emissions_ppm` | DECIMAL(8,2) | 0-50 | Carbon monoxide (ppm) | EPA testing | Health risk assessment |
| `fuel_consumption_kg_hour` | DECIMAL(5,3) | 0-1.0 | Fuel use rate | EPA testing | Cost savings calculation |
| `lifespan_years` | INT | 3-7 | Expected product life | Manufacturer | Depreciation, replacement |
| `maintenance_frequency_months` | INT | 3-12 | Maintenance interval | Manufacturer | Operations planning |
| `tier_rating` | INT | 1-5 | EPA Tier rating | EPA standards | Carbon credit eligibility |
| `unit_cost_usd` | DECIMAL(10,2) | 5-50 | Manufacturing cost | Finance | Subsidy calculation |
| `carbon_reduction_tons_year` | DECIMAL(5,2) | 0.3-2.5 | Annual CO2 reduction per unit | MRV methodology | Carbon credit calculation |
| `created_at` | TIMESTAMP | Valid timestamp | Record creation time | N/A | Audit trail |

### dim_date

Date dimension for time-based analysis with fiscal year support.

| Field | Data Type | Valid Range | Business Meaning | Used In |
|-------|-----------|-------------|------------------|---------|
| `date_key` | INT | YYYYMMDD format | Surrogate key (e.g., 20240115) | All date joins |
| `full_date` | DATE | 2023-01-01 to 2035-12-31 | Actual date | Date display |
| `year` | INT | 2023-2035 | Calendar year | YoY analysis |
| `quarter` | INT | 1-4 | Calendar quarter | QoQ analysis |
| `month` | INT | 1-12 | Month number | Monthly trends |
| `month_name` | VARCHAR(20) | January-December | Month name | Reporting |
| `week` | INT | 1-53 | ISO week number | Weekly analysis |
| `day_of_month` | INT | 1-31 | Day number | Daily patterns |
| `day_of_week` | INT | 0-6 | Day of week (0=Monday) | Operational patterns |
| `day_name` | VARCHAR(20) | Monday-Sunday | Day name | Reporting |
| `is_weekend` | BOOLEAN | True, False | Weekend indicator | Operational patterns |
| `fiscal_year` | INT | 2023-2035 | Fiscal year (July-June) | Financial reporting |
| `fiscal_quarter` | INT | 1-4 | Fiscal quarter | Financial reporting |

### dim_geography

Kenya county demographics and development indicators.

| Field | Data Type | Valid Range | Business Meaning | Source | Used In |
|-------|-----------|-------------|------------------|--------|---------|
| `geography_key` | SERIAL | Auto-increment | Surrogate key | N/A | All joins |
| `county` | VARCHAR(50) | 14 Kenya counties | County name | KNBS | Geographic analysis |
| `region` | VARCHAR(50) | Central, Western, Rift Valley, etc. | Kenya region | KNBS | Regional aggregation |
| `population` | INT | 500,000-5,000,000 | County population | Census 2019 | Penetration calculation |
| `area_sq_km` | DECIMAL(10,2) | 200-70,000 | County area | KNBS | Density analysis |
| `poverty_rate` | DECIMAL(5,2) | 15-80 | Poverty rate (%) | KNBS | Impact prioritization |
| `electrification_rate` | DECIMAL(5,2) | 15-80 | Grid access (%) | KPLC | Energy poverty assessment |
| `created_at` | TIMESTAMP | Valid timestamp | Record creation time | N/A | Audit trail |

### dim_donor

Donor profiles for segmented impact reporting.

| Field | Data Type | Valid Range | Business Meaning | Used In |
|-------|-----------|-------------|------------------|---------|
| `donor_key` | SERIAL | Auto-increment | Surrogate key | All joins |
| `donor_id` | VARCHAR(10) | D001-D999 | Donor identifier | Linking |
| `donor_name` | VARCHAR(100) | Free text | Organization name | Reporting |
| `donor_type` | VARCHAR(50) | Foundation, Government, Corporate, Multilateral | Donor category | Segmentation |
| `focus_area` | VARCHAR(50) | Health, Environment, Gender, Economic | Primary focus | Report customization |
| `funding_available_usd` | DECIMAL(12,2) | 0-100,000,000 | Available funding | Budget planning |
| `reporting_frequency` | VARCHAR(50) | Monthly, Quarterly, Annual | Report schedule | Operations |
| `cost_per_impact_target` | DECIMAL(10,2) | 0-1000 | Target $/impact unit | Performance evaluation |

---

## Fact Tables

### fact_adoptions

Records of clean cookstove/lantern distributions to households.

| Field | Data Type | Valid Range | Business Meaning | Used In |
|-------|-----------|-------------|------------------|---------|
| `adoption_key` | SERIAL | Auto-increment | Surrogate key | N/A |
| `household_key` | INT | FK to dim_household | Household reference | All household joins |
| `product_key` | INT | FK to dim_product | Product reference | Product analysis |
| `adoption_date_key` | INT | FK to dim_date | Distribution date | Time analysis |
| `geography_key` | INT | FK to dim_geography | County reference | Geographic analysis |
| `payment_method` | VARCHAR(50) | Cash, M-Pesa, Credit | How customer paid | Payment analysis |
| `subsidy_amount` | DECIMAL(10,2) | 0-2000 (KES) | Subsidy provided | Financial analysis |
| `actual_price_paid` | DECIMAL(10,2) | 500-700 (KES) | Customer payment (~$5) | Revenue analysis |
| `usage_intensity` | DECIMAL(3,2) | 0.00-1.00 | Percentage of exclusive clean cooking | Stacking behavior, impact calculation |
| `baseline_cooking_method` | VARCHAR(100) | Three-stone, Basic charcoal, etc. | Pre-intervention method | Counterfactual |
| `baseline_fuel_type` | VARCHAR(50) | Firewood, Charcoal, LPG | Pre-intervention fuel | Counterfactual |
| `baseline_weekly_fuel_cost_ksh` | DECIMAL(10,2) | 0-2000 | Pre-intervention weekly cost | Savings calculation |
| `baseline_cooking_hours_per_day` | DECIMAL(5,2) | 1-8 | Pre-intervention cooking time | Time savings |
| `created_at` | TIMESTAMP | Valid timestamp | Record creation time | Audit trail |

### fact_transactions

Financial transactions including payments, subsidies, and maintenance.

| Field | Data Type | Valid Range | Business Meaning | Used In |
|-------|-----------|-------------|------------------|---------|
| `transaction_key` | SERIAL | Auto-increment | Surrogate key | N/A |
| `transaction_id` | VARCHAR(20) | TXN-XXXXX-XXXXX | Unique transaction ID | Deduplication |
| `household_key` | INT | FK to dim_household | Household reference | Customer analysis |
| `product_key` | INT | FK to dim_product | Product reference | Product revenue |
| `transaction_date_key` | INT | FK to dim_date | Transaction date | Time analysis |
| `amount_ksh` | DECIMAL(12,2) | -10000 to 10000 | Transaction amount (KES) | Revenue, refunds |
| `transaction_type` | VARCHAR(50) | Purchase, Payment, Subsidy, Maintenance, Refund | Transaction category | Financial analysis |
| `payment_method` | VARCHAR(50) | Cash, M-Pesa, Bank | Payment channel | Payment analysis |
| `status` | VARCHAR(20) | Completed, Pending, Failed | Transaction status | Reconciliation |
| `created_at` | TIMESTAMP | Valid timestamp | Record creation time | Audit trail |

### fact_impact_metrics

Monthly aggregated impact metrics per household-product combination.

| Field | Data Type | Valid Range | Business Meaning | Used In |
|-------|-----------|-------------|------------------|---------|
| `impact_key` | SERIAL | Auto-increment | Surrogate key | N/A |
| `household_key` | INT | FK to dim_household | Household reference | Impact attribution |
| `product_key` | INT | FK to dim_product | Product reference | Product impact |
| `month_key` | INT | FK to dim_date | Month (first day) | Time aggregation |
| `geography_key` | INT | FK to dim_geography | County reference | Geographic impact |
| `dalys_avoided` | DECIMAL(10,4) | 0-0.1 | DALYs avoided this month | Health impact |
| `mortality_reduction` | DECIMAL(10,6) | 0-0.001 | Mortality reduction | Health impact |
| `respiratory_illness_reduced` | DECIMAL(10,4) | 0-0.5 | Illness reduction | Health impact |
| `co2_avoided_tons` | DECIMAL(10,4) | 0-0.3 | CO2 avoided this month | Environmental impact |
| `pm25_reduced_kg` | DECIMAL(10,4) | 0-1.0 | PM2.5 reduction | Environmental impact |
| `trees_saved_equivalent` | DECIMAL(10,2) | 0-5 | Tree equivalent | Environmental reporting |
| `fuel_cost_savings_ksh` | DECIMAL(12,2) | 0-2000 | Monthly fuel savings | Economic impact |
| `time_saved_hours` | DECIMAL(10,2) | 0-60 | Monthly time savings | Economic impact |
| `healthcare_savings_ksh` | DECIMAL(12,2) | 0-1000 | Healthcare cost avoided | Economic impact |
| `usage_days_in_month` | INT | 0-31 | Days product was used | Usage tracking |
| `stove_stacking_ratio` | DECIMAL(3,2) | 0-1 | Clean vs traditional usage | Behavior tracking |
| `created_at` | TIMESTAMP | Valid timestamp | Record creation time | Audit trail |

---

## Business Rules

### Household Classification

```
Income Bracket:
- Low:    monthly_income_ksh < 10,000 KES
- Medium: monthly_income_ksh >= 10,000 AND < 30,000 KES
- High:   monthly_income_ksh >= 30,000 KES

Family Type:
- Large Family:          children_under_18 > 3
- Family with Children:  children_under_18 > 0 AND <= 3
- No Children:           children_under_18 = 0

Age Group:
- Youth:  head_age < 30
- Adult:  head_age >= 30 AND < 60
- Senior: head_age >= 60
```

### Adoption Classification

```
Adoption Category (based on usage_intensity):
- Full Adoption:    usage_intensity >= 0.80
- Partial Adoption: usage_intensity >= 0.50 AND < 0.80
- Minimal Use:      usage_intensity < 0.50
```

### Impact Coefficients

| Coefficient | Value | Source |
|-------------|-------|--------|
| Mortality per 1,000 HH (baseline) | 2.3 deaths/year | WHO HAP Database |
| Mortality reduction factor | 35% | EPA Tier 3-4 studies |
| DALYs per 1,000 HH (baseline) | 19.4 | WHO Kenya data |
| DALY reduction factor | 40% | WHO methodology |
| Carbon price (voluntary market) | $14.50/ton | Carbon registry avg |
| Exchange rate (USD:KES) | 133 | CBK average |

---

## Calculated Fields

### Silver Layer Views

**silver_households** (derived classifications):
- `income_bracket`: Low/Medium/High
- `family_type`: Large Family/Family with Children/No Children
- `age_group`: Youth/Adult/Senior

**silver_impact_calculations** (impact metrics):
- `co2_avoided_annual`: carbon_reduction_tons_year × usage_intensity
- `carbon_credit_value_usd`: co2_avoided_annual × $14.50
- `mortality_reduction`: PM2.5 reduction × 0.00082 × usage_intensity
- `dalys_avoided`: PM2.5 reduction × 24.5 × usage_intensity
- `annual_fuel_savings_ksh`: baseline_weekly_fuel_cost × 52 × usage_intensity × 0.30

### Gold Layer Views

**gold_executive_summary**:
- `total_households_reached`: COUNT(DISTINCT household_key)
- `total_co2_avoided_tons`: SUM(co2_avoided_annual)
- `pct_of_goal_achieved`: total_households / 975,000 × 100

**gold_county_performance**:
- `penetration_rate`: households_reached / (population / 4.5) × 100
- `roi_ratio`: carbon_credit_value / subsidy_amount
