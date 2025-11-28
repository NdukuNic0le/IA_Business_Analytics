"""
Investment Optimization Model for Kiota SIC
============================================
Optimizes resource allocation across 14 Kenya counties to maximize impact
under budget constraints using linear programming.

Business Question: "How should we allocate $500K-$1M across 14 counties 
to maximize lives saved, CO2 avoided, or households reached?"

"""

import pandas as pd
import numpy as np
from pulp import (
    LpProblem, LpMaximize, LpVariable, lpSum, 
    LpStatus, value, PULP_CBC_CMD
)
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for professional visualizations
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# ============================================
# DATA SETUP
# ============================================

def load_county_data():
    """
    Load and prepare county-level parameters for optimization.
    Data sourced from Kenya census and project data.
    """
    counties = pd.DataFrame([
        {'county': 'Nairobi', 'region': 'Central', 'population': 4397073, 
         'poverty_rate': 16.7, 'electrification_rate': 77.6},
        {'county': 'Kiambu', 'region': 'Central', 'population': 2417735,
         'poverty_rate': 21.8, 'electrification_rate': 71.2},
        {'county': 'Nakuru', 'region': 'Rift Valley', 'population': 2162202,
         'poverty_rate': 29.9, 'electrification_rate': 51.3},
        {'county': 'Kakamega', 'region': 'Western', 'population': 1867579,
         'poverty_rate': 36.4, 'electrification_rate': 38.1},
        {'county': 'Bungoma', 'region': 'Western', 'population': 1670570,
         'poverty_rate': 52.2, 'electrification_rate': 31.5},
        {'county': 'Meru', 'region': 'Eastern', 'population': 1545714,
         'poverty_rate': 28.3, 'electrification_rate': 42.7},
        {'county': 'Kisumu', 'region': 'Nyanza', 'population': 1155574,
         'poverty_rate': 35.0, 'electrification_rate': 48.2},
        {'county': 'Machakos', 'region': 'Eastern', 'population': 1421932,
         'poverty_rate': 32.7, 'electrification_rate': 54.8},
        {'county': 'Mombasa', 'region': 'Coast', 'population': 1208333,
         'poverty_rate': 34.8, 'electrification_rate': 65.1},
        {'county': 'Kilifi', 'region': 'Coast', 'population': 1453787,
         'poverty_rate': 48.8, 'electrification_rate': 37.4},
        {'county': 'Uasin Gishu', 'region': 'Rift Valley', 'population': 1163186,
         'poverty_rate': 30.3, 'electrification_rate': 56.9},
        {'county': 'Nyeri', 'region': 'Central', 'population': 759164,
         'poverty_rate': 20.7, 'electrification_rate': 68.3},
        {'county': 'Kisii', 'region': 'Nyanza', 'population': 1266860,
         'poverty_rate': 44.2, 'electrification_rate': 29.4},
        {'county': 'Turkana', 'region': 'Rift Valley', 'population': 926976,
         'poverty_rate': 79.4, 'electrification_rate': 15.2}
    ])
    
    # Derived parameters for optimization
    # Households estimated as population / 4.5 (avg household size in Kenya)
    counties['est_households'] = (counties['population'] / 4.5).astype(int)
    
    # Energy poverty rate = 100% - electrification rate (simplified proxy)
    # This identifies households relying on traditional cooking fuels
    counties['energy_poverty_rate'] = 100 - counties['electrification_rate']
    
    # Target market = households * energy poverty rate
    counties['target_market'] = (counties['est_households'] * 
                                  counties['energy_poverty_rate'] / 100).astype(int)
    
    return counties


