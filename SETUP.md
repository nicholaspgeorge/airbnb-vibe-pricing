# Setup Guide: Vibe-Aware Pricing Engine

Complete setup instructions for running the analysis pipeline.

---

## Quick Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Run data exploration notebook
jupyter notebook 00_data_exploration.ipynb

# 3. Follow the task sequence in CLAUDE.md
```

---

## Prerequisites

### System Requirements
- **Python:** 3.8, 3.9, 3.10, 3.11, or 3.12
- **RAM:** 8GB minimum (16GB recommended for full dataset)
- **Disk Space:** ~1GB for data files and outputs
- **OS:** Windows (WSL), macOS, or Linux

### Software Requirements
- Python with pip
- Jupyter Notebook
- Git (optional, for version control)

---

## Installation Steps

### 1. Verify Python Installation

```bash
python3 --version
# Should show Python 3.8 or higher
```

If Python is not installed:
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **macOS:** `brew install python3`
- **Linux:** `sudo apt-get install python3 python3-pip`

### 2. Install Dependencies

From the project directory:

```bash
# Install all required packages
pip install -r requirements.txt

# Or with pip3 if needed
pip3 install -r requirements.txt

# For specific versions, use:
pip install -r requirements.txt --no-cache-dir
```

**Expected installation time:** 5-10 minutes

### 3. Verify Installation

```bash
python3 -c "import pandas as pd; import numpy as np; import sklearn; print('All packages imported successfully!')"
```

If successful, you should see: `All packages imported successfully!`

---

## Project Structure

```
adv_ba_project/
├── CLAUDE.md                              # Claude Code usage guide
├── AGENTS.md                              # ChatGPT agent definitions
├── DATA_EXPLORATION_REPORT.md             # Data quality findings
├── SETUP.md                               # This file
├── requirements.txt                       # Python dependencies
│
├── listings_London.csv                    # Main data (204MB)
├── 01_neighborhood_vibe_scores.csv        # Vibe scores
├── 01_neighborhood_vibe_dimensions.csv    # Vibe dimensions
├── 01_vibe_features_for_modeling.csv      # Model-ready vibe features
│
├── 00_data_exploration.ipynb              # Task 1: Data exploration
├── 01_feature_engineering.ipynb           # Task 2: Feature engineering (to create)
├── 02_price_bands_neighbors.py            # Task 3: k-NN engine (to create)
├── 03_predictive_model.ipynb              # Task 4: CF model (to create)
├── 04_revenue_optimizer.py                # Task 5: Revenue curves (to create)
├── 05_visualizations.ipynb                # Task 6: Visual deliverables (to create)
│
└── outputs/                               # Generated outputs
    ├── features_london_train.parquet      # Training data
    ├── features_london_test.parquet       # Test data
    ├── price_bands_neighbors.parquet      # k-NN recommendations
    ├── cf_model.pkl                       # Trained model
    └── visualizations/                    # Plots and maps
```

---

## Running the Analysis

### Step 1: Data Exploration

```bash
# Launch Jupyter
jupyter notebook

# Open: 00_data_exploration.ipynb
# Run all cells (Cell → Run All)
```

**Expected outputs:**
- `data_summary.csv` - Dataset overview
- `listings_schema.csv` - Column definitions
- Multiple visualizations in notebook

**Time:** ~5-10 minutes on 189K listings

### Step 2: Feature Engineering

Follow Task 2 in `CLAUDE.md`. Create `01_feature_engineering.ipynb`:

```python
# Key steps:
# 1. Load data
# 2. Clean price field
# 3. Compute occupancy proxies
# 4. Join vibe features
# 5. Handle missing data
# 6. Save train/test splits
```

**Expected outputs:**
- `features_london_train.parquet` (~150K rows)
- `features_london_test.parquet` (~38K rows)

### Step 3-6: Continue with Modeling

Follow the task sequence in `CLAUDE.md` for:
- High-Demand Twins engine
- Predictive model with control function
- Revenue optimization
- Visualizations

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
pip install pandas numpy scikit-learn matplotlib seaborn
```

### Issue: Jupyter Notebook won't start

**Solution:**
```bash
pip install jupyter
jupyter notebook --generate-config
jupyter notebook
```

### Issue: Out of memory when loading CSV

**Solution 1 - Load in chunks:**
```python
chunks = pd.read_csv('listings_London.csv', chunksize=10000)
df = pd.concat([chunk for chunk in chunks], ignore_index=True)
```

**Solution 2 - Use only necessary columns:**
```python
use_cols = ['id', 'neighbourhood_cleansed', 'price', 'availability_90', ...]
df = pd.read_csv('listings_London.csv', usecols=use_cols)
```

**Solution 3 - Sample the data:**
```python
# Use 50% of data
df = pd.read_csv('listings_London.csv', skiprows=lambda i: i > 0 and np.random.rand() > 0.5)
```

### Issue: Parquet files not saving

**Solution:**
```bash
pip install pyarrow
# OR
pip install fastparquet
```

### Issue: Plots not displaying in Jupyter

**Solution:**
```python
# Add to first cell
%matplotlib inline
import matplotlib.pyplot as plt
```

---

## Testing Your Setup

Run this test script to verify everything works:

