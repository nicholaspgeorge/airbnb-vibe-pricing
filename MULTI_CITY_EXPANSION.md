# Multi-City Expansion - Vibe Score Generation

**Date:** 2025-11-08
**Status:** 🚀 **IN PROGRESS - Austin Running, NYC Queued**

---

## Overview

This document tracks the expansion of the Vibe-Aware Pricing Engine to multiple cities. The original analysis was performed on **London**, and we are now replicating the vibe score generation process for **NYC** and **Austin**.

---

## Vibe Score Generation Process

### Original Source
- **File:** `vibescore.ipynb` (Jupyter notebook)
- **Created:** London vibe scores using review text analysis
- **Outputs:** 3 CSV files per city

### Conversion to Python Script
- **New File:** `scripts/01_vibe_score_generator.py`
- **Changes:** Minimal - only parameterized for multi-city compatibility
- **Approach:** Exact same methodology as original notebook

---

## Methodology (Same Across All Cities)

### Step 1: Data Loading
- **Inputs:**
  - `listings_{City}.csv` - Property listings
  - `reviews_{City}.csv` - Guest review text
  - `neighbourhoods_{City}.csv` - Neighborhood list

### Step 2: Text Preprocessing
- Clean review text (remove URLs, punctuation, numbers)
- Filter to reviews with ≥5 words
- Sample 100,000 reviews if dataset is larger (for performance)

### Step 3: Sentiment Analysis
- **Tool:** TextBlob (Python library)
- **Metrics:**
  - Polarity: -1 (negative) to +1 (positive)
  - Subjectivity: 0 (objective) to 1 (subjective)
- **Applied to:** Original review text (not over-cleaned)

### Step 4: Topic Modeling
- **Method:** Latent Dirichlet Allocation (LDA)
- **Features:** TF-IDF matrix (1000 max features, 1-2 n-grams)
- **Topics:** 10 latent topics extracted
- **Output:** Probability distribution over topics for each review

### Step 5: Aspect-Based Sentiment Extraction
**10 Vibe Dimensions:**

| Aspect | Keywords |
|--------|----------|
| walkability | walk, walking, walkable, foot, steps, distance |
| safety | safe, secure, safety, dangerous, unsafe, worried |
| nightlife | nightlife, bars, clubs, party, pub, drinks |
| quietness | quiet, peaceful, calm, noisy, loud, noise |
| family_friendly | family, kids, children, child, playground |
| local_authentic | local, authentic, traditional, touristy, tourist |
| convenience | convenient, close, near, metro, tram, transport |
| food_scene | restaurant, food, cafe, coffee, dining, eat |
| liveliness | lively, vibrant, busy, bustling, energetic, dead |
| charm | charming, beautiful, lovely, pretty, ugly, attractive |

**Method:**
- For each aspect keyword mention, extract 5-word context window
- Calculate sentiment of context using TextBlob
- Aggregate sentiment for each aspect per review

### Step 6: Neighborhood-Level Aggregation
- Group reviews by neighborhood
- Aggregate metrics:
  - Mean sentiment polarity/subjectivity
  - Aspect sentiment means
  - Aspect mention counts
  - Topic probability distributions
  - Review count per neighborhood

### Step 7: Vibe Score Calculation

**Formula:**
```
vibe_score = (
    (weighted_dimension_score * 0.6 + sentiment_score * 0.4) *
    confidence *
    (0.8 + consistency * 0.2)
) * 10
```

**Where:**
- `weighted_dimension_score` = Percentile-ranked aspect scores with weights:
  - Safety: 25%
  - Convenience: 20%
  - Walkability: 15%
  - Charm: 10%
  - Local authentic: 10%
  - Food scene: 8%
  - Liveliness: 5%
  - Quietness: 3%
  - Nightlife: 2%
  - Family friendly: 2%

- `sentiment_score` = Percentile-ranked overall sentiment
- `confidence` = Review volume relative to median (clipped 0.5-1.5x)
- `consistency` = 1 - (normalized sentiment std)

**Scale:** 0-100 (higher = better neighborhood vibe)

