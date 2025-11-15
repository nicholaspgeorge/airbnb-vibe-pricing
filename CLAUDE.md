# CLAUDE.md - Updated from Real Project Experience

A practical guide for using **Claude Code** to build the Vibe-Aware Pricing Engine from raw Inside Airbnb data to a production-ready pricing recommendation system. This guide is updated based on actual project experience (Nov 2025) and leverages Claude's strengths in analytical thinking, code generation, and systematic problem-solving.

---

## 0) Working with Claude Code: What We Learned

### Claude's Strengths (Proven in Practice)
- **Proactive exploration**: Claude analyzed 189K listings before writing any code
- **Environment troubleshooting**: Solved WSL/pip issues and created virtual environment
- **Systematic organization**: Proposed and implemented multi-city folder structure
- **Documentation-first**: Created METHODOLOGY.md to track all decisions
- **Parallel processing**: Read multiple files simultaneously for faster analysis
- **Error handling**: Built production-ready scripts with proper error messages

### What Works Best
1. **Start with exploration, not coding**: Let Claude understand your data first
2. **Request planning**: Claude will auto-create todos for complex tasks
3. **Ask "why" questions**: Get reasoning, not just solutions
4. **Iterate on structure**: Claude helped reorganize project mid-stream
5. **Document decisions**: METHODOLOGY.md captures all choices for writeup

### Key Difference from ChatGPT/Codex
- **Context retention**: Claude remembered project details across long session
- **Proactive planning**: Created folder structure without being asked
- **Environment aware**: Detected WSL, suggested venv, troubleshot pip
- **Production focus**: All code includes error handling and validation
- **Documentation**: Generated README, SETUP, METHODOLOGY automatically

---

## 1) Project Overview

**Goal:** Build a Vibe-Aware Pricing system that recommends optimal Airbnb prices by combining listing features with engineered Neighborhood Vibe Scores.

**Team:** Nicholas George, Sahil Medepalli, Heath Verhasselt
**Course:** MIS5460 Fall 2025
**Deadline:** November 17, 2025

**Current Status (as of 2025-11-06):**
- ✅ Task 1 Complete: Data exploration (London, 96,871 listings)
- ✅ Project structure organized for multi-city analysis
- ✅ Virtual environment set up with all dependencies
- ✅ METHODOLOGY.md tracks all decisions
- → Ready for Task 2: Feature Engineering

**Key Innovation:** Quantifying the subjective "neighborhood vibe" from review text and proving its economic impact on rental revenue.

---

## 2) Project Structure (Multi-City Ready)

```
adv_ba_project/
├── README.md                          # Project overview
├── CLAUDE.md                          # This guide (updated)
├── METHODOLOGY.md                     # Tracks all analytical decisions ⭐ NEW
├── PROJECT_STRUCTURE.md               # Detailed structure docs
├── requirements.txt                   # Python dependencies
├── venv/                              # Virtual environment
│
├── docs/                              # Documentation
│   ├── MIS5460_Project_Proposal_Group_1.pdf
│   ├── Inside Airbnb Data Dictionary.xlsx
│   └── Data Assumptions _ Inside Airbnb.html
│
├── notebooks/                         # Jupyter notebooks
│   └── 00_data_exploration.ipynb
│
├── scripts/                           # Reusable scripts
│   ├── run_data_exploration.py       # Multi-city compatible ⭐
│   └── (future: feature_engineering.py, etc.)
│
└── data/                              # City-specific data ⭐ NEW STRUCTURE
    ├── london/                        # 🇬🇧 London
    │   ├── raw/                       # Original data
    │   │   ├── listings_London.csv
    │   │   └── 01_vibe_*.csv
    │   ├── processed/                 # Engineered features
    │   ├── models/                    # Trained models
    │   └── outputs/                   # Results
    │       ├── visualizations/        # Generated plots
    │       ├── reports/               # CSV summaries
    │       └── recommendations/       # Price bands
    │
    ├── nyc/                           # 🇺🇸 NYC (future)
    └── austin/                        # 🇺🇸 Austin (future)
```