```python
# test_setup.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

print("✓ All imports successful!")

# Test data loading
df = pd.read_csv('listings_London.csv', nrows=100)
print(f"✓ Loaded {len(df)} rows from listings_London.csv")

# Test vibe data
df_vibe = pd.read_csv('01_vibe_features_for_modeling.csv')
print(f"✓ Loaded {len(df_vibe)} neighborhoods from vibe features")

# Test basic operations
df['price_test'] = df['price'].str.replace('$', '').str.replace(',', '').astype(float)
print(f"✓ Price cleaning works. Sample: ${df['price_test'].iloc[0]:.2f}")

# Test plotting
plt.figure(figsize=(6, 4))
plt.hist(df['price_test'], bins=20)
plt.title("Price Distribution Test")
plt.savefig('test_plot.png')
plt.close()
print("✓ Plotting works. Saved test_plot.png")

print("\n🎉 Setup test PASSED! You're ready to begin analysis.")
```

Save as `test_setup.py` and run:
```bash
python3 test_setup.py
```

---

## Performance Optimization Tips

### For Large Dataset Processing

1. **Use Parquet instead of CSV:**
   ```python
   # One-time conversion
   df = pd.read_csv('listings_London.csv')
   df.to_parquet('listings_London.parquet', compression='snappy')

   # Future loads are 5-10x faster
   df = pd.read_parquet('listings_London.parquet')
   ```

2. **Optimize data types:**
   ```python
   # Reduce memory usage by 50%+
   df['bedrooms'] = df['bedrooms'].astype('int8')  # instead of int64
   df['accommodates'] = df['accommodates'].astype('int8')
   df['room_type'] = df['room_type'].astype('category')
   ```

3. **Use vectorized operations:**
   ```python
   # Fast
   df['occ_90'] = 1 - (df['availability_90'] / 90)

   # Slow (avoid)
   df['occ_90'] = df.apply(lambda row: 1 - (row['availability_90'] / 90), axis=1)
   ```

4. **Parallel processing:**
   ```python
   from joblib import Parallel, delayed

   # For slow operations
   results = Parallel(n_jobs=-1)(
       delayed(process_listing)(listing)
       for listing in df.itertuples()
   )
   ```

---

## Getting Help

### Documentation Resources
- **Pandas:** https://pandas.pydata.org/docs/
- **Scikit-learn:** https://scikit-learn.org/stable/documentation.html
- **XGBoost:** https://xgboost.readthedocs.io/
- **SHAP:** https://shap.readthedocs.io/
- **Inside Airbnb:** http://insideairbnb.com/get-the-data.html

### Project-Specific Help

1. **Read the guides:**
   - `CLAUDE.md` - Detailed prompts for each task
   - `DATA_EXPLORATION_REPORT.md` - Data quality findings
   - `AGENTS.md` - Alternative task definitions

2. **Check existing outputs:**
   - Run `00_data_exploration.ipynb` to see expected patterns
   - Review sample outputs in `/outputs/` directory

3. **Ask Claude for help:**
   ```
   "I'm getting error X when trying to Y. Here's my code: [paste code].
   Can you help me debug and fix it?"
   ```

### Team Contact
- **Nicholas George:** georgen@iastate.edu (Data & Vibe Engineering)
- **Sahil Medepalli:** sahilmed@iastate.edu (Modeling & Control Functions)
- **Heath Verhasselt:** heathv@iastate.edu (Visuals & Documentation)

---

## Development Workflow

### Recommended Approach

1. **Explore First:** Run `00_data_exploration.ipynb` to understand the data
2. **Plan Your Task:** Read the relevant section in `CLAUDE.md`
3. **Prototype in Notebook:** Test code interactively
4. **Productionize:** Convert working code to `.py` scripts
5. **Version Control:** Commit working code frequently

### Code Quality Checklist

Before moving to next task:
- [ ] Code runs without errors
- [ ] Expected outputs are generated
- [ ] Validation checks pass
- [ ] Code is documented (docstrings and comments)
- [ ] Plots have clear labels and titles
- [ ] Files are saved with proper naming convention

---

## Next Steps

1. ✅ Complete setup (you are here)
2. Run `00_data_exploration.ipynb`
3. Review `DATA_EXPLORATION_REPORT.md`
4. Proceed to Task 2: Feature Engineering
5. Follow task sequence in `CLAUDE.md`

---

## Appendix: Full Dependency List

### Core Libraries
```
pandas>=2.0.0           # Data manipulation
numpy>=1.24.0           # Numerical computing
scipy>=1.10.0           # Scientific computing
```

### Machine Learning
```
scikit-learn>=1.3.0     # ML algorithms
xgboost>=2.0.0          # Gradient boosting
lightgbm>=4.0.0         # Gradient boosting (alternative)
shap>=0.42.0            # Model interpretation
```

### Visualization
```
matplotlib>=3.7.0       # Plotting
seaborn>=0.12.0         # Statistical plots
plotly>=5.14.0          # Interactive plots
folium>=0.14.0          # Maps
```

### Data I/O
```
pyarrow>=12.0.0         # Parquet support
```

### Development
```
jupyter>=1.0.0          # Notebooks
ipykernel>=6.23.0       # Kernel for notebooks
tqdm>=4.65.0            # Progress bars
```

### Optional
```
streamlit>=1.25.0       # For interactive dashboard
geopandas>=0.13.0       # For advanced geo operations
```

---

**Setup Guide Version:** 1.0
**Last Updated:** 2025-11-06
**Project Deadline:** 2025-11-17

Good luck with your analysis! 🚀