def load_product_data():
    """
    Load product performance metrics for impact calculations.
    """
    products = pd.DataFrame([
        {'product_type': 'charcoal_stove', 'unit_cost_usd': 15.0, 
         'sale_price_usd': 5.0, 'carbon_reduction_tons_year': 1.41,
         'pm25_reduction_pct': 70, 'thermal_efficiency': 31.5},
        {'product_type': 'firewood_stove', 'unit_cost_usd': 18.0, 
         'sale_price_usd': 5.0, 'carbon_reduction_tons_year': 1.68,
         'pm25_reduction_pct': 72, 'thermal_efficiency': 30.3},
        {'product_type': 'pellet_stove', 'unit_cost_usd': 45.0, 
         'sale_price_usd': 5.0, 'carbon_reduction_tons_year': 2.35,
         'pm25_reduction_pct': 85, 'thermal_efficiency': 47.1},
        {'product_type': 'solar_lantern', 'unit_cost_usd': 12.0, 
         'sale_price_usd': 5.0, 'carbon_reduction_tons_year': 0.34,
         'pm25_reduction_pct': 0, 'thermal_efficiency': 100}
    ])
    
    # Calculate subsidy per unit
    products['subsidy_per_unit'] = products['unit_cost_usd'] - products['sale_price_usd']
    
    return products


def calculate_impact_coefficients():
    """
    Calculate impact coefficients based on WHO/EPA standards.
    
    Sources:
    - WHO Global Health Observatory: HAP mortality rates
    - EPA emission factors for cookstoves
    - Kenya-specific epidemiological data
    """
    coefficients = {
        # Health Impact Coefficients
        'mortality_per_1000_hh_baseline': 2.3,  # Deaths per 1000 HH/year from HAP
        'mortality_reduction_factor': 0.35,      # 35% reduction with clean cookstoves
        'dalys_per_1000_hh_baseline': 19.4,     # WHO Kenya HAP data
        'dalys_reduction_factor': 0.40,          # 40% DALY reduction
        
        # Environmental Coefficients
        'avg_carbon_reduction_tons': 1.58,       # Weighted avg across cookstove types
        'carbon_price_usd': 14.50,               # Current voluntary market price
        
        # Economic Coefficients (annual)
        'fuel_savings_ksh_annual': 15600,        # Average household fuel savings
        'time_savings_hours_annual': 730,        # 2 hours/day saved
        'healthcare_savings_ksh_annual': 5000,   # Reduced medical expenses
        
        # Operational Costs (per household deployed)
        'distribution_cost_usd': 3.0,            # Last-mile delivery
        'training_cost_usd': 2.0,                # Household training
        'monitoring_cost_usd': 1.5,              # Annual monitoring
        'admin_overhead_pct': 0.15               # 15% administrative overhead
    }
    
    return coefficients


def calculate_county_costs(counties, products, coefficients):
    """
    Calculate cost per household reached for each county.
    
    Cost varies by:
    - Distance/remoteness (proxy: inverse of electrification rate)
    - Product mix (weighted by county preferences)
    - Operational efficiency (economies of scale)
    """
    # Base cost per household (product + operations)
    # Using weighted average product cost (55% charcoal, 35% firewood, 2% pellet, 8% solar)
    product_weights = {'charcoal_stove': 0.55, 'firewood_stove': 0.35, 
                       'pellet_stove': 0.02, 'solar_lantern': 0.08}
    
    weighted_product_cost = sum(
        products[products['product_type'] == pt]['subsidy_per_unit'].values[0] * weight
        for pt, weight in product_weights.items()
    )
    
    # Operational costs
    operational_cost = (coefficients['distribution_cost_usd'] + 
                       coefficients['training_cost_usd'] + 
                       coefficients['monitoring_cost_usd'])
    
    base_cost = weighted_product_cost + operational_cost
    
    # Remoteness multiplier (1.0 - 1.5x based on electrification)
    # Lower electrification = more remote = higher cost
    counties['remoteness_factor'] = 1.0 + (100 - counties['electrification_rate']) / 200
    
    # Total cost per household
    counties['cost_per_hh_usd'] = base_cost * counties['remoteness_factor']
    counties['cost_per_hh_usd'] = counties['cost_per_hh_usd'] * (1 + coefficients['admin_overhead_pct'])
    
    return counties


