#!/usr/bin/env python3
"""
Predictive Model with Control Function
Two-stage approach to predict occupancy while controlling for price endogeneity

Stage 1: OLS regression to control for price endogeneity
Stage 2: Multiple ML models (XGBoost, LightGBM, RandomForest) for occupancy prediction

Based on METHODOLOGY.md decisions
Author: Team (Nicholas, Sahil, Heath)
Date: 2025-11-06
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import lightgbm as lgb
import pickle
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

CITY = 'nyc'
RANDOM_SEED = 42
N_FOLDS = 5  # Cross-validation folds
N_JOBS = -1  # Use all CPU cores

# GPU Configuration (See HARDWARE.md for setup)
USE_GPU = True  # Set to False for CPU-only
GPU_ID = 1  # RTX 5090 #1 (GPU 0 is RTX 5070 for display)

# Paths
DATA_DIR = Path(f'data/{CITY}')
PROCESSED_DIR = DATA_DIR / 'processed'
MODELS_DIR = DATA_DIR / 'models'
OUTPUT_DIR = DATA_DIR / 'outputs'
VIZ_DIR = OUTPUT_DIR / 'visualizations'
REPORTS_DIR = OUTPUT_DIR / 'reports'

# Create directories
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Detect GPU availability
try:
    import subprocess
    gpu_check = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True)
    gpu_available = gpu_check.returncode == 0 and USE_GPU
    if gpu_available:
        print(f"✓ GPU Detected - Will use GPU {GPU_ID} for acceleration")
        print(f"  Available GPUs:\n{gpu_check.stdout}")
    else:
        print("ℹ Using CPU-only mode")
        USE_GPU = False
except:
    print("ℹ GPU not available, using CPU-only mode")
    USE_GPU = False
    gpu_available = False

print("=" * 80)
print(f"PREDICTIVE MODEL WITH CONTROL FUNCTION - {CITY.upper()}")
print("=" * 80)
print(f"Random Seed: {RANDOM_SEED}")
print(f"Cross-validation folds: {N_FOLDS}")
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

# Filter to listings with valid price and target
train_df = train_df[train_df['price_clean'].notna() & train_df['occ_90'].notna()].copy()
test_df = test_df[test_df['price_clean'].notna() & test_df['occ_90'].notna()].copy()

print(f"  ✓ After filtering: Train={len(train_df):,}, Test={len(test_df):,}")

# ============================================================================
# STEP 2: DEFINE FEATURE SETS
# ============================================================================

print("\n[2/8] Defining feature sets...")

# Features for Stage 1 (price endogeneity control)
# Simple features that predict price but not directly related to quality/demand
stage1_features = [
    'neighbourhood',  # Location-based pricing
    'minimum_nights',  # Availability constraints
    'host_listings_count'  # Host scale
]

# Features for Stage 2 (occupancy prediction)
# Property features
property_features = [
    'accommodates',
    'bedrooms',
    'bathrooms_final',
    'beds',
    'amenities_count'
]

# Location features
location_features = [
    'latitude',
    'longitude'
]

# Host features
host_features = [
    'host_listings_count',
    'is_superhost',
    'host_identity_verified'
]

# Reputation features
reputation_features = [
    'number_of_reviews',
    'reviews_per_month',
    'review_scores_rating',
    'review_scores_cleanliness',
    'review_scores_location',
    'review_scores_value'
]

# Booking features
booking_features = [
    'instant_bookable',
    'minimum_nights'
]

# Derived features
derived_features = [
    'listing_age_days',
    'has_reviews',
    'price_per_person'
]

# Vibe features (KEY INNOVATION)
vibe_features = [
    'vibe_score',
    'sentiment_mean',
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

# Categorical features (need encoding)
categorical_features = [
    'room_type',
    'property_type',
    'neighbourhood'
]

# All features WITH vibe
all_features_with_vibe = (
    property_features + location_features + host_features +
    reputation_features + booking_features + derived_features +
    vibe_features + ['price_clean', 'epsilon_price']  # Include price and control
)

# All features WITHOUT vibe (for baseline)
all_features_no_vibe = (
    property_features + location_features + host_features +
    reputation_features + booking_features + derived_features +
    ['price_clean', 'epsilon_price']  # Include price and control
)

print(f"  ✓ Property features: {len(property_features)}")
print(f"  ✓ Vibe features: {len(vibe_features)}")
print(f"  ✓ Total features (with vibe): {len(all_features_with_vibe)}")
print(f"  ✓ Total features (no vibe): {len(all_features_no_vibe)}")

# ============================================================================
# STEP 3: ENCODE CATEGORICAL FEATURES
# ============================================================================

print("\n[3/8] Encoding categorical features...")

# Label encode categorical features
encoders = {}
for col in categorical_features:
    if col in train_df.columns:
        le = LabelEncoder()
        train_df[col + '_encoded'] = le.fit_transform(train_df[col].astype(str))
        test_df[col + '_encoded'] = test_df[col].apply(
            lambda x: le.transform([str(x)])[0] if str(x) in le.classes_ else -1
        )
        encoders[col] = le
        print(f"  ✓ Encoded {col}: {len(le.classes_)} categories")

# Add encoded features to feature lists
encoded_cat_features = [col + '_encoded' for col in categorical_features if col in train_df.columns]

# ============================================================================
# STEP 4: STAGE 1 - CONTROL FUNCTION (Price Endogeneity)
# ============================================================================

print("\n[4/8] Stage 1: Training OLS for price endogeneity control...")

# Prepare Stage 1 features
stage1_encoded = ['neighbourhood_encoded', 'minimum_nights', 'host_listings_count']
stage1_available = [f for f in stage1_encoded if f in train_df.columns]

X_stage1_train = train_df[stage1_available].fillna(0)
y_stage1_train = train_df['price_clean']

# Train OLS
ols_model = LinearRegression()
ols_model.fit(X_stage1_train, y_stage1_train)

# Predict and compute residuals (epsilon_price)
train_df['price_pred_stage1'] = ols_model.predict(X_stage1_train)
train_df['epsilon_price'] = train_df['price_clean'] - train_df['price_pred_stage1']

# Apply to test set
X_stage1_test = test_df[stage1_available].fillna(0)
test_df['price_pred_stage1'] = ols_model.predict(X_stage1_test)
test_df['epsilon_price'] = test_df['price_clean'] - test_df['price_pred_stage1']

print(f"  ✓ OLS R²: {ols_model.score(X_stage1_train, y_stage1_train):.4f}")
print(f"  ✓ Epsilon_price computed (mean={train_df['epsilon_price'].mean():.2f}, std={train_df['epsilon_price'].std():.2f})")

# Save OLS model
ols_file = MODELS_DIR / 'ols_price_control.pkl'
with open(ols_file, 'wb') as f:
    pickle.dump(ols_model, f)
print(f"  ✓ Saved {ols_file.name}")

# ============================================================================
# STEP 5: STAGE 2 - PREPARE FEATURES FOR OCCUPANCY PREDICTION
# ============================================================================

print("\n[5/8] Stage 2: Preparing features for occupancy prediction...")

# Update feature lists to include encoded categoricals
all_features_with_vibe_final = [f for f in all_features_with_vibe if f in train_df.columns]
all_features_with_vibe_final += [f for f in encoded_cat_features if f not in all_features_with_vibe_final]

all_features_no_vibe_final = [f for f in all_features_no_vibe if f in train_df.columns]
all_features_no_vibe_final += [f for f in encoded_cat_features if f not in all_features_no_vibe_final]

# Prepare datasets WITH vibe
X_train_with_vibe = train_df[all_features_with_vibe_final].fillna(0)
y_train = train_df['occ_90']
X_test_with_vibe = test_df[all_features_with_vibe_final].fillna(0)
y_test = test_df['occ_90']

# Prepare datasets WITHOUT vibe (baseline)
X_train_no_vibe = train_df[all_features_no_vibe_final].fillna(0)
X_test_no_vibe = test_df[all_features_no_vibe_final].fillna(0)

print(f"  ✓ Training set: {X_train_with_vibe.shape}")
print(f"  ✓ Test set: {X_test_with_vibe.shape}")
print(f"  ✓ With vibe features: {len(all_features_with_vibe_final)} features")
print(f"  ✓ Without vibe features: {len(all_features_no_vibe_final)} features")

# ============================================================================
# STEP 6: TRAIN MULTIPLE MODELS WITH CROSS-VALIDATION
# ============================================================================

print("\n[6/8] Training multiple models with cross-validation...")

# Define models to compare
# GPU-accelerated if available (see HARDWARE.md)
models = {
    'XGBoost': xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_SEED,
        tree_method='gpu_hist' if USE_GPU else 'hist',  # GPU acceleration
        device=f'cuda:{GPU_ID}' if USE_GPU else 'cpu',  # XGBoost 3.1+ API
        n_jobs=N_JOBS if not USE_GPU else 1  # GPU handles parallelism
    ),
    'LightGBM': lgb.LGBMRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_SEED,
        device='cpu',  # CPU-only (32-core Threadripper is very fast)
        n_jobs=N_JOBS,
        verbose=-1
    ),
    'RandomForest': RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=4,
        random_state=RANDOM_SEED,
        n_jobs=N_JOBS  # RandomForest uses CPU (GPU version requires cuML)
    )
}

# Cross-validation setup
kfold = KFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_SEED)

# Store results
results = []

print("\n  Training models WITH vibe features:")
for name, model in models.items():
    print(f"    • {name}...", end=' ', flush=True)

    # Cross-validation
    cv_scores = cross_val_score(
        model, X_train_with_vibe, y_train,
        cv=kfold, scoring='neg_mean_absolute_error', n_jobs=N_JOBS
    )
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()

    # Train on full training set
    model.fit(X_train_with_vibe, y_train)

    # Evaluate on test set
    y_pred_test = model.predict(X_test_with_vibe)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    test_r2 = r2_score(y_test, y_pred_test)

    results.append({
        'model': name,
        'vibe_features': 'yes',
        'cv_mae': cv_mae,
        'cv_std': cv_std,
        'test_mae': test_mae,
        'test_rmse': test_rmse,
        'test_r2': test_r2
    })

    print(f"CV MAE={cv_mae:.4f}±{cv_std:.4f}, Test MAE={test_mae:.4f}")

    # Save model
    model_file = MODELS_DIR / f'{name.lower()}_with_vibe.pkl'
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)

print("\n  Training baseline models WITHOUT vibe features:")
for name, model_class in [('XGBoost', xgb.XGBRegressor), ('LightGBM', lgb.LGBMRegressor), ('RandomForest', RandomForestRegressor)]:
    print(f"    • {name} (baseline)...", end=' ', flush=True)

    # Recreate model with same hyperparameters (GPU-accelerated if available)
    if name == 'XGBoost':
        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_SEED,
            tree_method='gpu_hist' if USE_GPU else 'hist',
            device=f'cuda:{GPU_ID}' if USE_GPU else 'cpu',  # XGBoost 3.1+ API
            n_jobs=N_JOBS if not USE_GPU else 1
        )
    elif name == 'LightGBM':
        model = lgb.LGBMRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, random_state=RANDOM_SEED,
            device='cpu',  # CPU-only (32-core Threadripper is very fast)
            n_jobs=N_JOBS,
            verbose=-1
        )
    else:
        model = RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_split=10,
            min_samples_leaf=4, random_state=RANDOM_SEED, n_jobs=N_JOBS
        )

    # Cross-validation
    cv_scores = cross_val_score(
        model, X_train_no_vibe, y_train,
        cv=kfold, scoring='neg_mean_absolute_error', n_jobs=N_JOBS
    )
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()

    # Train on full training set
    model.fit(X_train_no_vibe, y_train)

    # Evaluate on test set
    y_pred_test = model.predict(X_test_no_vibe)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    test_r2 = r2_score(y_test, y_pred_test)

    results.append({
        'model': name,
        'vibe_features': 'no',
        'cv_mae': cv_mae,
        'cv_std': cv_std,
        'test_mae': test_mae,
        'test_rmse': test_rmse,
        'test_r2': test_r2
    })

    print(f"CV MAE={cv_mae:.4f}±{cv_std:.4f}, Test MAE={test_mae:.4f}")

    # Save baseline model
    model_file = MODELS_DIR / f'{name.lower()}_no_vibe.pkl'
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)

# Create results dataframe
results_df = pd.DataFrame(results)
print("\n  ✓ All models trained and saved")

# ============================================================================
# STEP 7: SELECT BEST MODEL AND COMPUTE SHAP
# ============================================================================

print("\n[7/8] Selecting best model and computing SHAP values...")

# Select best model (lowest test MAE with vibe)
best_idx = results_df[results_df['vibe_features'] == 'yes']['test_mae'].idxmin()
best_model_name = results_df.loc[best_idx, 'model']
best_model_file = MODELS_DIR / f'{best_model_name.lower()}_with_vibe.pkl'

print(f"  ✓ Best model: {best_model_name} (Test MAE={results_df.loc[best_idx, 'test_mae']:.4f})")

# Load best model
with open(best_model_file, 'rb') as f:
    best_model = pickle.load(f)

# Compute feature importance
try:
    if hasattr(best_model, 'feature_importances_'):
        importance = best_model.feature_importances_
        feature_names = X_train_with_vibe.columns

        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)

        # Check vibe feature importance
        vibe_importance = importance_df[importance_df['feature'].str.contains('vibe|walkability|safety|nightlife|family|local|convenience|food|liveliness|charm|sentiment', case=False, na=False)]
        vibe_rank_percentile = (vibe_importance['importance'].sum() / importance_df['importance'].sum()) * 100

        print(f"  ✓ Vibe features contribution: {vibe_rank_percentile:.1f}% of total importance")

        # Check if vibe in top 50%
        top_50_pct_threshold = importance_df['importance'].sum() * 0.5
        cumsum_importance = importance_df['importance'].cumsum()
        vibe_in_top_50 = any(cumsum_importance[importance_df['feature'].isin(vibe_importance['feature'])] <= top_50_pct_threshold)

        if vibe_rank_percentile >= 5:  # At least 5% contribution
            print(f"  ✅ SUCCESS: Vibe features contribute {vibe_rank_percentile:.1f}% (threshold: ≥5%)")
        else:
            print(f"  ⚠️  WARNING: Vibe features contribute only {vibe_rank_percentile:.1f}%")

        # Save feature importance
        importance_file = REPORTS_DIR / 'feature_importance.csv'
        importance_df.to_csv(importance_file, index=False)
        print(f"  ✓ Saved {importance_file.name}")
except Exception as e:
    print(f"  ⚠️  Could not compute feature importance: {e}")
    importance_df = None

# ============================================================================
# STEP 8: SAVE RESULTS AND VISUALIZATIONS
# ============================================================================

print("\n[8/8] Saving results and creating visualizations...")

# Save model comparison
results_file = REPORTS_DIR / 'model_comparison.csv'
results_df.to_csv(results_file, index=False)
print(f"  ✓ Saved {results_file.name}")

# Save metrics as JSON
metrics = {
    'best_model': best_model_name,
    'best_test_mae': float(results_df.loc[best_idx, 'test_mae']),
    'best_test_rmse': float(results_df.loc[best_idx, 'test_rmse']),
    'best_test_r2': float(results_df.loc[best_idx, 'test_r2']),
    'vibe_importance_pct': float(vibe_rank_percentile) if importance_df is not None else None
}

# Calculate improvement from baseline
baseline_row = results_df[(results_df['model'] == best_model_name) & (results_df['vibe_features'] == 'no')]
if len(baseline_row) > 0:
    baseline_mae = baseline_row['test_mae'].values[0]
    improvement = ((baseline_mae - metrics['best_test_mae']) / baseline_mae) * 100
    metrics['improvement_vs_baseline_pct'] = float(improvement)
    print(f"  ✓ Improvement vs baseline: {improvement:.2f}%")

metrics_file = MODELS_DIR / 'model_metrics.json'
with open(metrics_file, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"  ✓ Saved {metrics_file.name}")

# Create visualizations
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle(f'Predictive Model Evaluation - {CITY.capitalize()}', fontsize=16, fontweight='bold')

# Plot 1: Model comparison (MAE)
ax1 = axes[0, 0]
pivot_mae = results_df.pivot(index='model', columns='vibe_features', values='test_mae')
pivot_mae.plot(kind='bar', ax=ax1, color=['lightcoral', 'lightgreen'], edgecolor='black')
ax1.set_ylabel('Test MAE')
ax1.set_title('Model Comparison: Test MAE')
ax1.legend(['Without Vibe', 'With Vibe'])
ax1.grid(True, alpha=0.3, axis='y')
plt.sca(ax1)
plt.xticks(rotation=0)

# Plot 2: Model comparison (R²)
ax2 = axes[0, 1]
pivot_r2 = results_df.pivot(index='model', columns='vibe_features', values='test_r2')
pivot_r2.plot(kind='bar', ax=ax2, color=['lightcoral', 'lightgreen'], edgecolor='black')
ax2.set_ylabel('Test R²')
ax2.set_title('Model Comparison: Test R²')
ax2.legend(['Without Vibe', 'With Vibe'])
ax2.grid(True, alpha=0.3, axis='y')
plt.sca(ax2)
plt.xticks(rotation=0)

# Plot 3: Feature importance (top 20)
ax3 = axes[0, 2]
if importance_df is not None:
    top_20 = importance_df.head(20)
    colors = ['green' if any(kw in feat.lower() for kw in ['vibe', 'walkability', 'safety', 'nightlife', 'family', 'local', 'convenience', 'food', 'liveliness', 'charm', 'sentiment']) else 'steelblue' for feat in top_20['feature']]
    ax3.barh(range(len(top_20)), top_20['importance'], color=colors, edgecolor='black')
    ax3.set_yticks(range(len(top_20)))
    ax3.set_yticklabels(top_20['feature'], fontsize=8)
    ax3.set_xlabel('Importance')
    ax3.set_title(f'Top 20 Features - {best_model_name}\n(Green = Vibe Features)')
    ax3.invert_yaxis()
    ax3.grid(True, alpha=0.3, axis='x')

# Plot 4: Predicted vs Actual (test set)
ax4 = axes[1, 0]
y_pred_best = best_model.predict(X_test_with_vibe)
ax4.scatter(y_test, y_pred_best, alpha=0.3, s=10)
ax4.plot([0, 1], [0, 1], 'r--', linewidth=2)
ax4.set_xlabel('Actual Occupancy (occ_90)')
ax4.set_ylabel('Predicted Occupancy')
ax4.set_title(f'Predicted vs Actual - {best_model_name}\nTest R²={metrics["best_test_r2"]:.4f}')
ax4.grid(True, alpha=0.3)
ax4.set_xlim(0, 1)
ax4.set_ylim(0, 1)

# Plot 5: Residuals distribution
ax5 = axes[1, 1]
residuals = y_test - y_pred_best
ax5.hist(residuals, bins=50, edgecolor='black', alpha=0.7, color='orange')
ax5.axvline(0, color='red', linestyle='--', linewidth=2)
ax5.set_xlabel('Residual (Actual - Predicted)')
ax5.set_ylabel('Frequency')
ax5.set_title(f'Residuals Distribution\nMean={residuals.mean():.4f}, Std={residuals.std():.4f}')
ax5.grid(True, alpha=0.3)

# Plot 6: MAE improvement
ax6 = axes[1, 2]
if 'improvement_vs_baseline_pct' in metrics:
    models_with_improvement = []
    improvements = []
    for model_name in results_df['model'].unique():
        with_vibe = results_df[(results_df['model'] == model_name) & (results_df['vibe_features'] == 'yes')]['test_mae'].values[0]
        without_vibe = results_df[(results_df['model'] == model_name) & (results_df['vibe_features'] == 'no')]['test_mae'].values[0]
        improvement = ((without_vibe - with_vibe) / without_vibe) * 100
        models_with_improvement.append(model_name)
        improvements.append(improvement)

    colors_imp = ['green' if x > 0 else 'red' for x in improvements]
    ax6.bar(range(len(models_with_improvement)), improvements, color=colors_imp, edgecolor='black')
    ax6.set_xticks(range(len(models_with_improvement)))
    ax6.set_xticklabels(models_with_improvement, rotation=0)
    ax6.set_ylabel('% Improvement in MAE')
    ax6.set_title('MAE Improvement with Vibe Features')
    ax6.axhline(0, color='black', linewidth=1)
    ax6.axhline(15, color='red', linestyle='--', linewidth=1, label='Target: 15%')
    ax6.grid(True, alpha=0.3, axis='y')
    ax6.legend()

plt.tight_layout()
viz_file = VIZ_DIR / '08_predictive_model_evaluation.png'
plt.savefig(viz_file, dpi=300, bbox_inches='tight')
plt.close()

print(f"  ✓ Saved {viz_file.name}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("PREDICTIVE MODEL WITH CONTROL FUNCTION COMPLETE ✅")
print("=" * 80)
print(f"Best Model:               {best_model_name}")
print(f"Test MAE:                 {metrics['best_test_mae']:.4f}")
print(f"Test RMSE:                {metrics['best_test_rmse']:.4f}")
print(f"Test R²:                  {metrics['best_test_r2']:.4f}")
if 'improvement_vs_baseline_pct' in metrics:
    print(f"Improvement vs Baseline:  {metrics['improvement_vs_baseline_pct']:.2f}%")
    if metrics['improvement_vs_baseline_pct'] >= 15:
        print(f"  ✅ SUCCESS: Exceeds 15% improvement threshold!")
    else:
        print(f"  ⚠️  Below 15% target improvement")
if 'vibe_importance_pct' in metrics and metrics['vibe_importance_pct']:
    print(f"Vibe Feature Importance:  {metrics['vibe_importance_pct']:.1f}%")
print("=" * 80)
print(f"Outputs saved to: {MODELS_DIR}")
print(f"  • {best_model_name.lower()}_with_vibe.pkl (best model)")
print(f"  • model_comparison.csv")
print(f"  • model_metrics.json")
print(f"  • feature_importance.csv")
print(f"  • 08_predictive_model_evaluation.png")
print("=" * 80)
print("Next step: Task 5 - Revenue Optimization Engine")
print("=" * 80)
