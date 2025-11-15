"""
PREDICTION ENGINE

Handles k-NN price recommendations and XGBoost occupancy predictions

Author: Vibe-Aware Pricing Team
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import streamlit as st

from .model_loader import load_models, load_training_data, load_vibe_data, get_vibe_for_neighborhood

BASE_DIR = Path(__file__).parent.parent.parent

# Constants
K_NEIGHBORS = 25
MIN_HIGH_DEMAND = 5
OCC_THRESHOLD = 0.75

def build_feature_vector(city, property_data, vibe_scores):
    """
    Build feature vector for prediction

    Args:
        city: City name
        property_data: dict with property details
        vibe_scores: dict with vibe features

    Returns:
        dict with all features
    """
    features = property_data.copy()

    # Add vibe features
    for key, value in vibe_scores.items():
        if 'score' in key.lower() or key in ['sentiment_mean', 'sentiment_std', 'subjectivity']:
            features[key] = value

    return features

@st.cache_data
def get_knn_price_recommendation(city, property_data):
    """
    Get k-NN price band recommendation

    Args:
        city: City name
        property_data: dict with bedrooms, bathrooms, accommodates, amenities_count,
                      room_type, neighbourhood, vibe_score

    Returns:
        dict with recommendation results
    """
    # Load training data
    train_data = load_training_data(city)

    # Features for k-NN (match original script)
    knn_features = [
        'bedrooms', 'bathrooms', 'accommodates', 'amenities_count',
        'vibe_score', 'walkability_score', 'safety_score', 'nightlife_score',
        'quietness_score', 'family_friendly_score', 'local_authentic_score',
        'convenience_score', 'food_scene_score', 'liveliness_score', 'charm_score'
    ]

    # Filter train data to required features + price + high_demand
    available_features = [f for f in knn_features if f in train_data.columns]
    train_subset = train_data[available_features + ['price_clean', 'high_demand_90']].dropna()

    # Build input feature vector
    input_features = {}
    for feat in available_features:
        if feat in property_data:
            input_features[feat] = property_data[feat]
        else:
            # Use median from training data
            input_features[feat] = train_subset[feat].median()

    # Create DataFrame for input
    input_df = pd.DataFrame([input_features])

    # Fit scaler on training data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(train_subset[available_features])
    X_input_scaled = scaler.transform(input_df[available_features])

    # Fit k-NN
    knn = NearestNeighbors(n_neighbors=K_NEIGHBORS, metric='euclidean')
    knn.fit(X_train_scaled)

    # Find neighbors
    distances, indices = knn.kneighbors(X_input_scaled)

    # Get neighbor data
    neighbors = train_subset.iloc[indices[0]]

    # Filter to high-demand neighbors
    high_demand_neighbors = neighbors[neighbors['high_demand_90'] == 1]

    if len(high_demand_neighbors) >= MIN_HIGH_DEMAND:
        # Calculate price band
        prices = high_demand_neighbors['price_clean']
        p25 = prices.quantile(0.25)
        p50 = prices.median()
        p75 = prices.quantile(0.75)

        return {
            'success': True,
            'price_low': p25,
            'price_mid': p50,
            'price_high': p75,
            'n_neighbors': len(high_demand_neighbors),
            'confidence': 'High' if len(high_demand_neighbors) >= 10 else 'Medium',
            'message': f"Based on {len(high_demand_neighbors)} similar high-demand properties"
        }
    else:
        return {
            'success': False,
            'n_neighbors': len(high_demand_neighbors),
            'confidence': 'Low',
            'message': f"Only {len(high_demand_neighbors)} similar high-demand properties found (need {MIN_HIGH_DEMAND}+)"
        }

def predict_occupancy(city, property_data, price):
    """
    Predict occupancy at a given price using XGBoost

    Args:
        city: City name
        property_data: dict with property features
        price: Price to test

    Returns:
        Predicted occupancy rate (0-1)
    """
    try:
        # Load models
        models = load_models(city)
        xgb_model = models['xgboost']
        ols_model = models['ols']

        # Build full feature vector
        features = property_data.copy()
        features['price_clean'] = price
        features['price_per_person'] = price / max(features.get('accommodates', 1), 1)

        # Compute epsilon_price using OLS
        ols_features = ['neighbourhood_encoded', 'minimum_nights', 'host_listings_count']
        X_ols = pd.DataFrame([{f: features.get(f, 0) for f in ols_features}])
        price_pred = ols_model.predict(X_ols)[0]
        features['epsilon_price'] = price - price_pred

        # Get expected features for XGBoost
        expected_features = xgb_model.get_booster().feature_names

        # Build feature vector in correct order
        X = pd.DataFrame([{f: features.get(f, 0) for f in expected_features}])

        # Predict
        occ_pred = xgb_model.predict(X)[0]

        # Clip to [0, 1]
        return np.clip(occ_pred, 0, 1)

    except Exception as e:
        st.error(f"Prediction error: {e}")
        return 0.5  # Default fallback

def generate_revenue_curve(city, property_data, current_price, n_points=50):
    """
    Generate revenue curve by testing multiple price points

    Args:
        city: City name
        property_data: dict with property features
        current_price: Current/baseline price
        n_points: Number of price points to test

    Returns:
        DataFrame with price, occupancy, revenue columns
    """
    # Create price grid (0.5x to 2.0x current price)
    min_price = current_price * 0.5
    max_price = current_price * 2.0
    prices = np.linspace(min_price, max_price, n_points)

    results = []

    for price in prices:
        occ = predict_occupancy(city, property_data, price)
        revenue = price * occ * 30  # Monthly revenue

        results.append({
            'price': price,
            'occupancy': occ,
            'monthly_revenue': revenue
        })

    df = pd.DataFrame(results)

    # Find optimal price
    optimal_idx = df['monthly_revenue'].idxmax()
    df['is_optimal'] = False
    df.loc[optimal_idx, 'is_optimal'] = True

    # Mark current price
    current_idx = (df['price'] - current_price).abs().idxmin()
    df['is_current'] = False
    df.loc[current_idx, 'is_current'] = True

    # Mark safe band (occ >= 75%)
    df['is_safe'] = df['occupancy'] >= OCC_THRESHOLD

    return df

def get_optimization_summary(revenue_curve, current_price):
    """
    Get summary of revenue optimization

    Args:
        revenue_curve: DataFrame from generate_revenue_curve
        current_price: Current price

    Returns:
        dict with optimization metrics
    """
    # Current metrics
    current_row = revenue_curve[revenue_curve['is_current']].iloc[0]

    # Optimal metrics
    optimal_row = revenue_curve[revenue_curve['is_optimal']].iloc[0]

    # Safe band
    safe_band = revenue_curve[revenue_curve['is_safe']]

    summary = {
        'current_price': current_price,
        'current_occ': current_row['occupancy'],
        'current_revenue': current_row['monthly_revenue'],

        'optimal_price': optimal_row['price'],
        'optimal_occ': optimal_row['occupancy'],
        'optimal_revenue': optimal_row['monthly_revenue'],

        'revenue_lift_pct': ((optimal_row['monthly_revenue'] - current_row['monthly_revenue']) / current_row['monthly_revenue']) * 100,
        'price_change_pct': ((optimal_row['price'] - current_price) / current_price) * 100,

        'safe_band_low': safe_band['price'].min() if len(safe_band) > 0 else None,
        'safe_band_high': safe_band['price'].max() if len(safe_band) > 0 else None,
        'has_safe_band': len(safe_band) > 0
    }

    return summary
