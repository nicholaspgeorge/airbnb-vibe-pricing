# Vibe-Aware Pricing Engine

A data-driven pricing recommendation system for Airbnb listings that combines standard property features with engineered "Neighborhood Vibe Scores" derived from guest review text.

**Team:** Nicholas George, Sahil Medepalli, Heath Verhasselt
**Course:** MIS5460 Advanced Business Analytics, Fall 2025
**Iowa State University, Ivy College of Business**

---

## 🎉 PROJECT STATUS: COMPLETE & VERIFIED

**All core analysis complete across 3 cities + Interactive Streamlit app deployed!**
**Updated Nov 13, 2025 with Monotonic Constraints Implementation**

### Target Cities - All Complete ✅
- **London** ✅ (96,871 listings, £219M opportunity, 52.4% median lift)
- **Austin** ✅ (15,187 listings, $65M opportunity, 73.8% median lift)
- **NYC** ✅ (36,111 listings, $320M opportunity, 46.6% median lift)

**Total Market Opportunity: ~$600M+ annually across all three markets**

**Note:** Revenue lifts updated to reflect monotonic-constrained models (more conservative and realistic)

### Deliverables Complete
- ✅ Full analytical pipeline (6 tasks) for all 3 cities
- ✅ Academic paper sections (Methods, Results, Discussion)
- ✅ LaTeX-ready paper (PAPER_SECTIONS.tex)
- ✅ **Interactive Streamlit Web Application**
- ✅ Vibe heat maps for all cities (new color scheme)
- ✅ Comprehensive documentation

---

## 🚀 NEW: Interactive Streamlit Application

**Launch the app:**
```bash
cd app
source ../venv/bin/activate
streamlit run Home.py
```

**Access at:** http://localhost:8501

### App Features

**📍 London Pricing Tool (Fully Functional)**
- Property input form with 50 amenity checkboxes
- Neighborhood vibe visualization (radar chart)
- k-NN price band recommendations
- XGBoost revenue optimization curve
- Interactive price slider with real-time predictions
- Occupancy gauge and final recommendations

**🗺️ Interactive Vibe Maps**
- All 3 cities with clickable neighborhood bubbles
- Color gradient: Dark blue (low vibe) → Bright red (high vibe)
- Detailed vibe scores on click

**🏠 Austin & NYC Pages**
- Placeholder pages ready (copy London template to activate)

**See:** `app/README.md` for full documentation

---

## Project Overview

This project builds a transparent pricing aid that increases expected monthly revenue by quantifying the subjective "neighborhood vibe" from review text and proving its economic impact on rental revenue.

### Key Innovation
Transforming unstructured review text into quantitative vibe features using TF-IDF → SVD → Clustering, then proving these features improve occupancy prediction and revenue optimization.

### 3-City Vibe Comparison
- **NYC:** 217 neighborhoods, mean vibe **62.9** (HIGHEST!), 5 perfect scores 🏆
- **Austin:** 43 neighborhoods, mean vibe 48.9, sentiment 0.427 (happiest guests!), 2 perfect scores
- **London:** 33 neighborhoods, mean vibe 42.0, sentiment 0.367, 0 perfect scores

**Key Finding:** All top 5 NYC neighborhoods are in **Brooklyn** (not Manhattan!)

---

## Project Structure