### Step 8: Insights Generation
- Identify top 3 characteristics per neighborhood
- Classify sentiment categories (Very Positive → Very Negative)
- Generate human-readable descriptions

### Step 9: Save Outputs

**3 CSV Files Generated Per City:**

1. **`01_neighborhood_vibe_scores.csv`**
   - Columns: neighbourhood, vibe_score, characteristics, sentiment, sentiment_category, review_count
   - Use: High-level summary for stakeholder presentation

2. **`01_neighborhood_vibe_dimensions.csv`**
   - Columns: neighbourhood, vibe_score, review_count, 10 aspect scores
   - Use: Detailed breakdown of vibe dimensions

3. **`01_vibe_features_for_modeling.csv`**
   - Columns: neighbourhood, vibe_score, sentiment stats, 10 aspect scores
   - Use: Input features for predictive models

---

## City-Specific Execution

### London ✅ (Already Complete)

**Data:**
- Listings: 96,651 records
- Reviews: 2,019,207 records
- Neighborhoods: 33

**Results:**
- Vibe score range: 15.1 - 83.3
- Mean: 42.0
- Top neighborhood: Kensington and Chelsea (83.3)
- Bottom neighborhood: Redbridge (15.1)

**Outputs:**
- `data/london/raw/01_neighborhood_vibe_scores.csv`
- `data/london/raw/01_neighborhood_vibe_dimensions.csv`
- `data/london/raw/01_vibe_features_for_modeling.csv`

**Status:** ✅ Complete (used in all Tasks 1-6)

---

### Austin ✅ (Complete)

**Data:**
- Listings: 15,187 records
- Reviews: 670,923 records
- Neighborhoods: 43

**Results:**
- Vibe score range: 6.7 - 100.0
- Mean: 48.9 (vs London: 42.0) → Austin +16% more positive!
- Sentiment polarity: 0.437 (vs London: 0.354) → Austin +23% more positive
- Top aspect: Food Scene (91,138 mentions)

**Top 5 Neighborhoods:**
1. **78703** (100.0) - Excellent walkability, food scene, nightlife
2. **78704** (100.0) - Excellent convenience, walkability, food scene
3. **78701** (94.6) - Excellent food scene, walkability, nightlife
4. **78702** (93.2) - Excellent nightlife, food scene, convenience
5. **78756** (82.7) - Excellent food scene, walkability, convenience

**Outputs:**
- ✅ `data/austin/raw/01_neighborhood_vibe_scores.csv` (4.3K)
- ✅ `data/austin/raw/01_neighborhood_vibe_dimensions.csv` (8.3K)
- ✅ `data/austin/raw/01_vibe_features_for_modeling.csv` (12K)

**Status:** ✅ Complete (Time: 13 minutes)

---

### NYC ⏳ (Queued)

**Data Available:**
- `data/nyc/raw/listings_NYC.csv` (71M)
- `data/nyc/raw/reviews_NYC.csv` (296M)
- `data/nyc/raw/neighbourhoods_NYC.csv` (4.9K)

**Status:** ⏳ Queued (will run after Austin completes)

**Expected Outputs:**
- `data/nyc/raw/01_neighborhood_vibe_scores.csv`
- `data/nyc/raw/01_neighborhood_vibe_dimensions.csv`
- `data/nyc/raw/01_vibe_features_for_modeling.csv`

**Estimated Time:** 10-15 minutes

---

## Running Vibe Score Generation for New Cities

### Prerequisites
1. **Data files in place:**
   ```
   data/{city}/raw/
   ├── listings_{City}.csv
   ├── reviews_{City}.csv
   └── neighbourhoods_{City}.csv
   ```

2. **Virtual environment activated:**
   ```bash
   source venv/bin/activate
   ```

3. **TextBlob installed:**
   ```bash
   pip install textblob
   python -m textblob.download_corpora
   ```

### Execution

**Edit `scripts/01_vibe_score_generator.py`:**
```python
# Line 25: Change city name
CITY = 'austin'  # or 'nyc', 'london'
```

**Run script:**
```bash
python scripts/01_vibe_score_generator.py
```

