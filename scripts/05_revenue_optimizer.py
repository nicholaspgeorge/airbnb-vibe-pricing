"""
TASK 5: REVENUE OPTIMIZATION ENGINE

Generates revenue curves for Airbnb listings by sweeping price grids
and using the trained XGBoost model to predict occupancy at each price point.

Outputs:
- revenue_curves.parquet: Full grid predictions for sample listings
- revenue_recommendations.parquet: Summary of optimal prices
- Visualizations showing revenue opportunities

Author: Vibe-Aware Pricing Team
Date: 2025-11-06
"""

import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
import sys

# Configuration
CITY = 'austin'
RANDOM_SEED = 42
SAMPLE_SIZE = 500  # Number of listings to analyze (use 'all' for full test set)
N_PRICE_POINTS = 50  # Points in price grid
MIN_OCC_THRESHOLD = 0.75  # Minimum occupancy for "safe" price band

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / f'data/{CITY}'
MODEL_PATH = DATA_DIR / 'models/xgboost_with_vibe.pkl'
OLS_MODEL_PATH = DATA_DIR / 'models/ols_price_control.pkl'
TRAIN_DATA_PATH = DATA_DIR / f'processed/features_{CITY}_train.parquet'
TEST_DATA_PATH = DATA_DIR / f'processed/features_{CITY}_test.parquet'
OUTPUT_DIR = DATA_DIR / 'outputs/recommendations'
VIZ_DIR = DATA_DIR / 'outputs/visualizations'

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIZ_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("REVENUE OPTIMIZATION ENGINE - LONDON")
print("=" * 80)
print(f"Sample size: {SAMPLE_SIZE}")
print(f"Price grid points: {N_PRICE_POINTS}")
print(f"Minimum occupancy threshold: {MIN_OCC_THRESHOLD}")
print("=" * 80)
print()

# ============================================================================
# STEP 1: Load Model and Data
# ============================================================================

print("[1/7] Loading trained model and data...")

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f"  ✓ XGBoost model loaded: {MODEL_PATH.name}")
except Exception as e:
    print(f"  ✗ Error loading model: {e}")
    sys.exit(1)

try:
    with open(OLS_MODEL_PATH, 'rb') as f:
        ols_model = pickle.load(f)
    print(f"  ✓ OLS model loaded: {OLS_MODEL_PATH.name}")
except Exception as e:
    print(f"  ✗ Error loading OLS model: {e}")
    sys.exit(1)

try:
    train_data = pd.read_parquet(TRAIN_DATA_PATH)
    print(f"  ✓ Train data loaded: {len(train_data):,} listings")
    test_data = pd.read_parquet(TEST_DATA_PATH)
    print(f"  ✓ Test data loaded: {len(test_data):,} listings")
except Exception as e:
    print(f"  ✗ Error loading data: {e}")
    sys.exit(1)

# Filter out listings with missing price
test_data = test_data.dropna(subset=['price_clean'])
print(f"  ✓ After removing missing prices: {len(test_data):,} listings")

# Sample listings if specified
if SAMPLE_SIZE != 'all' and SAMPLE_SIZE < len(test_data):
    test_sample = test_data.sample(n=SAMPLE_SIZE, random_state=RANDOM_SEED)
    print(f"  ✓ Sampled {SAMPLE_SIZE} listings for analysis")
else:
    test_sample = test_data.copy()
    print(f"  ✓ Using all {len(test_sample):,} listings")

print()

# ============================================================================
# STEP 1.5: Preprocess Features (Encode Categoricals and Compute Epsilon_Price)
# ============================================================================

print("[2/7] Preprocessing features...")

# Categorical features that need encoding
categorical_features = ['room_type', 'property_type', 'neighbourhood']

# Fit label encoders on training data and transform both train and test
encoders = {}
for col in categorical_features:
    if col in train_data.columns:
        le = LabelEncoder()
        # Fit on train data
        le.fit(train_data[col].astype(str))
        # Transform test data (handle unseen categories)
        test_sample[col + '_encoded'] = test_sample[col].apply(
            lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
        )
        encoders[col] = le
        print(f"  ✓ Encoded {col}: {len(le.classes_)} categories")

# Compute epsilon_price using OLS model
# OLS was trained on: neighbourhood_encoded, minimum_nights, host_listings_count
stage1_features = ['neighbourhood_encoded', 'minimum_nights', 'host_listings_count']
stage1_available = [f for f in stage1_features if f in test_sample.columns]

X_stage1 = test_sample[stage1_available].fillna(0)
test_sample['price_pred_stage1'] = ols_model.predict(X_stage1)
test_sample['epsilon_price'] = test_sample['price_clean'] - test_sample['price_pred_stage1']
print(f"  ✓ Computed epsilon_price (price residuals)")

print()

# ============================================================================
# STEP 3: Define Revenue Optimization Functions
# ============================================================================

print("[3/7] Defining revenue optimization functions...")

