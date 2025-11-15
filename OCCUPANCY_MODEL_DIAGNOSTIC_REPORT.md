# Occupancy Prediction Model - Diagnostic Report

**Date:** 2025-11-14
**Issue:** Low predicted occupancy & non-monotonic price-occupancy relationship
**Status:** Root cause identified, solutions proposed

---

## Executive Summary

The XGBoost occupancy prediction model exhibits two concerning behaviors:
1. **Predicted occupancy appears "low"** (30-50% range)
2. **Non-monotonic relationship**: Occupancy sometimes increases as price increases (10.2% of price changes)

**CRITICAL FINDING:** The "low" predictions are **actually realistic** - training data shows mean occupancy of only 41.1% and median of 34.4%. However, the non-monotonic behavior indicates the model is overfitting to noise in the training data rather than learning the true price elasticity.

---

## Part 1: Training Data Analysis

### 1.1 Overall Occupancy Statistics (London)

| Metric | Value |
|--------|-------|
| **Mean occupancy** | 41.06% |
| **Median occupancy** | 34.44% |
| **Standard deviation** | 34.54% |
| **10th percentile** | 1.11% |
| **25th percentile** | 7.78% |
| **75th percentile** | 70.00% |
| **90th percentile** | 98.89% |
| **High-demand listings (≥75%)** | 11,216 / 49,621 (22.6%) |

**Insight:** Only 22.6% of listings achieve "high demand" status (≥75% occupancy). The market is competitive and most listings struggle with occupancy.

### 1.2 Price vs Occupancy Relationship in Training Data

| Price Range | Mean Occupancy | Median Occupancy | Listing Count |
|-------------|---------------|------------------|---------------|
| <£50 | 40.5% | 31.1% | 5,380 |
| £50-100 | 40.0% | 32.2% | 12,562 |
| **£100-150** | **44.9%** | **40.0%** | 9,992 |
| £150-200 | 43.5% | 37.8% | 7,227 |
| £200-300 | 40.7% | 34.4% | 7,458 |
| £300-500 | 37.5% | 28.9% | 4,556 |
| £500+ | 33.4% | 16.7% | 2,422 |

**Correlation (price vs occupancy):** -0.0104 (essentially ZERO)

**KEY FINDING:** The training data itself shows **non-monotonic patterns**:
- Occupancy **increases** from £50-100 (40.0%) to £100-150 (44.9%)
- Then generally decreases for higher prices
- This suggests the £100-150 range is a "sweet spot" in the London market

**Why This Happens:**
- Very cheap listings (<£50) may be perceived as low quality → lower occupancy
- Mid-range listings (£100-150) hit the sweet spot for value → higher occupancy
- Expensive listings (£300+) have smaller target market → lower occupancy

### 1.3 Vibe Score Impact

| Metric | Value |
|--------|-------|
| **Correlation (vibe vs occupancy)** | 0.1141 |
| **High vibe areas (top 25%)** | 43.7% occupancy, £224 avg price |
| **Low vibe areas (bottom 25%)** | 35.7% occupancy, £153 avg price |

Vibe scores **do** correlate with occupancy, proving their business value.

---

## Part 2: Model Behavior Analysis

### 2.1 XGBoost Prediction Test

**Test Property:**
- Entire home/apt (Entire rental unit) in Westminster
- 2 guests, 1 bedroom, 1 bathroom
- Vibe score: 50.80 (median)
- 50 reviews, 4.8 rating

**Price Sweep Results (£50 to £300):**

| Price | Predicted Occupancy | Monthly Revenue |
|-------|---------------------|-----------------|
| £50 | 75.56% | £1,133 |
| £100 | 68.62% | £2,059 |
| £150 | 55.88% | £2,514 |
| £200 | 44.20% | £2,652 |
| £250 | 38.29% | £2,872 |
| **£295** | **44.54%** | **£3,941** (optimal) |
| £300 | 43.28% | £3,895 |

### 2.2 Monotonicity Analysis

| Behavior | Frequency | Percentage |
|----------|-----------|------------|
| **Occupancy decreases** | 31 / 49 | 63.3% |
| **Occupancy increases** | 5 / 49 | **10.2%** ⚠️ |
| **Occupancy stable** | 13 / 49 | 26.5% |