```
adv_ba_project/
│
├── README.md                          # This file
├── PAPER_SECTIONS.md                  # Complete academic paper (Methods, Results, Discussion)
├── PAPER_SECTIONS.tex                 # LaTeX version for Overleaf
├── FINAL_3_CITY_RESULTS.md            # Executive summary with all city results
├── CLAUDE.md                          # Guide for using Claude Code
├── METHODOLOGY.md                     # Analytical decisions and methodology
├── HARDWARE.md                        # GPU optimization and hardware specs
├── requirements.txt                   # Python dependencies
├── venv/                              # Virtual environment
│
├── app/                               # 🆕 Interactive Streamlit Application
│   ├── Home.py                        # Landing page
│   ├── README.md                      # App documentation
│   ├── pages/
│   │   ├── 1_🇬🇧_London.py            # Full London pricing tool
│   │   ├── 2_🇺🇸_Austin.py            # Austin (placeholder)
│   │   ├── 3_🗽_NYC.py                 # NYC (placeholder)
│   │   └── 4_🗺️_Vibe_Maps.py          # Interactive vibe maps
│   └── utils/
│       ├── model_loader.py            # Load models and data
│       └── predictor.py               # k-NN and XGBoost predictions
│
├── docs/                              # Project documentation
│   ├── MIS5460_Project_Proposal_Group_1.pdf
│   ├── Inside Airbnb Data Dictionary.xlsx
│   └── Data Assumptions _ Inside Airbnb.html
│
├── scripts/                           # Analysis pipeline
│   ├── 01_vibe_score_generator.py    # Multi-city vibe generation
│   ├── 02_feature_engineering.py     # Feature engineering
│   ├── 03_high_demand_twins_knn.py   # k-NN pricing engine
│   ├── 04_predictive_model_control_function.py  # ML models
│   ├── 05_revenue_optimizer.py       # Revenue optimization
│   ├── 06_create_vibe_heatmaps.py    # 🆕 Interactive heat maps
│   └── 07_extract_amenities_list.py  # 🆕 Amenities extraction
│
└── data/                              # City-specific data
    ├── amenities_master_list.json     # 🆕 16,781 amenities
    │
    ├── london/                        # 🇬🇧 London (COMPLETE)
    │   ├── raw/                       # Original data
    │   ├── processed/                 # 77,496 train / 19,375 test
    │   ├── models/                    # 6 trained models
    │   └── outputs/
    │       ├── visualizations/        # 14 plots + vibe_map_app.html
    │       ├── reports/               # Metrics and summaries
    │       └── recommendations/       # Price bands & revenue curves
    │
    ├── austin/                        # 🇺🇸 Austin (COMPLETE)
    │   ├── raw/                       # 15,187 listings
    │   ├── processed/                 # 12,149 train / 3,038 test
    │   ├── models/                    # 6 trained models
    │   └── outputs/                   # Results + vibe_map_app.html
    │
    └── nyc/                           # 🗽 NYC (COMPLETE)
        ├── raw/                       # 36,111 listings
        ├── processed/                 # 28,888 train / 7,223 test
        ├── models/                    # 6 trained models
        └── outputs/                   # Results + vibe_map_app.html
```

---

## Quick Start

### 1. Run the Interactive App

```bash
# Navigate to app directory
cd app

# Activate virtual environment
source ../venv/bin/activate

# Launch Streamlit
streamlit run Home.py
```

**Open browser to:** http://localhost:8501

### 2. Run Analysis Pipeline (if needed)

```bash
# From project root
source venv/bin/activate

# Run for a specific city
python scripts/02_feature_engineering.py  # Update CITY variable in script
python scripts/03_high_demand_twins_knn.py
python scripts/04_predictive_model_control_function.py
python scripts/05_revenue_optimizer.py
```

---

## Completed Tasks (All 6 + Bonus)

### ✅ Task 1: Data Exploration
- London: 96,871 listings analyzed
- Austin: 15,187 listings analyzed
- NYC: 36,111 listings analyzed
- 100% vibe feature join rate across all cities

### ✅ Task 2: Feature Engineering
- 47 features engineered (property + vibe + host + reputation)
- Train/test splits (80/20, stratified)
- Missing data handled per METHODOLOGY.md

### ✅ Task 3: k-NN Pricing Engine
- London: 12,342 recommendations, 62.4% high confidence
- Austin: 2,126 recommendations, 27.3% high confidence
- NYC: 4,270 recommendations, 63.0% high confidence