**Why This Structure:**
- Scalable: Easy to add new cities
- Organized: Raw → Processed → Models → Outputs pipeline clear
- Team-friendly: Multiple people can work on different cities
- Git-friendly: City-specific work isolated

---

## 3) Environment Setup (Lessons Learned)

### 3.1 The Virtual Environment Approach

**What We Discovered:**
- Modern Python (3.12+) in WSL uses `externally-managed-environment` protection
- Direct `pip install` is blocked to prevent system corruption
- **Solution**: Use virtual environments (venv)

### 3.2 Correct Setup Process

```bash
# 1. Create virtual environment (one-time)
python3 -m venv venv

# 2. Activate it (every session)
source venv/bin/activate

# 3. Install packages
pip install pandas numpy matplotlib seaborn scikit-learn jupyter
pip install xgboost shap plotly pyarrow

# 4. Verify
python -c "import pandas; print('✓ Success!')"
```

### 3.3 Quick Activation Helper

We created `activate_env.sh`:
```bash
source activate_env.sh
# Shows: ✓ Virtual environment activated!
```

### 3.4 Common Pitfalls Avoided

❌ **Don't do this:**
```bash
pip3 install pandas  # Without venv - gets blocked
sudo pip install pandas  # System pollution
pip install --user pandas  # WSL/Windows PATH confusion
```

✅ **Do this:**
```bash
source venv/bin/activate  # Always activate first
pip install pandas  # Then install
```

---

## 4) Actual Task 1 Workflow (What We Did)

### Step 1: Initial Exploration (No Code Yet)

**Prompt Used:**
```
"Analyze all CSV files in this directory. For the listings_London.csv:
1. Show me the schema and data types
2. Compute missing data percentages for all columns
3. Check price field distribution and identify anomalies
4. Verify how the vibe features can be joined to listings
5. Suggest data cleaning steps before modeling"
```

**Claude's Response:**
- Read 4 files in parallel (listings + 3 vibe files)
- Identified 189K rows, 79 columns
- Found price field issues (string with $ and commas)
- Validated join compatibility (100% match rate)
- Created comprehensive DATA_EXPLORATION_REPORT.md

**Time Saved:** Would have taken hours manually; Claude did it in minutes

### Step 2: Environment Setup

**Challenge:** pip not working in WSL

**Prompt Used:**
```
"I tried running pip install and got 'externally-managed-environment' error.
Help me set up a virtual environment and install packages."
```

**Claude's Actions:**
1. Created virtual environment: `python3 -m venv venv`
2. Activated it: `source venv/bin/activate`
3. Installed all packages
4. Verified with test script
5. Created `activate_env.sh` helper for future use

### Step 3: Running Data Exploration

**Script Created:** `scripts/run_data_exploration.py`

**Key Features Claude Built In:**
- Multi-city compatible (change `CITY = 'london'` to analyze NYC, Austin)
- Automatic directory creation
- Comprehensive error handling
- Progress messages throughout
- Saves all outputs to organized folders

**Results Generated:**
- 5 visualizations (price, occupancy, missing data, vibes, properties)
- 2 summary CSVs (stats and schema)
- All in `data/london/outputs/`

### Step 4: Project Reorganization

**User Request:**
```
"Help me update the organization. I want London data in its own folder
since we'll analyze more cities."
```

**Claude's Response:**
- Proposed complete multi-city structure
- Created all necessary folders
- Moved files intelligently
- Updated scripts to use new paths
- Generated PROJECT_STRUCTURE.md documentation
- Created README.md with new structure

**Insight:** Claude understood the future scaling needs and designed accordingly

### Step 5: Documentation

**Unprompted Actions by Claude:**
- Created DATA_EXPLORATION_REPORT.md (15 pages)
- Generated SETUP.md with troubleshooting
- Built PROJECT_STRUCTURE.md
- Wrote comprehensive README.md
- All before being asked!

**When Prompted:**
- Created METHODOLOGY.md to track all analytical decisions
- This becomes the basis for the Methods section in final report

---

## 5) Recommended Prompting Patterns (Battle-Tested)

### 5.1 Exploration Pattern

**When to use:** Starting any new analysis task