**Examples of NON-MONOTONIC behavior (occupancy increases as price goes up):**
- £60 (74.22%) → £65 (74.42%) +0.20 ppts
- £91 (63.77%) → £96 (64.90%) +1.13 ppts
- £127 (57.59%) → £132 (58.15%) +0.56 ppts
- £259 (38.17%) → £264 (38.53%) +0.36 ppts
- **£285 (38.42%) → £290 (44.80%) +6.38 ppts** 🚨

The last example is particularly problematic - a £5 price increase causes a 6.4 percentage point JUMP in occupancy, which makes no business sense.

---

## Part 3: Root Cause Analysis

### 3.1 Why is occupancy "low"?

**Answer: It's not low - it's realistic.**

The model is correctly learning from the training data where:
- Mean occupancy is only 41.1%
- Median occupancy is only 34.4%
- Most listings (77.4%) have <75% occupancy

This reflects the competitive nature of the London Airbnb market. Predictions in the 30-50% range are **accurate** for many properties.

### 3.2 Why is the model non-monotonic?

**Answer: The model is overfitting to noise in the training data.**

**The Problem:**
1. Training data shows complex, non-monotonic patterns (£100-150 has higher occupancy than both cheaper and more expensive ranges)
2. XGBoost is very flexible and can learn these patterns
3. But these patterns include both signal (real sweet spots) and noise (random variations)
4. The model doesn't know price should have a monotonic effect on demand

**Economic Intuition:**
In reality, higher prices should cause lower demand (law of demand). But the training data violates this because:
- **Omitted variable bias**: Expensive listings may be in better locations, have better amenities, etc. The model sees "high price → high occupancy" for these, not realizing it's the location/amenities driving occupancy
- **Selection bias**: Hosts don't randomly assign prices. They charge based on quality. So price correlates with quality.
- **Sample size issues**: Fewer very cheap/expensive listings → noisier estimates

**What the control function was supposed to fix:**
The epsilon_price (price residual from Stage 1 OLS) is supposed to capture "unexpected" price variation after controlling for location and listing density. But:
1. It only controls for neighbourhood, minimum_nights, and host_listings_count
2. It doesn't control for all quality variables (amenities, reviews, property type, etc.)
3. So endogeneity remains

---

## Part 4: Proposed Solutions

### Solution 1: Add Monotonic Constraints ⭐ RECOMMENDED

**What:** Force XGBoost to learn that occupancy must decrease (or stay flat) as price increases.

**How:** XGBoost supports monotonic constraints via the `monotone_constraints` parameter.

```python
# In 04_predictive_model_control_function.py
# Find which column index is 'price_clean'
price_idx = all_features_with_vibe_final.index('price_clean')

# Create monotonic constraint list
# 0 = no constraint, -1 = decreasing, +1 = increasing
monotone_constraints = [0] * len(all_features_with_vibe_final)
monotone_constraints[price_idx] = -1  # Price must have negative effect on occupancy

models = {
    'XGBoost': xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_SEED,
        tree_method='gpu_hist' if USE_GPU else 'hist',
        device=f'cuda:{GPU_ID}' if USE_GPU else 'cpu',
        monotone_constraints=tuple(monotone_constraints),  # ⭐ ADD THIS
        n_jobs=N_JOBS if not USE_GPU else 1
    )
}
```

**Pros:**
- Forces economically sensible behavior
- Prevents wild jumps in predicted occupancy
- Improves interpretability and trust
- Easy to implement (one parameter)

**Cons:**
- Might slightly reduce model accuracy (R² might drop a bit)
- Loses ability to capture legitimate "sweet spot" effects
- Need to ensure price_per_person also has monotonic constraint (or remove it from features to avoid double-counting)

**Expected Impact:**
- Predictions will be smoother
- Revenue curves will be cleaner
- Optimal prices will be more stable

---

### Solution 2: Add Price Elasticity Features

**What:** Help the model learn the price-occupancy relationship more explicitly.

**How:** Create new features that capture price elasticity:

