# Vibe Score Generation - Quick Start Guide

**Purpose:** Generate neighborhood vibe scores for any city using review text analysis

**Time:** ~10-15 minutes per city

---

## Prerequisites

1. **Virtual environment activated:**
   ```bash
   source venv/bin/activate
   ```

2. **Dependencies installed:**
   ```bash
   pip install textblob
   python -m textblob.download_corpora
   ```

3. **Data files in place:**
   ```
   data/{city}/raw/
   ├── listings_{City}.csv
   ├── reviews_{City}.csv
   └── neighbourhoods_{City}.csv
   ```

---

## Method 1: Use Pre-Configured Scripts (Recommended)

### For NYC:
```bash
python scripts/01_vibe_score_generator_nyc.py
```

### For Austin:
```bash
python scripts/01_vibe_score_generator.py
# (Currently configured for Austin)
```

### For London:
London vibe scores already exist in `data/london/raw/01_*.csv`

---

## Method 2: Configure Generic Script

**Edit `scripts/01_vibe_score_generator.py` line 25:**

```python
CITY = 'nyc'  # Change to: 'london', 'nyc', or 'austin'
```

**Then run:**
```bash
python scripts/01_vibe_score_generator.py
```

---

## Expected Output

### Console Output:
```
================================================================================
VIBE SCORE GENERATOR - {CITY}
================================================================================

[1/9] Loading datasets...
[2/9] Preparing data...
[3/9] Preprocessing review texts...
[4/9] Analyzing sentiment...          ← ~5-8 min (100K reviews)
[5/9] Extracting latent topics...     ← ~3-5 min (LDA training)
[6/9] Extracting aspect-based sentiments...  ← ~2-3 min
[7/9] Aggregating to neighborhood level...
[8/9] Calculating vibe scores...
[9/9] Generating insights and saving outputs...

VIBE SCORE GENERATION COMPLETE - {CITY} ✅
```

### Files Created:
```
data/{city}/raw/
├── 01_neighborhood_vibe_scores.csv       ← Summary scores
├── 01_neighborhood_vibe_dimensions.csv   ← Detailed dimensions
└── 01_vibe_features_for_modeling.csv     ← Model-ready features
```

---

## Verify Success

### Check files exist:
```bash
ls -lh data/{city}/raw/01_*.csv
```

**Expected:** 3 CSV files

### Check neighborhood count:
```bash
wc -l data/{city}/raw/01_neighborhood_vibe_scores.csv
```

**Expected:** Number of neighborhoods + 1 header

### Quick peek at scores:
```bash
head -10 data/{city}/raw/01_neighborhood_vibe_scores.csv | column -t -s','
```

**Expected:** Neighborhoods with vibe scores (0-100 range)

---

## Troubleshooting

### Error: "No module named 'textblob'"
```bash
source venv/bin/activate
pip install textblob
python -m textblob.download_corpora
```

### Error: "FileNotFoundError: listings_{City}.csv"
- Check file naming: Must be `listings_NYC.csv` (capital C)
- Verify location: `data/{city}/raw/`
- Use `ls data/{city}/raw/` to confirm

### Script hangs at "Training LDA model"
- **Normal!** LDA takes 3-5 minutes for 100K reviews
- Be patient - you'll see "✓ Topic modeling complete" when done

### Warning: "Sampling 100,000 reviews for analysis"
- **Normal!** This is for performance (prevents 10+ hour runs)
- 100K sample is statistically sufficient for neighborhood aggregation

---

## Performance Notes

### By City:

| City | Reviews | Neighborhoods | Processing Time |
|------|---------|--------------|----------------|
| **London** | 2,019,207 | 33 | ~12 min |
| **Austin** | 670,923 | 43 | ~10 min |
| **NYC** | ~1,000,000+ | ~50+ | ~15 min (est) |

**Bottleneck:** Sentiment analysis (Step 4) and LDA training (Step 5)

---

## Understanding the Outputs

### 1. `01_neighborhood_vibe_scores.csv`
**Purpose:** High-level summary for stakeholder presentation

**Columns:**
- `neighbourhood` - Neighborhood name
- `vibe_score` - Overall vibe (0-100)
- `characteristics` - Top 3 aspects (e.g., "excellent food scene, good safety")
- `sentiment` - Mean sentiment polarity
- `sentiment_category` - Category (Very Positive, Positive, etc.)
- `review_count` - Number of reviews analyzed

