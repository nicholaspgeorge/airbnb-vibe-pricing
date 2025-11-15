#!/usr/bin/env python3
"""
High-Demand Twins k-NN Pricing Engine
Finds similar high-demand listings and recommends price bands

Uses k-NN to find comparable listings based on property features + vibe,
then filters to high-demand listings to provide pricing recommendations.

Based on METHODOLOGY.md decisions
Author: Team (Nicholas, Sahil, Heath)
Date: 2025-11-06
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

CITY = 'nyc'
K_NEIGHBORS = 25  # Number of neighbors to find
MIN_HIGH_DEMAND_NEIGHBORS = 5  # Minimum for high confidence
RANDOM_SEED = 42

# Paths
DATA_DIR = Path(f'data/{CITY}')
PROCESSED_DIR = DATA_DIR / 'processed'
OUTPUT_DIR = DATA_DIR / 'outputs'
RECO_DIR = OUTPUT_DIR / 'recommendations'
VIZ_DIR = OUTPUT_DIR / 'visualizations'

# Create directories
RECO_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print(f"HIGH-DEMAND TWINS k-NN PRICING ENGINE - {CITY.upper()}")
print("=" * 80)
print(f"k = {K_NEIGHBORS} neighbors")
print(f"Minimum high-demand neighbors for confidence: {MIN_HIGH_DEMAND_NEIGHBORS}")
print("=" * 80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print("\n[1/8] Loading train/test datasets...")

train_file = PROCESSED_DIR / f'features_{CITY}_train.parquet'
test_file = PROCESSED_DIR / f'features_{CITY}_test.parquet'

train_df = pd.read_parquet(train_file)
test_df = pd.read_parquet(test_file)

print(f"  ✓ Train set: {len(train_df):,} listings")
print(f"  ✓ Test set:  {len(test_df):,} listings")
print(f"  ✓ Train high-demand: {train_df['high_demand_90'].sum():,} ({train_df['high_demand_90'].mean()*100:.1f}%)")

# Filter out listings with missing price (can't recommend if no price data)
train_df = train_df[train_df['price_clean'].notna()].copy()
test_df = test_df[test_df['price_clean'].notna()].copy()

print(f"  ✓ After price filter - Train: {len(train_df):,}, Test: {len(test_df):,}")

# ============================================================================
# STEP 2: DEFINE FEATURES FOR k-NN
# ============================================================================

print("\n[2/8] Defining features for k-NN model...")

# Feature selection (from METHODOLOGY.md)
# Use property features + vibe dimensions for similarity matching

# Numerical features
numerical_features = [
    'accommodates',
    'bedrooms',
    'bathrooms_final',
    'beds',
    'amenities_count',
    'vibe_score',
    'walkability_score',
    'safety_score',
    'nightlife_score',
    'family_friendly_score',
    'local_authentic_score',
    'convenience_score',
    'food_scene_score',
    'liveliness_score',
    'charm_score'
]

# Categorical features
categorical_features = [
    'room_type',
    'property_type'
]

# Verify all features exist
available_numerical = [f for f in numerical_features if f in train_df.columns]
available_categorical = [f for f in categorical_features if f in train_df.columns]

print(f"  ✓ Numerical features: {len(available_numerical)}")
print(f"  ✓ Categorical features: {len(available_categorical)}")

# ============================================================================
# STEP 3: PREPROCESS FEATURES
# ============================================================================

print("\n[3/8] Preprocessing features...")

# Handle missing values in numerical features
for col in available_numerical:
    if train_df[col].isna().sum() > 0:
        median_val = train_df[col].median()
        train_df[col] = train_df[col].fillna(median_val)
        test_df[col] = test_df[col].fillna(median_val)
        print(f"  • Filled {col} missing values with median={median_val:.2f}")

# Limit categorical cardinality (top N categories + "Other")
MAX_CATEGORIES = 10

for col in available_categorical:
    top_categories = train_df[col].value_counts().head(MAX_CATEGORIES).index
    train_df[col] = train_df[col].apply(lambda x: x if x in top_categories else 'Other')
    test_df[col] = test_df[col].apply(lambda x: x if x in top_categories else 'Other')

# Create preprocessing pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), available_numerical),
        ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'),
         available_categorical)
    ],
    remainder='drop'
)

# Fit on training data
X_train = preprocessor.fit_transform(train_df)
X_test = preprocessor.transform(test_df)

print(f"  ✓ Preprocessed feature matrix: {X_train.shape[1]} dimensions")
print(f"  ✓ Train shape: {X_train.shape}")
print(f"  ✓ Test shape:  {X_test.shape}")

# ============================================================================
# STEP 4: BUILD k-NN MODEL
# ============================================================================

print(f"\n[4/8] Building k-NN model with k={K_NEIGHBORS}...")

# Use ball_tree for efficiency with mixed features
knn_model = NearestNeighbors(
    n_neighbors=K_NEIGHBORS,
    algorithm='ball_tree',
    metric='euclidean',
    n_jobs=-1  # Use all CPU cores
)

knn_model.fit(X_train)

print(f"  ✓ k-NN model fitted on {len(X_train):,} training listings")

# ============================================================================
# STEP 5: FIND NEIGHBORS FOR TEST SET
# ============================================================================

print(f"\n[5/8] Finding {K_NEIGHBORS} nearest neighbors for each test listing...")

# Find neighbors
distances, indices = knn_model.kneighbors(X_test)

print(f"  ✓ Found neighbors for {len(test_df):,} test listings")
print(f"  ✓ Distance matrix shape: {distances.shape}")

# ============================================================================
# STEP 6: FILTER TO HIGH-DEMAND NEIGHBORS & COMPUTE PRICE BANDS
# ============================================================================

print("\n[6/8] Filtering to high-demand neighbors and computing price bands...")

recommendations = []

for i, test_idx in enumerate(test_df.index):
    # Get neighbor indices
    neighbor_indices = indices[i]

    # Get neighbor data
    neighbors = train_df.iloc[neighbor_indices].copy()
    neighbors['distance'] = distances[i]

    # Filter to high-demand neighbors
    high_demand_neighbors = neighbors[neighbors['high_demand_90'] == 1]
    n_high_demand = len(high_demand_neighbors)

    # Get prices from high-demand neighbors
    if n_high_demand >= MIN_HIGH_DEMAND_NEIGHBORS:
        # Sufficient high-demand neighbors
        neighbor_prices = high_demand_neighbors['price_clean'].values

        # Compute price band [p25, p75]
        price_low = np.percentile(neighbor_prices, 25)
        price_high = np.percentile(neighbor_prices, 75)
        price_median = np.median(neighbor_prices)

        confidence = 'high' if n_high_demand >= 10 else 'medium'

    elif n_high_demand > 0:
        # Some high-demand neighbors but below threshold
        neighbor_prices = high_demand_neighbors['price_clean'].values

        # Use IQR but flag as low confidence
        price_low = np.percentile(neighbor_prices, 25)
        price_high = np.percentile(neighbor_prices, 75)
        price_median = np.median(neighbor_prices)

        confidence = 'low'

    else:
        # No high-demand neighbors - fallback to neighborhood median
        test_neighborhood = test_df.loc[test_idx, 'neighbourhood']
        neighborhood_prices = train_df[
            (train_df['neighbourhood'] == test_neighborhood) &
            (train_df['high_demand_90'] == 1)
        ]['price_clean']

        if len(neighborhood_prices) > 0:
            price_median = neighborhood_prices.median()
            price_low = np.percentile(neighborhood_prices, 25)
            price_high = np.percentile(neighborhood_prices, 75)
            confidence = 'very_low_fallback'
        else:
            # Ultimate fallback: use all neighbors regardless of demand
            all_neighbor_prices = neighbors['price_clean'].values
            price_median = np.median(all_neighbor_prices)
            price_low = np.percentile(all_neighbor_prices, 25)
            price_high = np.percentile(all_neighbor_prices, 75)
            confidence = 'very_low_all_neighbors'

    # Get actual price and listing details
    actual_price = test_df.loc[test_idx, 'price_clean']
    listing_id = test_df.loc[test_idx, 'id']

    # Calculate metrics
    price_band_width = price_high - price_low
    is_within_band = price_low <= actual_price <= price_high
    price_gap = 0 if is_within_band else min(abs(actual_price - price_low), abs(actual_price - price_high))

    recommendations.append({
        'id': listing_id,
        'actual_price': actual_price,
        'reco_price_low': price_low,
        'reco_price_median': price_median,
        'reco_price_high': price_high,
        'band_width': price_band_width,
        'n_neighbors_total': K_NEIGHBORS,
        'n_neighbors_high_demand': n_high_demand,
        'confidence': confidence,
        'is_within_band': is_within_band,
        'price_gap': price_gap,
        'avg_neighbor_distance': distances[i].mean(),
        'neighbourhood': test_df.loc[test_idx, 'neighbourhood'],
        'room_type': test_df.loc[test_idx, 'room_type'],
        'accommodates': test_df.loc[test_idx, 'accommodates'],
        'vibe_score': test_df.loc[test_idx, 'vibe_score']
    })

reco_df = pd.DataFrame(recommendations)

print(f"  ✓ Generated {len(reco_df):,} price recommendations")

# Confidence breakdown
confidence_counts = reco_df['confidence'].value_counts()
print(f"\n  Confidence Distribution:")
for conf, count in confidence_counts.items():
    print(f"    • {conf}: {count:,} ({count/len(reco_df)*100:.1f}%)")

# ============================================================================
# STEP 7: SAVE RECOMMENDATIONS
# ============================================================================

print("\n[7/8] Saving recommendations...")

reco_file = RECO_DIR / 'price_bands_neighbors.parquet'
reco_df.to_parquet(reco_file, index=False, engine='pyarrow')

print(f"  ✓ Saved {reco_file.name} ({len(reco_df):,} rows)")

# Also save CSV for easy viewing
csv_file = RECO_DIR / 'price_bands_neighbors.csv'
reco_df.to_csv(csv_file, index=False)
print(f"  ✓ Saved {csv_file.name}")

# ============================================================================
# STEP 8: EVALUATION METRICS & VISUALIZATIONS
# ============================================================================

print("\n[8/8] Generating evaluation metrics and visualizations...")

# Calculate evaluation metrics
metrics = {
    'total_listings': len(reco_df),
    'pct_high_confidence': (reco_df['confidence'] == 'high').sum() / len(reco_df) * 100,
    'pct_within_band': reco_df['is_within_band'].mean() * 100,
    'median_band_width': reco_df['band_width'].median(),
    'mean_band_width': reco_df['band_width'].mean(),
    'median_n_high_demand_neighbors': reco_df['n_neighbors_high_demand'].median(),
    'pct_sufficient_neighbors': (reco_df['n_neighbors_high_demand'] >= MIN_HIGH_DEMAND_NEIGHBORS).sum() / len(reco_df) * 100
}

print(f"\n  📊 EVALUATION METRICS:")
print(f"    • Total recommendations: {metrics['total_listings']:,}")
print(f"    • High confidence: {metrics['pct_high_confidence']:.1f}%")
print(f"    • Sufficient neighbors (≥{MIN_HIGH_DEMAND_NEIGHBORS}): {metrics['pct_sufficient_neighbors']:.1f}%")
print(f"    • Actual price within band: {metrics['pct_within_band']:.1f}%")
print(f"    • Median band width: £{metrics['median_band_width']:.2f}")
print(f"    • Mean band width: £{metrics['mean_band_width']:.2f}")
print(f"    • Median high-demand neighbors: {metrics['median_n_high_demand_neighbors']:.0f}")

# Create visualizations
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle(f'High-Demand Twins k-NN Pricing Engine - {CITY.capitalize()}',
             fontsize=16, fontweight='bold')

# Plot 1: Confidence distribution
ax1 = axes[0, 0]
conf_counts = reco_df['confidence'].value_counts()
colors = {'high': 'green', 'medium': 'orange', 'low': 'yellow',
          'very_low_fallback': 'red', 'very_low_all_neighbors': 'darkred'}
bar_colors = [colors.get(c, 'gray') for c in conf_counts.index]
ax1.bar(range(len(conf_counts)), conf_counts.values, color=bar_colors, edgecolor='black')
ax1.set_xticks(range(len(conf_counts)))
ax1.set_xticklabels(conf_counts.index, rotation=45, ha='right')
ax1.set_ylabel('Number of Listings')
ax1.set_title('Recommendation Confidence Distribution')
ax1.grid(True, alpha=0.3, axis='y')

# Plot 2: High-demand neighbors distribution
ax2 = axes[0, 1]
ax2.hist(reco_df['n_neighbors_high_demand'], bins=25, edgecolor='black', alpha=0.7, color='steelblue')
ax2.axvline(MIN_HIGH_DEMAND_NEIGHBORS, color='red', linestyle='--', linewidth=2,
            label=f'Min Threshold ({MIN_HIGH_DEMAND_NEIGHBORS})')
ax2.set_xlabel('Number of High-Demand Neighbors')
ax2.set_ylabel('Frequency')
ax2.set_title(f'High-Demand Neighbors Found (k={K_NEIGHBORS})')
ax2.legend()
ax2.grid(True, alpha=0.3)

# Plot 3: Price band width distribution
ax3 = axes[0, 2]
ax3.hist(reco_df['band_width'], bins=50, edgecolor='black', alpha=0.7, color='coral')
ax3.axvline(reco_df['band_width'].median(), color='red', linestyle='--', linewidth=2,
            label=f'Median: £{reco_df["band_width"].median():.2f}')
ax3.set_xlabel('Price Band Width (£)')
ax3.set_ylabel('Frequency')
ax3.set_title('Recommended Price Band Widths')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.set_xlim(0, reco_df['band_width'].quantile(0.95))

# Plot 4: Actual vs Recommended (scatter)
ax4 = axes[1, 0]
within_band = reco_df[reco_df['is_within_band']]
outside_band = reco_df[~reco_df['is_within_band']]
ax4.scatter(within_band['reco_price_median'], within_band['actual_price'],
           alpha=0.3, s=10, color='green', label='Within band')
ax4.scatter(outside_band['reco_price_median'], outside_band['actual_price'],
           alpha=0.3, s=10, color='red', label='Outside band')
ax4.plot([0, reco_df['reco_price_median'].max()], [0, reco_df['reco_price_median'].max()],
         'k--', linewidth=1, alpha=0.5)
ax4.set_xlabel('Recommended Price (Median)')
ax4.set_ylabel('Actual Price')
ax4.set_title(f'Actual vs Recommended Price\n({metrics["pct_within_band"]:.1f}% within band)')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.set_xlim(0, 500)
ax4.set_ylim(0, 500)

# Plot 5: Band width by room type
ax5 = axes[1, 1]
room_types = reco_df['room_type'].value_counts().head(4).index
data_by_room = [reco_df[reco_df['room_type'] == rt]['band_width'].values for rt in room_types]
ax5.boxplot(data_by_room, labels=room_types)
ax5.set_ylabel('Price Band Width (£)')
ax5.set_title('Band Width by Room Type')
ax5.grid(True, alpha=0.3, axis='y')
plt.sca(ax5)
plt.xticks(rotation=45, ha='right')

# Plot 6: Coverage by confidence level
ax6 = axes[1, 2]
coverage_by_conf = reco_df.groupby('confidence')['is_within_band'].mean() * 100
ax6.bar(range(len(coverage_by_conf)), coverage_by_conf.values,
       color=bar_colors, edgecolor='black')
ax6.set_xticks(range(len(coverage_by_conf)))
ax6.set_xticklabels(coverage_by_conf.index, rotation=45, ha='right')
ax6.set_ylabel('% Actual Price Within Band')
ax6.set_title('Coverage Rate by Confidence Level')
ax6.set_ylim(0, 100)
ax6.grid(True, alpha=0.3, axis='y')
ax6.axhline(50, color='gray', linestyle='--', linewidth=1, alpha=0.5)

plt.tight_layout()
viz_file = VIZ_DIR / '07_knn_pricing_evaluation.png'
plt.savefig(viz_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"  ✓ Saved {viz_file.name}")

# Save metrics to file
metrics_file = RECO_DIR / 'knn_metrics.txt'
with open(metrics_file, 'w') as f:
    f.write("=" * 60 + "\n")
    f.write(f"HIGH-DEMAND TWINS k-NN PRICING ENGINE - {CITY.upper()}\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"Configuration:\n")
    f.write(f"  k = {K_NEIGHBORS} neighbors\n")
    f.write(f"  Min high-demand neighbors threshold = {MIN_HIGH_DEMAND_NEIGHBORS}\n\n")
    f.write(f"Evaluation Metrics:\n")
    for key, value in metrics.items():
        if isinstance(value, float):
            f.write(f"  {key}: {value:.2f}\n")
        else:
            f.write(f"  {key}: {value}\n")

print(f"  ✓ Saved {metrics_file.name}")

# ============================================================================
# EXAMPLE RECOMMENDATIONS
# ============================================================================

print("\n" + "=" * 80)
print("EXAMPLE RECOMMENDATIONS")
print("=" * 80)

# Show 5 example recommendations (different confidence levels)
examples = []
for conf in ['high', 'medium', 'low']:
    sample = reco_df[reco_df['confidence'] == conf].sample(n=min(2, len(reco_df[reco_df['confidence'] == conf])))
    examples.append(sample)

example_df = pd.concat(examples).head(5)

for idx, row in example_df.iterrows():
    print(f"\nListing ID: {row['id']}")
    print(f"  Room Type: {row['room_type']}, Accommodates: {int(row['accommodates'])}, Vibe: {row['vibe_score']:.0f}")
    print(f"  Actual Price: £{row['actual_price']:.2f}")
    print(f"  Recommended Band: £{row['reco_price_low']:.2f} - £{row['reco_price_high']:.2f} (median: £{row['reco_price_median']:.2f})")
    print(f"  High-Demand Neighbors: {int(row['n_neighbors_high_demand'])} / {K_NEIGHBORS}")
    print(f"  Confidence: {row['confidence']}")
    print(f"  Within Band: {'✓ Yes' if row['is_within_band'] else '✗ No'}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("HIGH-DEMAND TWINS k-NN ENGINE COMPLETE ✅")
print("=" * 80)
print(f"Recommendations generated:    {len(reco_df):,}")
print(f"High confidence:              {metrics['pct_high_confidence']:.1f}%")
print(f"Sufficient neighbors:         {metrics['pct_sufficient_neighbors']:.1f}%")
print(f"Coverage (within band):       {metrics['pct_within_band']:.1f}%")
print(f"Median band width:            £{metrics['median_band_width']:.2f}")
print("=" * 80)
print(f"Outputs saved to: {RECO_DIR}")
print(f"  • price_bands_neighbors.parquet")
print(f"  • price_bands_neighbors.csv")
print(f"  • knn_metrics.txt")
print(f"  • 07_knn_pricing_evaluation.png")
print("=" * 80)
print("Next step: Task 4 - Predictive Model with Control Function")
print("=" * 80)
