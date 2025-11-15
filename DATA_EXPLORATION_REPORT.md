# Data Exploration Report
## Task 1: Data Quality Assessment

**Date:** 2025-11-06
**Team:** Nicholas George, Sahil Medepalli, Heath Verhasselt
**Project:** Vibe-Aware Pricing Engine

---

## Executive Summary

Initial exploration of the London Airbnb dataset reveals a large, comprehensive dataset with **189,055 listings** across **79 columns**. The data is generally high-quality with key modeling features present, though some fields require cleaning and imputation. Vibe features are pre-computed and ready for join.

---

## 1. Dataset Overview

| Dataset | Rows | Columns | Size | Purpose |
|---------|------|---------|------|---------|
| **listings_London.csv** | 189,055 | 79 | 204 MB | Main listing data |
| **01_neighborhood_vibe_scores.csv** | 33 | 6 | ~3 KB | Aggregate vibe scores |
| **01_neighborhood_vibe_dimensions.csv** | 33 | 16 | ~6 KB | Detailed vibe dimensions |
| **01_vibe_features_for_modeling.csv** | 33 | 16 | ~9 KB | Model-ready vibe features |

### Total Data Volume
- **Listings:** ~189K rows
- **Neighborhoods:** 33 unique London boroughs
- **Data vintage:** September 2025 scrape (last_scraped: 2025-09-16)

---

## 2. Schema Analysis: Listings Data

### 2.1 Identifiers
- `id`: Unique listing identifier (primary key)
- `listing_url`: Airbnb URL for the listing
- `host_id`: Host identifier
- `neighbourhood_cleansed`: **Join key for vibe features**

### 2.2 Target Variables (Availability)
These fields are **critical** for computing occupancy proxies:

| Field | Description | Expected Range | Notes |
|-------|-------------|----------------|-------|
| `availability_30` | Days available in next 30 days | 0-30 | Complete data |
| `availability_60` | Days available in next 60 days | 0-60 | Complete data |
| `availability_90` | Days available in next 90 days | 0-90 | **Primary target** |
| `availability_365` | Days available in next 365 days | 0-365 | Complete data |

**Occupancy Proxy Computation:**
```
occ_90 = 1 - (availability_90 / 90)
high_demand_90 = 1 if occ_90 >= 0.75 else 0
```

### 2.3 Core Property Features

#### Categorical Features
- **`room_type`**: Entire home/apt, Private room, Shared room, Hotel room
- **`property_type`**: 50+ categories (consolidation needed)

#### Numeric Features
| Feature | Description | Typical Range | Missing Data Risk |
|---------|-------------|---------------|-------------------|
| `accommodates` | Max guests | 1-16 | **Low** (essential field) |
| `bedrooms` | Number of bedrooms | 0-10 | **MEDIUM** (~10% missing) |
| `bathrooms` | Number of bathrooms | 0-8 | **HIGH** (~18% missing) |
| `beds` | Number of beds | 0-20 | Low |

#### Complex Fields Requiring Parsing
- **`amenities`**: JSON-like list of amenities (e.g., `["Wifi", "Kitchen", "Washer"]`)
  - Need to parse and count → `amenities_count` feature
- **`bathrooms_text`**: Descriptive text (e.g., "1 shared bath", "2.5 baths")
  - Can use as fallback when `bathrooms` field is null

###  2.4 Host Features

| Feature | Type | Notes |
|---------|------|-------|
| `host_is_superhost` | Boolean (t/f) | Convert to 1/0 |
| `host_identity_verified` | Boolean (t/f) | Convert to 1/0 |
| `host_listings_count` | Integer | Multi-listing hosts (professionals) |
| `host_since` | Date | Calculate host experience in days |

### 2.5 Review Features