**Template:**
```
"Explore [data/code/folder] and give me:
1. [Specific thing to analyze]
2. [Another specific thing]
3. Key findings and issues
4. Recommendations for next steps"
```

**Real Example:**
```
"Explore the listings_London.csv file and give me:
1. Schema and data types
2. Missing data patterns
3. Price distribution and anomalies
4. How to join vibe features
5. Cleaning recommendations"
```

**Claude Will:**
- Read files in parallel
- Provide structured summary
- Flag issues proactively
- Suggest concrete next steps

### 5.2 Implementation Pattern

**When to use:** Building code after exploration

**Template:**
```
"Create [script/notebook] that:
1. [Specific functionality]
2. [Another functionality]
3. [Error handling requirements]
4. [Output requirements]

Use best practices: [list key requirements]"
```

**Real Example:**
```
"Create a Python script 'run_data_exploration.py' that:
1. Loads data from data/{city}/raw/
2. Cleans price field and computes occupancy proxies
3. Generates 5 key visualizations
4. Saves outputs to data/{city}/outputs/
5. Works for any city by changing one variable

Use best practices: error handling, progress messages, documentation"
```

**Claude Will:**
- Write production-ready code
- Include error handling
- Add helpful comments
- Create reusable, parameterized code

### 5.3 Debugging Pattern

**When to use:** Something isn't working

**Template:**
```
"I'm getting error: [paste error]

Context:
- I'm trying to: [what you're doing]
- Environment: [OS, Python version, etc.]
- What I've tried: [your attempts]

Can you:
1. Diagnose the issue
2. Explain why it's happening
3. Provide the fix
4. Suggest how to prevent it"
```

**Real Example:**
```
"I'm getting 'externally-managed-environment' error when running pip.

Context:
- WSL on Windows
- Python 3.12
- Trying to install pandas

What should I do?"
```

**Claude Will:**
- Explain the root cause
- Provide immediate fix (venv)
- Give prevention tips
- Create helper scripts

### 5.4 Organizational Pattern

**When to use:** Need to restructure or organize

**Template:**
```
"Help me reorganize [project/code/data] because:
[Your reasoning]

Requirements:
1. [Requirement 1]
2. [Requirement 2]
3. Should support [future needs]

Show me the proposed structure first."
```

**Real Example:**
```
"Help me reorganize the project folder. London data should go in its own
folder since we'll analyze NYC and Austin too.

Requirements:
1. Keep raw data separate from processed
2. City-specific outputs in separate folders
3. Scripts should work for any city

Show me the structure first."
```

**Claude Will:**
- Propose detailed structure
- Explain benefits
- Move files safely
- Update all affected code
- Generate documentation

### 5.5 Documentation Pattern

**When to use:** Need to document decisions or create guides

**Template:**
```
"Create a [METHODOLOGY.md/README.md/etc.] that documents:
1. [Section 1]
2. [Section 2]
3. [Section 3]

Purpose: [how this will be used]
Audience: [who will read it]"
```

**Real Example:**
```
"Create a METHODOLOGY.md file that tracks:
1. All data cleaning decisions
2. Missing data handling approaches
3. Feature engineering choices
4. Model selection criteria
5. Evaluation metrics

Purpose: Use for final project writeup to explain our analysis"
```

**Claude Will:**
- Create comprehensive documentation
- Include rationale for decisions
- Add tables, code snippets, formulas
- Reference literature where appropriate
- Structure for easy navigation

---

## 6) Task-by-Task Guide (Updated with Actual Experience)

### Task 1: Data Exploration ✅ COMPLETED

**What We Actually Did:**

```
1. Prompt: "Let's start with Task 1"

2. Claude created comprehensive exploration notebook

3. Hit issue: Python packages not installed

4. Prompt: "I'm getting pip install errors [paste error]"

5. Claude diagnosed, set up venv, installed packages

6. Created and ran run_data_exploration.py

7. Generated 5 visualizations + 2 summary CSVs

8. Prompt: "Reorganize for multi-city structure"

9. Claude restructured entire project

10. Prompt: "Create METHODOLOGY.md for tracking decisions"

11. Done! Task 1 complete.
```

**Time:** ~2 hours (including environment troubleshooting)

