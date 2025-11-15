#!/usr/bin/env python3
"""
Feature Engineering Pipeline for Vibe-Aware Pricing Engine
Creates train/test datasets with engineered features for modeling

Based on decisions documented in METHODOLOGY.md
Author: Team (Nicholas, Sahil, Heath)
Date: 2025-11-06
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

CITY = 'nyc'  # Change for different cities
RANDOM_SEED = 42  # For reproducibility
HIGH_DEMAND_THRESHOLD = 0.75  # occ_90 threshold for high_demand label
TEST_SIZE = 0.20  # 80/20 train/test split

# Paths
DATA_DIR = Path(f'data/{CITY}')
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
OUTPUT_DIR = DATA_DIR / 'outputs'
VIZ_DIR = OUTPUT_DIR / 'visualizations'
REPORTS_DIR = OUTPUT_DIR / 'reports'

# Create directories
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print(f"FEATURE ENGINEERING PIPELINE - {CITY.upper()}")
print("=" * 80)
print(f"Random Seed: {RANDOM_SEED}")
print(f"High-Demand Threshold: {HIGH_DEMAND_THRESHOLD}")
print(f"Train/Test Split: {int((1-TEST_SIZE)*100)}/{int(TEST_SIZE*100)}")
print("=" * 80)

# ============================================================================
# STEP 1: LOAD AND CLEAN DATA
# ============================================================================

print("\n[1/8] Loading and cleaning listings data...")

# Load listings
listings_file = RAW_DIR / f'listings_{CITY.capitalize()}.csv'
df = pd.read_csv(listings_file)
print(f"  ✓ Loaded {len(df):,} listings from {listings_file.name}")

# Clean price field (from METHODOLOGY.md)
def clean_price(price_str):
    """Convert price string like '$100.00' to float"""
    if pd.isna(price_str):
        return np.nan
    try:
        # Remove currency symbols and commas
        cleaned = str(price_str).replace('$', '').replace('£', '').replace(',', '').strip()
        return float(cleaned)
    except:
        return np.nan

df['price_clean'] = df['price'].apply(clean_price)
print(f"  ✓ Cleaned price field: {df['price_clean'].notna().sum():,} non-null values")

# Store original row count for tracking
original_count = len(df)

# ============================================================================
# STEP 2: COMPUTE OCCUPANCY METRICS
# ============================================================================

print("\n[2/8] Computing occupancy metrics...")

# Occupancy proxy: occ = 1 - (availability / max_days)
df['occ_30'] = 1 - (df['availability_30'] / 30)
df['occ_60'] = 1 - (df['availability_60'] / 60)
df['occ_90'] = 1 - (df['availability_90'] / 90)  # Primary target
df['occ_365'] = 1 - (df['availability_365'] / 365)

# High-demand label (from METHODOLOGY.md threshold)
df['high_demand_90'] = (df['occ_90'] >= HIGH_DEMAND_THRESHOLD).astype(int)

print(f"  ✓ Computed occupancy metrics (occ_30, occ_60, occ_90, occ_365)")
print(f"  ✓ Created high_demand_90 label: {df['high_demand_90'].sum():,} high-demand listings ({df['high_demand_90'].mean()*100:.1f}%)")

# Sanity check: occupancy should be in [0, 1]
for occ_col in ['occ_30', 'occ_60', 'occ_90', 'occ_365']:
    assert df[occ_col].min() >= 0 and df[occ_col].max() <= 1, f"{occ_col} out of range!"

# ============================================================================
# STEP 3: ENGINEER LISTING-LEVEL FEATURES
# ============================================================================

print("\n[3/8] Engineering listing-level features...")

# 3.1 Amenities count
df['amenities_count'] = df['amenities'].fillna('[]').apply(lambda x: len(eval(x)) if x != '[]' else 0)
print(f"  ✓ amenities_count: mean={df['amenities_count'].mean():.1f}, max={df['amenities_count'].max()}")

# 3.2 Listing age (days since first review)
df['first_review'] = pd.to_datetime(df['first_review'], errors='coerce')
snapshot_date = pd.to_datetime(df['last_scraped'].iloc[0])  # Use scrape date as reference
df['listing_age_days'] = (snapshot_date - df['first_review']).dt.days
df['listing_age_days'] = df['listing_age_days'].clip(lower=0)  # No negative ages
df['has_reviews'] = df['first_review'].notna().astype(int)  # Flag for new listings
print(f"  ✓ listing_age_days: mean={df['listing_age_days'].mean():.0f} days, {df['has_reviews'].sum():,} listings with reviews")

# 3.3 Price per person
df['price_per_person'] = df['price_clean'] / df['accommodates'].replace(0, np.nan)
print(f"  ✓ price_per_person: mean=£{df['price_per_person'].mean():.2f}")

# 3.4 Host features (convert to binary)
df['is_superhost'] = (df['host_is_superhost'] == 't').astype(int)
df['host_identity_verified'] = (df['host_identity_verified'] == 't').astype(int)
df['instant_bookable'] = (df['instant_bookable'] == 't').astype(int)
print(f"  ✓ Binary host features: {df['is_superhost'].sum():,} superhosts, {df['instant_bookable'].sum():,} instant bookable")

# 3.5 Reviews velocity (reviews per month)
# Already exists as 'reviews_per_month', but ensure it's clean
df['reviews_per_month'] = df['reviews_per_month'].fillna(0)

# 3.6 Extract number from bathrooms_text
def parse_bathrooms(text):
    """Extract number from bathrooms_text (e.g., '2 baths' -> 2.0)"""
    if pd.isna(text):
        return np.nan
    try:
        # Look for numbers
        import re
        match = re.search(r'(\d+\.?\d*)', str(text))
        if match:
            return float(match.group(1))
        # Handle 'Half-bath' or 'Shared bath'
        if 'half' in str(text).lower():
            return 0.5
        return np.nan
    except:
        return np.nan

df['bathrooms_parsed'] = df['bathrooms_text'].apply(parse_bathrooms)
print(f"  ✓ Parsed bathrooms from text: {df['bathrooms_parsed'].notna().sum():,} values")

print(f"  ✓ Engineered {6} new features")

# ============================================================================
# STEP 4: JOIN VIBE FEATURES
# ============================================================================

print("\n[4/8] Joining vibe features by neighborhood...")

# Load vibe features
vibe_file = RAW_DIR / '01_vibe_features_for_modeling.csv'
vibe_df = pd.read_csv(vibe_file)
print(f"  ✓ Loaded vibe features from {vibe_file.name}: {len(vibe_df)} neighborhoods")

# Check join key
if 'neighbourhood_cleansed' not in df.columns:
    print("  ✗ ERROR: 'neighbourhood_cleansed' column not found!")
    raise KeyError("neighbourhood_cleansed missing from listings data")

# Standardize neighborhood names for joining (handle both string and numeric types)
df['neighbourhood'] = df['neighbourhood_cleansed'].astype(str).str.strip()
vibe_df['neighbourhood'] = vibe_df['neighbourhood'].astype(str).str.strip()

# Left join to preserve all listings
before_join = len(df)
df = df.merge(vibe_df, on='neighbourhood', how='left', suffixes=('', '_vibe'))
after_join = len(df)

print(f"  ✓ Joined vibe features: {before_join:,} → {after_join:,} rows")
assert before_join == after_join, "ERROR: Join created duplicate rows!"

# Check vibe match rate
vibe_match_rate = df['vibe_score'].notna().mean() * 100
print(f"  ✓ Vibe score match rate: {vibe_match_rate:.2f}%")

# Impute missing vibe features with city-wide means (from METHODOLOGY.md)
vibe_features = [col for col in vibe_df.columns if col != 'neighbourhood']
for col in vibe_features:
    if col in df.columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            city_mean = df[col].mean()
            df[col] = df[col].fillna(city_mean)
            print(f"    • Imputed {missing_count:,} missing {col} with mean={city_mean:.2f}")

# ============================================================================
# STEP 5: HANDLE MISSING DATA
# ============================================================================

print("\n[5/8] Handling missing data per METHODOLOGY.md...")

# 5.1 Bedrooms: Impute with median by room_type
for room_type in df['room_type'].unique():
    mask = (df['room_type'] == room_type) & df['bedrooms'].isna()
    if mask.sum() > 0:
        median_beds = df[df['room_type'] == room_type]['bedrooms'].median()
        df.loc[mask, 'bedrooms'] = median_beds
        print(f"  ✓ Imputed {mask.sum():,} missing bedrooms for {room_type} with median={median_beds:.0f}")

# 5.2 Bathrooms: Use parsed bathrooms_text, fallback to median
df['bathrooms_final'] = df['bathrooms'].fillna(df['bathrooms_parsed'])
missing_baths = df['bathrooms_final'].isna().sum()
if missing_baths > 0:
    overall_median = df['bathrooms_final'].median()
    df['bathrooms_final'] = df['bathrooms_final'].fillna(overall_median)
    print(f"  ✓ Imputed {missing_baths:,} missing bathrooms with median={overall_median:.1f}")

# 5.3 Review scores: Impute with neighborhood median + has_reviews flag
review_score_cols = ['review_scores_rating', 'review_scores_accuracy', 'review_scores_cleanliness',
                      'review_scores_checkin', 'review_scores_communication', 'review_scores_location',
                      'review_scores_value']

for col in review_score_cols:
    if col in df.columns:
        # Create neighborhood-level median lookup
        neighborhood_medians = df.groupby('neighbourhood')[col].median()

        # Impute missing with neighborhood median
        missing_mask = df[col].isna()
        df.loc[missing_mask, col] = df.loc[missing_mask, 'neighbourhood'].map(neighborhood_medians)

        # If still missing (entire neighborhood missing), use city-wide median
        still_missing = df[col].isna().sum()
        if still_missing > 0:
            city_median = df[col].median()
            df[col] = df[col].fillna(city_median)
            print(f"  ✓ Imputed {col}: neighborhood median + {still_missing:,} with city median")

# 5.4 Accommodates, beds: Fill with mode/median
if df['accommodates'].isna().sum() > 0:
    df['accommodates'] = df['accommodates'].fillna(df['accommodates'].median())
if df['beds'].isna().sum() > 0:
    df['beds'] = df['beds'].fillna(df['beds'].median())

# 5.5 Host listings count: Fill with 1 (assume single listing host)
if 'host_listings_count' in df.columns:
    df['host_listings_count'] = df['host_listings_count'].fillna(1)

print(f"  ✓ Missing data handled for all key features")

# ============================================================================
# STEP 6: SELECT FEATURES FOR MODELING
# ============================================================================

print("\n[6/8] Selecting features for modeling...")

# Define feature set (from METHODOLOGY.md)
feature_columns = [
    # Target
    'occ_90',
    'high_demand_90',

    # Property features
    'property_type',
    'room_type',
    'accommodates',
    'bedrooms',
    'bathrooms_final',
    'beds',
    'amenities_count',

    # Location
    'neighbourhood',
    'latitude',
    'longitude',

    # Host features
    'host_listings_count',
    'is_superhost',
    'host_identity_verified',

    # Reputation
    'number_of_reviews',
    'reviews_per_month',
    'review_scores_rating',
    'review_scores_accuracy',
    'review_scores_cleanliness',
    'review_scores_checkin',
    'review_scores_communication',
    'review_scores_location',
    'review_scores_value',

    # Booking
    'instant_bookable',
    'minimum_nights',

    # Derived
    'listing_age_days',
    'has_reviews',
    'price_per_person',
    'price_clean',

    # Vibe features (all columns from vibe_df except neighbourhood)
] + [col for col in vibe_features if col in df.columns]

# Add ID for tracking
feature_columns = ['id'] + feature_columns

# Select only columns that exist
available_features = [col for col in feature_columns if col in df.columns]
df_features = df[available_features].copy()

print(f"  ✓ Selected {len(available_features)} features for modeling")
print(f"  ✓ Feature categories: property, location, host, reputation, derived, vibe")

# Filter out rows with missing target variable
before_filter = len(df_features)
df_features = df_features[df_features['occ_90'].notna()].copy()
after_filter = len(df_features)
print(f"  ✓ Filtered to {after_filter:,} listings with valid occ_90 ({before_filter - after_filter:,} removed)")

# ============================================================================
# STEP 7: TRAIN/TEST SPLIT
# ============================================================================

print("\n[7/8] Creating train/test split...")

# Stratified split on high_demand_90
train_df, test_df = train_test_split(
    df_features,
    test_size=TEST_SIZE,
    random_state=RANDOM_SEED,
    stratify=df_features['high_demand_90']
)

print(f"  ✓ Train set: {len(train_df):,} listings ({len(train_df)/len(df_features)*100:.1f}%)")
print(f"  ✓ Test set:  {len(test_df):,} listings ({len(test_df)/len(df_features)*100:.1f}%)")
print(f"  ✓ Train high-demand rate: {train_df['high_demand_90'].mean()*100:.1f}%")
print(f"  ✓ Test high-demand rate:  {test_df['high_demand_90'].mean()*100:.1f}%")

# ============================================================================
# STEP 8: SAVE OUTPUTS
# ============================================================================

print("\n[8/8] Saving outputs...")

# Save train/test parquet files
train_file = PROCESSED_DIR / f'features_{CITY}_train.parquet'
test_file = PROCESSED_DIR / f'features_{CITY}_test.parquet'

train_df.to_parquet(train_file, index=False, engine='pyarrow')
test_df.to_parquet(test_file, index=False, engine='pyarrow')

print(f"  ✓ Saved {train_file.name} ({len(train_df):,} rows, {train_file.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"  ✓ Saved {test_file.name} ({len(test_df):,} rows, {test_file.stat().st_size / 1024 / 1024:.1f} MB)")

# Save feature summary
feature_summary = pd.DataFrame({
    'column': df_features.columns,
    'dtype': df_features.dtypes,
    'non_null_count': df_features.notna().sum(),
    'null_pct': (df_features.isna().sum() / len(df_features) * 100).round(2),
    'unique_values': df_features.nunique(),
    'mean': df_features.select_dtypes(include=[np.number]).mean(),
    'std': df_features.select_dtypes(include=[np.number]).std(),
    'min': df_features.select_dtypes(include=[np.number]).min(),
    'max': df_features.select_dtypes(include=[np.number]).max(),
})

summary_file = REPORTS_DIR / 'feature_summary.csv'
feature_summary.to_csv(summary_file, index=False)
print(f"  ✓ Saved {summary_file.name}")

# ============================================================================
# VALIDATION PLOTS
# ============================================================================

print("\n[BONUS] Generating validation plots...")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle(f'Feature Engineering Validation - {CITY.capitalize()}', fontsize=16, fontweight='bold')

# Plot 1: Target distribution
ax1 = axes[0, 0]
ax1.hist(df_features['occ_90'], bins=50, edgecolor='black', alpha=0.7)
ax1.axvline(HIGH_DEMAND_THRESHOLD, color='red', linestyle='--', linewidth=2, label=f'High-Demand Threshold ({HIGH_DEMAND_THRESHOLD})')
ax1.set_xlabel('Occupancy Rate (occ_90)')
ax1.set_ylabel('Frequency')
ax1.set_title('Target Variable Distribution')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: High-demand split
ax2 = axes[0, 1]
high_demand_counts = df_features['high_demand_90'].value_counts()
ax2.bar(['Low Demand', 'High Demand'], [high_demand_counts[0], high_demand_counts[1]], color=['skyblue', 'coral'], edgecolor='black')
ax2.set_ylabel('Number of Listings')
ax2.set_title(f'High-Demand Distribution (τ={HIGH_DEMAND_THRESHOLD})')
ax2.grid(True, alpha=0.3, axis='y')
for i, v in enumerate([high_demand_counts[0], high_demand_counts[1]]):
    ax2.text(i, v + 1000, f'{v:,}\n({v/len(df_features)*100:.1f}%)', ha='center', fontweight='bold')

# Plot 3: Vibe score distribution
ax3 = axes[0, 2]
ax3.hist(df_features['vibe_score'].dropna(), bins=30, edgecolor='black', alpha=0.7, color='mediumpurple')
ax3.set_xlabel('Vibe Score')
ax3.set_ylabel('Frequency')
ax3.set_title('Neighborhood Vibe Scores')
ax3.grid(True, alpha=0.3)

# Plot 4: Price per person by high-demand
ax4 = axes[1, 0]
df_features.boxplot(column='price_per_person', by='high_demand_90', ax=ax4)
ax4.set_xlabel('High Demand (0=No, 1=Yes)')
ax4.set_ylabel('Price per Person (£)')
ax4.set_title('Price per Person by Demand Level')
ax4.set_ylim(0, df_features['price_per_person'].quantile(0.95))
plt.sca(ax4)
plt.xticks([1, 2], ['Low Demand', 'High Demand'])

# Plot 5: Amenities count by room type
ax5 = axes[1, 1]
df_features.boxplot(column='amenities_count', by='room_type', ax=ax5)
ax5.set_xlabel('Room Type')
ax5.set_ylabel('Number of Amenities')
ax5.set_title('Amenities by Room Type')
plt.sca(ax5)
plt.xticks(rotation=45, ha='right')

# Plot 6: Review scores vs occupancy
ax6 = axes[1, 2]
ax6.scatter(df_features['review_scores_rating'], df_features['occ_90'], alpha=0.3, s=10)
ax6.set_xlabel('Review Score Rating')
ax6.set_ylabel('Occupancy Rate (occ_90)')
ax6.set_title('Review Scores vs Occupancy')
ax6.grid(True, alpha=0.3)

plt.tight_layout()
validation_plot = VIZ_DIR / '06_feature_engineering_validation.png'
plt.savefig(validation_plot, dpi=300, bbox_inches='tight')
plt.close()

print(f"  ✓ Saved {validation_plot.name}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("FEATURE ENGINEERING COMPLETE ✅")
print("=" * 80)
print(f"Original listings:     {original_count:,}")
print(f"Final dataset:         {len(df_features):,} ({len(df_features)/original_count*100:.1f}% retained)")
print(f"Train set:             {len(train_df):,} listings")
print(f"Test set:              {len(test_df):,} listings")
print(f"Total features:        {len(available_features)}")
print(f"High-demand rate:      {df_features['high_demand_90'].mean()*100:.1f}%")
print(f"Vibe match rate:       {vibe_match_rate:.2f}%")
print("=" * 80)
print(f"Outputs saved to: {PROCESSED_DIR}")
print(f"  • {train_file.name}")
print(f"  • {test_file.name}")
print(f"  • feature_summary.csv")
print(f"  • 06_feature_engineering_validation.png")
print("=" * 80)
print("Next step: Task 3 - High-Demand Twins k-NN Pricing Engine")
print("=" * 80)
