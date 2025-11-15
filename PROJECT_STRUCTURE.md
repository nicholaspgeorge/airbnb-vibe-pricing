# Project Structure - Multi-City Analysis

## Proposed Folder Structure

```
adv_ba_project/
│
├── README.md                              # Project overview
├── CLAUDE.md                              # Claude Code usage guide (AI-assisted development)
├── AGENTS.md                              # ChatGPT agent definitions
├── METHODOLOGY.md                         # Analytical decisions and methodology
├── HARDWARE.md                            # GPU optimization and hardware specs
├── SETUP.md                               # Setup instructions
├── GPU_SETUP_SUMMARY.md                   # GPU configuration reference
├── SESSION_SUMMARY_*.md                   # Session summaries and progress logs
├── TASK_5_PLAN.md                         # Task 5 implementation plan
├── requirements.txt                       # Python dependencies
├── activate_env.sh                        # Env activation helper
├── venv/                                  # Virtual environment
│
├── docs/                                  # Documentation
│   ├── MIS5460_Project_Proposal_Group_1.pdf
│   ├── Inside Airbnb Data Dictionary.xlsx
│   └── Data Assumptions _ Inside Airbnb.html
│
├── notebooks/                             # Analysis notebooks (generic)
│   ├── 00_data_exploration_template.ipynb
│   ├── 01_feature_engineering_template.ipynb
│   └── ...
│
├── scripts/                               # Reusable scripts
│   ├── run_data_exploration.py
│   ├── feature_engineering.py
│   └── utils.py
│
├── models/                                # Trained models (cross-city)
│   └── .gitkeep
│
├── data/                                  # City-specific data
│   │
│   ├── london/                            # London analysis
│   │   ├── raw/                           # Original data
│   │   │   ├── listings_London.csv
│   │   │   ├── 01_neighborhood_vibe_scores.csv
│   │   │   ├── 01_neighborhood_vibe_dimensions.csv
│   │   │   └── 01_vibe_features_for_modeling.csv
│   │   │
│   │   ├── processed/                     # Cleaned/engineered data
│   │   │   ├── features_london_train.parquet
│   │   │   ├── features_london_test.parquet
│   │   │   └── feature_summary.csv
│   │   │
│   │   ├── models/                        # London-specific models
│   │   │   ├── cf_model_london.pkl
│   │   │   └── model_metrics_london.json
│   │   │
│   │   └── outputs/                       # Results
│   │       ├── visualizations/
│   │       │   ├── 01_price_distribution.png
│   │       │   ├── 02_occupancy_distribution.png
│   │       │   └── ...
│   │       │
│   │       ├── reports/
│   │       │   ├── data_summary_stats.csv
│   │       │   └── listings_schema.csv
│   │       │
│   │       └── recommendations/
│   │           ├── price_bands_neighbors.parquet
│   │           └── revenue_recommendations.parquet
│   │
│   ├── nyc/                               # NYC analysis (future)
│   │   ├── raw/
│   │   ├── processed/
│   │   ├── models/
│   │   └── outputs/
│   │
│   └── austin/                            # Austin analysis (future)
│       ├── raw/
│       ├── processed/
│       ├── models/
│       └── outputs/
│
└── comparative_analysis/                  # Cross-city comparisons
    ├── multi_city_vibe_map.html
    └── cross_city_performance.ipynb
```

## Benefits of This Structure

1. **Scalability:** Easy to add new cities (NYC, Austin, etc.)
2. **Separation:** Raw data separate from processed data
3. **Reusability:** Generic scripts/notebooks in shared folders
4. **Organization:** Clear hierarchy for outputs and models
5. **Collaboration:** Team members can work on different cities simultaneously
6. **Version Control:** City-specific work isolated for cleaner commits

## File Organization Rules

- **Raw data:** Never modify, always in `data/{city}/raw/`
- **Processed data:** Parquet files in `data/{city}/processed/`
- **City-specific models:** In `data/{city}/models/`
- **Visualizations:** In `data/{city}/outputs/visualizations/`
- **Generic code:** In `scripts/` or `notebooks/` at root level
- **Documentation:** In `docs/` at root level