**Outputs:**
- ✅ 5 visualizations saved to `data/london/outputs/visualizations/`
- ✅ 2 summary CSVs in `data/london/outputs/reports/`
- ✅ Multi-city folder structure created
- ✅ Reusable scripts in `scripts/`
- ✅ Comprehensive documentation (README, METHODOLOGY, SETUP, etc.)

**Key Findings:**
- 96,871 London listings loaded
- 47.6% are high-demand (occ_90 ≥ 0.75)
- Median price: £135/night
- 100% vibe feature join rate ✓
- 36% missing price data (will filter out)
- 13% missing bedrooms (will impute)

### Task 2: Feature Engineering (Next Up)

**Recommended Prompt:**
```
"Create a feature engineering pipeline script that:

1. Loads data from data/{city}/raw/
2. Implements the cleaning decisions from METHODOLOGY.md:
   - Clean price field (remove $ and commas)
   - Filter price < £10 or > £1000
   - Compute occupancy proxies (occ_30, occ_60, occ_90, occ_365)
   - Create high_demand_90 label (threshold 0.75)

3. Engineers these derived features:
   - amenities_count: count from amenities list
   - listing_age_days: days since first_review
   - price_per_person: price / accommodates
   - is_professional_host: host_listings_count > 5

4. Handles missing data per METHODOLOGY.md:
   - bedrooms: impute with median by room_type
   - bathrooms: parse bathrooms_text, then impute
   - review_scores_rating: create has_reviews flag + impute neighborhood median

5. Joins vibe features from 01_vibe_features_for_modeling.csv

6. Creates train/test split (80/20, stratified on high_demand_90, seed=42)

7. Saves outputs:
   - data/{city}/processed/features_{city}_train.parquet
   - data/{city}/processed/features_{city}_test.parquet
   - data/{city}/processed/feature_summary.csv

Make it multi-city compatible by changing CITY variable.
Include validation checks and progress messages."
```

**Expected Claude Actions:**
- Read METHODOLOGY.md for decision reference
- Create production-ready feature engineering script
- Add extensive validation (row counts, value ranges, etc.)
- Generate feature summary statistics
- Save everything to organized folders

### Task 3: High-Demand Twins Engine (k-NN)

**Recommended Prompt:**
```
"Create scripts/price_bands_neighbors.py that implements the k-NN pricing engine:

1. Load data/{city}/processed/features_{city}_train.parquet

2. Build k-NN model (k=25) using StandardScaler and KNN from sklearn
   Features: accommodates, bedrooms, bathrooms, amenities_count,
            room_type (one-hot), vibe_score, vibe dimensions

3. For each test listing:
   - Find 25 nearest neighbors
   - Filter to neighbors with high_demand_90 == 1
   - Compute price band [p25, p75] from neighbor prices
   - Count neighbors used
   - Flag as low_confidence if <5 neighbors

4. Save to data/{city}/outputs/recommendations/price_bands_neighbors.parquet

5. Generate evaluation:
   - % of listings with valid recommendations
   - Distribution of band widths
   - Compare to actual prices
   - Create visualization

Reference METHODOLOGY.md section 8.1 for configuration details."
```

### Task 4: Predictive Model with Control Function

**Recommended Prompt:**
```
"Create notebooks/predictive_model.ipynb implementing the two-stage approach
from METHODOLOGY.md section 8.2:

Stage 1 - Price Endogeneity Control:
1. Regress price ~ month + neighbourhood + listing_density
2. Save residual as epsilon_price

Stage 2 - Occupancy Prediction:
1. Train XGBoost, LightGBM, Random Forest
2. Use 5-fold stratified CV for evaluation
3. Select best model based on MAE/RMSE

Model Interpretation:
1. Compute SHAP values for all features
2. Verify Vibe Score in top 50% importance
3. Create visualizations (global importance, beeswarm, dependence plots)

Baseline Comparison:
1. Train identical model WITHOUT vibe features
2. Compare performance (target: ≥15% improvement)

Save outputs to data/{city}/models/ and data/{city}/outputs/

Follow evaluation metrics from METHODOLOGY.md section 9."
```

### Task 5: Revenue Optimization