def calculate_impact_per_household(counties, coefficients):
    """
    Calculate impact metrics per household for each county.
    
    Impact varies by:
    - Baseline energy poverty (higher poverty = higher impact potential)
    - County vulnerability factors
    """
    # Lives saved per 1000 households per year
    base_lives_saved = (coefficients['mortality_per_1000_hh_baseline'] * 
                        coefficients['mortality_reduction_factor'])
    
    # Adjust by poverty rate (higher poverty = higher impact)
    counties['poverty_multiplier'] = 1.0 + (counties['poverty_rate'] - 30) / 100
    counties['poverty_multiplier'] = counties['poverty_multiplier'].clip(0.8, 1.5)
    
    # Lives saved per household
    counties['lives_saved_per_hh'] = (base_lives_saved / 1000) * counties['poverty_multiplier']
    
    # CO2 avoided per household (tons/year)
    counties['co2_per_hh'] = coefficients['avg_carbon_reduction_tons']
    
    return counties


# ============================================
# OPTIMIZATION MODEL
# ============================================

class KiotaOptimizer:
    """
    Linear Programming optimizer for Kiota SIC resource allocation.
    
    Supports three objectives:
    1. Maximize lives saved
    2. Maximize CO2 avoided
    3. Maximize households reached
    """
    
    def __init__(self, counties, budget_usd, objective='lives_saved'):
        """
        Initialize the optimizer.
        
        Parameters:
        -----------
        counties : DataFrame
            County data with costs and impact coefficients
        budget_usd : float
            Total budget in USD
        objective : str
            Optimization objective: 'lives_saved', 'co2_avoided', or 'households_reached'
        """
        self.counties = counties.copy()
        self.budget = budget_usd
        self.objective = objective
        self.model = None
        self.solution = None
        
        # Constraints
        self.min_allocation_pct = 0.03  # Minimum 3% per county
        self.max_penetration_pct = 0.25  # Maximum 25% penetration
        
    def build_model(self):
        """Build the linear programming model."""
        n_counties = len(self.counties)
        county_names = self.counties['county'].tolist()
        
        # Create the model
        self.model = LpProblem(f"Kiota_Allocation_{self.objective}", LpMaximize)
        
        # Decision variables: households to reach in each county
        self.households = {
            county: LpVariable(f"HH_{county}", lowBound=0, cat='Continuous')
            for county in county_names
        }
        
        # Objective function
        if self.objective == 'lives_saved':
            self.model += lpSum(
                self.households[row['county']] * row['lives_saved_per_hh']
                for _, row in self.counties.iterrows()
            ), "Total_Lives_Saved"
            
        elif self.objective == 'co2_avoided':
            self.model += lpSum(
                self.households[row['county']] * row['co2_per_hh']
                for _, row in self.counties.iterrows()
            ), "Total_CO2_Avoided"
            
        elif self.objective == 'households_reached':
            self.model += lpSum(
                self.households[county] for county in county_names
            ), "Total_Households_Reached"
        
        # CONSTRAINTS
        
        # 1. Budget constraint
        self.model += (
            lpSum(
                self.households[row['county']] * row['cost_per_hh_usd']
                for _, row in self.counties.iterrows()
            ) <= self.budget,
            "Budget_Constraint"
        )
        
        # 2. Equity constraint: minimum 3% of budget per county
        min_budget_per_county = self.budget * self.min_allocation_pct
        for _, row in self.counties.iterrows():
            min_households = min_budget_per_county / row['cost_per_hh_usd']
            self.model += (
                self.households[row['county']] >= min_households,
                f"Min_Equity_{row['county']}"
            )
        
        # 3. Capacity constraint: max 25% penetration of target market
        for _, row in self.counties.iterrows():
            max_households = row['target_market'] * self.max_penetration_pct
            self.model += (
                self.households[row['county']] <= max_households,
                f"Max_Penetration_{row['county']}"
            )
        
        return self
    
    def solve(self, verbose=False):
        """Solve the optimization model."""
        if self.model is None:
            self.build_model()
        
        # Solve with CBC solver
        solver = PULP_CBC_CMD(msg=0)
        self.model.solve(solver)
        
        # Extract solution
        self.solution = pd.DataFrame({
            'county': self.counties['county'],
            'households_allocated': [
                value(self.households[county]) 
                for county in self.counties['county']
            ]
        })
        
        # Merge with county data
        self.solution = self.solution.merge(self.counties, on='county')
        
        # Calculate investment and impact
        self.solution['investment_usd'] = (
            self.solution['households_allocated'] * self.solution['cost_per_hh_usd']
        )
        self.solution['allocation_pct'] = (
            self.solution['investment_usd'] / self.budget * 100
        )
        self.solution['lives_saved'] = (
            self.solution['households_allocated'] * self.solution['lives_saved_per_hh']
        )
        self.solution['co2_avoided_tons'] = (
            self.solution['households_allocated'] * self.solution['co2_per_hh']
        )
        self.solution['penetration_achieved_pct'] = (
            self.solution['households_allocated'] / self.solution['target_market'] * 100
        )
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"OPTIMIZATION RESULTS: {self.objective.upper().replace('_', ' ')}")
            print(f"Budget: ${self.budget:,.0f}")
            print(f"Status: {LpStatus[self.model.status]}")
            print(f"{'='*60}")
            
        return self
    
    def get_summary(self):
        """Get summary statistics of the solution."""
        if self.solution is None:
            raise ValueError("Model not solved yet. Call solve() first.")
        
        summary = {
            'objective': self.objective,
            'budget_usd': self.budget,
            'status': LpStatus[self.model.status],
            'total_households': self.solution['households_allocated'].sum(),
            'total_lives_saved': self.solution['lives_saved'].sum(),
            'total_co2_avoided_tons': self.solution['co2_avoided_tons'].sum(),
            'total_investment': self.solution['investment_usd'].sum(),
            'budget_utilization_pct': self.solution['investment_usd'].sum() / self.budget * 100,
            'avg_cost_per_household': self.solution['investment_usd'].sum() / 
                                       self.solution['households_allocated'].sum(),
            'avg_penetration_pct': self.solution['penetration_achieved_pct'].mean()
        }
        
        return summary


