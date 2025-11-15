"""
TASK 6: INTERACTIVE NEIGHBORHOOD VIBE MAP

Creates an interactive map showing vibe scores across London neighborhoods
with hover tooltips containing key statistics.

Uses Plotly for cross-platform compatibility (no GeoJSON needed).

Author: Vibe-Aware Pricing Team
Date: 2025-11-07
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Configuration
CITY = 'london'

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / f'data/{CITY}'
VIBE_PATH = DATA_DIR / 'raw/01_neighborhood_vibe_scores.csv'
VIBE_DIM_PATH = DATA_DIR / 'raw/01_neighborhood_vibe_dimensions.csv'
TEST_DATA_PATH = DATA_DIR / 'processed/features_london_test.parquet'
VIZ_DIR = DATA_DIR / 'outputs/visualizations'

print("=" * 80)
print("INTERACTIVE NEIGHBORHOOD VIBE MAP")
print("=" * 80)
print()

# ============================================================================
# Load Data
# ============================================================================

print("[1/4] Loading vibe and listing data...")

# Load vibe scores
vibes = pd.read_csv(VIBE_PATH)
print(f"  ✓ Loaded vibe scores: {len(vibes)} neighborhoods")

# Load vibe dimensions
vibe_dims = pd.read_csv(VIBE_DIM_PATH)
print(f"  ✓ Loaded vibe dimensions: {len(vibe_dims)} neighborhoods")

# Load test data for aggregate stats
test_data = pd.read_parquet(TEST_DATA_PATH)
print(f"  ✓ Loaded test listings: {len(test_data):,} listings")

print()

# ============================================================================
# Create Neighborhood Aggregates
# ============================================================================

print("[2/4] Computing neighborhood statistics...")

# Aggregate by neighborhood
neighborhood_stats = test_data.groupby('neighbourhood').agg({
    'price_clean': ['median', 'count'],
    'occ_90': 'mean',
    'high_demand_90': 'mean',
    'latitude': 'mean',  # Centroid
    'longitude': 'mean'
}).reset_index()

# Flatten column names
neighborhood_stats.columns = [
    'neighbourhood', 'median_price', 'listing_count',
    'avg_occupancy', 'pct_high_demand', 'latitude', 'longitude'
]

# Merge with vibe scores
map_data = vibes.merge(neighborhood_stats, on='neighbourhood', how='left')

# Merge with vibe dimensions
map_data = map_data.merge(vibe_dims[['neighbourhood', 'liveliness_score',
                                      'nightlife_score', 'safety_score',
                                      'walkability_score', 'convenience_score']],
                          on='neighbourhood', how='left')

print(f"  ✓ Created aggregate data for {len(map_data)} neighborhoods")
print()

# ============================================================================
# Create Interactive Map
# ============================================================================

print("[3/4] Creating interactive vibe map...")

# Create custom hover template
map_data['hover_text'] = map_data.apply(lambda row: f"""
<b>{row['neighbourhood']}</b><br>
<br>
<b>Vibe Score:</b> {row['vibe_score']:.1f}/100<br>
<br>
<b>Key Vibe Dimensions:</b><br>
  • Liveliness: {row['liveliness_score']:.1f}<br>
  • Safety: {row['safety_score']:.1f}<br>
  • Nightlife: {row['nightlife_score']:.1f}<br>
  • Walkability: {row['walkability_score']:.1f}<br>
  • Convenience: {row['convenience_score']:.1f}<br>
<br>
<b>Market Statistics:</b><br>
  • Listings: {int(row['listing_count']) if pd.notna(row['listing_count']) else 0}<br>
  • Median Price: £{row['median_price']:.0f}/night<br>
  • Avg Occupancy: {row['avg_occupancy']*100:.1f}%<br>
  • High-Demand: {row['pct_high_demand']*100:.1f}%<br>
