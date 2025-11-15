"""
VIBE-AWARE AIRBNB PRICING APP - HOME PAGE

Landing page with city selection and vibe map exploration

Author: Nicholas George, Sahil Medepalli, Heath Verhasselt
Course: MIS5460 Advanced Business Analytics, Fall 2025
"""

import streamlit as st
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Vibe-Aware Airbnb Pricing",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #08519c, #b30000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1.5rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .city-card {
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 1rem 0;
        transition: transform 0.2s;
    }
    .city-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .feature-box {
        padding: 1.5rem;
        background-color: white;
        border-radius: 8px;
        border-left: 4px solid #08519c;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🏠 Vibe-Aware Airbnb Pricing</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Data-Driven Price Recommendations for Your Rental Property</div>', unsafe_allow_html=True)

# Introduction
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Welcome to the Future of Airbnb Pricing")

    st.markdown("""
    Our **vibe-aware pricing engine** helps you determine the optimal price for your Airbnb rental
    property by analyzing **148,000+ listings** across three major cities and incorporating the
    **neighborhood vibe** that guests actually care about.

    #### How It Works:

    1. **Select Your City** - Choose from London, Austin, or NYC
    2. **Explore Neighborhood Vibes** - See interactive heat maps showing which neighborhoods command premium prices
    3. **Enter Property Details** - Tell us about your property (bedrooms, amenities, location)
    4. **Get Your Price Band** - Receive a recommended price range based on similar high-performing listings
    5. **Optimize Revenue** - Use our slider to see how different prices affect your expected occupancy
    """)

with col2:
    st.markdown("### Key Features")

    st.markdown("""
    <div class="feature-box">
        <strong>📊 Data-Driven</strong><br>
        Based on 148K+ real listings
    </div>

    <div class="feature-box">
        <strong>🗺️ Vibe-Aware</strong><br>
        Incorporates neighborhood sentiment
    </div>

    <div class="feature-box">
        <strong>🎯 Accurate</strong><br>
        Proven 47-74% revenue lift potential
    </div>

    <div class="feature-box">
        <strong>⚡ Real-Time</strong><br>
        Instant price predictions
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# City Selection
st.markdown("## Choose Your City")
st.markdown("Select a city to get started with price recommendations or explore neighborhood vibe maps:")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="city-card">
        <h3>🎡 London</h3>
        <p><strong>96,871</strong> listings analyzed</p>
        <p><strong>33</strong> neighborhoods</p>
        <p><strong>52.4%</strong> median revenue lift</p>
        <p><em>Vibe range: 15-83</em></p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📍 Analyze London Property", use_container_width=True, type="primary"):
        st.switch_page("pages/1_🎡_London.py")

    if st.button("🗺️ View London Vibe Map", use_container_width=True):
        st.switch_page("pages/4_🗺️_Vibe_Maps.py")

with col2:
    st.markdown("""
    <div class="city-card">
        <h3>🤠 Austin</h3>
        <p><strong>15,187</strong> listings analyzed</p>
        <p><strong>44</strong> neighborhoods</p>
        <p><strong>73.8%</strong> median revenue lift</p>
        <p><em>Vibe range: 7-100</em></p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📍 Analyze Austin Property", use_container_width=True, type="primary"):
        st.switch_page("pages/2_🤠_Austin.py")

    if st.button("🗺️ View Austin Vibe Map", use_container_width=True):
        st.switch_page("pages/4_🗺️_Vibe_Maps.py")

with col3:
    st.markdown("""
    <div class="city-card">
        <h3>🗽 NYC</h3>
        <p><strong>36,111</strong> listings analyzed</p>
        <p><strong>224</strong> neighborhoods</p>
        <p><strong>46.6%</strong> median revenue lift</p>
        <p><em>Vibe range: 11-100</em></p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📍 Analyze NYC Property", use_container_width=True, type="primary"):
        st.switch_page("pages/3_🗽_NYC.py")

    if st.button("🗺️ View NYC Vibe Map", use_container_width=True):
        st.switch_page("pages/4_🗺️_Vibe_Maps.py")

st.markdown("---")

# About Section
st.markdown("## About This Project")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### The Vibe Hypothesis

    We hypothesized that the **subjective "vibe" of a neighborhood** matters economically.
    Guests don't just pay for beds and bathrooms—they pay for the experience of staying
    in a lively nightlife district versus a quiet family neighborhood.

    Using **natural language processing** on thousands of guest reviews, we quantified 11 vibe
    dimensions for each neighborhood:

    - 🚶 Walkability
    - 🛡️ Safety
    - 🎉 Nightlife
    - 🤫 Quietness
    - 👨‍👩‍👧‍👦 Family-Friendliness
    - 🏘️ Local Authenticity
    - 🚇 Convenience
    - 🍽️ Food Scene
    - ✨ Liveliness
    - 💎 Charm
    """)

with col2:
    st.markdown("""
    ### The Results

    Our models proved that vibe features contribute **23-33% of total model importance**—
    often ranking as the **#1 most important feature** above even bedrooms or amenities!

    #### Revenue Opportunities Discovered:

    - **73-94%** of hosts are underpricing their listings
    - **47-74%** median revenue lift potential
    - **$500M+** total addressable market across the three cities

    #### Model Performance:

    - XGBoost with monotonic constraints achieved best performance
    - 11-37% R² on occupancy prediction (0.11 Austin, 0.26 London, 0.37 NYC)
    - MAE of 22-24 percentage points (consistent across all cities)
    - 29-55% reduction in monotonicity violations vs. baseline
    - Validated across 3 diverse markets
    """)

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>Created by:</strong> Nicholas George, Sahil Medepalli, Heath Verhasselt</p>
    <p>MIS5460 Advanced Business Analytics | Iowa State University | Fall 2025</p>
    <p><em>Powered by XGBoost, SHAP, and Natural Language Processing</em></p>
</div>
""", unsafe_allow_html=True)
