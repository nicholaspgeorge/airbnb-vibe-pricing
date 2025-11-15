# AGENTS.md

A compact playbook for using `codex` to drive this project from raw Inside Airbnb files to a pricing recommendation artifact. Write in a clear, semi-formal tone and keep outputs practical rather than academic.

---

## 0) Project in one paragraph

Build a **Vibe-Aware Pricing** system for Airbnb listings. We engineer a **Neighborhood Vibe Score** from reviews, infer **booking intensity** from availability fields, and recommend a **price band** for a given listing by combining nearest-neighbor “high-demand twins” with a predictive model that projects booking intensity across a price grid. The decision output is a **recommended price range** and an optional **revenue curve**, not a black-box “expected occupancy.”

**Deadline:** finish by **Mon, Nov 17**.
**Team size:** 3.
**City scope (current sample):** London (can be extended to NYC, Austin).

---

## 1) Files available in this working directory

* `listings_London.csv`  sample city listing snapshot
* `01_neighborhood_vibe_scores.csv`  one score per neighborhood
* `01_neighborhood_vibe_dimensions.csv`  multi-dimensional vibe features
* `01_vibe_features_for_modeling.csv`  modeling-ready vibe features (join key = neighborhood)
* `Data Assumptions _ Inside Airbnb.html`  notes on availability vs booked, review-based heuristics
* `MIS5460_VibeAware_Pricing_Proposal_UPDATED.tex`  proposal source (reference style and scope)

> If present later: `reviews.csv`, `neighbourhoods.csv`, `neighbourhoods.geojson` for richer NLP and mapping.

---

## 2) Core objectives (what “done” means)

1. **Booking intensity labels** from availability fields, with review-based triangulation (if data permits).
2. **Vibe features** joined and leakage-guarded (only information available at snapshot time).
3. **Two decision engines**:

   * **A. High-Demand Twins**: neighbor matching → empirical **price band**.
   * **B. Predictive Model**: occ₉₀ ~ f(price, listing, vibe, neighborhood, season) with a **control-function** for price endogeneity → **safe price band** and **revenue curve**.
4. **Visuals**: Vibe Map, price-band explorer, and a revenue-vs-price chart with the recommended range shaded.
5. **KPIs** reported: MAE/RMSE for occ₉₀ predictions, and a **business KPI**: share of listings where our recommended band historically achieves high booking intensity.

---

## 3) Assumptions we adopt (be explicit)

* Inside Airbnb **price** is the **listed price** at snapshot time, not necessarily realized.
* **availability_X** mixes booked and host-blocked nights. Treat as **booking-intensity proxies** and triangulate with review signals when available.
* Time alignment: for any snapshot, only use features **known on or before** that date.
* Light sampling and pre-aggregation keep RAM feasible on laptops.

---

## 4) Derived fields and labels

Let `availability_30`, `availability_60`, `availability_90`, `availability_365` exist.

```text
occ_30  = 1 - availability_30 / 30
occ_60  = 1 - availability_60 / 60
occ_90  = 1 - availability_90 / 90
occ_365 = 1 - availability_365 / 365
```

**High booking intensity** label (primary):
`high_demand_90 = 1(occ_90 ≥ τ)` with default **τ = 0.75**.

**Optional review triangulation (if counts available):**

```
estimated_bookings  ≈ reviews_last_year / review_rate   (review_rate ~ 0.5 default)
avg_stay            ~ 3 nights (city-specific override when known)
occ_reviews         = clip((estimated_bookings * avg_stay)/365, max=0.70)
```

Use `occ_reviews` only as a **sanity check** against availability-based `occ_365` or neighborhood means.

---

## 5) Feature sets

**User-input (for simulation):** bedrooms, accommodates, room_type, bathrooms, key amenities count, superhost flag, host_listings_count, neighborhood, snapshot month.

**Model features (engineered):**

* Structured: review counts, review score, listing age (days since first review), amenities_count.
* Vibe: from `01_vibe_*.csv` (either a single score + a compact PCA vector).
* Neighborhood context: neighborhood-level rolling averages for price and occ₉₀, listing density, seasonality dummies.