```python
# In feature engineering (scripts/03_feature_engineering.py)

# Price relative to neighborhood median
neighborhood_medians = df.groupby('neighbourhood')['price_clean'].transform('median')
df['price_vs_neighborhood'] = df['price_clean'] / neighborhood_medians

# Price relative to similar properties (same room_type + bedrooms)
similar_medians = df.groupby(['room_type', 'bedrooms'])['price_clean'].transform('median')
df['price_vs_similar'] = df['price_clean'] / similar_medians

# Log price (helps with non-linear effects)
df['log_price'] = np.log(df['price_clean'] + 1)

# Price bucket indicators (cheap/medium/expensive)
df['is_budget'] = (df['price_clean'] < df['price_clean'].quantile(0.25)).astype(int)
df['is_luxury'] = (df['price_clean'] > df['price_clean'].quantile(0.75)).astype(int)
```

**Pros:**
- Gives model more context about pricing
- Helps distinguish "overpriced" vs "premium quality"
- Captures neighborhood-specific pricing dynamics

**Cons:**
- Adds complexity
- Requires retraining from scratch
- May not fully solve monotonicity issue

---

### Solution 3: Improve Control Function (More Instruments)

**What:** Better control for price endogeneity by including more predictors in Stage 1.

**Current Stage 1 features:**
- neighbourhood
- minimum_nights
- host_listings_count

**Enhanced Stage 1 features:**
```python
stage1_features = [
    'neighbourhood_encoded',
    'minimum_nights',
    'host_listings_count',
    'property_type_encoded',  # Add: different property types command different prices
    'room_type_encoded',      # Add: entire home vs private room vs shared
    'bedrooms',               # Add: size affects price
    'bathrooms_final',        # Add: bathrooms affect price
    'amenities_count',        # Add: more amenities = higher price
    'is_superhost',           # Add: superhosts can charge more
    'listing_age_days'        # Add: established listings may price differently
]
```

**Pros:**
- Better isolates true price effect from quality/location
- More theoretically sound
- Improves causal interpretation

**Cons:**
- Risk of over-controlling (using variables that also affect demand directly)
- Requires careful economic reasoning
- Requires retraining

---

### Solution 4: Use Different Target Variable

**What:** Train on `occ_30` instead of `occ_90`.

**Rationale:**
- `occ_90` looks 90 days into the future → more uncertain, more noise
- `occ_30` is nearer-term → more stable, less noise
- Hosts care about next month's bookings most

**Trade-off:**
- `occ_30` might be less reflective of steady-state occupancy
- Some seasonal effects might be missed

---

### Solution 5: Ensemble with Monotonic Baseline

**What:** Combine XGBoost predictions with a simple monotonic baseline.

**How:**
```python
# Simple demand curve model
def simple_demand_curve(price, base_occupancy=0.5, elasticity=-0.3):
    """Simple price elasticity model"""
    price_ratio = price / 150  # Normalize around £150
    return base_occupancy * (price_ratio ** elasticity)

# Blend predictions
xgb_pred = xgb_model.predict(X)
simple_pred = simple_demand_curve(price, base_occupancy=0.5, elasticity=-0.3)

# Weighted average (70% XGBoost, 30% simple)
final_pred = 0.7 * xgb_pred + 0.3 * simple_pred
```

**Pros:**
- Preserves XGBoost's ability to capture complex patterns
- Adds monotonic "guard rail" to prevent wild predictions
- Easy to tune blend weight

**Cons:**
- Ad-hoc approach
- Requires tuning blend weight
- Doesn't fix root cause

---

## Part 5: Recommended Action Plan

### Phase 1: Quick Win (Implement This Week)

**Action:** Add monotonic constraints to XGBoost model

**Implementation:**
1. Modify `scripts/04_predictive_model_control_function.py`
2. Add monotone_constraints parameter for price_clean (set to -1)
3. Retrain models for all cities
4. Test predictions - verify occupancy now decreases monotonically
5. Compare model performance (expect small drop in R², but better behavior)

**Estimated Time:** 2-3 hours
**Risk:** Low
**Impact:** High (fixes non-monotonic issue)

### Phase 2: Feature Engineering (Next Sprint)

**Action:** Add price elasticity features

**Implementation:**
1. Modify `scripts/03_feature_engineering.py`
2. Add price_vs_neighborhood, price_vs_similar, log_price
3. Rerun full pipeline
4. Compare model performance