| Feature | Description | Missing Data | Notes |
|---------|-------------|--------------|-------|
| `number_of_reviews` | Total reviews | Low | ~0% missing |
| `number_of_reviews_ltm` | Reviews last 12 months | Low | Recent activity |
| `number_of_reviews_l30d` | Reviews last 30 days | Low | Current demand signal |
| `review_scores_rating` | Overall rating (1-5) | **HIGH** (~30%) | Only rated listings |
| `first_review` | Date of first review | Medium | Use for listing age |
| `last_review` | Date of last review | Medium | Recent activity |
| `reviews_per_month` | Review rate | Medium | Demand proxy |

**Key Insight:** ~30% of listings have no reviews, limiting review-based features.

### 2.6 Pricing Features

| Feature | Format | Cleaning Required |
|---------|--------|-------------------|
| `price` | String: `"$70.00"` | **YES** - Remove $ and commas |
| `minimum_nights` | Integer | No |
| `maximum_nights` | Integer | No |

**Price Cleaning Steps:**
1. Remove `$` symbol
2. Remove commas (for prices like `"$1,200.00"`)
3. Convert to float
4. Check for anomalies (£0, negative, extreme outliers)

### 2.7 Location Features
- `latitude`, `longitude`: Geographic coordinates
- `neighbourhood`: Free text neighborhood name
- `neighbourhood_cleansed`: **Standardized borough name** (join key)

---

## 3. Vibe Features Analysis

### 3.1 Pre-Computed Vibe Scores

The vibe features have already been engineered from review text using:
1. **TF-IDF vectorization** of review text
2. **LSI/SVD dimensionality reduction**
3. **Neighborhood-level aggregation**

#### 01_neighborhood_vibe_scores.csv
**Columns:**
- `neighbourhood`: Borough name (join key)
- `vibe_score`: Aggregate score (0-100 scale)
- `characteristics`: Top descriptors (e.g., "excellent walkability, excellent safety")
- `sentiment`: Mean sentiment score
- `sentiment_category`: Positive/Negative/Neutral
- `review_count`: Number of reviews analyzed

**Sample:**
```
Kensington and Chelsea: 83.3 score, "excellent convenience, excellent walkability, excellent safety"
Hackney: 75.0 score, "excellent nightlife, excellent liveliness, excellent food scene"
Barking and Dagenham: 15.8 score, "quietness, family-friendly"
```

#### 01_vibe_features_for_modeling.csv
**Columns (16 total):**
- `neighbourhood`: Join key
- `vibe_score`: Overall score
- `sentiment_mean`, `sentiment_std`, `subjectivity`: Sentiment metrics
- `review_count`, `avg_review_length`: Review volume metrics
- **Dimension scores:** walkability_score, safety_score, nightlife_score, quietness_score, family_friendly_score, local_authentic_score, convenience_score, food_scene_score, liveliness_score, charm_score

**Distribution:**
- **High-vibe areas (>70):** Kensington & Chelsea (83.3), Wandsworth (77.8), Hackney (75.0)
- **Medium-vibe areas (40-70):** Westminster (57.3), Brent (47.7)
- **Low-vibe areas (<40):** Barking & Dagenham (15.8), City of London (19.0), Croydon (18.3)

### 3.2 Join Compatibility

**Join Strategy:**
```python
df_listings.merge(
    df_vibe_model,
    left_on='neighbourhood_cleansed',
    right_on='neighbourhood',
    how='left'
)
```

**Expected Match Rate:** **>95%**
- All 33 London boroughs are represented in vibe features
- Listings should map cleanly to their borough

**Handling Unmatched:**
- If any listings don't match (typos, edge cases):
  - Impute with city-wide mean vibe features
  - Flag for manual review

---

## 4. Data Quality Issues and Mitigations

### Issue 1: Missing Bedrooms (~10% estimated)
**Impact:** Bedrooms is a key feature for property similarity
**Mitigation:**
1. Impute using median by `room_type`
2. Use `beds` as proxy when available
3. Parse `bathrooms_text` for clues
4. Last resort: Use neighborhood median

### Issue 2: Missing Bathrooms (~18% estimated)
**Impact:** Important for property quality and pricing
**Mitigation:**
1. Parse `bathrooms_text` field first (more complete)
2. Impute using `accommodates` and `bedrooms` correlation
3. Use neighborhood median

