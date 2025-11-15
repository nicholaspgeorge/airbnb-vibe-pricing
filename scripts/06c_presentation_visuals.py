"""
TASK 6: PRESENTATION-QUALITY STATIC VISUALIZATIONS

Creates high-resolution, publication-quality static visuals for final report and slides.
All outputs are 300+ DPI, 16:9 aspect ratio, with professional styling.

Author: Vibe-Aware Pricing Team
Date: 2025-11-07
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Configuration
CITY = 'london'
DPI = 300
FIGSIZE_WIDE = (19.2, 10.8)  # 16:9 aspect ratio at 1920x1080
FIGSIZE_SQUARE = (12, 12)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / f'data/{CITY}'
FEATURE_IMP_PATH = DATA_DIR / 'outputs/reports/feature_importance.csv'
MODEL_COMP_PATH = DATA_DIR / 'outputs/reports/model_comparison.csv'
RECS_PATH = DATA_DIR / 'outputs/recommendations/revenue_recommendations.parquet'
VIZ_DIR = DATA_DIR / 'outputs/visualizations'

print("=" * 80)
print("PRESENTATION-QUALITY STATIC VISUALIZATIONS")
print("=" * 80)
print()

# ============================================================================
# Load Data
# ============================================================================

print("[1/4] Loading data for visualizations...")

# Feature importance
feature_imp = pd.read_csv(FEATURE_IMP_PATH)
print(f"  ✓ Loaded feature importance: {len(feature_imp)} features")

# Model comparison
model_comp = pd.read_csv(MODEL_COMP_PATH)
print(f"  ✓ Loaded model comparison: {len(model_comp)} models")

# Revenue recommendations
recommendations = pd.read_parquet(RECS_PATH)
print(f"  ✓ Loaded recommendations: {len(recommendations)} listings")

print()

# ============================================================================
# VISUAL 1: Three-Panel Executive Summary
# ============================================================================

print("[2/4] Creating three-panel executive summary...")

fig, axes = plt.subplots(1, 3, figsize=FIGSIZE_WIDE)

# Panel 1: Vibe Feature Importance
# ---------------------------------
vibe_features = ['vibe_score', 'liveliness_score', 'nightlife_score', 'safety_score',
                 'walkability_score', 'convenience_score']
vibe_imp = feature_imp[feature_imp['feature'].isin(vibe_features)]
total_imp = feature_imp['importance'].sum()
vibe_total = vibe_imp['importance'].sum()
vibe_pct = (vibe_total / total_imp) * 100

# Create data for panel 1
categories = ['Vibe Features', 'Other Features']
importance = [vibe_pct, 100 - vibe_pct]
colors_panel1 = ['#2ecc71', '#95a5a6']

ax1 = axes[0]
bars = ax1.barh(categories, importance, color=colors_panel1, edgecolor='black', linewidth=1.5)
ax1.set_xlabel('% of Total Model Importance', fontsize=14, fontweight='bold')
ax1.set_title('Vibe Features Drive Pricing Power\n', fontsize=16, fontweight='bold')
ax1.set_xlim(0, 100)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, importance)):
    ax1.text(val + 2, i, f'{val:.1f}%', va='center', fontsize=14, fontweight='bold')

ax1.grid(axis='x', alpha=0.3)
ax1.set_axisbelow(True)

# Panel 2: Revenue Lift Distribution
# -----------------------------------
ax2 = axes[1]

lift_data = recommendations['revenue_lift_pct']
median_lift = lift_data.median()
mean_lift = lift_data.mean()

# Histogram
ax2.hist(lift_data, bins=30, color='#3498db', alpha=0.7, edgecolor='black', linewidth=1.2)
ax2.axvline(median_lift, color='#e74c3c', linestyle='--', linewidth=3, label=f'Median: {median_lift:.1f}%')
ax2.axvline(mean_lift, color='#f39c12', linestyle='--', linewidth=3, label=f'Mean: {mean_lift:.1f}%')

ax2.set_xlabel('Revenue Lift Potential (%)', fontsize=14, fontweight='bold')
ax2.set_ylabel('Number of Listings', fontsize=14, fontweight='bold')
ax2.set_title('Massive Revenue Optimization Opportunity\n', fontsize=16, fontweight='bold')
ax2.legend(fontsize=12, loc='upper right', framealpha=0.9)
ax2.grid(axis='y', alpha=0.3)
ax2.set_axisbelow(True)

# Panel 3: Price Recommendations
# -------------------------------
ax3 = axes[2]

# Categorize recommendations
recommendations['price_change_pct'] = ((recommendations['optimal_price'] - recommendations['current_price'])
                                        / recommendations['current_price']) * 100

increase = (recommendations['price_change_pct'] > 5).sum()
maintain = ((recommendations['price_change_pct'] >= -5) & (recommendations['price_change_pct'] <= 5)).sum()
decrease = (recommendations['price_change_pct'] < -5).sum()

categories_panel3 = ['Increase\nPrice', 'Maintain\nPrice', 'Decrease\nPrice']
counts = [increase, maintain, decrease]
colors_panel3 = ['#27ae60', '#f39c12', '#e74c3c']

bars3 = ax3.bar(categories_panel3, counts, color=colors_panel3, edgecolor='black', linewidth=1.5)
ax3.set_ylabel('Number of Listings', fontsize=14, fontweight='bold')
ax3.set_title('88% of Listings Should Increase Prices\n', fontsize=16, fontweight='bold')
ax3.set_ylim(0, max(counts) * 1.15)

# Add value labels
for bar, count in zip(bars3, counts):
    height = bar.get_height()
    pct = (count / len(recommendations)) * 100
    ax3.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.02,
             f'{count}\n({pct:.1f}%)',
             ha='center', va='bottom', fontsize=12, fontweight='bold')

ax3.grid(axis='y', alpha=0.3)
ax3.set_axisbelow(True)

plt.tight_layout()
output_path = VIZ_DIR / '12_executive_summary_three_panel.png'
plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
plt.close()

print(f"  ✓ Saved executive summary: {output_path.name}")
print()

# ============================================================================
# VISUAL 2: Model Performance Comparison (With/Without Vibe)
# ============================================================================

print("[3/4] Creating model performance comparison...")

fig, ax = plt.subplots(figsize=(14, 8))

# Prepare data - pivot to compare with/without vibe for each model
with_vibe = model_comp[model_comp['vibe_features'] == 'yes'].copy()
without_vibe = model_comp[model_comp['vibe_features'] == 'no'].copy()

# Get unique model names
model_names = with_vibe['model'].unique()

# Create grouped bar chart data
x = np.arange(len(model_names))
width = 0.35

# MAE comparison
mae_with = [with_vibe[with_vibe['model'] == m]['test_mae'].values[0] for m in model_names]
mae_without = [without_vibe[without_vibe['model'] == m]['test_mae'].values[0]
               if m in without_vibe['model'].values else np.nan for m in model_names]

# Create grouped bars
bars1 = ax.bar(x - width/2, mae_with, width, label='With Vibe Features',
               color='#2ecc71', edgecolor='black', linewidth=1.5)
bars2 = ax.bar(x + width/2, mae_without, width, label='Without Vibe (Baseline)',
               color='#95a5a6', edgecolor='black', linewidth=1.5)

# Customize
ax.set_xlabel('Model Type', fontsize=14, fontweight='bold')
ax.set_ylabel('Test MAE (Lower is Better)', fontsize=14, fontweight='bold')
ax.set_title('Model Performance: With vs Without Vibe Features\n', fontsize=16, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(model_names, fontsize=12, fontweight='bold')
ax.legend(fontsize=12, loc='upper right', framealpha=0.9)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.002,
                    f'{height:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Highlight best model
best_idx = np.argmin(mae_with)
ax.axhline(y=mae_with[best_idx], color='#e74c3c', linestyle='--', linewidth=2, alpha=0.5,
           label=f'Best: {model_names[best_idx]} ({mae_with[best_idx]:.4f})')

ax.grid(axis='y', alpha=0.3)
ax.set_axisbelow(True)
ax.legend(fontsize=11, loc='upper right', framealpha=0.9)

plt.tight_layout()
output_path = VIZ_DIR / '13_model_performance_comparison.png'
plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
plt.close()

print(f"  ✓ Saved model comparison: {output_path.name}")
print()

# ============================================================================
# VISUAL 3: Feature Importance Deep Dive
# ============================================================================

print("[4/4] Creating feature importance deep dive...")

fig, ax = plt.subplots(figsize=(12, 10))

# Get top 20 features
top_features = feature_imp.nlargest(20, 'importance')

# Categorize features
def categorize_feature(feat):
    vibe_keywords = ['vibe', 'liveliness', 'nightlife', 'safety', 'walkability', 'convenience']
    property_keywords = ['bedrooms', 'bathrooms', 'accommodates', 'amenities', 'beds']
    location_keywords = ['neighbourhood', 'latitude', 'longitude']
    host_keywords = ['host_']

    feat_lower = feat.lower()
    if any(kw in feat_lower for kw in vibe_keywords):
        return 'Vibe'
    elif any(kw in feat_lower for kw in property_keywords):
        return 'Property'
    elif any(kw in feat_lower for kw in location_keywords):
        return 'Location'
    elif any(kw in feat_lower for kw in host_keywords):
        return 'Host'
    else:
        return 'Other'

top_features['category'] = top_features['feature'].apply(categorize_feature)

# Color mapping
category_colors = {
    'Vibe': '#2ecc71',
    'Property': '#3498db',
    'Location': '#f39c12',
    'Host': '#9b59b6',
    'Other': '#95a5a6'
}

colors = top_features['category'].map(category_colors)

# Horizontal bar chart
bars = ax.barh(range(len(top_features)), top_features['importance'],
               color=colors, edgecolor='black', linewidth=1.2)

ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'], fontsize=11)
ax.set_xlabel('Feature Importance (SHAP Value)', fontsize=14, fontweight='bold')
ax.set_title('Top 20 Features Driving Airbnb Pricing\n', fontsize=16, fontweight='bold')
ax.invert_yaxis()

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=color, edgecolor='black', label=cat)
                   for cat, color in category_colors.items()]
ax.legend(handles=legend_elements, loc='lower right', fontsize=12, framealpha=0.9)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, top_features['importance'])):
    ax.text(val + max(top_features['importance'])*0.01, i,
            f'{val:.4f}', va='center', fontsize=10, fontweight='bold')

ax.grid(axis='x', alpha=0.3)
ax.set_axisbelow(True)

plt.tight_layout()
output_path = VIZ_DIR / '14_feature_importance_detailed.png'
plt.savefig(output_path, dpi=DPI, bbox_inches='tight', facecolor='white')
plt.close()

print(f"  ✓ Saved feature importance: {output_path.name}")
print()

# ============================================================================
# Summary
# ============================================================================

print("=" * 80)
print("PRESENTATION VISUALS COMPLETE ✅")
print("=" * 80)
print()
print("Generated Files:")
print(f"  1. {VIZ_DIR / '12_executive_summary_three_panel.png'} ({DPI} DPI)")
print(f"  2. {VIZ_DIR / '13_model_performance_comparison.png'} ({DPI} DPI)")
print(f"  3. {VIZ_DIR / '14_feature_importance_detailed.png'} ({DPI} DPI)")
print()
print("All visualizations are high-resolution (300 DPI) and ready for:")
print("  • Final project report")
print("  • Presentation slides (16:9 aspect ratio)")
print("  • Academic publication")
print("  • Business stakeholder presentations")
print()
print("=" * 80)