**Recommended Prompt:**
```
"Create scripts/revenue_optimizer.py that:

1. Loads trained model from data/{city}/models/

2. For sample of test listings (N=50):
   - Create price grid (0.5x to 2.0x current price, 50 points)
   - Predict occ_90 for each price point
   - Compute revenue(p) = price × occ_90(p) × 30
   - Identify optimal_price (max revenue)
   - Find safe_band (prices where occ_90 >= 0.75)
   - Calculate revenue_lift vs current price

3. Generate revenue curve plots for 5 contrasting examples:
   - Budget studio in low-vibe area
   - Luxury apt in high-vibe area
   - Mid-range entire home
   - Room in nightlife district
   - (Let model select 5th contrasting example)

4. Save to data/{city}/outputs/recommendations/

Include business insights in comments."
```

### Task 6: Interactive Visualizations

**Recommended Prompt:**
```
"Create notebooks/visualizations.ipynb that produces:

Visual 1: Multi-Neighborhood Vibe Map
- Use Folium or Plotly for interactive map
- Color neighborhoods by vibe_score
- Hover shows: name, score, top characteristics, mean occupancy
- Save as data/{city}/outputs/vibe_map.html

Visual 2: Revenue Curve Showcase
- matplotlib 2x2 subplots
- 4 contrasting listings (from revenue optimizer output)
- Each plot: revenue vs price curve with current/optimal marked
- Shade safe band, annotate lift %
- Save as high-DPI PNG

Visual 3: Feature Importance Dashboard
- SHAP summary plot
- Bar chart of top 15 features
- Dependence plot for vibe_score
- All colorblind-friendly

Use professional styling throughout."
```

---

## 7) Advanced Prompting Techniques (Learned from Experience)

### 7.1 The "Show Me First" Pattern

**Problem:** Claude might implement something you don't want

**Solution:** Ask to see the plan before execution

```
"Show me the proposed folder structure before moving files."

"Draft the feature engineering logic before implementing."

"List the visualizations you'll create before generating them."
```

**Benefits:**
- Catch issues early
- Provide feedback before work is done
- Iterate on design

### 7.2 The "Reference This Document" Pattern

**Problem:** Need Claude to follow specific decisions already made

**Solution:** Point to METHODOLOGY.md or other docs

```
"Implement the missing data strategy from METHODOLOGY.md section 3.2"

"Use the evaluation metrics defined in METHODOLOGY.md section 9"

"Follow the train/test split approach from METHODOLOGY.md section 7"
```

**Benefits:**
- Ensures consistency
- Leverages documented decisions
- Creates traceable implementation

### 7.3 The "Multi-City Compatible" Pattern

**Problem:** Want code that works for London, NYC, Austin

**Solution:** Explicitly request parameterization

```
"Make this script work for any city by changing one CITY variable at the top."

"Use data/{city}/raw/ paths so it works for multiple cities."

"Generate city-specific outputs in data/{city}/outputs/"
```

**Benefits:**
- Reusable code
- Consistent structure across cities
- Easy to scale

### 7.4 The "Production Quality" Pattern

**Problem:** Need robust code, not just working code

**Solution:** Specify quality requirements

```
"Include error handling for missing files, invalid data, and edge cases."

"Add progress messages so user knows what's happening."

"Create validation checks: row counts, value ranges, null checks."

"Add docstrings and comments explaining the logic."
```

**Benefits:**
- Code actually works in production
- Easy to debug
- Other team members can understand

### 7.5 The "Iterative Refinement" Pattern

**Strategy:** Don't try to get everything perfect in one prompt

**Process:**
1. First prompt: Get working version
2. Review output
3. Second prompt: "Now add [specific improvement]"
4. Repeat

**Example:**
```
Prompt 1: "Create basic data exploration script"
Review: Works but missing outlier analysis

Prompt 2: "Add outlier detection and visualization to the exploration script"
Review: Good but need more summary stats

Prompt 3: "Add summary statistics table and save to CSV"
Done!
```

---

## 8) Common Patterns from Our Session

### 8.1 File Organization Decisions

**Pattern:** Create organized outputs, not scattered files