**Monitor progress:**
- Step 1-3: Data loading and preprocessing (~1 min)
- Step 4: Sentiment analysis (~5-8 min for 100K reviews)
- Step 5: Topic modeling (~1-2 min)
- Step 6: Aspect extraction (~2-3 min)
- Step 7-9: Aggregation and saving (~30 sec)

**Total:** ~10-15 minutes per city

---

## Validation Checks

After vibe score generation, verify:

### 1. File Existence
```bash
ls -lh data/{city}/raw/01_*.csv
```
**Expected:** 3 CSV files

### 2. Neighborhood Coverage
```bash
wc -l data/{city}/raw/01_neighborhood_vibe_scores.csv
```
**Expected:** Number of unique neighborhoods + 1 header row

### 3. Vibe Score Distribution
```bash
# Check for reasonable range (0-100)
# Check for variation (not all same score)
# Check for no nulls
```

### 4. Aspect Score Coverage
```bash
# Verify all 10 aspects have scores
# Check aspect mention counts > 0
```

### 5. Compare with London
```bash
# London: 33 neighborhoods, range 15.1-83.3, mean 42.0
# Austin: ? neighborhoods, range ?, mean ?
# NYC: ? neighborhoods, range ?, mean ?
```

---

## Cross-City Comparison (After All Cities Complete)

### Vibe Score Statistics

| City | Neighborhoods | Min | Max | Mean | Std | Median |
|------|--------------|-----|-----|------|-----|--------|
| **London** | 33 | 15.1 | 83.3 | 42.0 | 20.1 | 41.2 |
| **Austin** | 43 | 6.7 | 100.0 | 48.9 | 26.9 | 46.1 |
| **NYC** | ? | ? | ? | ? | ? | ? |

### Top Aspect by City

| City | Top Mentioned Aspect | Top Scored Aspect |
|------|---------------------|------------------|
| **London** | Food Scene (67,828) | ? |
| **Austin** | ? | ? |
| **NYC** | ? | ? |

### Sentiment Distribution

| City | Mean Polarity | Mean Subjectivity | % Positive |
|------|--------------|------------------|------------|
| **London** | 0.354 | 0.550 | 83.7% |
| **Austin** | 0.437 | 0.643 | 95.6% |
| **NYC** | ? | ? | ? |

**Key Insight:** Austin guests are significantly happier (+23%) and more expressive (+17%) than London guests!

---

## Next Steps After Vibe Generation

### For Each City:

1. **Data Exploration** (Task 1)
   - Run `scripts/run_data_exploration.py` (update CITY variable)
   - Generate visualizations

2. **Feature Engineering** (Task 2)
   - Run `scripts/02_feature_engineering.py`
   - Create train/test split

3. **k-NN Pricing** (Task 3)
   - Run `scripts/03_high_demand_twins_knn.py`
   - Generate price band recommendations

4. **Predictive Models** (Task 4)
   - Run `scripts/04_predictive_model_control_function.py`
   - Train XGBoost/LightGBM/RandomForest
   - Verify vibe importance %

5. **Revenue Optimization** (Task 5)
   - Run `scripts/05_revenue_optimizer.py`
   - Generate revenue curves

6. **Interactive Visualizations** (Task 6)
   - Run `scripts/06a_interactive_vibe_map.py`
   - Run `scripts/06b_interactive_revenue_curves.py`
   - Run `scripts/06c_presentation_visuals.py`

---

## Comparative Analysis (Future)

Once all cities complete, create:

### 1. Cross-City Model Comparison
- Does vibe importance vary by city?
- Are some cities more vibe-sensitive?
- Do weights need to be city-specific?

### 2. Market Opportunity Comparison
- Revenue lift % by city
- Total opportunity size
- Pricing efficiency differences

### 3. Vibe Dimension Comparison
- Which aspects matter most in each city?
- Cultural differences (e.g., Austin nightlife vs London safety)
- Aspect mention frequency variations

### 4. Pricing Dynamics
- Price-vibe correlation by city
- Optimal price ranges
- Market maturity indicators

---

## Documentation Updates Required

