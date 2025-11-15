#!/usr/bin/env python3
"""
Retrain XGBoost Model with Monotonic Constraints

This script retrains the XGBoost model with monotonic constraints to ensure
occupancy predictions decrease (or stay flat) as price increases.

Based on OCCUPANCY_MODEL_DIAGNOSTIC_REPORT.md recommendations

Author: Team (Nicholas, Sahil, Heath)
Date: 2025-11-14
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import pickle
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

CITY = 'london'
RANDOM_SEED = 42
N_FOLDS = 5
N_JOBS = -1

# GPU Configuration
USE_GPU = True
GPU_ID = 1

# Paths
DATA_DIR = Path(f'data/{CITY}')
PROCESSED_DIR = DATA_DIR / 'processed'
MODELS_DIR = DATA_DIR / 'models'
OUTPUT_DIR = DATA_DIR / 'outputs'
VIZ_DIR = OUTPUT_DIR / 'visualizations'
REPORTS_DIR = OUTPUT_DIR / 'reports'

# Detect GPU
try:
    import subprocess
    gpu_check = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True)
    gpu_available = gpu_check.returncode == 0 and USE_GPU
    if not gpu_available:
        USE_GPU = False
except:
    USE_GPU = False

print("=" * 80)
print(f"RETRAINING XGBOOST WITH MONOTONIC CONSTRAINTS - {CITY.upper()}")
print("=" * 80)
print(f"GPU: {'Enabled (GPU ' + str(GPU_ID) + ')' if USE_GPU else 'Disabled (CPU)'}")
print("=" * 80)

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

print("\n[1/5] Loading train/test datasets...")

train_file = PROCESSED_DIR / f'features_{CITY}_train.parquet'
test_file = PROCESSED_DIR / f'features_{CITY}_test.parquet'

train_df = pd.read_parquet(train_file)
test_df = pd.read_parquet(test_file)

# Filter to valid data
train_df = train_df[train_df['price_clean'].notna() & train_df['occ_90'].notna()].copy()
test_df = test_df[test_df['price_clean'].notna() & test_df['occ_90'].notna()].copy()

print(f"  ✓ Train set: {len(train_df):,} listings")
print(f"  ✓ Test set:  {len(test_df):,} listings")

# ============================================================================
# STEP 2: PREPARE FEATURES
# ============================================================================

print("\n[2/5] Preparing features...")

# Features for occupancy prediction
property_features = [
    'accommodates', 'bedrooms', 'bathrooms_final', 'beds', 'amenities_count'
]
location_features = ['latitude', 'longitude']
host_features = ['host_listings_count', 'is_superhost', 'host_identity_verified']
reputation_features = [
    'number_of_reviews', 'reviews_per_month', 'review_scores_rating',
    'review_scores_cleanliness', 'review_scores_location', 'review_scores_value'
]
booking_features = ['instant_bookable', 'minimum_nights']
derived_features = ['listing_age_days', 'has_reviews', 'price_per_person']
vibe_features = [
    'vibe_score', 'sentiment_mean', 'walkability_score', 'safety_score',
    'nightlife_score', 'family_friendly_score', 'local_authentic_score',
    'convenience_score', 'food_scene_score', 'liveliness_score', 'charm_score'
]
categorical_features = ['room_type', 'property_type', 'neighbourhood']

# Encode categoricals
encoders = {}
for col in categorical_features:
    if col in train_df.columns:
        le = LabelEncoder()
        train_df[col + '_encoded'] = le.fit_transform(train_df[col].astype(str))
        test_df[col + '_encoded'] = test_df[col].apply(
            lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
        )
        encoders[col] = le

encoded_cat_features = [col + '_encoded' for col in categorical_features if col in train_df.columns]

# Load OLS model (already trained)
ols_file = MODELS_DIR / 'ols_price_control.pkl'
with open(ols_file, 'rb') as f:
    ols_model = pickle.load(f)

# Apply OLS to get epsilon_price (if not already in data)
if 'epsilon_price' not in train_df.columns:
    stage1_features = ['neighbourhood_encoded', 'minimum_nights', 'host_listings_count']
    X_stage1_train = train_df[stage1_features].fillna(0)
    train_df['price_pred_stage1'] = ols_model.predict(X_stage1_train)
    train_df['epsilon_price'] = train_df['price_clean'] - train_df['price_pred_stage1']

    X_stage1_test = test_df[stage1_features].fillna(0)
    test_df['price_pred_stage1'] = ols_model.predict(X_stage1_test)
    test_df['epsilon_price'] = test_df['price_clean'] - test_df['price_pred_stage1']

# All features WITH vibe
all_features_with_vibe = (
    property_features + location_features + host_features +
    reputation_features + booking_features + derived_features +
    vibe_features + ['price_clean', 'epsilon_price']
)

# Filter to available features and add encoded categoricals
all_features_with_vibe_final = [f for f in all_features_with_vibe if f in train_df.columns]
all_features_with_vibe_final += [f for f in encoded_cat_features if f not in all_features_with_vibe_final]

# Prepare datasets
X_train = train_df[all_features_with_vibe_final].fillna(0)
y_train = train_df['occ_90']
X_test = test_df[all_features_with_vibe_final].fillna(0)
y_test = test_df['occ_90']

print(f"  ✓ Features: {len(all_features_with_vibe_final)}")
print(f"  ✓ Training samples: {len(X_train):,}")

# ============================================================================
# STEP 3: CREATE MONOTONIC CONSTRAINTS
# ============================================================================

print("\n[3/5] Creating monotonic constraints...")

# Find indices of price features
price_idx = all_features_with_vibe_final.index('price_clean')
price_per_person_idx = all_features_with_vibe_final.index('price_per_person') if 'price_per_person' in all_features_with_vibe_final else None

# Create monotonic constraint list
# 0 = no constraint, -1 = negative monotonic (occupancy decreases as feature increases), +1 = positive monotonic
monotone_constraints = [0] * len(all_features_with_vibe_final)
monotone_constraints[price_idx] = -1  # Price must have negative effect on occupancy

# Also constrain price_per_person if present (avoid double-counting)
if price_per_person_idx is not None:
    monotone_constraints[price_per_person_idx] = -1

print(f"  ✓ Monotonic constraints created:")
print(f"    - price_clean (index {price_idx}): negative (-1)")
if price_per_person_idx is not None:
    print(f"    - price_per_person (index {price_per_person_idx}): negative (-1)")
print(f"    - All other features: unconstrained (0)")

# ============================================================================
# STEP 4: TRAIN MODELS (WITH AND WITHOUT CONSTRAINTS)
# ============================================================================

print("\n[4/5] Training XGBoost models...")

# Cross-validation setup
kfold = KFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)

# Model WITHOUT constraints (baseline)
print("\n  Training XGBoost WITHOUT monotonic constraints (baseline)...")
xgb_baseline = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=RANDOM_SEED,
    tree_method='gpu_hist' if USE_GPU else 'hist',
    device=f'cuda:{GPU_ID}' if USE_GPU else 'cpu',
    n_jobs=N_JOBS if not USE_GPU else 1
)

# Cross-validation
cv_scores_baseline = cross_val_score(
    xgb_baseline, X_train, y_train,
    cv=kfold, scoring='neg_mean_absolute_error', n_jobs=N_JOBS
)
cv_mae_baseline = -cv_scores_baseline.mean()

# Train on full training set
xgb_baseline.fit(X_train, y_train)

# Evaluate
y_pred_baseline = xgb_baseline.predict(X_test)
test_mae_baseline = mean_absolute_error(y_test, y_pred_baseline)
test_rmse_baseline = np.sqrt(mean_squared_error(y_test, y_pred_baseline))
test_r2_baseline = r2_score(y_test, y_pred_baseline)

print(f"    CV MAE:    {cv_mae_baseline:.4f}")
print(f"    Test MAE:  {test_mae_baseline:.4f}")
print(f"    Test RMSE: {test_rmse_baseline:.4f}")
print(f"    Test R²:   {test_r2_baseline:.4f}")

# Model WITH constraints
print("\n  Training XGBoost WITH monotonic constraints...")
xgb_monotonic = xgb.XGBRegressor(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=RANDOM_SEED,
    tree_method='gpu_hist' if USE_GPU else 'hist',
    device=f'cuda:{GPU_ID}' if USE_GPU else 'cpu',
    monotone_constraints=tuple(monotone_constraints),  # ⭐ KEY CHANGE
    n_jobs=N_JOBS if not USE_GPU else 1
)

# Cross-validation
cv_scores_monotonic = cross_val_score(
    xgb_monotonic, X_train, y_train,
    cv=kfold, scoring='neg_mean_absolute_error', n_jobs=N_JOBS
)
cv_mae_monotonic = -cv_scores_monotonic.mean()

# Train on full training set
xgb_monotonic.fit(X_train, y_train)

# Evaluate
y_pred_monotonic = xgb_monotonic.predict(X_test)
test_mae_monotonic = mean_absolute_error(y_test, y_pred_monotonic)
test_rmse_monotonic = np.sqrt(mean_squared_error(y_test, y_pred_monotonic))
test_r2_monotonic = r2_score(y_test, y_pred_monotonic)

print(f"    CV MAE:    {cv_mae_monotonic:.4f}")
print(f"    Test MAE:  {test_mae_monotonic:.4f}")
print(f"    Test RMSE: {test_rmse_monotonic:.4f}")
print(f"    Test R²:   {test_r2_monotonic:.4f}")

# ============================================================================
# STEP 5: COMPARE MODELS
# ============================================================================

print("\n[5/5] Comparing models...")

# Performance comparison
mae_change = ((test_mae_monotonic - test_mae_baseline) / test_mae_baseline) * 100
r2_change = ((test_r2_monotonic - test_r2_baseline) / test_r2_baseline) * 100

print(f"\n  Performance Impact:")
print(f"    MAE change:  {mae_change:+.2f}%")
print(f"    R² change:   {r2_change:+.2f}%")

if abs(mae_change) < 5:
    print(f"    ✓ Performance impact is minimal (<5%)")
else:
    print(f"    ⚠️  Performance impact is {abs(mae_change):.1f}%")

# Test monotonicity on a sample property
print(f"\n  Monotonicity Test (Sample Property):")

# Create test property
test_property = {
    'accommodates': 2,
    'bedrooms': 1,
    'bathrooms_final': 1,
    'beds': 1,
    'amenities_count': 20,
    'latitude': train_df['latitude'].median(),
    'longitude': train_df['longitude'].median(),
    'host_listings_count': 1,
    'is_superhost': 0,
    'host_identity_verified': 1,
    'number_of_reviews': 50,
    'reviews_per_month': 2,
    'review_scores_rating': 4.8,
    'review_scores_cleanliness': 4.8,
    'review_scores_location': 4.7,
    'review_scores_value': 4.6,
    'instant_bookable': 1,
    'minimum_nights': 2,
    'listing_age_days': 365,
    'has_reviews': 1,
    'vibe_score': train_df['vibe_score'].median(),
    'sentiment_mean': train_df['sentiment_mean'].median(),
    'walkability_score': train_df['walkability_score'].median(),
    'safety_score': train_df['safety_score'].median(),
    'nightlife_score': train_df['nightlife_score'].median(),
    'family_friendly_score': train_df['family_friendly_score'].median(),
    'local_authentic_score': train_df['local_authentic_score'].median(),
    'convenience_score': train_df['convenience_score'].median(),
    'food_scene_score': train_df['food_scene_score'].median(),
    'liveliness_score': train_df['liveliness_score'].median(),
    'charm_score': train_df['charm_score'].median()
}

# Encode categoricals
most_common_room = train_df['room_type'].mode()[0]
most_common_prop = train_df['property_type'].mode()[0]
most_common_neigh = train_df['neighbourhood'].mode()[0]

test_property['room_type_encoded'] = encoders['room_type'].transform([most_common_room])[0]
test_property['property_type_encoded'] = encoders['property_type'].transform([most_common_prop])[0]
test_property['neighbourhood_encoded'] = encoders['neighbourhood'].transform([most_common_neigh])[0]

# Test across price range
prices = np.linspace(50, 300, 50)

baseline_predictions = []
monotonic_predictions = []

for price in prices:
    features = test_property.copy()
    features['price_clean'] = price
    features['price_per_person'] = price / test_property['accommodates']

    # Epsilon price
    ols_features_list = ['neighbourhood_encoded', 'minimum_nights', 'host_listings_count']
    X_ols = pd.DataFrame([{f: features.get(f, 0) for f in ols_features_list}])
    price_pred = ols_model.predict(X_ols)[0]
    features['epsilon_price'] = price - price_pred

    # Build feature vector
    X = pd.DataFrame([{f: features.get(f, 0) for f in all_features_with_vibe_final}])

    # Predict with both models
    occ_baseline = np.clip(xgb_baseline.predict(X)[0], 0, 1)
    occ_monotonic = np.clip(xgb_monotonic.predict(X)[0], 0, 1)

    baseline_predictions.append(occ_baseline)
    monotonic_predictions.append(occ_monotonic)

# Analyze monotonicity
baseline_diff = np.diff(baseline_predictions)
monotonic_diff = np.diff(monotonic_predictions)

baseline_violations = (baseline_diff > 0.001).sum()
monotonic_violations = (monotonic_diff > 0.001).sum()

print(f"\n    Baseline Model:")
print(f"      Non-monotonic cases: {baseline_violations} / {len(baseline_diff)} ({100*baseline_violations/len(baseline_diff):.1f}%)")

print(f"\n    Monotonic Model:")
print(f"      Non-monotonic cases: {monotonic_violations} / {len(monotonic_diff)} ({100*monotonic_violations/len(monotonic_diff):.1f}%)")

if monotonic_violations == 0:
    print(f"      ✅ SUCCESS: Perfect monotonic behavior!")
elif monotonic_violations < baseline_violations / 2:
    print(f"      ✓ Significant improvement in monotonicity")
else:
    print(f"      ⚠️  Monotonicity improvement less than expected")

# Save new model
model_file = MODELS_DIR / 'xgboost_with_vibe_monotonic.pkl'
with open(model_file, 'wb') as f:
    pickle.dump(xgb_monotonic, f)
print(f"\n  ✓ Saved monotonic model: {model_file.name}")

# Save comparison results
results = {
    'baseline': {
        'cv_mae': float(cv_mae_baseline),
        'test_mae': float(test_mae_baseline),
        'test_rmse': float(test_rmse_baseline),
        'test_r2': float(test_r2_baseline),
        'monotonicity_violations': int(baseline_violations),
        'monotonicity_violation_pct': float(100*baseline_violations/len(baseline_diff))
    },
    'monotonic': {
        'cv_mae': float(cv_mae_monotonic),
        'test_mae': float(test_mae_monotonic),
        'test_rmse': float(test_rmse_monotonic),
        'test_r2': float(test_r2_monotonic),
        'monotonicity_violations': int(monotonic_violations),
        'monotonicity_violation_pct': float(100*monotonic_violations/len(monotonic_diff) if len(monotonic_diff) > 0 else 0)
    },
    'impact': {
        'mae_change_pct': float(mae_change),
        'r2_change_pct': float(r2_change)
    }
}

results_file = MODELS_DIR / 'monotonic_comparison.json'
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"  ✓ Saved comparison results: {results_file.name}")

# Create visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Occupancy curves
ax1 = axes[0]
ax1.plot(prices, baseline_predictions, 'o-', label='Baseline (no constraints)', alpha=0.7, markersize=3)
ax1.plot(prices, monotonic_predictions, 's-', label='Monotonic constraints', alpha=0.7, markersize=3)
ax1.set_xlabel('Nightly Price (£)')
ax1.set_ylabel('Predicted Occupancy')
ax1.set_title('Occupancy Predictions: Baseline vs Monotonic')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Plot 2: Change in occupancy
ax2 = axes[1]
ax2.plot(prices[1:], baseline_diff, 'o-', label='Baseline', alpha=0.7, markersize=3)
ax2.plot(prices[1:], monotonic_diff, 's-', label='Monotonic', alpha=0.7, markersize=3)
ax2.axhline(0, color='red', linestyle='--', linewidth=1, label='Zero line')
ax2.set_xlabel('Nightly Price (£)')
ax2.set_ylabel('Change in Occupancy (from previous price)')
ax2.set_title('Occupancy Changes as Price Increases')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
viz_file = VIZ_DIR / 'monotonic_constraint_comparison.png'
plt.savefig(viz_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"  ✓ Saved visualization: {viz_file.name}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("MONOTONIC CONSTRAINT RETRAINING COMPLETE ✅")
print("=" * 80)
print(f"Baseline Model (no constraints):")
print(f"  Test MAE:  {test_mae_baseline:.4f}")
print(f"  Test R²:   {test_r2_baseline:.4f}")
print(f"  Monotonicity violations: {baseline_violations} ({100*baseline_violations/len(baseline_diff):.1f}%)")
print()
print(f"Monotonic Model (with constraints):")
print(f"  Test MAE:  {test_mae_monotonic:.4f} ({mae_change:+.2f}%)")
print(f"  Test R²:   {test_r2_monotonic:.4f} ({r2_change:+.2f}%)")
print(f"  Monotonicity violations: {monotonic_violations} ({100*monotonic_violations/len(monotonic_diff) if len(monotonic_diff) > 0 else 0:.1f}%)")
print()
if abs(mae_change) < 5 and monotonic_violations < baseline_violations / 2:
    print("✅ SUCCESS: Monotonicity improved with minimal performance cost!")
    print("   Recommended: Replace xgboost_with_vibe.pkl with xgboost_with_vibe_monotonic.pkl")
else:
    print("⚠️  Review results before deploying monotonic model")
print("=" * 80)