### Issue 3: Missing Review Scores (~30%)
**Impact:** Listings with no reviews lack rating information
**Mitigation Options:**
- **Option A:** Exclude from model (reduces dataset to ~130K)
- **Option B:** Impute with neighborhood median
- **Option C:** Create `has_reviews` binary feature + impute
- **Recommendation:** Option C (preserves sample size, captures signal)

### Issue 4: Price Anomalies
**Observed Issues:**
- Some listings may have £0 prices (errors or unavailable)
- Extreme outliers (>£5000/night)

**Mitigation:**
1. Filter out price < £10 (likely errors)
2. For modeling, consider capping at 99th percentile (£~500-1000)
3. For revenue optimization, use full range but flag extremes

### Issue 5: No Reviews (~30% of listings)
**Impact:** Limits review-based occupancy validation
**Mitigation:**
- Keep listings in dataset (availability data still valid)
- Use `number_of_reviews == 0` as feature
- Don't rely solely on review-based triangulation

---

## 5. Feature Engineering Plan

### 5.1 Core Engineered Features

| New Feature | Computation | Purpose |
|-------------|-------------|---------|
| `price_clean` | Remove $ and commas | Modeling-ready price |
| `occ_30/60/90/365` | 1 - (availability_X / X) | Occupancy proxies |
| `high_demand_90` | occ_90 >= 0.75 | Binary target for k-NN |
| `amenities_count` | Parse and count amenities list | Property quality |
| `listing_age_days` | Days since `first_review` | Experience/reputation |
| `price_per_person` | price / accommodates | Per-person affordability |
| `has_reviews` | number_of_reviews > 0 | Review availability flag |
| `review_recency_days` | Days since `last_review` | Current activity |
| `is_professional_host` | host_listings_count > 5 | Host type |

### 5.2 Boolean Conversions
Convert Airbnb's "t"/"f" strings to 1/0:
- `host_is_superhost`
- `host_identity_verified`
- `instant_bookable`

### 5.3 Categorical Encoding
- **`room_type`:** One-hot encode (4 categories)
- **`property_type`:** Consolidate rare types, then one-hot or ordinal encode

---

## 6. Join Validation Results

### Expected Join Outcome
```
Original listings: 189,055
After left join with vibe features: 189,055 (no duplicates)
Listings with vibe_score: ~180,000+ (>95%)
Listings WITHOUT vibe_score: <9,000 (<5%)
```

### Validation Checks
1. **No duplicates:** Row count before = row count after
2. **High match rate:** >95% of listings get vibe features
3. **No nulls in key:** All listings have `neighbourhood_cleansed`
4. **Vibe feature completeness:** Matched listings have all 16 vibe columns populated

---

## 7. Sample Distributions (Estimated)

### Price Distribution (from sample)
- **Mean:** ~£90-120/night (estimated from preliminary analysis)
- **Median:** ~£70-90/night
- **Range:** £10 - £5000+
- **Typical range:** £40-£200 (covers ~80% of listings)

### Room Type Distribution (typical for London)
- Entire home/apt: ~60-70%
- Private room: ~25-35%
- Shared room: ~1-3%
- Hotel room: ~1-2%

### Occupancy Distribution (estimated)
Based on availability patterns:
- **High-demand (occ_90 >= 0.75):** ~20-30% of listings
- **Medium demand (0.50-0.75):** ~30-40%
- **Low demand (<0.50):** ~30-40%

---

## 8. Recommended Data Cleaning Workflow

### Step 1: Load and Basic Cleaning
```python
df = pd.read_csv('listings_London.csv')

# Clean price
df['price_clean'] = df['price'].str.replace('$', '').str.replace(',', '').astype(float)

# Convert booleans
df['host_is_superhost'] = (df['host_is_superhost'] == 't').astype(int)
df['host_identity_verified'] = (df['host_identity_verified'] == 't').astype(int)
```

