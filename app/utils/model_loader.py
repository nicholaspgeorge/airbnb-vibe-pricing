"""
MODEL LOADING UTILITIES

Handles loading of trained models and data for predictions

Author: Vibe-Aware Pricing Team
"""

import pickle
import pandas as pd
import json
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).parent.parent.parent

# Austin zip code to neighborhood name mapping
AUSTIN_ZIP_TO_NAME = {
    "78701": "Downtown Austin",
    "78702": "East Austin / Holly",
    "78703": "West Campus / Clarksville",
    "78704": "South Congress (SoCo)",
    "78705": "UT / Hyde Park",
    "78721": "Montopolis / Riverside",
    "78722": "Mueller / Cherrywood",
    "78723": "Windsor Park",
    "78724": "Del Valle",
    "78725": "Pleasant Valley",
    "78726": "Four Points",
    "78727": "North Lamar",
    "78728": "Anderson Mill",
    "78729": "Anderson Mill West",
    "78730": "Barton Creek",
    "78731": "Tarrytown",
    "78732": "Steiner Ranch",
    "78733": "Bee Cave / Lakeway",
    "78734": "Lakeway",
    "78735": "Circle C Ranch",
    "78736": "Davenport Ranch",
    "78737": "Driftwood",
    "78738": "Bee Cave",
    "78739": "Barton Creek",
    "78741": "South Austin",
    "78742": "Del Valle / Airport",
    "78744": "South Manchaca",
    "78745": "South Lamar / Zilker",
    "78746": "West Lake Hills",
    "78747": "Shady Hollow",
    "78748": "Circle C",
    "78749": "Southwest Austin",
    "78750": "Avery Ranch",
    "78751": "North Loop / Crestview",
    "78752": "North Austin",
    "78753": "Georgian Acres",
    "78754": "Windsor Park",
    "78756": "Rosedale / Allandale",
    "78757": "Crestview / Brentwood",
    "78758": "Tech Ridge",
    "78759": "Great Hills / Arboretum",
    "78660": "Pflugerville",
    "78717": "Cedar Park",
    "78613": "Cedar Park West"
}

@st.cache_resource
def load_models(city):
    """
    Load trained models for a city

    Args:
        city: City name (london, austin, nyc)

    Returns:
        dict with xgboost_model, ols_model
    """
    data_dir = BASE_DIR / f'data/{city}'
    models_dir = data_dir / 'models'

    models = {}

    # Load XGBoost model (with vibe)
    xgb_path = models_dir / 'xgboost_with_vibe.pkl'
    with open(xgb_path, 'rb') as f:
        models['xgboost'] = pickle.load(f)

    # Load OLS model (for price residuals)
    ols_path = models_dir / 'ols_price_control.pkl'
    with open(ols_path, 'rb') as f:
        models['ols'] = pickle.load(f)

    # Note: k-NN model is built on-the-fly in predictor.py, no need to load

    return models

@st.cache_data
def load_vibe_data(city):
    """
    Load neighborhood vibe scores

    Args:
        city: City name (london, austin, nyc)

    Returns:
        DataFrame with neighbourhood and vibe features
    """
    data_dir = BASE_DIR / f'data/{city}'
    vibe_file = data_dir / 'raw/01_vibe_features_for_modeling.csv'

    vibes = pd.read_csv(vibe_file)
    vibes['neighbourhood'] = vibes['neighbourhood'].astype(str).str.strip()

    return vibes

@st.cache_data
def load_training_data(city):
    """
    Load training data for reference

    Args:
        city: City name (london, austin, nyc)

    Returns:
        DataFrame with training features
    """
    data_dir = BASE_DIR / f'data/{city}'
    train_file = data_dir / f'processed/features_{city}_train.parquet'

    return pd.read_parquet(train_file)

@st.cache_data
def get_neighborhoods(city):
    """
    Get list of neighborhoods for a city

    For Austin, returns friendly names like "Downtown Austin (78701)"
    For other cities, returns neighborhood names as-is

    Args:
        city: City name (london, austin, nyc)

    Returns:
        Sorted list of neighborhood names
    """
    vibes = load_vibe_data(city)
    neighborhoods = vibes['neighbourhood'].unique().tolist()

    if city == 'austin':
        # Convert zip codes to friendly names with zip in parentheses
        friendly_names = []
        for zip_code in neighborhoods:
            name = AUSTIN_ZIP_TO_NAME.get(str(zip_code), f"Austin {zip_code}")
            friendly_names.append(f"{name} ({zip_code})")
        return sorted(friendly_names)
    else:
        return sorted(neighborhoods)

@st.cache_data
def get_vibe_for_neighborhood(city, neighbourhood):
    """
    Get vibe scores for a specific neighborhood

    Args:
        city: City name
        neighbourhood: Neighborhood name

    Returns:
        dict with vibe scores
    """
    vibes = load_vibe_data(city)
    row = vibes[vibes['neighbourhood'] == neighbourhood]

    if len(row) == 0:
        return None

    return row.iloc[0].to_dict()

@st.cache_data
def get_average_price(city, neighbourhood=None, property_type=None):
    """
    Get average price for a city, optionally filtered by neighborhood and property type

    Args:
        city: City name
        neighbourhood: Optional neighborhood name
        property_type: Optional property type

    Returns:
        Average price as integer
    """
    train_data = load_training_data(city)

    # Filter data
    filtered = train_data.copy()

    if neighbourhood and 'neighbourhood' in filtered.columns:
        filtered = filtered[filtered['neighbourhood'] == neighbourhood]

    if property_type and 'room_type' in filtered.columns:
        filtered = filtered[filtered['room_type'] == property_type]

    # Get median price (more robust than mean)
    if 'price_clean' in filtered.columns and len(filtered) > 0:
        return int(filtered['price_clean'].median())

    # Fallback to overall median if no matches
    if 'price_clean' in train_data.columns:
        return int(train_data['price_clean'].median())

    # Final fallback
    return 100

def extract_zip_from_friendly_name(friendly_name):
    """
    Extract zip code from friendly name like "Downtown Austin (78701)"

    Args:
        friendly_name: Neighborhood name in format "Name (12345)"

    Returns:
        Zip code as string, or original name if no match
    """
    import re
    match = re.search(r'\((\d{5})\)$', friendly_name)
    if match:
        return match.group(1)
    return friendly_name

def parse_neighbourhood_for_city(city, neighbourhood_display):
    """
    Parse displayed neighborhood name to get the actual value for backend

    For Austin: Extracts zip code from "Name (78701)" format
    For other cities: Returns as-is

    Args:
        city: City name
        neighbourhood_display: Display name from dropdown

    Returns:
        Actual neighbourhood value for backend queries
    """
    if city == 'austin':
        return extract_zip_from_friendly_name(neighbourhood_display)
    return neighbourhood_display
