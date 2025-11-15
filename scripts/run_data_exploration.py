#!/usr/bin/env python3
"""
Data Exploration Script - Task 1
Comprehensive analysis of Airbnb listings and vibe features
Multi-city compatible
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from pathlib import Path
import sys

warnings.filterwarnings('ignore')
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# Configuration - change this for different cities
CITY = 'nyc'  # Options: 'london', 'nyc', 'austin'

# Define paths
DATA_DIR = Path(f'data/{CITY}')
RAW_DIR = DATA_DIR / 'raw'
OUTPUT_DIR = DATA_DIR / 'outputs'
VIZ_DIR = OUTPUT_DIR / 'visualizations'
REPORTS_DIR = OUTPUT_DIR / 'reports'

# Create output directories
VIZ_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print(f"VIBE-AWARE PRICING ENGINE - DATA EXPLORATION: {CITY.upper()}")
print("="*80)
print()

#  ============================================================================
# 1. LOAD DATA
print("1. Loading data files...")
print("-" * 80)

# Find listings file (handles different naming conventions)
listings_files = list(RAW_DIR.glob('listings*.csv'))
if not listings_files:
    print(f"✗ Error: No listings*.csv found in {RAW_DIR}")
    sys.exit(1)

listings_file = listings_files[0]
print(f"Found: {listings_file.name}")

try:
    df_listings = pd.read_csv(listings_file, low_memory=False)
    print(f"✓ Loaded {len(df_listings):,} listings with {len(df_listings.columns)} columns")
    print(f"  Memory: {df_listings.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
except Exception as e:
    print(f"✗ Error loading listings: {e}")
    sys.exit(1)

try:
    df_vibe_scores = pd.read_csv(RAW_DIR / '01_neighborhood_vibe_scores.csv')
    df_vibe_model = pd.read_csv(RAW_DIR / '01_vibe_features_for_modeling.csv')
    print(f"✓ Loaded {len(df_vibe_model)} neighborhoods with vibe features")
except Exception as e:
    print(f"✗ Error loading vibe features: {e}")
    sys.exit(1)

print()

# ============================================================================
# 2. PRICE FIELD ANALYSIS
print("2. Analyzing and cleaning price field...")
print("-" * 80)

def clean_price(price_str):
    """Convert price string like '$100.00' to float"""
    if pd.isna(price_str):
        return np.nan
    try:
        return float(str(price_str).replace('$', '').replace(',', ''))
    except:
        return np.nan

df_listings['price_clean'] = df_listings['price'].apply(clean_price)

print(f"Price statistics:")
print(df_listings['price_clean'].describe())
print(f"\nPrice issues:")
print(f"  Zero prices: {(df_listings['price_clean'] == 0).sum():,}")
print(f"  Null prices: {df_listings['price_clean'].isnull().sum():,}")
print(f"  Price < £10: {(df_listings['price_clean'] < 10).sum():,}")
print(f"  Price > £1000: {(df_listings['price_clean'] > 1000).sum():,}")
print()

# Visualize price distribution
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

price_clean = df_listings['price_clean'].dropna()
p1, p99 = price_clean.quantile([0.01, 0.99])
price_viz = price_clean[(price_clean >= p1) & (price_clean <= p99)]

# Histogram
axes[0, 0].hist(price_viz, bins=100, color='skyblue', edgecolor='black', alpha=0.7)
axes[0, 0].set_xlabel('Price (£)', fontsize=11)
axes[0, 0].set_ylabel('Frequency', fontsize=11)
axes[0, 0].set_title('Price Distribution (1st-99th percentile)', fontsize=12, fontweight='bold')
axes[0, 0].axvline(price_viz.median(), color='red', linestyle='--', label=f'Median: £{price_viz.median():.0f}')
axes[0, 0].axvline(price_viz.mean(), color='orange', linestyle='--', label=f'Mean: £{price_viz.mean():.0f}')
axes[0, 0].legend()

# Log-scale
axes[0, 1].hist(np.log1p(price_viz), bins=100, color='lightcoral', edgecolor='black', alpha=0.7)
axes[0, 1].set_xlabel('log(Price + 1)', fontsize=11)
axes[0, 1].set_ylabel('Frequency', fontsize=11)
axes[0, 1].set_title('Price Distribution (Log Scale)', fontsize=12, fontweight='bold')

# Box plot
axes[1, 0].boxplot(price_viz, vert=False, patch_artist=True,
                    boxprops=dict(facecolor='lightgreen', alpha=0.7))
axes[1, 0].set_xlabel('Price (£)', fontsize=11)
axes[1, 0].set_title('Price Box Plot', fontsize=12, fontweight='bold')
axes[1, 0].set_yticks([])

# By room type
price_by_room = df_listings[df_listings['price_clean'].notna()].groupby('room_type')['price_clean'].median().sort_values()
axes[1, 1].barh(price_by_room.index, price_by_room.values, color='mediumpurple', alpha=0.7)
axes[1, 1].set_xlabel('Median Price (£)', fontsize=11)
axes[1, 1].set_ylabel('Room Type', fontsize=11)
axes[1, 1].set_title('Median Price by Room Type', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(VIZ_DIR / '01_price_distribution.png', dpi=150)
print(f"✓ Saved: {VIZ_DIR / '01_price_distribution.png'}")
plt.close()

# ============================================================================
# 3. OCCUPANCY PROXIES
print("\n3. Computing occupancy proxies...")
print("-" * 80)

df_listings['occ_30'] = 1 - (df_listings['availability_30'] / 30)
df_listings['occ_60'] = 1 - (df_listings['availability_60'] / 60)
df_listings['occ_90'] = 1 - (df_listings['availability_90'] / 90)
df_listings['occ_365'] = 1 - (df_listings['availability_365'] / 365)
df_listings['high_demand_90'] = (df_listings['occ_90'] >= 0.75).astype(int)

print("Occupancy statistics:")
print(df_listings[['occ_30', 'occ_60', 'occ_90', 'occ_365']].describe())
print(f"\nHigh-demand distribution (occ_90 >= 0.75):")
print(df_listings['high_demand_90'].value_counts())
print(f"Percentage high-demand: {df_listings['high_demand_90'].mean() * 100:.1f}%")
print()

# Visualize occupancy
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for idx, (field, ax) in enumerate(zip(['occ_30', 'occ_60', 'occ_90', 'occ_365'], axes.flatten())):
    data = df_listings[field].dropna()
    ax.hist(data, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    ax.axvline(0.75, color='red', linestyle='--', linewidth=2, label='High-demand threshold (0.75)')
    ax.axvline(data.median(), color='orange', linestyle='--', linewidth=2, label=f'Median: {data.median():.2f}')
    ax.set_xlabel('Occupancy Rate', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title(f'{field.upper()} Distribution', fontsize=12, fontweight='bold')
    ax.legend()
    ax.set_xlim(0, 1)

plt.tight_layout()
plt.savefig(VIZ_DIR / '02_occupancy_distribution.png', dpi=150)
print(f"✓ Saved: {VIZ_DIR / '02_occupancy_distribution.png'}")
plt.close()

# ============================================================================
# 4. MISSING DATA ANALYSIS
print("\n4. Analyzing missing data...")
print("-" * 80)

modeling_fields = [
    'price_clean', 'availability_90', 'accommodates', 'bedrooms', 'bathrooms',
    'room_type', 'host_is_superhost', 'number_of_reviews', 'review_scores_rating',
    'first_review', 'last_review', 'neighbourhood_cleansed'
]

missing_model = df_listings[modeling_fields].isnull().sum().sort_values(ascending=False)
missing_model_pct = (missing_model / len(df_listings) * 100)

print("Missing data for key modeling fields:")
for field, pct in missing_model_pct.items():
    print(f"  {field:30s}: {pct:5.1f}%")
print()

# Visualize
fig, ax = plt.subplots(figsize=(10, 6))
missing_model_pct.plot(kind='barh', color='coral', ax=ax)
ax.set_xlabel('Missing Data (%)', fontsize=12)
ax.set_ylabel('Feature', fontsize=12)
ax.set_title('Missing Data for Key Modeling Fields', fontsize=14, fontweight='bold')
ax.axvline(5, color='red', linestyle='--', alpha=0.5, label='5% threshold')
ax.legend()
plt.tight_layout()
plt.savefig(VIZ_DIR / '03_missing_data.png', dpi=150)
print(f"✓ Saved: {VIZ_DIR / '03_missing_data.png'}")
plt.close()

# ============================================================================
# 5. VIBE FEATURES ANALYSIS
print("\n5. Analyzing vibe features...")
print("-" * 80)

print("Top 5 high-vibe neighborhoods:")
top_vibes = df_vibe_scores.nlargest(5, 'vibe_score')[['neighbourhood', 'vibe_score', 'characteristics']]
for _, row in top_vibes.iterrows():
    print(f"  {str(row['neighbourhood']):30s}: {row['vibe_score']:5.1f} - {row['characteristics']}")

print("\nBottom 5 low-vibe neighborhoods:")
bottom_vibes = df_vibe_scores.nsmallest(5, 'vibe_score')[['neighbourhood', 'vibe_score', 'characteristics']]
for _, row in bottom_vibes.iterrows():
    print(f"  {str(row['neighbourhood']):30s}: {row['vibe_score']:5.1f} - {row['characteristics']}")
print()

# Visualize vibe scores
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Bar chart
vibe_sorted = df_vibe_scores.sort_values('vibe_score', ascending=True)
axes[0].barh(vibe_sorted['neighbourhood'], vibe_sorted['vibe_score'],
             color=plt.cm.RdYlGn(vibe_sorted['vibe_score']/100))
axes[0].set_xlabel('Vibe Score', fontsize=11)
axes[0].set_ylabel('Neighbourhood', fontsize=11)
axes[0].set_title('Neighborhood Vibe Scores', fontsize=12, fontweight='bold')
axes[0].axvline(50, color='black', linestyle='--', alpha=0.3, label='Mid-point')
axes[0].legend()

# Distribution of vibe dimensions
vibe_dims = ['walkability_score', 'safety_score', 'nightlife_score', 'family_friendly_score']
df_vibe_model[vibe_dims].mean().plot(kind='bar', ax=axes[1], color='skyblue', alpha=0.7)
axes[1].set_xlabel('Vibe Dimension', fontsize=11)
axes[1].set_ylabel('Average Score', fontsize=11)
axes[1].set_title(f'Average Vibe Dimensions - {CITY.title()}', fontsize=12, fontweight='bold')
axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.savefig(VIZ_DIR / '04_vibe_features.png', dpi=150)
print(f"✓ Saved: {VIZ_DIR / '04_vibe_features.png'}")
plt.close()

# ============================================================================
# 6. JOIN VALIDATION
print("\n6. Validating vibe feature join...")
print("-" * 80)

# Test join
df_test_join = df_listings[['id', 'neighbourhood_cleansed', 'price_clean']].merge(
    df_vibe_model,
    left_on='neighbourhood_cleansed',
    right_on='neighbourhood',
    how='left'
)

matched = df_test_join['vibe_score'].notna().sum()
match_pct = matched / len(df_listings) * 100

print(f"Join results:")
print(f"  Original listings: {len(df_listings):,}")
print(f"  After join: {len(df_test_join):,}")
print(f"  Listings with vibe_score: {matched:,} ({match_pct:.2f}%)")
print(f"  Listings WITHOUT vibe_score: {len(df_listings) - matched:,} ({(100-match_pct):.2f}%)")

if match_pct >= 95:
    print("\n✓ JOIN QUALITY: EXCELLENT (≥95% match rate)")
elif match_pct >= 90:
    print("\n✓ JOIN QUALITY: GOOD (≥90% match rate)")
else:
    print("\n⚠️  JOIN QUALITY: NEEDS ATTENTION (<90% match rate)")
print()

# ============================================================================
# 7. PROPERTY FEATURES
print("\n7. Analyzing property features...")
print("-" * 80)

print("Room type distribution:")
print(df_listings['room_type'].value_counts())
print()

# Visualize
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Room type
room_counts = df_listings['room_type'].value_counts()
axes[0, 0].barh(room_counts.index, room_counts.values, color='teal', alpha=0.7)
axes[0, 0].set_xlabel('Count', fontsize=11)
axes[0, 0].set_title('Room Type Distribution', fontsize=12, fontweight='bold')

# Accommodates
axes[0, 1].hist(df_listings['accommodates'].dropna(), bins=30, color='salmon', edgecolor='black', alpha=0.7)
axes[0, 1].set_xlabel('Number of Guests', fontsize=11)
axes[0, 1].set_ylabel('Frequency', fontsize=11)
axes[0, 1].set_title('Accommodates Distribution', fontsize=12, fontweight='bold')

# Bedrooms
bedroom_counts = df_listings['bedrooms'].value_counts().sort_index()
axes[1, 0].bar(bedroom_counts.index, bedroom_counts.values, color='lightblue', edgecolor='black', alpha=0.7)
axes[1, 0].set_xlabel('Number of Bedrooms', fontsize=11)
axes[1, 0].set_ylabel('Count', fontsize=11)
axes[1, 0].set_title('Bedrooms Distribution', fontsize=12, fontweight='bold')
axes[1, 0].set_xlim(-0.5, 10.5)

# Bathrooms
bathroom_counts = df_listings['bathrooms'].value_counts().sort_index()
axes[1, 1].bar(bathroom_counts.index, bathroom_counts.values, color='lightgreen', edgecolor='black', alpha=0.7)
axes[1, 1].set_xlabel('Number of Bathrooms', fontsize=11)
axes[1, 1].set_ylabel('Count', fontsize=11)
axes[1, 1].set_title('Bathrooms Distribution', fontsize=12, fontweight='bold')
axes[1, 1].set_xlim(-0.5, 8.5)

plt.tight_layout()
plt.savefig(VIZ_DIR / '05_property_features.png', dpi=150)
print(f"✓ Saved: {VIZ_DIR / '05_property_features.png'}")
plt.close()

# ============================================================================
# 8. EXPORT SUMMARY
print("\n8. Exporting summary statistics...")
print("-" * 80)

# Create summary
summary_stats = pd.DataFrame({
    'Metric': [
        'City',
        'Total Listings',
        'Neighborhoods',
        'Mean Price (£)',
        'Median Price (£)',
        'Mean occ_90',
        'High-Demand %',
        'Vibe Match Rate %',
        'Bedrooms Missing %',
        'Bathrooms Missing %',
        'Review Scores Missing %'
    ],
    'Value': [
        CITY.title(),
        f"{len(df_listings):,}",
        f"{df_listings['neighbourhood_cleansed'].nunique()}",
        f"£{df_listings['price_clean'].mean():.2f}",
        f"£{df_listings['price_clean'].median():.2f}",
        f"{df_listings['occ_90'].mean():.3f}",
        f"{df_listings['high_demand_90'].mean() * 100:.1f}%",
        f"{match_pct:.2f}%",
        f"{df_listings['bedrooms'].isnull().sum() / len(df_listings) * 100:.1f}%",
        f"{df_listings['bathrooms'].isnull().sum() / len(df_listings) * 100:.1f}%",
        f"{df_listings['review_scores_rating'].isnull().sum() / len(df_listings) * 100:.1f}%"
    ]
})

summary_stats.to_csv(REPORTS_DIR / 'data_summary_stats.csv', index=False)
print(f"✓ Saved: {REPORTS_DIR / 'data_summary_stats.csv'}")

# Save schema
schema_df = pd.DataFrame({
    'Column': df_listings.columns,
    'Dtype': df_listings.dtypes.values,
    'Non-Null': df_listings.count().values,
    'Null_Pct': (df_listings.isnull().sum() / len(df_listings) * 100).values.round(1),
    'Unique': [df_listings[col].nunique() for col in df_listings.columns]
})
schema_df.to_csv(REPORTS_DIR / 'listings_schema.csv', index=False)
print(f"✓ Saved: {REPORTS_DIR / 'listings_schema.csv'}")

print()
print("="*80)
print(f"DATA EXPLORATION COMPLETE - {CITY.upper()}")
print("="*80)
print()
print("📊 Generated Visualizations:")
print(f"   {VIZ_DIR}/01_price_distribution.png")
print(f"   {VIZ_DIR}/02_occupancy_distribution.png")
print(f"   {VIZ_DIR}/03_missing_data.png")
print(f"   {VIZ_DIR}/04_vibe_features.png")
print(f"   {VIZ_DIR}/05_property_features.png")
print()
print("📄 Generated Reports:")
print(f"   {REPORTS_DIR}/data_summary_stats.csv")
print(f"   {REPORTS_DIR}/listings_schema.csv")
print()
print("✅ Next Step: Review findings and proceed to Task 2 (Feature Engineering)")
print()