# ============================================
# SENSITIVITY ANALYSIS
# ============================================

def run_sensitivity_analysis(counties, budget_levels, objectives):
    """
    Run sensitivity analysis across budget levels and objectives.
    
    Parameters:
    -----------
    counties : DataFrame
        Prepared county data
    budget_levels : list
        Budget amounts to test (in USD)
    objectives : list
        Objectives to optimize for
        
    Returns:
    --------
    DataFrame with sensitivity results
    """
    results = []
    
    for budget in budget_levels:
        for objective in objectives:
            optimizer = KiotaOptimizer(counties, budget, objective)
            optimizer.solve()
            summary = optimizer.get_summary()
            results.append(summary)
    
    return pd.DataFrame(results)


def compare_equity_tradeoff(counties, budget):
    """
    Compare constrained (equity) vs unconstrained optimization.
    Shows the cost of the equity requirement.
    """
    results = {}
    
    for objective in ['lives_saved', 'co2_avoided', 'households_reached']:
        # With equity constraint (standard)
        opt_equity = KiotaOptimizer(counties, budget, objective)
        opt_equity.solve()
        
        # Without equity constraint
        opt_no_equity = KiotaOptimizer(counties, budget, objective)
        opt_no_equity.min_allocation_pct = 0.0  # Remove equity constraint
        opt_no_equity.build_model()
        opt_no_equity.solve()
        
        results[objective] = {
            'with_equity': opt_equity.get_summary(),
            'without_equity': opt_no_equity.get_summary()
        }
    
    return results


# ============================================
# VISUALIZATION FUNCTIONS
# ============================================

