"""
VIBE MAPS EXPLORATION PAGE

Interactive neighborhood vibe heat maps for all three cities

Author: Vibe-Aware Pricing Team
"""

import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="Neighborhood Vibe Maps",
    page_icon="🗺️",
    layout="wide"
)

# Header
st.title("🗺️ Neighborhood Vibe Heat Maps")
st.markdown("Explore how neighborhood vibe varies across our three markets")

# City selection tabs
tab1, tab2, tab3 = st.tabs(["🎡 London", "🤠 Austin", "🗽 NYC"])

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent

with tab1:
    st.markdown("### London Neighborhood Vibes")
    st.markdown("""
    **33 neighborhoods analyzed** | Vibe scores range from 15 to 83

    Color coding: 🔵 Dark Blue = Low Vibe | 🔴 Bright Red = High Vibe

    Click on any neighborhood circle to see its vibe score and characteristics.
    """)

    # Load and display map
    london_map_path = BASE_DIR / 'data/london/outputs/vibe_map_app.html'

    if london_map_path.exists():
        with open(london_map_path, 'r', encoding='utf-8') as f:
            map_html = f.read()
        components.html(map_html, height=600, scrolling=True)
    else:
        st.error("London vibe map not found. Please run scripts/06_create_vibe_heatmaps.py")

with tab2:
    st.markdown("### Austin Neighborhood Vibes")
    st.markdown("""
    **44 neighborhoods analyzed** | Vibe scores range from 7 to 100

    Color coding: 🔵 Dark Blue = Low Vibe | 🔴 Bright Red = High Vibe

    Click on any neighborhood circle to see its vibe score and characteristics.
    """)

    # Load and display map
    austin_map_path = BASE_DIR / 'data/austin/outputs/vibe_map_app.html'

    if austin_map_path.exists():
        with open(austin_map_path, 'r', encoding='utf-8') as f:
            map_html = f.read()
        components.html(map_html, height=600, scrolling=True)
    else:
        st.error("Austin vibe map not found. Please run scripts/06_create_vibe_heatmaps.py")

with tab3:
    st.markdown("### NYC Neighborhood Vibes")
    st.markdown("""
    **224 neighborhoods analyzed** | Vibe scores range from 11 to 100

    Color coding: 🔵 Dark Blue = Low Vibe | 🔴 Bright Red = High Vibe

    Click on any neighborhood circle to see its vibe score and characteristics.
    """)

    # Load and display map
    nyc_map_path = BASE_DIR / 'data/nyc/outputs/vibe_map_app.html'

    if nyc_map_path.exists():
        with open(nyc_map_path, 'r', encoding='utf-8') as f:
            map_html = f.read()
        components.html(map_html, height=600, scrolling=True)
    else:
        st.error("NYC vibe map not found. Please run scripts/06_create_vibe_heatmaps.py")

# Interpretation guide
st.markdown("---")
st.markdown("### How to Interpret Vibe Scores")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **High Vibe (70-100)**
    - Prime entertainment districts
    - Excellent walkability
    - Rich food & nightlife scenes
    - Higher price potential
    - Examples: Hackney (London), West Campus / Clarksville (78703) (Austin), Upper West Side (NYC)
    """)

with col2:
    st.markdown("""
    **Medium Vibe (40-69)**
    - Balanced neighborhoods
    - Good amenities
    - Mix of quiet and lively areas
    - Moderate price potential
    - Examples: Camden (London), Montopolis / Riverside (78721) (Austin), Midtown (NYC)
    """)

with col3:
    st.markdown("""
    **Low Vibe (0-39)**
    - Residential/suburban areas
    - Quieter family neighborhoods
    - Limited nightlife
    - Value-oriented pricing
    - Examples: Barking and Dagenham (London), Circle C Ranch / Oak Hill (78735) (Austin), Soundview (NYC)
    """)

st.markdown("---")

# Call to action
st.markdown("### Ready to Price Your Property?")
st.markdown("Choose a city to get started with personalized price recommendations:")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📍 Analyze London Property", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🎡_London.py")

with col2:
    if st.button("📍 Analyze Austin Property", use_container_width=True, type="primary"):
        st.switch_page("pages/2_🤠_Austin.py")

with col3:
    if st.button("📍 Analyze NYC Property", use_container_width=True, type="primary"):
        st.switch_page("pages/3_🗽_NYC.py")