def create_price_grid(current_price, n_points=N_PRICE_POINTS):
    """
    Create price grid from 0.5x to 2.0x current price

    Args:
        current_price: Current nightly price
        n_points: Number of points in grid

    Returns:
        numpy array of prices
    """
    min_price = current_price * 0.5
    max_price = current_price * 2.0
    return np.linspace(min_price, max_price, n_points)


def generate_revenue_curve(model, listing_row, feature_columns, n_points=N_PRICE_POINTS):
    """
    Generate revenue curve for a single listing

    Args:
        model: Trained model
        listing_row: Pandas Series with listing features
        feature_columns: List of feature column names
        n_points: Number of price points to test

    Returns:
        DataFrame with columns: price, predicted_occ_90, monthly_revenue
    """
    current_price = listing_row['price_clean']
    accommodates = listing_row['accommodates']

    price_grid = create_price_grid(current_price, n_points)
    results = []

    # Prepare feature vector (need to match training features)
    for price in price_grid:
        # Create a copy of the listing features
        features = listing_row[feature_columns].copy()

        # Update price-related features
        features['price_clean'] = price
        features['price_per_person'] = price / accommodates if accommodates > 0 else price

        # Predict occupancy
        try:
            predicted_occ = model.predict([features])[0]
            predicted_occ = np.clip(predicted_occ, 0, 1)  # Ensure [0, 1] range
        except Exception as e:
            print(f"    ⚠ Prediction error for listing {listing_row['id']}: {e}")
            predicted_occ = 0

        # Calculate monthly revenue (30 days)
        monthly_revenue = price * predicted_occ * 30

        results.append({
            'price': price,
            'predicted_occ_90': predicted_occ,
            'monthly_revenue': monthly_revenue
        })

    return pd.DataFrame(results)


def optimize_price(revenue_curve, current_price, min_occ=MIN_OCC_THRESHOLD):
    """
    Find optimal price and safe range from revenue curve

    Args:
        revenue_curve: DataFrame with price, predicted_occ_90, monthly_revenue
        current_price: Current listing price
        min_occ: Minimum occupancy for safe band

    Returns:
        dict with optimization results
    """
    # Find optimal price (max revenue)
    optimal_idx = revenue_curve['monthly_revenue'].idxmax()
    optimal_price = revenue_curve.loc[optimal_idx, 'price']
    optimal_revenue = revenue_curve.loc[optimal_idx, 'monthly_revenue']
    optimal_occ = revenue_curve.loc[optimal_idx, 'predicted_occ_90']

    # Current revenue (find closest price in grid)
    current_idx = (revenue_curve['price'] - current_price).abs().idxmin()
    current_revenue = revenue_curve.loc[current_idx, 'monthly_revenue']
    current_occ = revenue_curve.loc[current_idx, 'predicted_occ_90']

    # Safe range (where occ_90 >= min_occ)
    safe_prices = revenue_curve[revenue_curve['predicted_occ_90'] >= min_occ]

    if len(safe_prices) > 0:
        safe_low = safe_prices['price'].min()
        safe_high = safe_prices['price'].max()
        safe_revenue_max = safe_prices['monthly_revenue'].max()
    else:
        safe_low = safe_high = safe_revenue_max = None

    # Revenue lift
    revenue_lift = ((optimal_revenue - current_revenue) / current_revenue) * 100 if current_revenue > 0 else 0

    # Price change
    price_change_pct = ((optimal_price - current_price) / current_price) * 100 if current_price > 0 else 0

    return {
        'current_price': current_price,
        'current_revenue': current_revenue,
        'current_occ': current_occ,
        'optimal_price': optimal_price,
        'optimal_revenue': optimal_revenue,
        'optimal_occ': optimal_occ,
        'safe_low': safe_low,
        'safe_high': safe_high,
        'safe_revenue_max': safe_revenue_max,
        'revenue_lift_pct': revenue_lift,
        'price_change_pct': price_change_pct,
        'has_safe_band': safe_low is not None
    }

print("  ✓ Functions defined")
print()

# ============================================================================
# STEP 4: Get Feature Columns from Model
# ============================================================================

print("[4/7] Identifying feature columns...")

# Get feature names from model
try:
    feature_names = model.get_booster().feature_names
    print(f"  ✓ Model expects {len(feature_names)} features")

    # Verify all features exist in test data
    missing_features = [f for f in feature_names if f not in test_sample.columns]
    if missing_features:
        print(f"  ✗ Missing features in test data: {missing_features}")
        sys.exit(1)

except Exception as e:
    print(f"  ⚠ Could not get feature names from model, using all numeric columns")
    feature_names = test_sample.select_dtypes(include=[np.number]).columns.tolist()
    # Remove target and ID columns
    feature_names = [f for f in feature_names if f not in ['id', 'occ_90', 'high_demand_90', 'price_clean', 'price_per_person']]

print()

# ============================================================================
# STEP 5: Generate Revenue Curves for All Sampled Listings
# ============================================================================

print(f"[5/7] Generating revenue curves for {len(test_sample):,} listings...")
print("  (This may take 2-3 minutes with GPU acceleration)")

revenue_curves_data = []
optimization_results = []