**Leakage guard:** compute review-based features using only reviews with dates ≤ snapshot; smooth tiny neighborhoods by borrowing from nearest area.

---

## 6) Decision Engine A — “High-Demand Twins” (nearest-neighbors band)

1. Build a neighbor space on `[accommodates, bedrooms, room_type, amenities_count, vibe_dims…]`.
2. For each listing, collect **k = 25** nearest neighbors.
3. Keep neighbors with `high_demand_90 == 1`.
4. The recommendation is the **IQR of list prices** among those neighbors: `[p25, p75]`.
5. If fewer than 5 high-demand neighbors, back off to neighborhood-level bins or widen k.

**Why:** simple, explainable, directly tied to empirical “like me and heavily booked”.

---

## 7) Decision Engine B — Predictive + Control Function

**Goal:** project booking intensity across a **price grid** while reducing bias from endogenous price setting.

1. **Stage 1 (price equation):**
   Predict `price` using **instruments** known at snapshot: month-of-year, weekday/weekend mix, neighborhood cluster, seasonality, density. Save residual `ε̂_price`.

2. **Stage 2 (occupancy):**
   Fit `occ_90 = f(price, listing_features, vibe_features, neighborhood_profile, ε̂_price)` with Gradient Boosting or Random Forest. Evaluate via CV (MAE, RMSE).

3. **Inference:**
   For a listing, sweep price over a grid, get predicted `occ_90(p)`, compute **revenue(p) = p * occ_90(p) * 30**, and return:

   * **Safe band:** contiguous price interval where `occ_90(p) ≥ τ`.
   * **Revenue peak:** `argmax_p revenue(p)` with value.

---

## 8) Evaluation & KPIs

* **Predictive:** MAE and RMSE for `occ_90`, plus calibration plot (predicted vs empirical) by price decile.
* **Decision quality:** % of listings where our recommended band yields `occ_90 ≥ τ` historically.
* **Robustness:** city/neighborhood scatter of `occ_365` vs `occ_reviews`; flag outliers.
* **Business KPI:** On a fixed price grid for three example listings, **≥ 5%** improvement in expected monthly revenue vs baseline (no-vibe, no control function).

---

## 9) Visual deliverables

* **Multi-City Vibe Map**: choropleth by neighborhood vibe cluster with hover keywords and mean `occ_90`.
* **Price-Band Explorer**: interactive slider for price showing share of high-demand listings in bin.
* **Revenue Curve**: line of revenue(p) with shaded recommended band and annotated optimum.

Keep labels clear, titles descriptive, axes units obvious.

---

## 10) Risks and mitigations

* **Booked vs blocked:** triangulate with review-based estimates; show uncertainty bands.
* **Sparse reviews:** minimum review thresholds; smooth to nearest area.
* **Endogeneity:** control-function residual in stage 2; seasonality instruments.
* **Compute limits:** pre-aggregate to neighborhood×month; use Parquet/Feather; sample if needed.

---

## 11) Agent definitions (what to ask `codex` to do)

> Use short, imperative prompts. Each agent produces concrete artifacts (scripts/notebooks/plots). Keep code simple and reproducible.

### Agent A — Ingest & Features

**Goal:** produce a modeling table with occupancy proxies and vibe joins.
**Inputs:** `listings_London.csv`, `01_vibe_features_for_modeling.csv`
**Outputs:** `features_london.parquet` with columns:
`[id, neighbourhood, price, availability_*, occ_*, room_type, accommodates, bathrooms, bedrooms, host_is_superhost, host_listings_count, number_of_reviews, review_scores_rating, amenities_count, listing_age_days, vibe_*]`

**Prompt to codex:**

* Read CSVs, engineer `occ_30/60/90/365`, `amenities_count`, `listing_age_days`.
* Clean `price` to float.
* Left-join vibe features on neighborhood.
* Save Parquet and print shape + missingness summary.

### Agent B — High-Demand Twins

**Goal:** compute recommended price bands from empirical neighbors.
**Inputs:** `features_london.parquet`
**Outputs:** `price_bands_nn.parquet` with `[id, reco_price_low, reco_price_high, k_used, neighbors_used]`

**Prompt:**

