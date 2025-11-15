# Task 5: Revenue Optimization Engine

**Objective:** Use the trained XGBoost model to generate revenue curves by sweeping price grids and finding optimal prices that maximize expected monthly revenue.

**Timeline:** 1-2 hours
**Prerequisites:** Task 4 complete (trained models available)

---

## Overview

For each listing in the test set, we will:
1. Create a price grid from 0.5x to 2.0x current price
2. Predict occupancy (occ_90) at each price point using trained model
3. Calculate monthly revenue: `revenue = price × occ_90 × 30`
4. Identify optimal price and safe price range

---

## Revenue Formula

```
monthly_revenue = nightly_price × occupancy_rate × 30 days
```

**Key Insight:** As price increases, revenue may initially increase (higher price offsets lower occupancy), but eventually revenue decreases (occupancy drops too much).

---

## Implementation Plan

### Script: `scripts/05_revenue_optimizer.py`

#### 1. Load Trained Model and Data
```python
import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load best model
model = pickle.load(open('data/london/models/xgboost_with_vibe.pkl', 'rb'))

# Load test data
test_data = pd.read_parquet('data/london/processed/features_london_test.parquet')
```

#### 2. Create Price Grid Function
```python
def create_price_grid(current_price, n_points=50):
    """Create price grid from 0.5x to 2.0x current price"""
    min_price = current_price * 0.5
    max_price = current_price * 2.0
    return np.linspace(min_price, max_price, n_points)
```

#### 3. Revenue Curve Generator
```python
def generate_revenue_curve(model, listing_features, current_price, n_points=50):
    """
    Generate revenue curve for a single listing

    Returns:
        DataFrame with columns: price, predicted_occ_90, monthly_revenue
    """
    price_grid = create_price_grid(current_price, n_points)
    results = []

    for price in price_grid:
        # Update price feature
        features_copy = listing_features.copy()
        features_copy['price'] = price
        features_copy['price_per_person'] = price / features_copy['accommodates']

        # Predict occupancy
        predicted_occ = model.predict([features_copy])[0]
        predicted_occ = np.clip(predicted_occ, 0, 1)  # Ensure [0, 1] range

        # Calculate monthly revenue
        monthly_revenue = price * predicted_occ * 30

        results.append({
            'price': price,
            'predicted_occ_90': predicted_occ,
            'monthly_revenue': monthly_revenue
        })

    return pd.DataFrame(results)
```

#### 4. Optimization Function
```python
def optimize_price(revenue_curve, current_price, min_occ=0.75):
    """
    Find optimal price and safe range

    Returns:
        dict with optimal_price, safe_low, safe_high, revenue_lift
    """
    # Find optimal price (max revenue)
    optimal_idx = revenue_curve['monthly_revenue'].idxmax()
    optimal_price = revenue_curve.loc[optimal_idx, 'price']
    optimal_revenue = revenue_curve.loc[optimal_idx, 'monthly_revenue']

    # Current revenue
    current_idx = (revenue_curve['price'] - current_price).abs().idxmin()
    current_revenue = revenue_curve.loc[current_idx, 'monthly_revenue']

    # Safe range (where occ_90 >= min_occ)
    safe_prices = revenue_curve[revenue_curve['predicted_occ_90'] >= min_occ]

    if len(safe_prices) > 0:
        safe_low = safe_prices['price'].min()
        safe_high = safe_prices['price'].max()
    else:
        safe_low = safe_high = None

    # Revenue lift
    revenue_lift = ((optimal_revenue - current_revenue) / current_revenue) * 100

    return {
        'current_price': current_price,
        'optimal_price': optimal_price,
        'safe_low': safe_low,
        'safe_high': safe_high,
        'current_revenue': current_revenue,
        'optimal_revenue': optimal_revenue,
        'revenue_lift_pct': revenue_lift
    }
```

#### 5. Batch Processing
```python
# Process all test listings (or sample)
sample_size = 100  # Or use all: len(test_data)
sample_listings = test_data.sample(n=sample_size, random_state=42)

# Store results
revenue_curves_data = []
optimization_results = []

for idx, row in sample_listings.iterrows():
    listing_id = row['id']
    current_price = row['price']

    # Generate revenue curve
    curve = generate_revenue_curve(model, row, current_price)
    curve['listing_id'] = listing_id
    revenue_curves_data.append(curve)

    # Optimize price
    opt_result = optimize_price(curve, current_price)
    opt_result['listing_id'] = listing_id
    optimization_results.append(opt_result)

# Combine and save
revenue_curves_all = pd.concat(revenue_curves_data, ignore_index=True)
revenue_curves_all.to_parquet('data/london/outputs/recommendations/revenue_curves.parquet')

optimization_df = pd.DataFrame(optimization_results)
optimization_df.to_parquet('data/london/outputs/recommendations/revenue_recommendations.parquet')
optimization_df.to_csv('data/london/outputs/recommendations/revenue_recommendations.csv', index=False)
```

