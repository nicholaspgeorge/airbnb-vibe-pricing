"""
EXTRACT COMPREHENSIVE AMENITIES LIST

Parses amenities from all three cities' training data and creates a master
amenities list for the Streamlit app checklist interface.

Outputs: amenities_master_list.json in data/ directory

Author: Vibe-Aware Pricing Team
Date: 2025-11-13
"""

import pandas as pd
import json
import ast
from pathlib import Path
from collections import Counter

# Configuration
CITIES = ['london', 'austin', 'nyc']
BASE_DIR = Path(__file__).parent.parent
OUTPUT_FILE = BASE_DIR / 'data/amenities_master_list.json'

def parse_amenities_string(amenities_str):
    """
    Parse amenities from string representation

    Args:
        amenities_str: String like '["WiFi", "Kitchen", "TV"]' or similar

    Returns:
        List of amenity names
    """
    if pd.isna(amenities_str):
        return []

    try:
        # Try parsing as JSON/Python list
        if isinstance(amenities_str, str):
            # Remove any special characters and parse
            amenities_str = amenities_str.strip()
            if amenities_str.startswith('[') and amenities_str.endswith(']'):
                return ast.literal_eval(amenities_str)
            elif amenities_str.startswith('{') and amenities_str.endswith('}'):
                # Handle set notation
                return list(ast.literal_eval(amenities_str))
            else:
                # Try splitting by common delimiters
                return [a.strip() for a in amenities_str.split(',') if a.strip()]
        elif isinstance(amenities_str, list):
            return amenities_str
        else:
            return []
    except Exception as e:
        # If parsing fails, return empty list
        return []

def extract_amenities_from_city(city):
    """
    Extract all unique amenities from a city's listings

    Args:
        city: City name (london, austin, nyc)

    Returns:
        Set of amenity names
    """
    print(f"  Extracting amenities from {city.title()}...")

    data_dir = BASE_DIR / f'data/{city}'

    # Try to load from raw listings first (has full amenities list)
    listings_file = list(data_dir.glob('raw/listings_*.csv'))[0]

    # Load amenities column only
    try:
        df = pd.read_csv(listings_file, low_memory=False, usecols=['amenities'])
    except:
        # If amenities column doesn't exist in raw, try processed
        train_file = data_dir / f'processed/features_{city}_train.parquet'
        df = pd.read_parquet(train_file, columns=['amenities'])

    # Parse all amenities
    all_amenities = set()
    amenities_counter = Counter()

    for amenities_str in df['amenities']:
        parsed = parse_amenities_string(amenities_str)
        for amenity in parsed:
            if amenity:  # Skip empty strings
                amenity_clean = amenity.strip()
                all_amenities.add(amenity_clean)
                amenities_counter[amenity_clean] += 1

    print(f"    ✓ Found {len(all_amenities)} unique amenities")
    print(f"    ✓ Total listings analyzed: {len(df):,}")

    # Return top amenities by frequency (for reference)
    top_10 = amenities_counter.most_common(10)
    print(f"    ✓ Top 10 most common:")
    for amenity, count in top_10:
        print(f"       - {amenity}: {count:,} listings ({count/len(df)*100:.1f}%)")

    return all_amenities

def main():
    """Extract amenities from all cities and create master list"""
    print("=" * 80)
    print("EXTRACTING COMPREHENSIVE AMENITIES LIST")
    print("=" * 80)
    print(f"Cities: {', '.join([c.title() for c in CITIES])}")
    print("=" * 80)
    print()

    # Extract amenities from each city
    all_amenities = set()

    for city in CITIES:
        try:
            city_amenities = extract_amenities_from_city(city)
            all_amenities.update(city_amenities)
            print()
        except Exception as e:
            print(f"  ✗ Error extracting from {city}: {e}")
            print()
            continue

    # Sort alphabetically
    amenities_list = sorted(list(all_amenities))

    print("=" * 80)
    print(f"MASTER AMENITIES LIST: {len(amenities_list)} unique amenities")
    print("=" * 80)

    # Categorize amenities (for better UX in app)
    categories = {
        "Essentials": [],
        "Kitchen & Dining": [],
        "Bathroom": [],
        "Bedroom & Laundry": [],
        "Entertainment": [],
        "Heating & Cooling": [],
        "Internet & Office": [],
        "Outdoor": [],
        "Safety": [],
        "Accessibility": [],
        "Other": []
    }

    # Categorization keywords
    keywords = {
        "Essentials": ['wifi', 'towels', 'bed sheets', 'soap', 'toilet paper', 'hangers', 'iron'],
        "Kitchen & Dining": ['kitchen', 'microwave', 'coffee', 'refrigerator', 'fridge', 'oven', 'stove', 'dishwasher', 'dishes', 'silverware'],
        "Bathroom": ['shampoo', 'conditioner', 'body soap', 'hot water', 'shower gel', 'hair dryer'],
        "Bedroom & Laundry": ['washer', 'dryer', 'laundry', 'bedroom', 'bed'],
        "Entertainment": ['tv', 'cable', 'netflix', 'roku', 'game', 'books', 'sound system'],
        "Heating & Cooling": ['heating', 'air conditioning', 'ac ', 'fireplace', 'fan'],
        "Internet & Office": ['wifi', 'ethernet', 'desk', 'office', 'workspace', 'printer'],
        "Outdoor": ['balcony', 'patio', 'backyard', 'garden', 'bbq', 'grill', 'outdoor', 'pool', 'beach'],
        "Safety": ['smoke detector', 'carbon monoxide', 'fire extinguisher', 'first aid', 'lock', 'safe'],
        "Accessibility": ['accessible', 'wheelchair', 'elevator', 'wide doorway', 'step-free', 'grab bars'],
    }

    # Categorize each amenity
    for amenity in amenities_list:
        amenity_lower = amenity.lower()
        categorized = False

        for category, kws in keywords.items():
            if any(kw in amenity_lower for kw in kws):
                categories[category].append(amenity)
                categorized = True
                break

        if not categorized:
            categories["Other"].append(amenity)

    # Create output data structure
    output_data = {
        "all_amenities": amenities_list,
        "total_count": len(amenities_list),
        "categories": {cat: items for cat, items in categories.items() if items}
    }

    # Save to JSON
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✓ Saved master amenities list: {OUTPUT_FILE}")
    print(f"\nBreakdown by category:")
    for category, items in sorted(categories.items()):
        if items:
            print(f"  {category}: {len(items)} amenities")

    print("\n" + "=" * 80)
    print("AMENITIES EXTRACTION COMPLETE ✅")
    print("=" * 80)
    print(f"\nThe master amenities list is ready for the Streamlit app!")
    print("=" * 80)

if __name__ == '__main__':
    main()
