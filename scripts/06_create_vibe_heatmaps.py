"""
CREATE INTERACTIVE VIBE HEAT MAPS FOR STREAMLIT APP

Generates interactive Folium heat maps for all three cities with
neighborhood vibe scores visualized using a dark blue -> bright red
color gradient.

Outputs: Interactive HTML maps saved to data/{city}/outputs/vibe_map_app.html

Author: Vibe-Aware Pricing Team
Date: 2025-11-13
"""

import pandas as pd
import numpy as np
import folium
from folium import plugins
from pathlib import Path
import sys

# Configuration
CITIES = ['london', 'austin', 'nyc']
BASE_DIR = Path(__file__).parent.parent

# Austin zip code to neighborhood name mapping
AUSTIN_ZIP_TO_NAME = {
    "78701": "Downtown Austin",
    "78702": "East Austin / Holly",
    "78703": "West Campus / Clarksville",
    "78704": "South Congress (SoCo) / Bouldin Creek",
    "78705": "University of Texas / Hyde Park",
    "78721": "Montopolis / Riverside",
    "78722": "Mueller / Cherrywood",
    "78723": "Windsor Park / Georgian Acres",
    "78724": "Del Valle",
    "78725": "Pleasant Valley",
    "78726": "Four Points",
    "78727": "North Lamar / Metric",
    "78728": "Anderson Mill / Jollyville",
    "78729": "Anderson Mill West",
    "78730": "Barton Creek / Lost Creek",
    "78731": "Tarrytown / West Lake Hills",
    "78732": "Steiner Ranch",
    "78733": "Bee Cave / Lakeway",
    "78734": "Lakeway / Bee Cave",
    "78735": "Circle C Ranch / Oak Hill",
    "78736": "Davenport Ranch",
    "78737": "Driftwood / Dripping Springs",
    "78738": "Bee Cave",
    "78739": "Barton Creek",
    "78741": "South Austin / St. Edwards",
    "78742": "Del Valle / Airport",
    "78744": "South Austin / Manchaca",
    "78745": "South Lamar / Zilker",
    "78746": "West Lake Hills / Rollingwood",
    "78747": "Shady Hollow / Sunset Valley",
    "78748": "Circle C / Slaughter",
    "78749": "Southwest Austin / Westlake",
    "78750": "Avery Ranch / Wells Branch",
    "78751": "North Loop / Crestview",
    "78752": "North Austin / Brentwood",
    "78753": "North Austin / Georgian Acres",
    "78754": "Windsor Park",
    "78756": "Rosedale / Allandale",
    "78757": "Crestview / Brentwood",
    "78758": "North Lamar / Tech Ridge",
    "78759": "Great Hills / Arboretum",
    "78660": "Pflugerville",
    "78717": "Cedar Park",
    "78613": "Cedar Park West"
}

# Color gradient: dark blue (low) -> bright red (high)
COLOR_SCALE = [
    (0.0, '#08519c'),   # Dark blue
    (0.2, '#3182bd'),   # Medium blue
    (0.4, '#6baed6'),   # Light blue
    (0.6, '#fee391'),   # Yellow
    (0.8, '#fc8d59'),   # Orange
    (1.0, '#b30000')    # Bright red
]

def create_colormap():
    """Create continuous colormap from dark blue to bright red"""
    from branca.colormap import LinearColormap
    return LinearColormap(
        colors=['#08519c', '#3182bd', '#6baed6', '#fee391', '#fc8d59', '#b30000'],
        vmin=0,
        vmax=100,
        caption='Neighborhood Vibe Score'
    )

def compute_neighborhood_centroids(city):
    """
    Compute geographic centroids for each neighborhood

    Args:
        city: City name (london, austin, nyc)

    Returns:
        DataFrame with neighbourhood, latitude, longitude
    """
    print(f"  Computing neighborhood centroids for {city}...")

    data_dir = BASE_DIR / f'data/{city}'
    listings_file = list(data_dir.glob('raw/listings_*.csv'))[0]

    # Load listings (only need neighbourhood and coordinates)
    df = pd.read_csv(listings_file, low_memory=False,
                     usecols=['neighbourhood_cleansed', 'latitude', 'longitude'])

    # Clean neighbourhood names (handle both string and numeric)
    df['neighbourhood'] = df['neighbourhood_cleansed'].astype(str).str.strip().str.replace('.0', '', regex=False)

    # Compute centroids (mean lat/long per neighbourhood)
    centroids = df.groupby('neighbourhood').agg({
        'latitude': 'mean',
        'longitude': 'mean'
    }).reset_index()

    print(f"    ✓ Computed centroids for {len(centroids)} neighborhoods")

    return centroids