### ✅ Task 4: Predictive Models
**Best Model: XGBoost (all cities)**

| City | Test MAE | Test R² | Vibe Importance |
|------|----------|---------|-----------------|
| London | 0.2417 | 0.2616 | **32.5%** |
| Austin | 0.2245 | 0.1077 | **31.7%** |
| NYC | **0.2287** | **0.3726** | **23.3%** |

**Key Finding:** Vibe features are #1 most important across all cities!

### ✅ Task 5: Revenue Optimization

| City | Median Lift | Optimal Price | Should Increase |
|------|-------------|---------------|-----------------|
| London | 61.2% | £242/night | 88.2% |
| Austin | **103.7%** | $262/night | 97.8% |
| NYC | 55.5% | $260/night | 80.4% |

**Total Opportunity:** £219M (London) + $65M (Austin) + $320M (NYC) = **~$600M+**

### ✅ Task 6: Visualizations
- Interactive vibe heat maps (3 cities)
- Revenue curve visualizations
- Feature importance charts
- Executive summary panels

### ✅ BONUS: Interactive Streamlit App
- Full property input form
- Real-time k-NN recommendations
- XGBoost revenue optimization
- Interactive price slider
- Vibe radar charts
- Occupancy predictions

---

## Key Features

### Two Decision Engines

**Engine A: High-Demand Twins (k-NN)**
- Find 25 nearest neighbors based on property + vibe features
- Filter to high-demand listings (occ_90 ≥ 0.75)
- Recommend price band: [p25, p75] of neighbor prices

**Engine B: Predictive Model + Control Function**
- Stage 1: Control for price endogeneity (OLS)
- Stage 2: Train XGBoost for occupancy prediction
- Generate revenue curves: revenue(p) = price × occ_90(p) × 30
- Identify optimal price and safe band

### Vibe Features
- **vibe_score:** Overall neighborhood appeal (0-100)
- **11 Dimensions:** walkability, safety, nightlife, quietness, family-friendly, local authentic, convenience, food scene, liveliness, charm
- **Source:** TF-IDF on review text → SVD → clustering

---

## Data Sources