def plot_county_allocation(solution, title="Optimal Budget Allocation by County"):
    """Create horizontal bar chart of county allocations."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Sort by investment
    sorted_data = solution.sort_values('investment_usd', ascending=True)
    
    # Create bars
    bars = ax.barh(sorted_data['county'], sorted_data['investment_usd'], 
                   color=plt.cm.viridis(sorted_data['poverty_rate'] / 100))
    
    # Add percentage labels
    for bar, pct in zip(bars, sorted_data['allocation_pct']):
        width = bar.get_width()
        ax.annotate(f'{pct:.1f}%',
                   xy=(width, bar.get_y() + bar.get_height()/2),
                   xytext=(3, 0), textcoords='offset points',
                   ha='left', va='center', fontsize=9)
    
    ax.set_xlabel('Investment (USD)', fontsize=12)
    ax.set_ylabel('County', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add colorbar for poverty rate
    sm = plt.cm.ScalarMappable(cmap='viridis', 
                                norm=plt.Normalize(vmin=15, vmax=80))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6)
    cbar.set_label('Poverty Rate (%)', fontsize=10)
    
    plt.tight_layout()
    return fig


def plot_impact_comparison(sensitivity_df, budget):
    """Compare impact across different objectives for a given budget."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    budget_data = sensitivity_df[sensitivity_df['budget_usd'] == budget]
    
    metrics = [
        ('total_households', 'Households Reached', '#2ecc71'),
        ('total_lives_saved', 'Lives Saved', '#e74c3c'),
        ('total_co2_avoided_tons', 'CO2 Avoided (tons)', '#3498db')
    ]
    
    for ax, (metric, label, color) in zip(axes, metrics):
        values = budget_data[metric].values
        objectives = ['Lives\nSaved', 'CO2\nAvoided', 'Households\nReached']
        
        bars = ax.bar(objectives, values, color=color, alpha=0.8)
        
        # Highlight the maximum
        max_idx = values.argmax()
        bars[max_idx].set_alpha(1.0)
        bars[max_idx].set_edgecolor('black')
        bars[max_idx].set_linewidth(2)
        
        ax.set_ylabel(label, fontsize=11)
        ax.set_title(f'{label}', fontsize=12, fontweight='bold')
        
        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.annotate(f'{val:,.0f}',
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords='offset points',
                       ha='center', va='bottom', fontsize=10)
    
    fig.suptitle(f'Impact Comparison by Optimization Objective\n(Budget: ${budget:,.0f})', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig


def plot_budget_sensitivity(sensitivity_df):
    """Show how outcomes change across budget levels."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    metrics = [
        ('total_households', 'Households Reached', '#2ecc71'),
        ('total_lives_saved', 'Lives Saved', '#e74c3c'),
        ('total_co2_avoided_tons', 'CO2 Avoided (tons)', '#3498db')
    ]
    
    objectives = sensitivity_df['objective'].unique()
    budgets = sensitivity_df['budget_usd'].unique()
    
    for ax, (metric, label, _) in zip(axes, metrics):
        for obj in objectives:
            data = sensitivity_df[sensitivity_df['objective'] == obj]
            ax.plot(data['budget_usd'] / 1000, data[metric], 
                   marker='o', label=obj.replace('_', ' ').title(), linewidth=2)
        
        ax.set_xlabel('Budget ($K)', fontsize=11)
        ax.set_ylabel(label, fontsize=11)
        ax.set_title(f'{label} vs Budget', fontsize=12, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
    
    fig.suptitle('Budget Sensitivity Analysis', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig


def plot_efficiency_scatter(solution, title="Cost Efficiency vs Impact"):
    """Scatter plot showing cost efficiency vs impact by county."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Calculate efficiency metric
    solution['cost_efficiency'] = solution['lives_saved'] / solution['investment_usd'] * 1000
    
    scatter = ax.scatter(
        solution['investment_usd'],
        solution['lives_saved'],
        s=solution['households_allocated'] / 100,
        c=solution['cost_efficiency'],
        cmap='RdYlGn',
        alpha=0.7,
        edgecolors='black',
        linewidths=0.5
    )
    
    # Add county labels
    for _, row in solution.iterrows():
        ax.annotate(row['county'], 
                   (row['investment_usd'], row['lives_saved']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=8)
    
    ax.set_xlabel('Investment (USD)', fontsize=12)
    ax.set_ylabel('Lives Saved', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Efficiency (Lives per $1000)', fontsize=10)
    
    # Add legend for bubble size
    sizes = [500, 2000, 5000]
    for size in sizes:
        ax.scatter([], [], s=size/100, c='gray', alpha=0.5, 
                  label=f'{size:,} HH')
    ax.legend(title='Households', loc='lower right', fontsize=9)
    
    plt.tight_layout()
    return fig


def plot_equity_tradeoff(equity_results):
    """Visualize the cost of equity constraints."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    objectives = ['lives_saved', 'co2_avoided', 'households_reached']
    labels = ['Lives Saved', 'CO2 Avoided (tons)', 'Households Reached']
    metrics = ['total_lives_saved', 'total_co2_avoided_tons', 'total_households']
    colors = ['#e74c3c', '#3498db', '#2ecc71']
    
    for ax, obj, label, metric, color in zip(axes, objectives, labels, metrics, colors):
        with_eq = equity_results[obj]['with_equity'][metric]
        without_eq = equity_results[obj]['without_equity'][metric]
        
        x = ['With Equity\n(3% min)', 'Without Equity\n(Unconstrained)']
        values = [with_eq, without_eq]
        
        bars = ax.bar(x, values, color=color, alpha=0.8)
        
        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.annotate(f'{val:,.0f}',
                       xy=(bar.get_x() + bar.get_width()/2, height),
                       xytext=(0, 3), textcoords='offset points',
                       ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Calculate tradeoff percentage
        if without_eq > 0:
            tradeoff_pct = (without_eq - with_eq) / without_eq * 100
            ax.text(0.5, 0.95, f'Equity Cost: {tradeoff_pct:.1f}%', 
                   transform=ax.transAxes, ha='center', fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_ylabel(label, fontsize=11)
        ax.set_title(f'Optimize: {label}', fontsize=12, fontweight='bold')
    
    fig.suptitle('Equity vs Efficiency Tradeoff Analysis', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    return fig


def create_recommendation_table(results_500k, results_1m):
    """Create summary recommendation table."""
    recommendations = []
    
    for budget, results in [('$500K', results_500k), ('$1M', results_1m)]:
        for obj in ['lives_saved', 'co2_avoided', 'households_reached']:
            optimizer = results[obj]
            summary = optimizer.get_summary()
            
            # Find top 3 counties
            top_counties = (optimizer.solution
                           .nlargest(3, 'investment_usd')['county']
                           .tolist())
            
            recommendations.append({
                'Budget': budget,
                'Objective': obj.replace('_', ' ').title(),
                'Households': f"{summary['total_households']:,.0f}",
                'Lives Saved': f"{summary['total_lives_saved']:.1f}",
                'CO2 Avoided': f"{summary['total_co2_avoided_tons']:,.0f}",
                'Top 3 Counties': ', '.join(top_counties),
                'Avg Cost/HH': f"${summary['avg_cost_per_household']:.2f}"
            })
    
    return pd.DataFrame(recommendations)


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Run the complete optimization analysis."""
    print("="*70)
    print("KIOTA SIC INVESTMENT OPTIMIZATION MODEL")
    print("="*70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # 1. LOAD AND PREPARE DATA
    print("Step 1: Loading and preparing data...")
    counties = load_county_data()
    products = load_product_data()
    coefficients = calculate_impact_coefficients()
    
    counties = calculate_county_costs(counties, products, coefficients)
    counties = calculate_impact_per_household(counties, coefficients)
    
    print(f"  - Loaded {len(counties)} counties")
    print(f"  - Total target market: {counties['target_market'].sum():,} households")
    print()
    
    # 2. RUN OPTIMIZATION FOR BOTH BUDGETS
    print("Step 2: Running optimization models...")
    
    budget_levels = [500_000, 1_000_000]
    objectives = ['lives_saved', 'co2_avoided', 'households_reached']
    
    all_results = {}
    
    for budget in budget_levels:
        print(f"\n  Budget: ${budget:,}")
        all_results[budget] = {}
        
        for objective in objectives:
            optimizer = KiotaOptimizer(counties, budget, objective)
            optimizer.solve(verbose=False)
            all_results[budget][objective] = optimizer
            
            summary = optimizer.get_summary()
            print(f"    {objective.replace('_', ' ').title()}: "
                  f"{summary['total_households']:,.0f} HH, "
                  f"{summary['total_lives_saved']:.1f} lives, "
                  f"{summary['total_co2_avoided_tons']:,.0f} tCO2")
    
    # 3. SENSITIVITY ANALYSIS
    print("\n\nStep 3: Running sensitivity analysis...")
    sensitivity_df = run_sensitivity_analysis(counties, budget_levels, objectives)
    
    # 4. EQUITY TRADEOFF ANALYSIS
    print("Step 4: Analyzing equity vs efficiency tradeoff...")
    equity_results = compare_equity_tradeoff(counties, 500_000)
    
    # 5. CREATE VISUALIZATIONS
    print("\nStep 5: Generating visualizations...")
    
    figures = {}
    
    # Plot 1: County allocation for $500K - Lives Saved objective
    figures['allocation_500k'] = plot_county_allocation(
        all_results[500_000]['lives_saved'].solution,
        "Optimal Budget Allocation - $500K (Maximize Lives Saved)"
    )
    
    # Plot 2: County allocation for $1M - Lives Saved objective
    figures['allocation_1m'] = plot_county_allocation(
        all_results[1_000_000]['lives_saved'].solution,
        "Optimal Budget Allocation - $1M (Maximize Lives Saved)"
    )
    
    # Plot 3: Impact comparison across objectives
    figures['impact_comparison'] = plot_impact_comparison(sensitivity_df, 500_000)
    
    # Plot 4: Budget sensitivity
    figures['budget_sensitivity'] = plot_budget_sensitivity(sensitivity_df)
    
    # Plot 5: Cost efficiency scatter
    figures['efficiency_scatter'] = plot_efficiency_scatter(
        all_results[500_000]['lives_saved'].solution,
        "Cost Efficiency Analysis - $500K Budget"
    )
    
    # Plot 6: Equity tradeoff
    figures['equity_tradeoff'] = plot_equity_tradeoff(equity_results)
    
    # 6. GENERATE RECOMMENDATIONS
    print("\nStep 6: Generating recommendations...")
    recommendations = create_recommendation_table(
        all_results[500_000], 
        all_results[1_000_000]
    )
    
    # 7. PRINT SUMMARY RESULTS
    print("\n" + "="*70)
    print("OPTIMIZATION RESULTS SUMMARY")
    print("="*70)
    
    print("\n--- RECOMMENDATION TABLE ---")
    print(recommendations.to_string(index=False))
    
    print("\n--- KEY INSIGHTS ---")
    
    # Best counties for impact
    lives_solution = all_results[500_000]['lives_saved'].solution
    top_impact = lives_solution.nlargest(5, 'lives_saved')[['county', 'investment_usd', 
                                                            'households_allocated', 'lives_saved']]
    print("\nTop 5 Counties for Lives Saved ($500K Budget):")
    print(top_impact.to_string(index=False))
    
    # Equity cost
    eq_cost = equity_results['lives_saved']
    without_eq = eq_cost['without_equity']['total_lives_saved']
    with_eq = eq_cost['with_equity']['total_lives_saved']
    equity_cost_pct = (without_eq - with_eq) / without_eq * 100
    
    print(f"\n\nEquity Constraint Cost:")
    print(f"  Without equity: {without_eq:.1f} lives saved")
    print(f"  With equity:    {with_eq:.1f} lives saved")
    print(f"  Cost of equity: {equity_cost_pct:.1f}% reduction")
    print(f"  (This ensures all 14 counties receive at least 3% of budget)")
    
    # 8. SAVE OUTPUTS
    print("\n\nStep 7: Saving outputs...")
    
    # Save figures
    for name, fig in figures.items():
        filename = f"optimization_{name}.png"
        fig.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"  Saved: {filename}")
    
    # Save recommendation table
    recommendations.to_csv('optimization_recommendations.csv', index=False)
    print("  Saved: optimization_recommendations.csv")
    
    # Save detailed county allocations
    for budget in budget_levels:
        for objective in objectives:
            solution = all_results[budget][objective].solution
            filename = f'allocation_{budget//1000}k_{objective}.csv'
            solution[['county', 'investment_usd', 'households_allocated', 
                     'lives_saved', 'co2_avoided_tons', 'penetration_achieved_pct']].to_csv(
                filename, index=False
            )
    print("  Saved: allocation CSV files for each scenario")
    
    print("\n" + "="*70)
    print("OPTIMIZATION COMPLETE")
    print("="*70)
    
    return all_results, sensitivity_df, recommendations, figures


if __name__ == "__main__":
    results, sensitivity, recommendations, figures = main()
    plt.show()