**Usage:** Quick neighborhood ranking, presentation slides

---

### 2. `01_neighborhood_vibe_dimensions.csv`
**Purpose:** Detailed breakdown by aspect

**Columns:**
- `neighbourhood`
- `vibe_score`
- `review_count`
- `walkability_score`
- `safety_score`
- `nightlife_score`
- `quietness_score`
- `family_friendly_score`
- `local_authentic_score`
- `convenience_score`
- `food_scene_score`
- `liveliness_score`
- `charm_score`

**Usage:** Aspect-specific analysis, visualizations

---

### 3. `01_vibe_features_for_modeling.csv`
**Purpose:** Input features for predictive models

**Columns:**
- All from dimensions file above
- `sentiment_mean` - Average polarity
- `sentiment_std` - Sentiment consistency
- `subjectivity` - Subjectivity level
- `avg_review_length` - Mean words per review

**Usage:** Merge with listings data for modeling (Tasks 2-6)

---

## Next Steps After Vibe Generation

### 1. Data Exploration (Task 1)
```bash
# Edit scripts/run_data_exploration.py
# Change: CITY = 'austin'  (or 'nyc')
python scripts/run_data_exploration.py
```

### 2. Feature Engineering (Task 2)
```bash
# Edit scripts/02_feature_engineering.py
# Change: CITY = 'austin'
python scripts/02_feature_engineering.py
```

### 3. Continue Tasks 3-6
See `MULTI_CITY_EXPANSION.md` for full pipeline details

---

## Comparing Cities

### After all cities complete, compare:

```bash
# London
head -6 data/london/raw/01_neighborhood_vibe_scores.csv

# Austin
head -6 data/austin/raw/01_neighborhood_vibe_scores.csv

# NYC
head -6 data/nyc/raw/01_neighborhood_vibe_scores.csv
```

### Create comparison table:
```python
import pandas as pd

london = pd.read_csv('data/london/raw/01_neighborhood_vibe_scores.csv')
austin = pd.read_csv('data/austin/raw/01_neighborhood_vibe_scores.csv')
nyc = pd.read_csv('data/nyc/raw/01_neighborhood_vibe_scores.csv')

print(f"London: {len(london)} neighborhoods, mean vibe: {london['vibe_score'].mean():.1f}")
print(f"Austin: {len(austin)} neighborhoods, mean vibe: {austin['vibe_score'].mean():.1f}")
print(f"NYC: {len(nyc)} neighborhoods, mean vibe: {nyc['vibe_score'].mean():.1f}")
```

---

## FAQ

**Q: Why sample 100K reviews instead of using all?**
A: Performance. Sentiment analysis on 2M+ reviews would take 10+ hours. 100K is statistically sufficient for neighborhood-level aggregation.

**Q: Can I change the sample size?**
A: Yes! Edit line 26 in the script: `SAMPLE_SIZE = 200000` (or any number)

**Q: Are vibe scores comparable across cities?**
A: Yes - they use percentile ranking within each city, so scores are relative. A 75 in London vs 75 in Austin both mean "top 25% of neighborhoods in that city."

**Q: What if I have new review data?**
A: Re-run the script with updated `reviews_{City}.csv` file. Vibe scores will automatically recalculate.

**Q: Can I customize aspect weights?**
A: Yes! Edit line ~350 in the script (`BASE_WEIGHTS` dictionary). Current weights are based on empirical importance.

---

## Technical Details

**Sentiment Analysis:** TextBlob (Python library)
- Polarity: -1 (negative) to +1 (positive)
- Subjectivity: 0 (objective) to 1 (subjective)

**Topic Modeling:** LDA (Latent Dirichlet Allocation)
- 10 topics extracted from TF-IDF matrix
- 1000 max features, 1-2 word n-grams

**Aspect Extraction:** Keyword-based with context windows
- 5-word context before/after keyword
- Sentiment of context assigned to aspect

**Vibe Score Formula:**
```
vibe_score = (
    (weighted_dimension_score * 0.6 + sentiment_score * 0.4) *
    confidence *
    (0.8 + consistency * 0.2)
) * 10
```

---

## Contact

**Issues:** See `MULTI_CITY_EXPANSION.md` for detailed troubleshooting

**Updates:** Check `README.md` for multi-city status

**Methodology:** See `METHODOLOGY.md` for full approach details

---

**Last Updated:** 2025-11-08
**Version:** 1.0 (Multi-City)