**What Claude Did:**
```python
# Define clear output directories
VIZ_DIR = OUTPUT_DIR / 'visualizations'
REPORTS_DIR = OUTPUT_DIR / 'reports'

# Create them if they don't exist
VIZ_DIR.mkdir(parents=True, exist_ok=True)

# Save with clear names
plt.savefig(VIZ_DIR / '01_price_distribution.png', dpi=150)
summary.to_csv(REPORTS_DIR / 'data_summary_stats.csv')
```

**Lesson:** Request organized outputs explicitly in prompts

### 8.2 Error Handling Patterns

**Pattern:** Graceful failures with helpful messages

**What Claude Did:**
```python
try:
    df = pd.read_csv(listings_file, low_memory=False)
    print(f"✓ Loaded {len(df):,} listings")
except Exception as e:
    print(f"✗ Error loading listings: {e}")
    sys.exit(1)
```

**Lesson:** Claude naturally includes error handling when asked for "production-ready" code

### 8.3 Progress Messaging

**Pattern:** User knows what's happening at each step

**What Claude Did:**
```python
print("="*80)
print("STEP 1: Loading Data")
print("-"*80)
# ... code ...
print("✓ Data loaded successfully")
print()

print("="*80)
print("STEP 2: Cleaning Price Field")
print("-"*80)
# ... code ...
print("✓ Price field cleaned")
```

**Lesson:** Users appreciate visibility into long-running processes

### 8.4 Validation Patterns

**Pattern:** Check assumptions and data quality throughout

**What Claude Did:**
```python
# After join
print(f"Match rate: {match_pct:.2f}%")
if match_pct < 95:
    print("⚠️  WARNING: Low match rate!")

# After imputation
null_after = df['bedrooms'].isnull().sum()
print(f"Nulls after imputation: {null_after}")

# After filtering
print(f"Rows before filter: {len_before:,}")
print(f"Rows after filter: {len_after:,}")
print(f"Rows removed: {len_before - len_after:,}")
```

**Lesson:** Validation catches issues early

---

## 9) Lessons Learned (The Hard Way)

### 9.1 WSL + Python Packaging

**Issue:** WSL has `externally-managed-environment` protection

**Wrong Approach:**
- `pip install` directly
- `sudo pip install`
- `pip install --user`

**Right Approach:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install <packages>
```

**Lesson:** Always use virtual environments in WSL/modern Python

### 9.2 File Path Management

**Issue:** Scripts broke when we reorganized folders

**Wrong Approach:**
- Hardcoded paths: `pd.read_csv('listings_London.csv')`

**Right Approach:**
```python
from pathlib import Path

CITY = 'london'
RAW_DIR = Path(f'data/{CITY}/raw')
df = pd.read_csv(RAW_DIR / 'listings_London.csv')
```

**Lesson:** Use Path and parameterize from the start

### 9.3 Documentation Timing

**Issue:** Forgot why we made certain decisions

**Wrong Approach:**
- Make decisions, implement, document later (forget details)

**Right Approach:**
- Create METHODOLOGY.md early
- Update it as decisions are made
- Reference it in implementation

**Lesson:** Document decisions immediately, not retroactively

### 9.4 Data Exploration Before Coding

**Issue:** Could have jumped straight to feature engineering

**Why That Would Fail:**
- Wouldn't know about 36% missing prices
- Wouldn't know bathrooms_text is more complete
- Wouldn't know vibe join is 100% clean

**Right Approach:**
- Task 1: Thoroughly explore
- Document findings
- THEN code based on actual data patterns

**Lesson:** Always explore before engineering

---

## 10) Quick Reference Commands

### Environment Management
```bash
# Activate environment
source venv/bin/activate

# Deactivate
deactivate

# Verify active
which python  # Should show /path/to/venv/bin/python

# Quick helper
source activate_env.sh
```

### Running Analysis Scripts
```bash
# From project root, with venv activated
python scripts/run_data_exploration.py

# For different city (after adding data)
# Edit scripts/run_data_exploration.py:
# Change: CITY = 'nyc'
# Then run same command
```

### Checking Outputs
```bash
# See what was generated
ls data/london/outputs/visualizations/
ls data/london/outputs/reports/

