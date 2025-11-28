# Impact Measurement & ROI Analytics System

**Strategic Decision-Support for Org X SIC Clean Energy Scale-Up**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg)](https://postgresql.org)
[![Power BI](https://img.shields.io/badge/Power%20BI-Desktop-F2C811.svg)](https://powerbi.microsoft.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Project Overview

This analytics system supports **Org X** in measuring impact, optimizing resource allocation, and ensuring accountability for their clean energy deployment across Kenya. The system complements Org X's operational Salesforce platform by providing strategic decision-support capabilities.


### Solution

A comprehensive analytics layer that transforms operational data into actionable insights through:

- **5-page interactive Power BI dashboard** covering executive KPIs, impact analysis, financial performance, and scenario planning
- **Investment optimization model** using linear programming to allocate resources across 14 counties
- **Carbon MRV documentation** ready for CCP verification and auditor review

## Key Results

| Metric | Value |
|--------|-------|
| Households Reached | 81,423 |
| Lives Saved | 85 |
| CO2 Avoided | 128,648 tons |
| Carbon Credit Revenue Potential | $1.86M |
| Cost per DALY Avoided | KES 16,000 (~$120) |

## Data Scope

| Parameter | Value |
|-----------|-------|
| Total Households | 200,000 (81,423 adopted) |
| Financial Transactions | 251,168 records |
| Counties Covered | 14 Kenya counties |
| Product Types | Charcoal stoves, Firewood stoves, Pellet stoves, Solar lanterns |
| Time Period | Year 1 (2024) |

## Repository Structure

```
Org X-sic-analytics/
├── data/
│   ├── raw/                          # Bronze layer (original data)
│   └── processed/                    # Silver/Gold layers
├── sql/
│   └── create_star_schema.sql        # PostgreSQL star schema
├── etl/
│   ├── raw_to_processed.py           # Bronze → Silver transformation
│   ├── processed_to_final.py         # Silver → Gold transformation
│   └── load_to_database.py           # Data loading scripts
├── models/
│   └── investment_optimization_model.py  # Linear programming model
├── powerbi/
│   └── Org X_SIC_Dashboard.pbix      # Power BI report
├── docs/
│   ├── ARCHITECTURE.md               # System architecture
│   ├── DATA_DICTIONARY.md            # Field definitions
│   ├── ETL_PIPELINE.md               # ETL documentation
│   └── SALESFORCE_INTEGRATION.md     # Integration guide
├── outputs/
│   ├── optimization_*.png            # Model visualizations
│   └── allocation_*.csv              # Optimization results
├── requirements.txt
└── README.md
```

## Deliverables

### 1. Power BI Dashboard (5 Pages)

| Page | Purpose | Key Questions Answered |
|------|---------|----------------------|
| Executive Dashboard | At-a-glance KPIs | Are we on track? What's our overall impact? |
| Impact Deep Dive | Counterfactual analysis | Can we prove additionality? |
| Financial Performance | Cost efficiency | What's our cost per DALY? |
| Customer Analytics | Segmentation | Who's at risk of churning? |
| Scenario Planning | What-if analysis | What if we change product mix? |

### 2. Investment Optimization Model

Linear programming model that determines optimal resource allocation across 14 counties with:

**Objectives:**
- Maximize lives saved
- Maximize CO2 avoided
- Maximize households reached

**Constraints:**
- Budget (≤ $500K or $1M)
- Equity (minimum 3% per county)
- Capacity (maximum 25% penetration per county)

### 3. Documentation Package

- Carbon MRV Methodology (CCP-compliant)
- Technical Architecture
- Data Dictionary (35+ fields)
- ETL Pipeline Documentation
- Salesforce Integration Guide

## Technologies

| Category | Technologies |
|----------|-------------|
| Database | PostgreSQL 15+ |
| ETL | Python (pandas, SQLAlchemy) |
| Visualization | Power BI Desktop |
| Optimization | Python (PuLP) |
| Version Control | Git, GitHub |

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 15+
- Power BI Desktop
- ODBC Driver 17 for PostgreSQL

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/Org X-sic-analytics.git
cd Org X-sic-analytics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### Database Setup

```bash
# Create database
psql -U postgres -c "CREATE DATABASE Org X_sic_impact;"

# Create schema
psql -U postgres -d Org X_sic_impact -f sql/create_star_schema.sql

# Load data
python etl/load_to_database.py
```

### Run ETL Pipeline

```bash
# Bronze → Silver transformation
python etl/raw_to_processed.py

# Silver → Gold transformation
python etl/processed_to_final.py
```

### Run Optimization Model

```bash
python models/investment_optimization_model.py
```

## Key Findings

### 1. Geographic Prioritization

Turkana County shows highest impact potential due to 79.4% poverty rate. Optimal allocation for lives saved: 61% of budget to Turkana.

### 2. Equity vs Efficiency Tradeoff

The 3% equity constraint costs only 8.1% efficiency but ensures all 14 counties receive intervention.

### 3. Cost Effectiveness

Cost per DALY avoided of KES 16,000 (~$120) is highly cost-effective by WHO standards (<$500/DALY is excellent).

### 4. Counterfactual Evidence

Clear additionality demonstrated: treatment group shows 30% fuel cost reduction vs 0% in control group.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- WHO Global Health Observatory for health impact coefficients
- EPA for cookstove emission standards