""", axis=1)

# Create scatter mapbox
fig = px.scatter_mapbox(
    map_data,
    lat='latitude',
    lon='longitude',
    color='vibe_score',
    size='listing_count',
    hover_name='neighbourhood',
    hover_data={
        'latitude': False,
        'longitude': False,
        'vibe_score': ':.1f',
        'listing_count': ':,',
        'median_price': ':.0f',
        'avg_occupancy': ':.1%'
    },
    color_continuous_scale='YlGnBu',
    size_max=40,
    zoom=10,
    title='London Neighborhood Vibe Scores & Market Statistics',
    labels={
        'vibe_score': 'Vibe Score',
        'listing_count': 'Listings',
        'median_price': 'Median Price (£)',
        'avg_occupancy': 'Avg Occupancy'
    }
)

# Use OpenStreetMap tiles
fig.update_layout(
    mapbox_style='open-street-map',
    mapbox=dict(
        center=dict(lat=51.5074, lon=-0.1278),  # London center
        zoom=10
    ),
    height=700,
    font=dict(size=12),
    title=dict(
        text='London Airbnb: Neighborhood Vibe Scores & Market Performance',
        font=dict(size=18, color='#333'),
        x=0.5,
        xanchor='center'
    ),
    coloraxis_colorbar=dict(
        title='Vibe<br>Score',
        thicknessmode='pixels',
        thickness=20,
        lenmode='pixels',
        len=300,
        yanchor='middle',
        y=0.5
    )
)

# Add annotations
fig.add_annotation(
    text='Bubble size = Number of listings | Color = Vibe score',
    xref='paper', yref='paper',
    x=0.5, y=-0.05,
    showarrow=False,
    font=dict(size=11, color='#666')
)

# Save interactive HTML
output_path = VIZ_DIR / 'vibe_map_interactive.html'
fig.write_html(output_path)
print(f"  ✓ Saved interactive map: {output_path.name}")

print()

# ============================================================================
# Create Summary Statistics
# ============================================================================

print("[4/4] Generating summary insights...")

print("\n" + "=" * 80)
print("VIBE MAP INSIGHTS")
print("=" * 80)

# Top 5 vibe scores
print("\nTop 5 Highest Vibe Neighborhoods:")
top5_vibe = map_data.nlargest(5, 'vibe_score')[['neighbourhood', 'vibe_score', 'median_price']]
for idx, row in top5_vibe.iterrows():
    print(f"  {idx+1}. {row['neighbourhood']}: Vibe={row['vibe_score']:.1f}, Price=£{row['median_price']:.0f}")

# Bottom 5 vibe scores
print("\nBottom 5 Vibe Neighborhoods:")
bottom5_vibe = map_data.nsmallest(5, 'vibe_score')[['neighbourhood', 'vibe_score', 'median_price']]
for idx, row in bottom5_vibe.iterrows():
    print(f"  {idx+1}. {row['neighbourhood']}: Vibe={row['vibe_score']:.1f}, Price=£{row['median_price']:.0f}")

# Vibe-price correlation
vibe_price_corr = map_data[['vibe_score', 'median_price']].corr().iloc[0, 1]
print(f"\nVibe-Price Correlation: {vibe_price_corr:.3f}")
if vibe_price_corr > 0.5:
    print("  → Strong positive correlation! High vibe = higher prices ✓")
elif vibe_price_corr > 0.3:
    print("  → Moderate positive correlation")
else:
    print("  → Weak correlation")

# Market concentration
total_listings = map_data['listing_count'].sum()
top_5_listings = map_data.nlargest(5, 'listing_count')['listing_count'].sum()
concentration_pct = (top_5_listings / total_listings) * 100
print(f"\nMarket Concentration:")
print(f"  Top 5 neighborhoods have {top_5_listings:.0f} / {total_listings:.0f} listings ({concentration_pct:.1f}%)")

print("\n" + "=" * 80)
print("INTERACTIVE VIBE MAP COMPLETE ✅")
print("=" * 80)
print(f"\nOutput: {output_path}")
print("\nTo view: Open the HTML file in any web browser")
print("  • Hover over bubbles for detailed neighborhood stats")
print("  • Zoom and pan to explore different areas")
print("  • Color scale shows vibe intensity (blue=low, green=high)")
print("=" * 80)