---

## Visualizations

### Visualization 1: Revenue Curve Examples (4 listings)
Select 4 diverse listings:
- Budget studio in low-vibe area
- Luxury apartment in high-vibe area
- Mid-range entire home in family-friendly area
- Room in nightlife district

**For each:**
- Plot revenue vs price curve
- Mark current price (vertical line)
- Mark optimal price (star)
- Shade safe band (occ_90 ≥ 0.75)
- Annotate revenue lift %

```python
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
# ... (implementation in script)
```

### Visualization 2: Revenue Lift Distribution
- Histogram of revenue lift opportunities across all listings
- Show median, mean, quartiles

### Visualization 3: Optimal vs Current Price Scatter
- X-axis: current price
- Y-axis: optimal price
- Color by property type
- Diagonal line (optimal = current)
- Points above line: should increase price
- Points below line: should decrease price

---

## Expected Outputs

### Files Generated:
1. `revenue_curves.parquet` - Full grid predictions for sample listings
2. `revenue_recommendations.parquet` - Summary of optimal prices
3. `revenue_recommendations.csv` - Human-readable summary
4. `09_revenue_optimization_curves.png` - 4-panel revenue curves
5. `10_revenue_lift_distribution.png` - Distribution of opportunities
6. `11_optimal_vs_current_price.png` - Scatter plot

### Summary Statistics:
- Median revenue lift
- % of listings that could increase revenue by >10%
- Optimal price range statistics
- Safe band coverage

---

## Success Criteria

- [ ] Revenue curves generated for ≥100 test listings
- [ ] All curves show sensible peak (not at extremes)
- [ ] ≥60% of listings have revenue lift >5%
- [ ] Visualizations are publication-quality
- [ ] Results documented in outputs/reports/

---

## Performance Considerations

With GPU acceleration (XGBoost on RTX 5090):
- 100 listings × 50 price points = 5,000 predictions
- Estimated time: ~10-20 seconds
- Full test set (19,375 listings): ~2-3 minutes

---

## Edge Cases to Handle

1. **Listings with very high/low current prices**
   - Adjust price grid bounds if needed

2. **Flat revenue curves**
   - Flag listings where revenue varies <5% across grid

3. **No safe prices (all occ_90 < 0.75)**
   - Report as "high risk" - price may be too high already

4. **Multiple local maxima**
   - Report global maximum, flag if multiple peaks exist

---

## Integration with Task 3 (k-NN Engine)

Compare recommendations:
- Task 3: Price bands from high-demand neighbors
- Task 5: Optimal price from revenue curves

Create comparison table:
- Listing ID
- Task 3 recommendation: [low, median, high]
- Task 5 optimal price
- Agreement level

---

## Business Insights to Extract

1. **Which property types benefit most from optimization?**
   - Analyze revenue lift by room_type, property_type

2. **How does vibe score affect price sensitivity?**
   - Compare optimal price changes in high-vibe vs low-vibe areas

3. **What's the revenue opportunity at scale?**
   - Sum potential revenue lift across all listings

4. **How much price flexibility do hosts have?**
   - Measure width of safe bands (occ_90 ≥ 0.75)

---

## Next Steps After Task 5

1. Task 6: Interactive visualizations
2. Create Streamlit app for user input
3. Generate final report with business recommendations
4. Prepare presentation slides

---

## Estimated Timeline

- Script development: 30 min
- Testing and debugging: 20 min
- Visualization creation: 30 min
- Analysis and documentation: 20 min
- **Total: 1.5-2 hours**

---

**Ready to implement!** 🚀

---

## Using Claude Code for Task 5

**For AI-assisted implementation:**
- See [CLAUDE.md](CLAUDE.md) for detailed prompts and workflows
- Section 5 covers Task 5 (Revenue Optimization) specifically
- Contains example prompts for:
  - Script creation and debugging
  - Visualization generation
  - Performance optimization
  - Error handling

**Quick Start Prompt:**
```
"Create scripts/05_revenue_optimizer.py following TASK_5_PLAN.md.
Load the trained XGBoost model and generate revenue curves for test listings.
Include progress tracking and create all specified visualizations."
```