### Files to Update After Each City:

1. **README.md**
   - Add city completion status
   - Update data structure section

2. **METHODOLOGY.md**
   - Add city-specific statistics
   - Update comparison tables

3. **City-Specific Summaries**
   - Create `AUSTIN_COMPLETION_SUMMARY.md`
   - Create `NYC_COMPLETION_SUMMARY.md`

4. **Requirements.txt**
   - Add TextBlob and nltk
   - Document corpora download requirement

---

## Known Differences from London Notebook

### Changes Made to Python Script:

1. **Parameterized city name:**
   - Variable: `CITY = 'austin'`
   - Easy to change for each city

2. **Dynamic file paths:**
   - Uses `Path` for cross-platform compatibility
   - Reads from `data/{city}/raw/`
   - Saves to `data/{city}/raw/`

3. **Auto-capitalization:**
   - File names: `listings_Austin.csv` (not `listings_austin.csv`)
   - City display: "AUSTIN" in headers

4. **Structured logging:**
   - Progress messages for each step
   - Summary statistics at end

5. **No changes to methodology:**
   - Same preprocessing
   - Same sentiment analysis
   - Same LDA parameters
   - Same aspect keywords
   - Same scoring formula
   - **100% identical to London approach**

---

## Success Criteria

### Per City:
- [x] Vibe scores generated for all neighborhoods
- [x] All 3 CSV files created
- [x] Scores in 0-100 range
- [x] No null values in critical columns
- [x] Variation in scores (not all identical)
- [x] Top aspects identified for each neighborhood

### Cross-City:
- [ ] Austin vibe scores complete
- [ ] NYC vibe scores complete
- [ ] Comparison analysis created
- [ ] Documentation updated
- [ ] Ready to run full pipeline on all cities

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| **London** (original) | N/A | ✅ Complete |
| **Austin vibe generation** | 15 min | 🔄 In progress |
| **NYC vibe generation** | 15 min | ⏳ Queued |
| **Documentation updates** | 30 min | 🔄 In progress |
| **Austin full pipeline (Tasks 1-6)** | 2-3 hours | ⏳ Queued |
| **NYC full pipeline (Tasks 1-6)** | 2-3 hours | ⏳ Queued |
| **Comparative analysis** | 1-2 hours | ⏳ Queued |

**Total Estimated Time:** 6-9 hours for full multi-city expansion

---

## Files Modified/Created

### New Files (1 script)
1. `scripts/01_vibe_score_generator.py` (multi-city compatible)

### New Documentation (1)
1. `MULTI_CITY_EXPANSION.md` (this file)

### Files to be Created
1. `AUSTIN_COMPLETION_SUMMARY.md` (after Austin pipeline complete)
2. `NYC_COMPLETION_SUMMARY.md` (after NYC pipeline complete)
3. `COMPARATIVE_ANALYSIS.md` (after all cities complete)

### Files to be Updated
1. `README.md` - Add multi-city status
2. `METHODOLOGY.md` - Add cross-city comparisons
3. `requirements.txt` - Add TextBlob

---

## Current Status Summary

**Date:** 2025-11-08, 4:17 PM

**Completed:**
- ✅ Analyzed original `vibescore.ipynb` notebook
- ✅ Created multi-city Python script (`01_vibe_score_generator.py`)
- ✅ Installed TextBlob and NLTK corpora
- ✅ Started Austin vibe generation (running in background)
- ✅ Created comprehensive documentation

**In Progress:**
- 🔄 Austin vibe score generation (Step 4/9: Sentiment analysis)
- 🔄 Documentation updates

**Next:**
- ⏳ Complete Austin vibe generation
- ⏳ Run NYC vibe generation
- ⏳ Update all project documentation
- ⏳ Begin Austin full pipeline (Tasks 1-6)

---

**Status:** 🚀 **EXPANSION IN PROGRESS - 50% COMPLETE**

**Austin Vibe Generation:** Running (ETA: ~10 minutes)
**NYC Vibe Generation:** Queued (ETA: ~15 minutes after Austin)
**Full Multi-City Deployment:** On track for completion within 1 day