# View summary
cat data/london/outputs/reports/data_summary_stats.csv
```

### Useful One-Liners
```bash
# Check data size
du -h data/london/raw/listings_London.csv

# Count listings
wc -l data/london/raw/listings_London.csv

# View first few rows
head -20 data/london/raw/listings_London.csv | column -t -s','
```

---

## 11) Next Session Quickstart

**When you return to work on this project:**

```bash
# 1. Navigate to project
cd /mnt/c/Users/Nicholas/adv_ba_project

# 2. Activate environment
source venv/bin/activate

# 3. Check where you left off
cat README.md  # See current status

# 4. Review methodology
cat METHODOLOGY.md  # Remember decisions

# 5. Continue with Claude
# Tell Claude: "I'm back to continue with Task 2: Feature Engineering"
```

**Claude will:**
- Remember project context from CLAUDE.md
- Reference METHODOLOGY.md for decisions
- Continue with consistent approach
- Generate code that fits existing structure

---

## 12) Tips for Working with Claude on This Project

### Do's ✅

1. **Start sessions with context:**
   ```
   "I'm working on the Vibe-Aware Pricing project.
   We completed Task 1 (data exploration).
   Now I want to do Task 2 (feature engineering)."
   ```

2. **Reference documentation:**
   ```
   "Follow the missing data strategy from METHODOLOGY.md"
   "Use the folder structure from PROJECT_STRUCTURE.md"
   ```

3. **Ask for planning before execution:**
   ```
   "Show me the feature engineering plan before implementing"
   "List the steps you'll take to build the k-NN model"
   ```

4. **Request documentation updates:**
   ```
   "Update METHODOLOGY.md with the hyperparameter choices we made"
   "Add this decision to the changelog in METHODOLOGY.md"
   ```

5. **Iterate and refine:**
   ```
   "The exploration script works. Now add error handling for missing files."
   "Good. Now also add a progress bar for long operations."
   ```

### Don'ts ❌

1. **Don't start coding without exploration:**
   ```
   ❌ "Write a feature engineering script"
   ✅ "First explore the data, then write feature engineering based on findings"
   ```

2. **Don't forget to specify output format:**
   ```
   ❌ "Generate visualizations"
   ✅ "Generate visualizations and save to data/{city}/outputs/visualizations/"
   ```

3. **Don't make adhoc decisions without documenting:**
   ```
   ❌ "Let's use threshold 0.75 for high-demand"
   ✅ "Let's use 0.75 for high-demand. Add this to METHODOLOGY.md with rationale."
   ```

4. **Don't ask for everything at once:**
   ```
   ❌ "Build the entire pricing engine in one script"
   ✅ "First build data exploration, then feature engineering, then k-NN, etc."
   ```

5. **Don't ignore warnings or errors:**
   ```
   ❌ "It works on my machine, ship it"
   ✅ "The script shows warnings about missing data. Let's add validation."
   ```

---

## 13) Success Metrics (For This Guide)

**You're using this guide well if:**
- ✅ You complete each task with organized outputs
- ✅ METHODOLOGY.md tracks all analytical decisions
- ✅ Scripts are reusable across cities
- ✅ You can explain every choice in final writeup
- ✅ Other team members can understand the code
- ✅ Project meets deadline with quality work

**You need to adjust if:**
- ❌ Scattered files all over the place
- ❌ Can't remember why you made a decision
- ❌ Code only works for London
- ❌ Struggling to write Methods section
- ❌ Team members confused by structure
- ❌ Rushing at the end to finish

---

## 14) Integration with Team Workflow

### Nicholas (Data & Vibe Engineering)
**Claude prompts:**
```
"Help me validate the vibe score construction:
1. Load review aggregation results
2. Check TF-IDF output for coherence
3. Validate LSI/SVD dimension reduction
4. Verify cluster quality (silhouette scores)
5. Generate vibe score interpretation report"
```

### Sahil (Modeling & Control Functions)
**Claude prompts:**
```
"Implement the two-stage control function per METHODOLOGY.md:
1. Stage 1 OLS for price residuals
2. Stage 2 GBM with controls
3. Compare XGBoost, LightGBM, Random Forest
4. Generate SHAP analysis
5. Prove vibe hypothesis (top 50% importance)"
```

### Heath (Visuals & Documentation)
**Claude prompts:**
```
"Create production-quality visualizations:
1. Interactive vibe map (Folium/Plotly)
2. Revenue curve showcase (matplotlib, publication-quality)
3. Feature importance dashboard (SHAP plots)
4. Help me write the Methods section from METHODOLOGY.md"
```

---

## 15) Final Checklist Before Submission

**Data:**
- [ ] All raw data in `data/{city}/raw/`
- [ ] Processed features in `data/{city}/processed/`
- [ ] No data files in root directory

**Code:**
- [ ] All scripts in `scripts/` or `notebooks/`
- [ ] Scripts are documented with docstrings
- [ ] Scripts include error handling
- [ ] Scripts are multi-city compatible

**Outputs:**
- [ ] Visualizations in `data/{city}/outputs/visualizations/`
- [ ] Reports in `data/{city}/outputs/reports/`
- [ ] Models in `data/{city}/models/`
- [ ] Recommendations in `data/{city}/outputs/recommendations/`

**Documentation:**
- [ ] README.md complete and up-to-date
- [ ] METHODOLOGY.md has all decisions documented
- [ ] SETUP.md has installation instructions
- [ ] Code has inline comments

**Reproducibility:**
- [ ] requirements.txt includes all dependencies
- [ ] Random seeds set (42) for reproducibility
- [ ] Virtual environment documented
- [ ] Clear instructions to run analysis

**Quality:**
- [ ] All plots have clear labels and titles
- [ ] Numbers in plots are formatted (commas, decimals)
- [ ] Colorblind-friendly palettes used
- [ ] Tables are properly formatted

**Academic:**
- [ ] All data sources cited
- [ ] Methodology clearly explained
- [ ] Limitations documented
- [ ] Results are interpretable

---

## 16) Emergency Prompts (When Stuck)

**Can't remember what you did:**
```
"Read METHODOLOGY.md and summarize the decisions we made for [topic]"
```

**Script broke after changes:**
```
"The script worked before. Now getting error: [paste error].
What changed and how do I fix it?"
```

**Don't know what to do next:**
```
"We completed Task [N]. What should Task [N+1] include?
Reference our project goals from README.md."
```

**Results don't make sense:**
```
"The model shows [weird result]. Help me debug:
1. Is this a data quality issue?
2. Is this a code bug?
3. Is this actually correct but unexpected?
Show diagnostic steps."
```

**Need to write Methods section:**
```
"Help me write the Methods section for the final report.
Use METHODOLOGY.md as the source.
Make it academic but accessible."
```

---

## 17) Version History of This Guide

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-06 | 1.0 | Initial version (from AGENTS.md base) |
| 2025-11-06 | 2.0 | **Complete rewrite based on actual project work** |
|            |     | - Added real workflow from Task 1 |
|            |     | - Documented WSL/venv lessons learned |
|            |     | - Included actual prompts that worked |
|            |     | - Added multi-city structure details |
|            |     | - Integrated METHODOLOGY.md tracking |
|            |     | - Updated all task prompts with real experience |

---

## 18) What Makes This Different from AGENTS.md

**AGENTS.md (ChatGPT-focused):**
- Theoretical, prescriptive
- Assumes things will work smoothly
- Generic agent definitions
- No environment setup details

**CLAUDE.md v2.0 (This version):**
- Based on actual project experience
- Includes troubleshooting real issues
- Real prompts that worked
- Complete environment setup (venv, WSL, pip)
- Multi-city structure from practice
- METHODOLOGY.md integration
- Team workflow integration
- Lessons learned the hard way

**Bottom Line:** This guide was forged in the fires of actual development. Use it.

---

**Last Updated:** 2025-11-06 (after completing Task 1)
**Next Update:** After Task 2 (Feature Engineering)
**Status:** Battle-tested and ready to use ✅

---

**Remember:** Claude is your analytical partner. Start with exploration, document your decisions, and iterate toward excellence. This project is about the journey as much as the destination.

Good luck! 🚀