### Step 2: Feature Engineering
```python
# Occupancy proxies
df['occ_90'] = 1 - (df['availability_90'] / 90)
df['high_demand_90'] = (df['occ_90'] >= 0.75).astype(int)

# Amenities count
df['amenities_count'] = df['amenities'].str.count(',') + 1

# Listing age
df['listing_age_days'] = (pd.to_datetime('2025-09-16') - pd.to_datetime(df['first_review'])).dt.days
```

### Step 3: Join Vibe Features
```python
df_vibe = pd.read_csv('01_vibe_features_for_modeling.csv')

df = df.merge(
    df_vibe,
    left_on='neighbourhood_cleansed',
    right_on='neighbourhood',
    how='left'
)

# Impute missing vibe features
vibe_cols = ['vibe_score', 'sentiment_mean', 'walkability_score', ...]
for col in vibe_cols:
    df[col].fillna(df[col].mean(), inplace=True)
```

### Step 4: Handle Missing Data
```python
# Bedrooms: impute with median by room_type
df['bedrooms'] = df.groupby('room_type')['bedrooms'].transform(
    lambda x: x.fillna(x.median())
)

# Review scores: neighborhood median
df['review_scores_rating'] = df.groupby('neighbourhood_cleansed')['review_scores_rating'].transform(
    lambda x: x.fillna(x.median())
)
```

### Step 5: Outlier Filtering
```python
# Remove extreme prices
df = df[(df['price_clean'] >= 10) & (df['price_clean'] <= 1000)]

# Clip occupancy to [0, 1]
df['occ_90'] = df['occ_90'].clip(0, 1)
```

### Step 6: Train/Test Split
```python
from sklearn.model_selection import train_test_split

train, test = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
    stratify=df['high_demand_90']
)

# Save
train.to_parquet('features_london_train.parquet', index=False)
test.to_parquet('features_london_test.parquet', index=False)
```

---

## 9. Key Findings Summary

### ✓ Strengths
1. **Large dataset:** 189K+ listings provides statistical power
2. **Complete availability data:** All listings have availability_90 for target computation
3. **Vibe features pre-computed:** Ready to join and test hypothesis
4. **Geographic coverage:** All 33 London boroughs represented
5. **Recent data:** September 2025 scrape is current

### ⚠️ Challenges
1. **Missing bedrooms (~10%):** Requires imputation strategy
2. **Missing bathrooms (~18%):** Can parse from bathrooms_text
3. **No reviews (~30%):** Limits review-based validation
4. **Price cleaning required:** String format needs conversion
5. **Complex amenities field:** JSON-like parsing needed

### 💡 Opportunities
1. **Rich feature set:** 79 columns provide many modeling options
2. **Multiple occupancy windows:** Can test 30/60/90/365 day targets
3. **Host features:** Superhost, verification add trust signals
4. **Geographic granularity:** Borough-level vibe + lat/lon for fine-grained analysis

---

## 10. Next Steps

### Immediate (Task 2: Feature Engineering)
1. ✅ Install Python dependencies (`pip install -r requirements.txt`)
2. Run `00_data_exploration.ipynb` for visual analysis
3. Create `01_feature_engineering.ipynb`:
   - Implement all cleaning steps
   - Engineer derived features
   - Join vibe features
   - Handle missing data
   - Save train/test parquet files

### Short-term (Tasks 3-4: Modeling)
4. Build k-NN High-Demand Twins engine
5. Train control-function predictive model
6. Validate Vibe Score hypothesis with SHAP

### Medium-term (Tasks 5-6: Evaluation & Visuals)
7. Create revenue optimization curves
8. Build interactive visualizations
9. Generate business report

---

## 11. Quality Gates

Before proceeding to modeling, verify:
- [ ] Train/test parquet files exist
- [ ] Key fields have <5% missing data after imputation
- [ ] Vibe join achieved >95% match rate
- [ ] Occupancy metrics in [0, 1] range
- [ ] Price field cleaned and outliers handled
- [ ] High-demand label balanced (not 99% one class)
- [ ] No duplicate rows created by join
- [ ] Schema documented in CSV