for idx, (_, row) in enumerate(test_sample.iterrows(), 1):
    if idx % 100 == 0:
        print(f"  Processing listing {idx}/{len(test_sample)}...")

    listing_id = row['id']
    current_price = row['price_clean']

    # Generate revenue curve
    try:
        curve = generate_revenue_curve(model, row, feature_names)
        curve['listing_id'] = listing_id
        revenue_curves_data.append(curve)

        # Optimize price
        opt_result = optimize_price(curve, current_price)
        opt_result['listing_id'] = listing_id
        opt_result['property_type'] = row['property_type']
        opt_result['room_type'] = row['room_type']
        opt_result['accommodates'] = row['accommodates']
        opt_result['vibe_score'] = row['vibe_score']
        opt_result['neighbourhood'] = row['neighbourhood']
        optimization_results.append(opt_result)

    except Exception as e:
        print(f"  ⚠ Error processing listing {listing_id}: {e}")
        continue

print(f"  ✓ Generated curves for {len(revenue_curves_data):,} listings")
print()

# ============================================================================
# STEP 6: Save Results
# ============================================================================

print("[6/7] Saving results...")

# Combine and save revenue curves
revenue_curves_all = pd.concat(revenue_curves_data, ignore_index=True)
curves_path = OUTPUT_DIR / 'revenue_curves.parquet'
revenue_curves_all.to_parquet(curves_path)
print(f"  ✓ Saved revenue curves: {curves_path}")

# Save optimization recommendations
optimization_df = pd.DataFrame(optimization_results)
parquet_path = OUTPUT_DIR / 'revenue_recommendations.parquet'
csv_path = OUTPUT_DIR / 'revenue_recommendations.csv'
optimization_df.to_parquet(parquet_path)
optimization_df.to_csv(csv_path, index=False)
print(f"  ✓ Saved recommendations: {parquet_path}")
print(f"  ✓ Saved recommendations (CSV): {csv_path}")

print()

# ============================================================================
# STEP 7: Generate Summary Statistics
# ============================================================================

print("[7/7] Computing summary statistics...")

# Overall statistics
print("\n" + "="*80)
print("REVENUE OPTIMIZATION SUMMARY")
print("="*80)

print(f"\nListings Analyzed: {len(optimization_df):,}")
print(f"Listings with Safe Band (occ≥{MIN_OCC_THRESHOLD}): {optimization_df['has_safe_band'].sum():,} ({optimization_df['has_safe_band'].mean()*100:.1f}%)")

print("\nRevenue Lift Opportunities:")
print(f"  Median revenue lift: {optimization_df['revenue_lift_pct'].median():.1f}%")
print(f"  Mean revenue lift: {optimization_df['revenue_lift_pct'].mean():.1f}%")
print(f"  Listings with >10% lift: {(optimization_df['revenue_lift_pct'] > 10).sum():,} ({(optimization_df['revenue_lift_pct'] > 10).mean()*100:.1f}%)")
print(f"  Listings with >20% lift: {(optimization_df['revenue_lift_pct'] > 20).sum():,} ({(optimization_df['revenue_lift_pct'] > 20).mean()*100:.1f}%)")

print("\nPrice Change Recommendations:")
print(f"  Should increase price: {(optimization_df['price_change_pct'] > 5).sum():,} ({(optimization_df['price_change_pct'] > 5).mean()*100:.1f}%)")
print(f"  Price about right (±5%): {(optimization_df['price_change_pct'].abs() <= 5).sum():,} ({(optimization_df['price_change_pct'].abs() <= 5).mean()*100:.1f}%)")
print(f"  Should decrease price: {(optimization_df['price_change_pct'] < -5).sum():,} ({(optimization_df['price_change_pct'] < -5).mean()*100:.1f}%)")

print("\nCurrent vs Optimal Pricing:")
print(f"  Current median price: £{optimization_df['current_price'].median():.0f}")
print(f"  Optimal median price: £{optimization_df['optimal_price'].median():.0f}")
print(f"  Current median revenue: £{optimization_df['current_revenue'].median():.0f}/month")
print(f"  Optimal median revenue: £{optimization_df['optimal_revenue'].median():.0f}/month")

print("\nBy Property Type:")
by_property = optimization_df.groupby('property_type').agg({
    'revenue_lift_pct': 'median',
    'listing_id': 'count'
}).sort_values('revenue_lift_pct', ascending=False).head(10)
by_property.columns = ['Median Revenue Lift %', 'Count']
print(by_property.to_string())

print("\nBy Room Type:")
by_room = optimization_df.groupby('room_type').agg({
    'revenue_lift_pct': 'median',
    'price_change_pct': 'median',
    'listing_id': 'count'
})
by_room.columns = ['Median Revenue Lift %', 'Median Price Change %', 'Count']
print(by_room.to_string())

print("\n" + "="*80)
print("REVENUE OPTIMIZATION COMPLETE ✅")
print("="*80)
print("\nOutputs saved to:")
print(f"  • {curves_path}")
print(f"  • {parquet_path}")
print(f"  • {csv_path}")
print("\nNext step: Task 5 Visualizations - Run visualization script")
print("="*80)