def create_vibe_heatmap(city):
    """
    Create interactive Folium heat map for a city

    Args:
        city: City name (london, austin, nyc)
    """
    print(f"\n[Creating vibe heat map for {city.upper()}]")

    data_dir = BASE_DIR / f'data/{city}'
    output_dir = data_dir / 'outputs'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load vibe scores
    vibe_file = data_dir / 'raw/01_vibe_features_for_modeling.csv'
    vibes = pd.read_csv(vibe_file)
    vibes['neighbourhood'] = vibes['neighbourhood'].astype(str).str.strip().str.replace('.0', '', regex=False)

    # Compute centroids from listings
    centroids = compute_neighborhood_centroids(city)

    # Join vibe scores with centroids
    map_data = centroids.merge(vibes[['neighbourhood', 'vibe_score']],
                                on='neighbourhood',
                                how='left')

    # Drop neighborhoods with missing vibe scores or coordinates
    map_data = map_data.dropna(subset=['vibe_score', 'latitude', 'longitude'])

    print(f"  ✓ Joined data: {len(map_data)} neighborhoods with vibe scores")

    # Determine map center
    center_lat = map_data['latitude'].mean()
    center_lon = map_data['longitude'].mean()

    # City-specific zoom levels
    zoom_levels = {'london': 10, 'austin': 11, 'nyc': 11}

    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_levels.get(city, 10),
        tiles='CartoDB positron'  # Clean, light background
    )

    # Create colormap
    colormap = create_colormap()
    colormap.add_to(m)

    # Add circle markers for each neighborhood
    for idx, row in map_data.iterrows():
        # Determine color based on vibe score
        color = colormap(row['vibe_score'])

        # Size based on vibe score (larger = higher vibe)
        radius = 300 + (row['vibe_score'] / 100) * 700  # 300-1000m radius

        # Format neighborhood name (friendly name for Austin)
        neighbourhood_display = row['neighbourhood']
        if city == 'austin':
            zip_code = str(row['neighbourhood'])
            friendly_name = AUSTIN_ZIP_TO_NAME.get(zip_code, f"Austin {zip_code}")
            neighbourhood_display = f"{friendly_name} ({zip_code})"

        # Create popup with neighborhood info
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4 style="margin-bottom: 5px;">{neighbourhood_display}</h4>
            <p style="margin: 5px 0;">
                <b>Vibe Score:</b> {row['vibe_score']:.1f}/100
            </p>
        </div>
        """

        # Add circle marker
        folium.Circle(
            location=[row['latitude'], row['longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=250),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            opacity=0.8,
            weight=2
        ).add_to(m)

    # Add title
    title_html = f'''
    <div style="position: fixed;
                top: 10px; left: 50px; width: 400px; height: 60px;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:16px; padding: 10px; border-radius: 5px;">
        <h4 style="margin: 0;">{city.title()} Neighborhood Vibe Scores</h4>
        <p style="margin: 5px 0; font-size: 12px;">Darker blue = lower vibe | Brighter red = higher vibe</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Save map
    output_path = output_dir / 'vibe_map_app.html'
    m.save(str(output_path))

    print(f"  ✓ Saved interactive map: {output_path}")
    print(f"  ✓ Vibe score range: {map_data['vibe_score'].min():.1f} - {map_data['vibe_score'].max():.1f}")

    return output_path

def main():
    """Create vibe heat maps for all cities"""
    print("=" * 80)
    print("CREATING VIBE HEAT MAPS FOR STREAMLIT APP")
    print("=" * 80)
    print(f"Cities: {', '.join([c.title() for c in CITIES])}")
    print(f"Color scheme: Dark Blue (low) → Bright Red (high)")
    print("=" * 80)

    created_maps = []

    for city in CITIES:
        try:
            output_path = create_vibe_heatmap(city)
            created_maps.append(str(output_path))
        except Exception as e:
            print(f"  ✗ Error creating map for {city}: {e}")
            continue

    print("\n" + "=" * 80)
    print("VIBE HEAT MAPS COMPLETE ✅")
    print("=" * 80)
    print(f"\nCreated {len(created_maps)} interactive maps:")
    for path in created_maps:
        print(f"  • {path}")
    print("\nThese maps are ready to integrate into the Streamlit app!")
    print("=" * 80)

if __name__ == '__main__':
    main()
