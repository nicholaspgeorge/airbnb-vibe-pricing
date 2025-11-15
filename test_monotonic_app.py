"""
Quick test to verify monotonic constraints work in the app
"""
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
CITY = 'london'
DATA_DIR = Path(f'data/{CITY}')

# Load active model (should be monotonic)
active_model = pickle.load(open(DATA_DIR / 'models/xgboost_with_vibe.pkl', 'rb'))

# Load test data
test_df = pd.read_parquet(DATA_DIR / f'processed/features_{CITY}_test.parquet')

# Get feature columns (exclude targets)
feature_cols = [col for col in test_df.columns if col not in ['occupancy_rate_90', 'high_demand_90']]

# Get one sample property
sample = test_df.sample(1, random_state=42)
print("\n" + "="*70)
print("TESTING MONOTONIC CONSTRAINTS IN ACTIVE MODEL")
print("="*70)
print(f"\nProperty Details:")
print(f"  Neighborhood: {sample['neighbourhood'].values[0]}")
print(f"  Current price: £{sample['price_clean'].values[0]:.0f}")
print(f"  Bedrooms: {sample['bedrooms'].values[0]}")
print(f"  Room type: {sample['room_type'].values[0]}")

# Create price grid
original_price = sample['price_clean'].values[0]
prices = np.linspace(original_price * 0.5, original_price * 2, 15)

print("\n" + "="*70)
print("Price (£) | Predicted Occupancy | Change from Previous | Status")
print("="*70)

prev_occ = None
violations = 0

for price in prices:
    # Update price
    test_sample = sample[feature_cols].copy()
    test_sample['price_clean'] = price
    test_sample['price_per_person'] = price / test_sample['accommodates']
    
    # Predict
    pred_occ = active_model.predict(test_sample)[0]
    
    # Check for violations
    status = ""
    if prev_occ is not None:
        change = pred_occ - prev_occ
        if change > 0.001:  # Small tolerance for floating point
            status = "⚠️ VIOLATION!"
            violations += 1
        else:
            status = "✓ Good"
        print(f"  {price:5.0f}   |       {pred_occ:.4f}        |      {change:+.4f}        | {status}")
    else:
        print(f"  {price:5.0f}   |       {pred_occ:.4f}        |       (baseline)      | ✓ Good")
    
    prev_occ = pred_occ

print("="*70)
print(f"\n📊 Results:")
print(f"   Total price points tested: 15")
print(f"   Monotonicity violations: {violations}/14 price increases")
print(f"   Violation rate: {violations/14*100:.1f}%")

if violations == 0:
    print("\n   ✅ PERFECT! No violations - occupancy always decreases with price")
elif violations <= 2:
    print("\n   ✅ EXCELLENT! Very few violations (<15%) - mostly monotonic")
elif violations <= 4:
    print("\n   ⚠️  GOOD: Some violations but much better than baseline")
else:
    print("\n   ❌ NEEDS WORK: Too many violations")

print("\n💡 This is what you'll see in the app's revenue curves!")
print("   Open http://localhost:8501 to see it visually.\n")