* Build NN on `[accommodates, bedrooms, amenities_count, room_type (one-hot), vibe_dims]`.
* k=25, Euclidean.
* Filter neighbors to `high_demand_90==1`, compute p25/p75 of price; handle low-support gracefully.

### Agent C — Control-Function Model

**Goal:** predictive occ₉₀ across a price grid with endogeneity control.
**Inputs:** `features_london.parquet`
**Outputs:** `cf_model.pkl`, `grid_predictions.parquet`, `metrics.json`, `calibration_plot.png`

**Prompt:**

* Stage-1: regress `price` on seasonality, neighborhood cluster, density; save residual.
* Stage-2: GBM/RF for `occ_90` using features + residual. Report CV MAE/RMSE.
* For 50 random listings, sweep price grid, save predictions and plot calibration.

### Agent D — Visuals

**Goal:** produce the three visuals.
**Inputs:** outputs from B and C + `neighbourhoods.geojson` (if present)
**Outputs:** `vibe_map.html`, `price_band_explorer.html`, `revenue_curve_examples.png`

**Prompt:**

* Choropleth by vibe cluster with hover keywords and mean `occ_90`.
* Interactive band explorer by neighborhood showing share_high_occ vs price bins.
* For three listings, revenue curves with shaded bands and optimal price markers.

### Agent E — Docs & Packaging

**Goal:** lightweight report and README sections.
**Outputs:** `REPORT.md` (4–6 pp), updated `README.md` usage notes.

**Prompt:**

* Summarize methods, assumptions, KPIs, and how to interpret outputs.
* Include a short “Ethics & Privacy” note and “Known Limitations.”

---

## 12) Quality gates (acceptance criteria)

* `features_london.parquet` exists, with ≥ 95% non-missing for key fields.
* `metrics.json` reports **MAE and RMSE**; calibration plot shows roughly monotone trend.
* ≥ 60% of listings have a non-null `[reco_price_low, reco_price_high]`.
* Visuals render without hardcoded paths; files open from repo root.

---

## 13) Quickstart (suggested codex task order)

1. Run **Agent A** to build features.
2. Run **Agent B** to get neighbor price bands.
3. Run **Agent C** to train CF model and generate grid predictions.
4. Run **Agent D** to render visuals.
5. Run **Agent E** to produce the brief report.

---

## 14) Prompts you can paste to codex

* “Create `notebooks/01_features.ipynb` that reads `listings_London.csv` and `01_vibe_features_for_modeling.csv`, engineers `occ_*`, cleans price, joins vibe, and saves `features_london.parquet` with a summary table.”
* “Create `scripts/02_price_bands_nn.py` that loads `features_london.parquet`, computes neighbor-based price bands with k=25, threshold τ=0.75, and writes `price_bands_nn.parquet`.”
* “Create `notebooks/03_cf_model.ipynb` implementing the two-stage control-function occ_90 model, outputs `cf_model.pkl`, `grid_predictions.parquet`, `metrics.json`, and `calibration_plot.png`.”
* “Create `notebooks/04_visuals.ipynb` generating `vibe_map.html`, `price_band_explorer.html`, and `revenue_curve_examples.png` using Plotly/Folium and the model outputs.”

---

## 15) Team roles (map to agents)

* **Member A:** Agent A + neighborhood profiles; leakage checks.
* **Member B:** Agents B & C; model selection; sensitivity analyses.
* **Member C:** Agent D + E; dashboards; write-up and business translation.

---

## 16) Glossary (short)

* **occ_X**: proxy occupancy over next X days from availability fields.
* **high-demand**: occ_90 ≥ τ (default 0.75).
* **Vibe Score / Vibe dims**: text-derived neighborhood features from reviews.
* **Control function**: residual from price equation used as a control in the occ model.
* **High-Demand Twins**: nearest neighbors among similar listings that achieved high demand.

---

## 17) Ethics & privacy

Use only public text, do not attempt to identify individuals, document processing steps, and be explicit about the booked-vs-blocked ambiguity and its impact on conclusions.

---

Keep responses and code minimal and readable. Favor simple checks, labeled plots, and clear docstrings over algorithmic complexity.