**Primary:** [Inside Airbnb](https://insideairbnb.com/get-the-data/)
- Listings data (property features, pricing, availability)
- Review text (for vibe score engineering)
- Neighborhood boundaries

**Snapshot Date:** September 2025
**Cities:** London, Austin, NYC (all complete)

---

## Technical Stack

### Core Libraries
- **Data:** pandas, numpy, pyarrow
- **ML:** scikit-learn, xgboost (GPU-accelerated), lightgbm
- **Interpretation:** shap
- **Visualization:** matplotlib, seaborn, plotly, folium
- **Web App:** streamlit

### Hardware
- **GPU:** 2× NVIDIA RTX 5090 (32GB VRAM each)
- **CPU:** AMD Ryzen Threadripper PRO 7975WX (32 cores)
- **RAM:** 512GB DDR5
- **Storage:** 28TB NVMe SSD
- **GPU Acceleration:** 15-20x speedup for XGBoost

### Development
- **Environment:** WSL2 (Ubuntu) on Windows 11 Pro
- **Python:** 3.12.3 in virtual environment
- **Version Control:** Git

---

## Academic Deliverables

### Papers & Reports
- **PAPER_SECTIONS.md:** Complete Methods, Results, Discussion sections
- **PAPER_SECTIONS.tex:** LaTeX version ready for Overleaf
- **FINAL_3_CITY_RESULTS.md:** Executive summary with comparative analysis
- **METHODOLOGY.md:** All analytical decisions documented

### Key Findings for Paper
1. **Vibe features contribute 23-33% of model importance** (far exceeds 5% threshold)
2. **88-98% of hosts are systematically underpricing** their properties
3. **60-104% median revenue lift potential** across markets
4. **Cross-city validation:** Results hold across London (mature), Austin (emerging), NYC (largest)
5. **$600M+ market opportunity** for data-driven pricing tools

---

## Model Performance Summary

### XGBoost (Best Model)
- **London:** MAE 0.24, R² 0.26, Vibe 32.5%
- **Austin:** MAE 0.22, R² 0.11, Vibe 31.7%
- **NYC:** MAE 0.23, R² 0.37, Vibe 23.3%

### k-NN Coverage
- **London:** 62.4% high confidence (≥5 neighbors)
- **Austin:** 27.3% high confidence (smaller market)
- **NYC:** 63.0% high confidence (largest market)

### Revenue Optimization
- **London:** 61.2% median lift, £219M opportunity
- **Austin:** 103.7% median lift, $65M opportunity (HIGHEST!)
- **NYC:** 55.5% median lift, $320M opportunity

---

## Team Contributions

| Member | Responsibilities |
|--------|------------------|
| **Nicholas George** | Data ingestion, vibe score engineering, review text pipeline, app development |
| **Sahil Medepalli** | Models, hyperparameter tuning, control function, SHAP analysis |
| **Heath Verhasselt** | Visualizations, documentation, business analysis, presentation |

---

## Documentation

- **[app/README.md](app/README.md):** Streamlit app documentation and usage guide
- **[CLAUDE.md](CLAUDE.md):** Complete guide for using Claude Code with this project
- **[METHODOLOGY.md](METHODOLOGY.md):** All analytical decisions documented
- **[HARDWARE.md](HARDWARE.md):** GPU acceleration setup and hardware specs
- **[PAPER_SECTIONS.md](PAPER_SECTIONS.md):** Academic paper sections
- **[FINAL_3_CITY_RESULTS.md](FINAL_3_CITY_RESULTS.md):** 3-city comparative analysis

---

## Next Steps (Optional Enhancements)

- [ ] Complete Austin & NYC app pages (copy London template)
- [ ] Deploy to Streamlit Cloud for team access
- [ ] Add PDF export of recommendations
- [ ] Implement address geocoding for auto-neighborhood detection
- [ ] Build comparison mode (multiple neighborhoods side-by-side)

---

## Timeline

- **Weeks 1-2:** Data setup and vibe engineering ✅
- **Week 3:** Modeling (Tasks 2-4) ✅
- **Week 4:** Revenue optimization (Task 5) ✅
- **Week 4:** Visualizations (Task 6) ✅
- **Week 5:** Multi-city expansion (Austin, NYC) ✅
- **Week 5:** Academic paper writing ✅
- **Week 5:** Streamlit app development ✅
- **Week 6:** Final presentation preparation (current)
- **Deadline:** November 17, 2025

---

## Getting Help

### Common Issues
- **App won't start:** Ensure venv is activated and all dependencies installed
- **Models not loading:** Check `data/{city}/models/` directory exists
- **Predictions failing:** Verify training data in `data/{city}/processed/`

### Contact
- Nicholas George: georgen@iastate.edu
- Sahil Medepalli: sahilmed@iastate.edu
- Heath Verhasselt: heathv@iastate.edu

---

## License & Acknowledgments

**Data Source:** Inside Airbnb (Creative Commons CC0 1.0 Universal License)
**Course:** MIS5460 Advanced Business Analytics, Iowa State University
**Tools:** XGBoost, Streamlit, Plotly, Folium, SHAP

---

## References

1. Inside Airbnb. (2025). *Get the Data*. Retrieved from http://insideairbnb.com/get-the-data/
2. Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press.
3. Lundberg, S. M., & Lee, S. I. (2017). *A Unified Approach to Interpreting Model Predictions*. NIPS 2017.

---

**Last Updated:** 2025-11-13
**Project Status:** ✅ COMPLETE - All tasks finished, app deployed, paper ready!
**Deliverables:** 3-city analysis + Interactive web app + Academic paper + Visualizations
