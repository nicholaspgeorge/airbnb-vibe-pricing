# Methodology Documentation

**Project:** Vibe-Aware Pricing Engine
**Team:** Nicholas George, Sahil Medepalli, Heath Verhasselt
**Course:** MIS5460 Fall 2025

This document tracks all methodological decisions, data processing steps, and analytical choices made throughout the project. It serves as a reference for the final writeup and ensures reproducibility.

**AI Development Notes:** This project leverages Claude Code for development. See [CLAUDE.md](CLAUDE.md) for prompts and workflows used throughout implementation.

---

## Table of Contents

1. [Data Sources and Acquisition](#1-data-sources-and-acquisition)
2. [Data Cleaning Decisions](#2-data-cleaning-decisions)
3. [Missing Data Handling](#3-missing-data-handling)
4. [Feature Engineering](#4-feature-engineering)
5. [Target Variable Definition](#5-target-variable-definition)
6. [Vibe Score Integration](#6-vibe-score-integration)
7. [Train/Test Split Strategy](#7-traintest-split-strategy)
8. [Model Selection Criteria](#8-model-selection-criteria)
9. [Evaluation Metrics](#9-evaluation-metrics)
10. [Limitations and Assumptions](#10-limitations-and-assumptions)

---

## 1. Data Sources and Acquisition

### Primary Data Source
**Source:** Inside Airbnb (http://insideairbnb.com/get-the-data/)
**License:** Creative Commons CC0 1.0 Universal (Public Domain)
**Snapshot Date:** September 16, 2025
**City:** London, United Kingdom

### Files Used
1. **listings_London.csv** (204 MB, 189,056 rows initially)
   - Contains property features, host information, pricing, availability
   - 79 columns covering comprehensive listing attributes

2. **Vibe Feature Files** (Pre-computed by team)
   - `01_neighborhood_vibe_scores.csv` - Aggregate scores (33 neighborhoods)
   - `01_neighborhood_vibe_dimensions.csv` - Multi-dimensional features
   - `01_vibe_features_for_modeling.csv` - Model-ready join table

### Data Volume
- **Initial listings:** 189,056
- **After initial load:** 96,871 (51.2% - data appears filtered/sampled by Inside Airbnb)
- **Neighborhoods:** 33 London boroughs
- **Time period:** Next 90 days from snapshot date

### Rationale
- Inside Airbnb provides comprehensive, public, regularly-updated data
- Multi-city availability supports future expansion (NYC, Austin)
- Transparent data collection methodology documented on their website
- No personally identifiable information (PII) in dataset

---

## 2. Data Cleaning Decisions

### 2.1 Price Field Cleaning

**Issue:** Price stored as string with currency symbol and commas (e.g., "$70.00", "$1,200.00")

**Solution Implemented:**
```python
def clean_price(price_str):
    """Convert price string like '$100.00' to float"""
    if pd.isna(price_str):
        return np.nan
    try:
        return float(str(price_str).replace('$', '').replace(',', ''))
    except:
        return np.nan
```

**Decision Log:**
- **Date:** 2025-11-06
- **Decision:** Strip '$' and commas, convert to float
- **Rationale:** Standard numeric format required for modeling
- **Alternative Considered:** Use pandas' `str.extract()` with regex - rejected for simplicity
- **Impact:** Successfully cleaned 64% of price fields (36% null in original data)

**Outlier Treatment:**
- **Identified Issues:**
  - Zero prices: 0 instances (good)
  - Price < £10: 3 instances (likely errors)
  - Price > £1000: 723 instances (1.2% of non-null prices)
  - Maximum: £1,085,147 (extreme outlier)

- **Decision for Modeling (pending Task 2):**
  - **Lower bound:** Filter out price < £10 (data entry errors)
  - **Upper bound:** Cap at 99th percentile (~£500-600) for robust modeling
  - **Justification:** Extreme outliers distort model training; 99th percentile retains 99% of data while removing statistical aberrations
  - **Documentation:** Flagged extreme listings separately for manual review

### 2.2 Boolean Field Conversion

**Issue:** Boolean fields stored as 't'/'f' strings

**Fields Affected:**
- `host_is_superhost`
- `host_identity_verified`
- `instant_bookable`

**Solution (to implement in Task 2):**
```python
df['host_is_superhost'] = (df['host_is_superhost'] == 't').astype(int)
```

**Rationale:** Binary 1/0 encoding required for most ML algorithms

### 2.3 Amenities Field Parsing

**Issue:** Amenities stored as JSON-like string: `["Wifi", "Kitchen", "Washer"]`

**Solution (to implement in Task 2):**
```python
df['amenities_count'] = df['amenities'].str.count(',') + 1
```

**Rationale:**
- Count provides simple numeric proxy for listing quality
- Full text parsing adds complexity with minimal predictive gain
- Amenities count correlates with price and occupancy

---

## 3. Missing Data Handling

### 3.1 Missing Data Assessment Results

**Analysis Date:** 2025-11-06

| Field | Missing % | Strategy | Rationale |
|-------|-----------|----------|-----------|
| **price_clean** | 36.0% | Filter out | Core target variable - cannot impute price for modeling |
| **bathrooms** | 36.0% | Parse from `bathrooms_text`, then impute | Alternative field available; important feature |
| **review_scores_rating** | 24.9% | Create `has_reviews` flag + impute neighborhood median | Missing = no reviews; capture this signal |
| **first_review** | 24.9% | Set to listing creation date or impute | Required for `listing_age_days` feature |
| **last_review** | 24.9% | Impute with snapshot date for active listings | Recency important for demand signal |
| **bedrooms** | 13.2% | Impute with median by `room_type` | Predictable from room type |
| **host_is_superhost** | 1.8% | Assume 'f' (not superhost) | Low missing rate; conservative assumption |
| **availability_90** | 0.0% | No action needed | Complete data ✓ |
| **accommodates** | 0.0% | No action needed | Complete data ✓ |

### 3.2 Imputation Strategy Detail

#### Bedrooms Imputation
**Method:** Conditional median imputation
```python
df['bedrooms'] = df.groupby('room_type')['bedrooms'].transform(
    lambda x: x.fillna(x.median())
)
```

**Rationale:**
- Strong correlation between room_type and bedrooms
- Private room → typically 1 bedroom
- Entire home/apt → varies, use median
- Shared room → typically 0-1 bedroom
- Preserves room type patterns

**Alternative Considered:** Use `beds` as proxy
- Rejected: `beds` also has missing data
- Rejected: Median by accommodates - too many bins

#### Bathrooms Imputation
**Method:** Two-stage approach
1. Parse `bathrooms_text` field (more complete than numeric field)
2. If still missing, impute with median by (accommodates, bedrooms)

```python
# Stage 1: Parse bathrooms_text
df['bathrooms_parsed'] = df['bathrooms_text'].str.extract(r'(\d+\.?\d*)').astype(float)
df['bathrooms'] = df['bathrooms'].fillna(df['bathrooms_parsed'])

# Stage 2: Conditional imputation
df['bathrooms'] = df.groupby(['accommodates', 'bedrooms'])['bathrooms'].transform(
    lambda x: x.fillna(x.median())
)
```

**Rationale:**
- `bathrooms_text` contains descriptions like "1 shared bath", "2.5 baths"
- Strong relationship: more bedrooms/accommodates → more bathrooms
- Two-stage captures maximum information

#### Review Scores Imputation
**Method:** Neighborhood median + binary flag
```python
df['has_reviews'] = (df['number_of_reviews'] > 0).astype(int)
df['review_scores_rating'] = df.groupby('neighbourhood_cleansed')['review_scores_rating'].transform(
    lambda x: x.fillna(x.median())
)
```

**Rationale:**
- Missing review scores = no reviews (not random)
- Capture this information with `has_reviews` flag
- Neighborhood median assumes similar quality within area
- Prevents losing 25% of dataset

**Alternative Considered:**
- Global median - rejected (ignores neighborhood quality differences)
- Drop listings - rejected (loses too much data, introduces bias toward established listings)

### 3.3 Filtering vs Imputation Decision Framework

**Filter out when:**
1. Field is the target variable or critical predictor (e.g., price, availability_90)
2. Missing data is >50% and not recoverable
3. Imputation would introduce excessive bias

**Impute when:**
1. Alternative data source exists (e.g., bathrooms_text)
2. Strong correlation with other features allows prediction
3. Missing pattern is informative (e.g., no reviews)
4. Preserving sample size is critical (e.g., review scores at 25%)

**Document when:**
- All imputation methods recorded in this file
- Imputation flags added to dataset (e.g., `bedrooms_imputed`)
- Impact assessed in final model evaluation

---

## 4. Feature Engineering

### 4.1 Occupancy Proxy Creation

**Core Innovation:** Transform availability into occupancy rate

**Formulas:**
```python
occ_30  = 1 - (availability_30 / 30)
occ_60  = 1 - (availability_60 / 60)
occ_90  = 1 - (availability_90 / 90)   # Primary target
occ_365 = 1 - (availability_365 / 365)
```

**Theoretical Basis:**
- Inside Airbnb's `availability_X` = days available in next X days
- Lower availability → Higher presumed occupancy
- Proxy for booking intensity (acknowledges host-blocked days)

**Validation:**
- Cross-correlation: occ_30, occ_60, occ_90, occ_365 should be highly correlated
- Sanity check: Compare with `number_of_reviews_ltm` (recent booking activity)
- Distribution check: Ensure values in [0, 1] range

**Limitations:**
- **Booked vs Blocked:** Availability mixes truly booked nights with host-blocked nights
- **Mitigation:** Document as limitation; triangulate with review-based estimates where possible
- **Assumption:** Hosts generally keep calendars open; blocked nights are minority

### 4.2 Derived Features

#### Listing Age
```python
listing_age_days = (pd.to_datetime('2025-09-16') - pd.to_datetime(first_review)).dt.days
```
**Rationale:** Older listings may have more reviews, established reputation
**Handling Missing:** If `first_review` missing, set age to 0 or use host registration date

#### Price Per Person
```python
price_per_person = price_clean / accommodates
```
**Rationale:** Normalizes price by capacity; better for comparing across property sizes
**Handling Division by Zero:** Filter out accommodates=0 (data errors)

#### Amenities Count
```python
amenities_count = amenities.str.count(',') + 1
```
**Rationale:** Proxy for listing quality and completeness
**Note:** Treats empty amenities list as 1 amenity (the list itself)

#### Professional Host Flag
```python
is_professional_host = (host_listings_count > 5).astype(int)
```
**Rationale:** Multi-listing hosts may have different pricing strategies
**Threshold:** 5+ listings = professional (based on EDA distribution)

### 4.3 Feature Engineering Principles Applied

1. **Domain Knowledge:** Use insights from Airbnb market (e.g., price_per_person meaningful)
2. **Simplicity:** Prefer simple transformations (counts, ratios) over complex NLP
3. **Interpretability:** All features have clear business meaning
4. **Leakage Prevention:** Only use information available at snapshot time
5. **Robustness:** Handle edge cases (division by zero, missing values)

---

## 5. Target Variable Definition

### 5.1 Primary Target: Occupancy Rate (90-day)

**Variable:** `occ_90`
**Formula:** `occ_90 = 1 - (availability_90 / 90)`
**Range:** [0, 1] where 1 = fully booked, 0 = fully available

**Selection Rationale:**
- **90-day window:** Balances near-term accuracy with sufficient data
  - Too short (30-day): Volatile, seasonal spikes
  - Too long (365-day): Includes far-future uncertainty
  - 90-day: Industry standard for STR performance metrics

- **Continuous vs Binary:** Continuous preserves more information for regression models

### 5.2 Secondary Target: High-Demand Label

**Variable:** `high_demand_90`
**Formula:** `high_demand_90 = 1 if occ_90 >= 0.75 else 0`
**Use Case:** k-NN "High-Demand Twins" pricing engine

**Threshold Selection: τ = 0.75**

**Decision Date:** 2025-11-06

**Rationale:**
1. **Industry Benchmark:** 75% occupancy considered "high performance" in STR industry
2. **Revenue Optimization:** 75% × price often yields higher revenue than 100% × (lower price)
3. **Data Distribution:** London data shows 47.6% of listings achieve ≥75% occupancy (balanced classes)
4. **Risk Management:** Conservative threshold ensures recommended prices maintain demand

**Sensitivity Analysis (planned for Task 4):**
- Test thresholds: 0.60, 0.70, 0.75, 0.80, 0.85
- Evaluate impact on:
  - Classification balance
  - Neighbor availability in k-NN
  - Revenue outcomes
  - Price band widths

**Alternative Approaches Considered:**
- **Percentile-based:** Top 30% of listings → Rejected (threshold varies by city)
- **Revenue-based:** Max revenue threshold → Rejected (requires price×occupancy optimization first)
- **Dynamic threshold:** By neighborhood → Rejected (too complex for initial model)

---

## 6. Vibe Score Integration

### 6.1 Vibe Features Overview

**Source:** Pre-computed by team from review text analysis

**Methodology (Prior Work):**
1. **Text Collection:** Aggregate all reviews by neighborhood
2. **TF-IDF Vectorization:** Weight terms by frequency and uniqueness
3. **LSI/SVD:** Reduce dimensionality to capture latent "concepts"
4. **Clustering:** Group neighborhoods into vibe segments
5. **Scoring:** Assign aggregate score (0-100) and dimension scores

**Features Available:**
- **vibe_score:** Overall neighborhood appeal (0-100)
- **sentiment_mean:** Average sentiment across reviews
- **Dimensions (11):** walkability, safety, nightlife, quietness, family_friendly, local_authentic, convenience, food_scene, liveliness, charm

### 6.2 Join Strategy

**Method:** Left join on neighborhood
```python
df_final = df_listings.merge(
    df_vibe_features,
    left_on='neighbourhood_cleansed',
    right_on='neighbourhood',
    how='left'
)
```

**Validation Results (London):**
- **Match rate:** 100.00% ✓
- **Reason:** All 33 boroughs represented in both datasets
- **Duplicates:** None (verified row count unchanged)

**Quality Assurance:**
- Verify no duplicate rows created
- Check for null vibe_score in joined data
- Validate vibe_score range [0, 100]

### 6.3 Handling Unmatched Listings (Future Cities)

**If match rate < 95%:**

**Option A:** Impute with city-wide mean
```python
city_mean_vibe = df_vibe_features['vibe_score'].mean()
df_final['vibe_score'].fillna(city_mean_vibe, inplace=True)
```
**Pros:** Preserves all listings
**Cons:** Loses neighborhood signal for unmatched

**Option B:** Spatial imputation (nearest neighbor)
- Use lat/lon to find nearest neighborhood with vibe data
- Assign that neighborhood's vibe scores
**Pros:** Geographically informed
**Cons:** Requires additional computation

**Option C:** Filter out unmatched
- Only if unmatched < 5% of data
**Pros:** Clean, no imputation assumptions
**Cons:** Potential bias if unmatched not random

**Decision Framework:**
- If unmatched < 5% → Option C (filter)
- If 5-10% unmatched → Option A (city mean)
- If >10% unmatched → Option B (spatial) or improve vibe data coverage

---

## 7. Train/Test Split Strategy

### 7.1 Split Configuration

**Ratio:** 80% train / 20% test
**Method:** Stratified random sampling
**Stratification Variable:** `high_demand_90`
**Random Seed:** 42 (for reproducibility)

```python
from sklearn.model_selection import train_test_split

train, test = train_test_split(
    df_final,
    test_size=0.20,
    random_state=42,
    stratify=df_final['high_demand_90']
)
```

### 7.2 Rationale

**80/20 Split:**
- Standard in ML when dataset size is adequate (96K listings)
- 20% test (≈19K listings) sufficient for robust evaluation
- 80% train (≈77K listings) provides ample data for GBM/RF

**Stratification:**
- Ensures train and test have similar high-demand proportions
- Critical when target distribution is not 50/50 (London: 47.6% high-demand)
- Prevents evaluation bias

**Random Seed:**
- `random_state=42` enables reproducibility
- Team can re-run and get identical splits
- Facilitates comparison across model iterations

### 7.3 Temporal Considerations

**Issue:** Inside Airbnb is a snapshot (Sept 2025), not time-series

**Decision:** Random split acceptable because:
- No temporal leakage (all data from same snapshot)
- No future information used
- Goal is cross-sectional prediction, not time-series forecasting

**Alternative Considered:**
- Time-based split (if using multiple snapshots) - N/A for current data

### 7.4 Cross-Validation

**Method:** 5-fold cross-validation on training set
**Purpose:** Hyperparameter tuning and model selection
**Stratification:** Also stratify CV folds on `high_demand_90`

```python
from sklearn.model_selection import StratifiedKFold

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

**Rationale:**
- 5 folds = 20% held-out per fold (reasonable for 77K train set)
- More folds (10) = less bias but higher variance
- Fewer folds (3) = more bias but lower variance
- 5 is standard compromise

---

## 8. Model Selection Criteria

### 8.1 Decision Engine A: k-NN High-Demand Twins

**Algorithm:** k-Nearest Neighbors (similarity-based)
**Purpose:** Empirical price band recommendation

**Configuration:**
- **k = 25:** Number of neighbors to consider
- **Distance Metric:** Euclidean
- **Features:** accommodates, bedrooms, bathrooms, amenities_count, room_type (one-hot), vibe_score, vibe dimensions
- **Normalization:** StandardScaler (features have different scales)

**Rationale:**
1. **Interpretability:** "Properties like yours that are heavily booked charge £X-Y"
2. **No Parametric Assumptions:** Data-driven, distribution-free
3. **Local Patterns:** Captures neighborhood-specific pricing

**k=25 Selection:**
- **Too Small (k=5):** Noisy, sensitive to outliers
- **Too Large (k=100):** Over-smoothed, loses local patterns
- **k=25:** Balances local precision with statistical stability
- **Validation:** Ensure ≥5 high-demand neighbors for 60%+ of listings

**Fallback Strategy:**
- If <5 high-demand neighbors found → Use neighborhood-level price bins
- Flag as "low_confidence" recommendation

### 8.2 Decision Engine B: Predictive Model

**Model Candidates:**
1. **XGBoost** (Gradient Boosted Trees)
2. **LightGBM** (Gradient Boosted Trees, optimized)
3. **Random Forest**

**Selection Criteria:**
1. **Performance:** MAE, RMSE on validation set
2. **Interpretability:** SHAP value support
3. **Training Speed:** Important for iteration
4. **Robustness:** Handles mixed feature types (categorical + numeric)
5. **Overfitting Control:** Built-in regularization

**Expected Winner:** XGBoost or LightGBM
- **Reason:** Superior performance on tabular data with mixed types
- **Advantage:** Built-in handling of missing values
- **Interpretability:** SHAP library has excellent GBM support

**Hyperparameters to Tune:**
- **Learning Rate:** [0.01, 0.05, 0.1]
- **Max Depth:** [3, 5, 7, 10]
- **Number of Estimators:** [100, 300, 500]
- **Regularization:** L1/L2 penalties

**Method:** GridSearchCV or RandomizedSearchCV with 5-fold CV

### 8.3 Control Function for Price Endogeneity

**Problem:** Price affects occupancy, but occupancy also affects price (simultaneity bias)

**Solution:** Two-stage approach

**Stage 1: Price Prediction**
```
price ~ month + neighbourhood + listing_density + seasonality
```
**Purpose:** Model exogenous determinants of price
**Save:** Residual ε̂_price (captures endogenous component)

**Stage 2: Occupancy Prediction**
```
occ_90 ~ price + features + vibe + ε̂_price
```
**Purpose:** Including ε̂_price as control function reduces endogeneity bias

**Theoretical Basis:**
- Control function approach (Heckman-style)
- ε̂_price captures unobserved factors correlated with both price and occupancy
- Allows causal interpretation of price coefficient

**Alternative Considered:**
- Instrumental Variables (IV) regression → Rejected (no strong instruments available)
- Ignore endogeneity → Rejected (biased price elasticity estimates)

---

## 9. Evaluation Metrics

### 9.1 Predictive Performance

**Primary Metrics:**
1. **MAE (Mean Absolute Error):**
   ```
   MAE = (1/n) Σ |y_true - y_pred|
   ```
   - **Interpretation:** Average prediction error in occupancy units (0-1 scale)
   - **Target:** MAE < 0.15 (±15 percentage points)

2. **RMSE (Root Mean Squared Error):**
   ```
   RMSE = sqrt((1/n) Σ (y_true - y_pred)²)
   ```
   - **Interpretation:** Penalizes large errors more than MAE
   - **Target:** RMSE < 0.20

3. **R² (Coefficient of Determination):**
   ```
   R² = 1 - (SS_res / SS_tot)
   ```
   - **Interpretation:** % of variance explained by model
   - **Target:** R² > 0.40 (40% of variance explained)

**Baseline Comparison:**
- Train identical model WITHOUT vibe features
- **Success Criterion:** Vibe model beats baseline by ≥15% on MAE/RMSE

### 9.2 Feature Importance

**Method:** SHAP (SHapley Additive exPlanations) values

**Validation of Hypothesis:**
- **H0:** Vibe Score has negligible impact on predictions
- **H1:** Vibe Score ranks in top 50% of feature importance
- **Test:** Examine global SHAP importance ranking
- **Success:** Vibe Score in top 50% of features by mean(|SHAP value|)

**Visualizations:**
1. **Global Importance:** Bar chart of mean |SHAP| per feature
2. **Beeswarm Plot:** SHAP values colored by feature value
3. **Dependence Plot:** SHAP(vibe_score) vs vibe_score

### 9.3 Business Metrics

**1. Recommendation Coverage:**
```
Coverage = (Listings with valid price band) / (Total listings)
```
**Target:** ≥60% of listings receive recommendations

**2. Price Band Validation:**
- For test set: Do recommendations historically achieve high_demand_90?
- **Metric:** Precision = (Recommended & high-demand) / (Recommended)
- **Target:** Precision ≥ 0.70 (70% of recommendations are actually high-demand)

**3. Revenue Lift:**
```
Revenue_Lift = (Optimal_Revenue - Current_Revenue) / Current_Revenue
```
**Measurement:** For sample of test listings, compute:
- Current revenue: `current_price × occ_90(current_price) × 30`
- Optimal revenue: `optimal_price × occ_90(optimal_price) × 30`
**Target:** Mean revenue lift ≥5% across sample

**4. Calibration:**
- Plot predicted vs actual occupancy by decile
- **Visual Check:** Should see roughly diagonal line (well-calibrated)
- **Metric:** Calibration error < 0.05

### 9.4 Robustness Checks

1. **By Neighborhood:** Performance consistent across London boroughs?
2. **By Property Type:** Model works for all room types?
3. **By Price Decile:** No systematic bias for cheap vs expensive listings?
4. **Outlier Analysis:** Identify listings with >0.30 absolute error

---

## 10. Limitations and Assumptions

### 10.1 Data Limitations

**1. Booked vs Blocked Ambiguity**
- **Issue:** `availability_X` mixes truly booked nights with host-blocked nights
- **Impact:** Overestimates occupancy if hosts frequently block calendars
- **Mitigation:** Document as limitation; triangulate with review-based estimates
- **Assumption:** Host-blocked nights are minority of unavailable nights

**2. Snapshot Nature**
- **Issue:** Single point-in-time (Sept 2025), no temporal dynamics
- **Impact:** Cannot model seasonality or trends
- **Mitigation:** Use month-of-year as feature (capture seasonal patterns)
- **Future Work:** Multi-snapshot analysis if data available

**3. Missing Price Data (36%)**
- **Issue:** Over 1/3 of listings missing price
- **Impact:** Reduces usable sample size
- **Analysis:** Check if missing is random or systematic (e.g., inactive listings)
- **Decision:** Filter out (cannot impute dependent variable)

**4. Review Selection Bias**
- **Issue:** Only guests who completed stays leave reviews
- **Impact:** Vibe scores may reflect "successful" bookings, not all attempts
- **Mitigation:** Acknowledge in limitations section

### 10.2 Modeling Assumptions

**1. Price Elasticity is Stable**
- **Assumption:** Relationship between price and occupancy is consistent within neighborhood/property type
- **Risk:** External shocks (events, policy changes) could break relationship
- **Mitigation:** Model retraining recommended quarterly

**2. Vibe Features are Exogenous**
- **Assumption:** Vibe scores capture neighborhood characteristics, not affected by individual listing pricing
- **Justification:** Vibe computed at neighborhood level, aggregated over many reviews
- **Risk:** Minimal reverse causality

**3. High-Demand Threshold (0.75) Generalizes**
- **Assumption:** 75% occupancy is meaningful across all property types/neighborhoods
- **Validation:** Sensitivity analysis planned (test 0.60, 0.70, 0.80, 0.85)
- **Risk:** Optimal threshold may vary (e.g., luxury vs budget)

**4. Training Distribution Holds**
- **Assumption:** Future listings will be similar to training data
- **Risk:** Market shifts, new property types emerge
- **Mitigation:** Monitor model performance over time, retrain as needed

### 10.3 Methodological Limitations

**1. Cross-Sectional, Not Causal**
- **Limitation:** Associations observed, not necessarily causal effects
- **Exception:** Control function approach attempts causal interpretation of price
- **Communication:** Clearly state "associated with" not "causes" in writeup

**2. London-Specific**
- **Limitation:** Model trained on London may not generalize to other cities
- **Plan:** Validate on NYC, Austin when data available
- **Hypothesis:** Vibe concept should generalize, but coefficients may differ

**3. No Dynamic Pricing**
- **Limitation:** Model recommends fixed price, not dynamic by season/events
- **Future Work:** Extend to time-varying recommendations

**4. Assumed Constant Operating Costs**
- **Limitation:** Revenue optimization assumes costs are fixed
- **Reality:** Cleaning, utilities vary
- **Justification:** For relative comparisons (lift %), fixed costs cancel out

### 10.4 Ethical Considerations

**1. Fair Housing**
- **Concern:** Could model perpetuate neighborhood stereotypes via vibe scores?
- **Mitigation:** Vibe scores based on aggregate guest sentiment, not demographics
- **Transparency:** Publish methodology and feature importance

**2. Price Discrimination**
- **Concern:** Recommending high prices in high-demand areas
- **Justification:** Reflects market dynamics; tool is guidance, not compulsory
- **Alternative:** Hosts can choose lower prices for social reasons

**3. Data Privacy**
- **Concern:** Using public review text
- **Mitigation:** Reviews are public, voluntarily shared by users
- **Aggregation:** Individual reviews not identifiable in vibe scores

---

## Changelog

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-11-06 | Initial methodology document created | Document decisions from Task 1 |
| 2025-11-06 | Defined occupancy proxy formulas | Core target variable definition |
| 2025-11-06 | Set high-demand threshold τ=0.75 | Based on industry standards and data distribution |
| 2025-11-06 | Documented missing data strategies | Prepare for Task 2 implementation |
| 2025-11-06 | Defined evaluation metrics | Set success criteria |

---

## References

1. Inside Airbnb. (2025). *Data Assumptions*. Retrieved from http://insideairbnb.com/data-assumptions/
2. Lundberg, S. M., & Lee, S. I. (2017). *A unified approach to interpreting model predictions*. NIPS 2017.
3. James, G., Witten, D., Hastie, T., & Tibshirani, R. (2013). *An introduction to statistical learning* (Vol. 112). Springer.
4. Inside Airbnb. (2025). *About Inside Airbnb*. Retrieved from http://insideairbnb.com/about.html

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Next Review:** After Task 2 (Feature Engineering) completion