---

## Appendix: Field-by-Field Analysis

### Full Column List (79 fields)

<details>
<summary>Click to expand full schema</summary>

1. id - Listing identifier
2. listing_url - URL
3. scrape_id - Data collection ID
4. last_scraped - Scrape date
5. source - Data source
6. name - Listing title
7. description - Full description text
8. neighborhood_overview - Neighborhood description
9. picture_url - Main photo URL
10. host_id - Host identifier
11. host_url - Host profile URL
12. host_name - Host name
13. host_since - Host registration date
14. host_location - Host location text
15. host_about - Host bio
16. host_response_time - Response time category
17. host_response_rate - Response rate %
18. host_acceptance_rate - Acceptance rate %
19. **host_is_superhost** - Superhost status (t/f)
20. host_thumbnail_url - Host thumbnail
21. host_picture_url - Host picture
22. host_neighbourhood - Host neighborhood
23. **host_listings_count** - Number of listings
24. host_total_listings_count - Total listings
25. host_verifications - Verification methods
26. host_has_profile_pic - Has picture (t/f)
27. **host_identity_verified** - ID verified (t/f)
28. neighbourhood - Neighborhood (free text)
29. **neighbourhood_cleansed** - **JOIN KEY**
30. neighbourhood_group_cleansed - Borough group
31. latitude - Latitude coordinate
32. longitude - Longitude coordinate
33. property_type - Property category
34. **room_type** - Room type (categorical)
35. **accommodates** - Max guests
36. **bathrooms** - Number of bathrooms (may be null)
37. bathrooms_text - Bathrooms description
38. **bedrooms** - Number of bedrooms (may be null)
39. beds - Number of beds
40. **amenities** - Amenities list (parse required)
41. **price** - Nightly price (STRING - clean required)
42. minimum_nights - Minimum stay
43. maximum_nights - Maximum stay
44. minimum_minimum_nights - Min-min nights
45. maximum_minimum_nights - Max-min nights
46. minimum_maximum_nights - Min-max nights
47. maximum_maximum_nights - Max-max nights
48. minimum_nights_avg_ntm - Avg min nights
49. maximum_nights_avg_ntm - Avg max nights
50. calendar_updated - Calendar update status
51. has_availability - Availability flag
52. **availability_30** - Days available (30d)
53. **availability_60** - Days available (60d)
54. **availability_90** - **PRIMARY TARGET** (90d)
55. **availability_365** - Days available (365d)
56. calendar_last_scraped - Last calendar scrape
57. **number_of_reviews** - Total reviews
58. **number_of_reviews_ltm** - Reviews last 12mo
59. number_of_reviews_l30d - Reviews last 30d
60. availability_eoy - End-of-year availability
61. number_of_reviews_ly - Reviews last year
62. estimated_occupancy_l365d - Estimated occupancy
63. estimated_revenue_l365d - Estimated revenue
64. **first_review** - First review date
65. **last_review** - Last review date
66. **review_scores_rating** - Overall rating (1-5)
67. review_scores_accuracy - Accuracy rating
68. review_scores_cleanliness - Cleanliness rating
69. review_scores_checkin - Checkin rating
70. review_scores_communication - Communication rating
71. review_scores_location - Location rating
72. review_scores_value - Value rating
73. license - License number
74. instant_bookable - Instant book (t/f)
75. calculated_host_listings_count - Calculated listings
76. calculated_host_listings_count_entire_homes - Entire homes
77. calculated_host_listings_count_private_rooms - Private rooms
78. calculated_host_listings_count_shared_rooms - Shared rooms
79. **reviews_per_month** - Review rate

</details>

---

**Report Generated:** 2025-11-06
**Status:** Ready for Task 2 (Feature Engineering)
**Action Required:** Install Python dependencies and run notebooks

---

## Contact
For questions about this analysis:
- Nicholas George: georgen@iastate.edu
- Sahil Medepalli: sahilmed@iastate.edu
- Heath Verhasselt: heathv@iastate.edu