**Estimated Time:** 1 day
**Risk:** Medium (need to retrain everything)
**Impact:** Medium-High (better price understanding)

### Phase 3: Enhanced Control Function (If Needed)

**Action:** Expand Stage 1 OLS to include more price determinants

**Implementation:**
1. Carefully select additional Stage 1 variables (avoid over-controlling)
2. Retrain models
3. Compare improvement

**Estimated Time:** 2-3 days (including validation)
**Risk:** Medium (requires economic reasoning)
**Impact:** Medium (better causal inference)

---

## Part 6: FAQ

### Q: Why not just use a simpler model?

A: XGBoost with monotonic constraints gives us the best of both worlds:
- Flexibility to capture complex interactions (vibe × amenities, location × property type)
- Economic sensibility (price → occupancy is monotonic)

Simple linear regression would miss important interactions and likely perform worse.

### Q: Will fixing this improve revenue recommendations?

A: Yes, significantly:
- Revenue curves will be smoother (no weird jumps)
- Optimal prices will be more stable and trustworthy
- 75% occupancy threshold will be properly respected
- Hosts will have more confidence in recommendations

### Q: Will predictions still be "low"?

A: Possibly yes, and **that's okay**. If the training data shows most listings have 30-50% occupancy, then predictions in that range are accurate. The goal isn't to predict high occupancy - it's to predict **correct** occupancy.

However, we should verify:
- Are we using the right occupancy metric? (occ_90 vs occ_30)
- Are we filtering to active listings only?
- Are we excluding listings with data quality issues?

### Q: What if monotonic constraints hurt model accuracy too much?

A: Then we can:
1. Use softer constraints (allow small increases within noise threshold)
2. Apply constraints only to price_clean, not price_per_person
3. Use Solution 5 (ensemble with monotonic baseline)
4. Accept small accuracy trade-off for better business logic

---

## Part 7: Validation Plan

After implementing solutions, validate with:

### 7.1 Quantitative Tests
- ✅ Monotonicity check: Occupancy should decrease in ≥95% of price increases
- ✅ Model accuracy: R² should stay within 5% of current value
- ✅ Revenue curve smoothness: No jumps >10 percentage points
- ✅ Cross-validation: Performance should be stable across folds

### 7.2 Qualitative Tests
- ✅ Spot-check 10 random properties - do predictions make business sense?
- ✅ Test edge cases (very cheap, very expensive, high vibe, low vibe)
- ✅ Compare to k-NN recommendations - are they roughly aligned?
- ✅ User testing - show revenue curves to team, do they look right?

### 7.3 Business Logic Tests
- ✅ For same property, doubling price should roughly halve occupancy (elasticity ~-1)
- ✅ High-vibe properties should maintain higher occupancy at same price
- ✅ Luxury properties should tolerate higher prices better
- ✅ Budget properties should be more price-sensitive

---

## Part 8: Expected Outcomes

### Before (Current State)
- ✗ Occupancy increases in 10.2% of price changes
- ✗ Wild jumps (£285 → £290 causes +6.4 ppts occupancy)
- ✗ Revenue curves have bumps and wiggles
- ✗ Users don't trust recommendations

### After (With Monotonic Constraints)
- ✓ Occupancy decreases in ≥95% of price changes
- ✓ Smooth, predictable revenue curves
- ✓ Economically sensible behavior
- ✓ Users trust recommendations

**Estimated Impact on Key Metrics:**
- Model R²: -2% to -5% (acceptable trade-off)
- Revenue recommendation quality: +30% (subjective, based on business logic)
- User trust: +50% (revenue curves make sense)
- Computational cost: +0% (same model, just one extra parameter)

---

## Conclusion

The "low occupancy" concern is actually a misunderstanding - predictions are realistic given market conditions. However, the non-monotonic behavior is a genuine issue caused by the model overfitting to complex patterns in the training data.

**Bottom line:** Implement monotonic constraints on XGBoost. This is a simple, low-risk change that will dramatically improve the business value of your pricing engine while maintaining the model's ability to capture important interactions.

The fact that you noticed these issues shows good analytical thinking. Many data science projects ship models with these problems and never realize it!
