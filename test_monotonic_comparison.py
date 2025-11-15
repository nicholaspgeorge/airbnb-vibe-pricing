"""
Quick script to compare baseline vs monotonic model predictions
"""
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
CITY = 'london'
DATA_DIR = Path(f'data/{CITY}')

# Load models
baseline_model = pickle.load(open(DATA_DIR / 'models/xgboost_with_vibe_baseline.pkl', 'rb'))
monotonic_model = pickle.load(open(DATA_DIR / 'models/xgboost_with_vibe.pkl', 'rb'))

# Load test data
test_df = pd.read_parquet(DATA_DIR / f'processed/features_{CITY}_test.parquet')

# Get one sample property
sample = test_df.sample(1, random_state=42)
print(f"\nTesting on: {sample['neighbourhood'].values[0]}")
print(f"Current price: £{sample['price_clean'].values[0]:.0f}")
print(f"Bedrooms: {sample['bedrooms'].values[0]}")
print(f"Room type: {sample['room_type'].values[0]}")

# Create price grid
original_price = sample['price_clean'].values[0]
prices = np.linspace(original_price * 0.5, original_price * 2, 10)

print("\n" + "="*70)
print("Price | Baseline Occ | Monotonic Occ | Difference | Violation?")
print("="*70)

prev_baseline = None
prev_monotonic = None
baseline_violations = 0
monotonic_violations = 0

for price in prices:
    # Update price
    test_sample = sample.copy()
    test_sample['price_clean'] = price
    test_sample['price_per_person'] = price / test_sample['accommodates']
    
    # Predict with both models
    baseline_pred = baseline_model.predict(test_sample.drop(columns=['occupancy_rate_90', 'high_demand_90']))[0]
    monotonic_pred = monotonic_model.predict(test_sample.drop(columns=['occupancy_rate_90', 'high_demand_90']))[0]
    
    # Check for violations
    baseline_violation = ""
    monotonic_violation = ""
    
    if prev_baseline is not None and baseline_pred > prev_baseline:
        baseline_violation = "⚠️ VIOLATION"
        baseline_violations += 1
    
    if prev_monotonic is not None and monotonic_pred > prev_monotonic:
        monotonic_violation = "⚠️ VIOLATION"
        monotonic_violations += 1
    
    diff = baseline_pred - monotonic_pred
    
    print(f"£{price:4.0f} |    {baseline_pred:.3f}     |     {monotonic_pred:.3f}     | {diff:+.3f}     | {baseline_violation or monotonic_violation or '✓'}")
    
    prev_baseline = baseline_pred
    prev_monotonic = monotonic_pred

print("="*70)
print(f"\nBaseline violations: {baseline_violations}/9 price increases")
print(f"Monotonic violations: {monotonic_violations}/9 price increases")
print("\n✓ Lower violations = better economic logic!")

