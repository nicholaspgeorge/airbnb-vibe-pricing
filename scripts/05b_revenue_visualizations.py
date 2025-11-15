"""
TASK 5: REVENUE OPTIMIZATION VISUALIZATIONS

Creates publication-quality visualizations of revenue curves and optimization results.

Visualizations:
1. Revenue curve examples (4 contrasting listings)
2. Revenue lift distribution
3. Optimal vs current price scatter plot

Author: Vibe-Aware Pricing Team
Date: 2025-11-06
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
CITY = 'london'
RANDOM_SEED = 42

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / f'data/{CITY}'
CURVES_PATH = DATA_DIR / 'outputs/recommendations/revenue_curves.parquet'
RECS_PATH = DATA_DIR / 'outputs/recommendations/revenue_recommendations.parquet'
VIZ_DIR = DATA_DIR / 'outputs/visualizations'

# Visualization settings
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

print("=" * 80)
print("REVENUE OPTIMIZATION VISUALIZATIONS")
print("=" * 80)
print()

# ============================================================================
# Load Data
# ============================================================================

print("[1/4] Loading revenue curves and recommendations...")

revenue_curves = pd.read_parquet(CURVES_PATH)
recommendations = pd.read_parquet(RECS_PATH)

print(f"  ✓ Loaded curves for {recommendations.shape[0]} listings")
print(f"  ✓ Total price points: {revenue_curves.shape[0]:,}")
print()

# ============================================================================
# Visualization 1: Revenue Curve Examples (4 Contrasting Listings)
# ============================================================================

print("[2/4] Creating revenue curve examples...")

# Select 4 diverse listings
# Criteria: different room types, vibe scores, and price ranges

# Group by characteristics
high_vibe = recommendations[recommendations['vibe_score'] > recommendations['vibe_score'].quantile(0.75)]
low_vibe = recommendations[recommendations['vibe_score'] < recommendations['vibe_score'].quantile(0.25)]
budget = recommendations[recommendations['current_price'] < recommendations['current_price'].quantile(0.33)]
luxury = recommendations[recommendations['current_price'] > recommendations['current_price'].quantile(0.67)]

# Select examples
examples = []

# Example 1: Budget listing in low-vibe area
if len(budget[budget['vibe_score'] < recommendations['vibe_score'].median()]) > 0:
    ex1 = budget[budget['vibe_score'] < recommendations['vibe_score'].median()].iloc[0]
    examples.append((ex1['listing_id'], "Budget in Low-Vibe Area"))

# Example 2: Luxury listing in high-vibe area
if len(luxury[luxury['vibe_score'] > recommendations['vibe_score'].median()]) > 0:
    ex2 = luxury[luxury['vibe_score'] > recommendations['vibe_score'].median()].iloc[0]
    examples.append((ex2['listing_id'], "Luxury in High-Vibe Area"))

# Example 3: Mid-range entire home
mid_range = recommendations[
    (recommendations['current_price'] >= recommendations['current_price'].quantile(0.4)) &
    (recommendations['current_price'] <= recommendations['current_price'].quantile(0.6)) &
    (recommendations['room_type'] == 'Entire home/apt')
]
if len(mid_range) > 0:
    ex3 = mid_range.iloc[0]
    examples.append((ex3['listing_id'], "Mid-Range Entire Home"))

# Example 4: Private room with high lift potential
high_lift = recommendations[
    (recommendations['revenue_lift_pct'] > recommendations['revenue_lift_pct'].quantile(0.75)) &
    (recommendations['room_type'] == 'Private room')
]
if len(high_lift) > 0:
    ex4 = high_lift.iloc[0]
    examples.append((ex4['listing_id'], "Private Room (High Lift Potential)"))

# Create figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for idx, (listing_id, title) in enumerate(examples[:4]):
    ax = axes[idx]

    # Get curve and recommendation data
    curve = revenue_curves[revenue_curves['listing_id'] == listing_id]
    rec = recommendations[recommendations['listing_id'] == listing_id].iloc[0]

    # Plot revenue curve
    ax.plot(curve['price'], curve['monthly_revenue'], 'b-', linewidth=2, label='Revenue Curve')

    # Mark current price
    ax.axvline(rec['current_price'], color='gray', linestyle='--', linewidth=1.5, label=f"Current (£{rec['current_price']:.0f})")

    # Mark optimal price
    ax.axvline(rec['optimal_price'], color='green', linestyle='--', linewidth=1.5, label=f"Optimal (£{rec['optimal_price']:.0f})")
    ax.plot(rec['optimal_price'], rec['optimal_revenue'], 'g*', markersize=15, label=f"Max Revenue (£{rec['optimal_revenue']:.0f}/mo)")

    # Shade safe band if exists
    if rec['has_safe_band']:
        ax.axvspan(rec['safe_low'], rec['safe_high'], alpha=0.2, color='green', label=f'Safe Band (occ≥0.75)')

    # Labels and styling
    ax.set_xlabel('Nightly Price (£)', fontsize=10)
    ax.set_ylabel('Monthly Revenue (£)', fontsize=10)
    ax.set_title(f"{title}\n{rec['property_type']} - {rec['room_type']}\nVibe Score: {rec['vibe_score']:.2f} | Revenue Lift: {rec['revenue_lift_pct']:.1f}%",
                 fontsize=10, fontweight='bold')
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, alpha=0.3)

    # Format y-axis with commas
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))

plt.tight_layout()
viz1_path = VIZ_DIR / '09_revenue_optimization_curves.png'
plt.savefig(viz1_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"  ✓ Saved revenue curve examples: {viz1_path.name}")

# ============================================================================
# Visualization 2: Revenue Lift Distribution
# ============================================================================

print("[3/4] Creating revenue lift distribution...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
ax1 = axes[0]
ax1.hist(recommendations['revenue_lift_pct'], bins=50, color='steelblue', edgecolor='black', alpha=0.7)
ax1.axvline(recommendations['revenue_lift_pct'].median(), color='red', linestyle='--', linewidth=2, label=f"Median: {recommendations['revenue_lift_pct'].median():.1f}%")
ax1.axvline(recommendations['revenue_lift_pct'].mean(), color='orange', linestyle='--', linewidth=2, label=f"Mean: {recommendations['revenue_lift_pct'].mean():.1f}%")
ax1.set_xlabel('Revenue Lift (%)', fontsize=11)
ax1.set_ylabel('Number of Listings', fontsize=11)
ax1.set_title('Distribution of Revenue Lift Opportunities', fontsize=12, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)

# Box plot by room type
ax2 = axes[1]
room_order = recommendations.groupby('room_type')['revenue_lift_pct'].median().sort_values(ascending=False).index
sns.boxplot(data=recommendations, y='room_type', x='revenue_lift_pct', order=room_order, ax=ax2, palette='Set2')
ax2.set_xlabel('Revenue Lift (%)', fontsize=11)
ax2.set_ylabel('Room Type', fontsize=11)
ax2.set_title('Revenue Lift by Room Type', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
viz2_path = VIZ_DIR / '10_revenue_lift_distribution.png'
plt.savefig(viz2_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"  ✓ Saved revenue lift distribution: {viz2_path.name}")

# ============================================================================
# Visualization 3: Optimal vs Current Price Scatter
# ============================================================================

print("[4/4] Creating optimal vs current price scatter...")

fig, ax = plt.subplots(figsize=(10, 10))

# Color by room type
room_types = recommendations['room_type'].unique()
colors = plt.cm.Set1(np.linspace(0, 1, len(room_types)))

for room_type, color in zip(room_types, colors):
    data = recommendations[recommendations['room_type'] == room_type]
    ax.scatter(data['current_price'], data['optimal_price'],
               alpha=0.6, s=50, label=room_type, color=color)

# Diagonal line (optimal = current)
max_price = max(recommendations['current_price'].max(), recommendations['optimal_price'].max())
ax.plot([0, max_price], [0, max_price], 'k--', linewidth=2, alpha=0.5, label='No Change')

# Labels and styling
ax.set_xlabel('Current Price (£)', fontsize=12)
ax.set_ylabel('Optimal Price (£)', fontsize=12)
ax.set_title('Optimal vs Current Pricing Recommendations\n(Points above diagonal should increase price)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10, loc='upper left')
ax.grid(True, alpha=0.3)

# Format axes
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'£{x:,.0f}'))

# Set equal aspect ratio
ax.set_aspect('equal', adjustable='box')

# Add annotation showing price change zones
ax.text(0.95, 0.05, 'Above diagonal:\nIncrease price',
        transform=ax.transAxes, fontsize=10,
        verticalalignment='bottom', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

ax.text(0.05, 0.95, 'Below diagonal:\nDecrease price',
        transform=ax.transAxes, fontsize=10,
        verticalalignment='top', horizontalalignment='left',
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))

plt.tight_layout()
viz3_path = VIZ_DIR / '11_optimal_vs_current_price.png'
plt.savefig(viz3_path, dpi=150, bbox_inches='tight')
plt.close()

print(f"  ✓ Saved optimal vs current scatter: {viz3_path.name}")

# ============================================================================
# Summary
# ============================================================================

print()
print("=" * 80)
print("REVENUE VISUALIZATIONS COMPLETE ✅")
print("=" * 80)
print("\nGenerated visualizations:")
print(f"  1. {viz1_path}")
print(f"  2. {viz2_path}")
print(f"  3. {viz3_path}")
print()
print("Key Insights:")
print(f"  • {(recommendations['revenue_lift_pct'] > 50).sum()} listings ({(recommendations['revenue_lift_pct'] > 50).mean()*100:.1f}%) have >50% revenue lift potential")
print(f"  • {(recommendations['price_change_pct'] > 0).sum()} listings ({(recommendations['price_change_pct'] > 0).mean()*100:.1f}%) should increase their price")
print(f"  • Optimal pricing could generate £{recommendations['optimal_revenue'].sum() - recommendations['current_revenue'].sum():,.0f} additional monthly revenue across {len(recommendations)} listings")
print("=" * 80)
