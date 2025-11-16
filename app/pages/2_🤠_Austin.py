"""
AUSTIN PRICING PAGE - Comprehensive Implementation

Complete property pricing tool with:
- Session state management (fixes slider reset issue)
- Horizontal property input layout (not sidebar)
- Light background vibe profile
- Dual-axis revenue/occupancy chart with 75% threshold
- Interactive price slider that PERSISTS

Author: Vibe-Aware Pricing Team
Created: November 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.model_loader import (
    get_neighborhoods,
    get_vibe_for_neighborhood,
    get_average_price,
    parse_neighbourhood_for_city
)
from utils.predictor import (
    get_knn_price_recommendation,
    generate_revenue_curve,
    get_optimization_summary,
    predict_occupancy
)

# Page config
st.set_page_config(
    page_title="Austin Pricing",
    page_icon="🤠",
    layout="wide"
)

# =============================================================================
# SESSION STATE INITIALIZATION - CRITICAL FOR SLIDER FIX
# =============================================================================
if 'calculated' not in st.session_state:
    st.session_state.calculated = False
if 'property_data' not in st.session_state:
    st.session_state.property_data = {}
if 'revenue_curve' not in st.session_state:
    st.session_state.revenue_curve = None
if 'optimization' not in st.session_state:
    st.session_state.optimization = {}
if 'knn_result' not in st.session_state:
    st.session_state.knn_result = {}
if 'vibe_data' not in st.session_state:
    st.session_state.vibe_data = {}

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    /* Vibe container with light blue gradient */
    .vibe-container {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* Property input section */
    .property-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Recommendation boxes */
    .recommendation-box {
        padding: 1.5rem;
        background-color: #e8f4f8;
        border-radius: 10px;
        border: 2px solid #08519c;
        margin: 1rem 0;
    }

    /* Vibe score badge */
    .vibe-score {
        font-size: 3rem;
        font-weight: bold;
        color: #b30000;
        text-align: center;
    }

    /* Safe zone badge */
    .safe-zone {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# TITLE
# =============================================================================
st.title("🤠 Austin Property Pricing")
st.markdown("**Data-driven price recommendations powered by 15,187 Austin listings**")
st.markdown("---")

# =============================================================================
# PROPERTY INPUT FORM - NOW IN MAIN AREA (NOT SIDEBAR!)
# =============================================================================
st.markdown('<div class="property-section">', unsafe_allow_html=True)
st.subheader("📝 Property Details")

# Load data
BASE_DIR = Path(__file__).parent.parent.parent
with open(BASE_DIR / 'data/amenities_master_list.json', 'r') as f:
    amenities_data = json.load(f)

TOP_AMENITIES = [
    "Wifi", "Kitchen", "Washer", "Dryer", "Air conditioning", "Heating",
    "TV", "Iron", "Hair dryer", "Smoke alarm", "Carbon monoxide alarm",
    "Fire extinguisher", "Basic toiletries (soap, towels, toilet paper)", "Hangers",
    "Bed linens", "Hot water", "Shampoo", "Coffee maker", "Refrigerator",
    "Dishes and silverware", "Cooking basics", "Oven/Stove", "Microwave",
    "Dishwasher", "Freezer", "Dining table", "Private entrance", "Lockbox",
    "Self check-in", "Free street parking", "Paid parking", "Elevator",
    "Gym", "Pool", "Bathtub", "First aid kit", "Laptop friendly workspace",
    "Ethernet connection", "Balcony", "Patio", "BBQ grill", "Garden",
    "Luggage dropoff", "Long term stays allowed", "Pets allowed",
    "Smoking allowed", "Suitable for events", "Family/kid friendly"
]

neighborhoods = get_neighborhoods('austin')

# Row 1: Basic property details (4 columns)
col1, col2, col3, col4 = st.columns(4)

with col1:
    property_type = st.selectbox(
        "Property Type",
        ["Entire home/apt", "Private room", "Shared room", "Hotel room"]
    )

with col2:
    neighbourhood = st.selectbox("Neighborhood", neighborhoods)

with col3:
    accommodates = st.number_input("Guests", min_value=1, max_value=16, value=2)
    bedrooms = st.number_input("Bedrooms", min_value=0, max_value=10, value=1)

with col4:
    bathrooms = st.number_input("Bathrooms", min_value=0.0, max_value=10.0, value=1.0, step=0.5)
    beds = st.number_input("Beds", min_value=0, max_value=20, value=1)

# Row 2: Amenities (expandable)
with st.expander("🏠 Amenities (click to expand)", expanded=False):
    st.caption("All amenities are pre-selected by default. Remove any that don't apply to your property.")
    selected_amenities = st.multiselect(
        "Amenities",
        TOP_AMENITIES,
        default=TOP_AMENITIES,  # Pre-select all amenities
        label_visibility="collapsed"
    )
    amenities_count = len(selected_amenities)
    st.info(f"✓ {amenities_count} amenities selected")

# Row 3: Price and analyze button
col1, col2 = st.columns([2, 1])

with col1:
    # Get average price for this property type and neighborhood
    # Parse neighborhood to get actual zip code for backend query
    neighbourhood_actual = parse_neighbourhood_for_city('austin', neighbourhood)
    avg_price = get_average_price('austin', neighbourhood=neighbourhood_actual, property_type=property_type)
    estimated_price = st.number_input(
        "💵 Estimated Price (per night)",
        min_value=10,
        max_value=1000,
        value=avg_price,
        step=5,
        help=f"Pre-filled with average (${avg_price}) for {property_type} in {neighbourhood}"
    )

with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    calculate_button = st.button("🎯 Analyze Property", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# BUTTON HANDLER - SET SESSION STATE
# =============================================================================
if calculate_button:
    with st.spinner("🔄 Analyzing property and market data..."):
        # Parse neighborhood (extract zip code from friendly name)
        neighbourhood_actual = parse_neighbourhood_for_city('austin', neighbourhood)

        # Get vibe data
        vibe_data = get_vibe_for_neighborhood('austin', neighbourhood_actual)

        if vibe_data is None:
            st.error(f"No vibe data found for {neighbourhood}")
            st.stop()

        # Build property data dict
        property_data = {
            'property_type': property_type,
            'room_type': property_type,
            'neighbourhood': neighbourhood_actual,
            'neighbourhood_display': neighbourhood,  # Keep friendly name for display
            'accommodates': accommodates,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'beds': beds,
            'amenities_count': amenities_count,
            'minimum_nights': 1,
            'maximum_nights': 30,
            'vibe_score': vibe_data['vibe_score'],
            'walkability_score': vibe_data['walkability_score'],
            'safety_score': vibe_data['safety_score'],
            'nightlife_score': vibe_data['nightlife_score'],
            'quietness_score': vibe_data['quietness_score'],
            'family_friendly_score': vibe_data['family_friendly_score'],
            'local_authentic_score': vibe_data['local_authentic_score'],
            'convenience_score': vibe_data['convenience_score'],
            'food_scene_score': vibe_data['food_scene_score'],
            'liveliness_score': vibe_data['liveliness_score'],
            'charm_score': vibe_data['charm_score'],
            'neighbourhood_encoded': 0,
            'host_listings_count': 1,
        }

        # Run analyses
        knn_result = get_knn_price_recommendation('austin', property_data)
        revenue_curve = generate_revenue_curve('austin', property_data, estimated_price, n_points=50)
        optimization = get_optimization_summary(revenue_curve, estimated_price)

        # Store in session state
        st.session_state.calculated = True
        st.session_state.property_data = property_data
        st.session_state.revenue_curve = revenue_curve
        st.session_state.optimization = optimization
        st.session_state.knn_result = knn_result
        st.session_state.vibe_data = vibe_data

    st.success("✅ Analysis complete!")
    st.rerun()

# =============================================================================
# RESULTS DISPLAY - ONLY IF CALCULATED (SESSION STATE CHECK)
# =============================================================================
if st.session_state.calculated:

    # Retrieve from session state
    property_data = st.session_state.property_data
    revenue_curve = st.session_state.revenue_curve
    optimization = st.session_state.optimization
    knn_result = st.session_state.knn_result
    vibe_data = st.session_state.vibe_data

    st.markdown("---")

    # =========================================================================
    # SECTION 1: NEIGHBORHOOD VIBE PROFILE (LIGHT BLUE BACKGROUND)
    # =========================================================================
    st.markdown('<div class="vibe-container">', unsafe_allow_html=True)
    # Display friendly name if available, otherwise zip code
    display_name = property_data.get('neighbourhood_display', property_data['neighbourhood'])
    st.markdown(f"## 🗺️ Neighborhood: {display_name}")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown(f'<div class="vibe-score">{vibe_data["vibe_score"]:.0f}</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Vibe Score (out of 100)</p>", unsafe_allow_html=True)

        vibe_score = vibe_data['vibe_score']
        if vibe_score >= 70:
            st.success("🔥 High Vibe - Premium pricing potential!")
        elif vibe_score >= 40:
            st.info("👍 Medium Vibe - Balanced neighborhood")
        else:
            st.warning("📍 Lower Vibe - Value-oriented pricing")

    with col2:
        # Radar chart with WHITE background and BLACK text
        vibe_dimensions = {
            'Walkability': vibe_data['walkability_score'],
            'Safety': vibe_data['safety_score'],
            'Nightlife': vibe_data['nightlife_score'],
            'Quietness': vibe_data['quietness_score'],
            'Family-Friendly': vibe_data['family_friendly_score'],
            'Local Authentic': vibe_data['local_authentic_score'],
            'Convenience': vibe_data['convenience_score'],
            'Food Scene': vibe_data['food_scene_score'],
            'Liveliness': vibe_data['liveliness_score'],
            'Charm': vibe_data['charm_score']
        }

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=list(vibe_dimensions.values()),
            theta=list(vibe_dimensions.keys()),
            fill='toself',
            line_color='#08519c',
            fillcolor='rgba(8, 81, 156, 0.3)',
            hovertemplate='<b>%{theta}</b><br>Score: %{r:.1f}<extra></extra>'
        ))

        fig_radar.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            font=dict(color='#000000', size=12),
            polar=dict(
                bgcolor='white',
                radialaxis=dict(visible=True, range=[0, 10], gridcolor='#CCCCCC', linecolor='#666666'),
                angularaxis=dict(gridcolor='#CCCCCC', linecolor='#666666', color='#000000')
            ),
            showlegend=False,
            title=dict(text=f"{display_name} Vibe Profile", font=dict(color='#000000')),
            height=400
        )

        st.plotly_chart(fig_radar, use_container_width=True)

    with col3:
        st.markdown("**Top Vibe Dimensions:**")
        sorted_vibes = sorted(vibe_dimensions.items(), key=lambda x: x[1], reverse=True)
        for i, (dim, score) in enumerate(sorted_vibes[:5], 1):
            st.markdown(f"{i}. **{dim}**: {score:.1f}/10")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # SECTION 2: K-NN PRICE BAND RECOMMENDATION
    # =========================================================================
    st.markdown("## 📊 Market Comparison (k-NN)")
    st.caption("Based on similar high-demand properties (≥75% occupancy)")

    if knn_result['success']:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Low (25th %ile)", f"${knn_result['price_low']:.0f}",
                     help="Conservative pricing - lower risk")
        with col2:
            st.metric("Mid (Median)", f"${knn_result['price_mid']:.0f}",
                     help="Typical price for similar listings")
        with col3:
            st.metric("High (75th %ile)", f"${knn_result['price_high']:.0f}",
                     help="Premium pricing - higher reward")
        with col4:
            st.metric("Confidence", knn_result['confidence'],
                     delta=f"{knn_result['n_neighbors']} comps")

        st.success(f"✓ Based on {knn_result['n_neighbors']} similar high-performing properties")
    else:
        st.warning(f"⚠️ {knn_result['message']}")
        st.info("💡 Using XGBoost model below for predictions with limited comparable data.")

    st.markdown("---")

    # =========================================================================
    # SECTION 3: REVENUE & OCCUPANCY OPTIMIZATION (DUAL-AXIS CHART)
    # =========================================================================
    st.markdown("## 📈 Revenue & Occupancy Optimization")
    st.caption("See how price affects both revenue AND occupancy")

    # Create dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    prices = revenue_curve['price'].values
    revenues = revenue_curve['monthly_revenue'].values
    occupancies = revenue_curve['occupancy'].values

    # Revenue line (left axis, blue)
    fig.add_trace(
        go.Scatter(
            x=prices, y=revenues,
            name="Monthly Revenue",
            line=dict(color='#08519c', width=3),
            hovertemplate='$%{x:.0f}/night<br>Revenue: $%{y:.0f}/month<extra></extra>'
        ),
        secondary_y=False
    )

    # Occupancy line (right axis, red)
    fig.add_trace(
        go.Scatter(
            x=prices, y=occupancies*100,
            name="Occupancy %",
            line=dict(color='#d62728', width=2, dash='dot'),
            hovertemplate='$%{x:.0f}/night<br>Occupancy: %{y:.1f}%<extra></extra>'
        ),
        secondary_y=True
    )

    # 75% threshold line (dashed red)
    fig.add_hline(
        y=75, line_dash="dash", line_color="red", line_width=2,
        annotation_text="75% Target",
        annotation_position="top right",
        secondary_y=True
    )

    # Shade safe zone (where occupancy >= 75%)
    safe_prices = prices[occupancies >= 0.75]
    if len(safe_prices) > 0:
        fig.add_vrect(
            x0=safe_prices.min(),
            x1=safe_prices.max(),
            fillcolor="green",
            opacity=0.15,
            layer="below",
            annotation_text="Safe Zone (≥75% occupancy)",
            annotation_position="top left"
        )

    # Mark optimal price
    optimal_idx = revenue_curve['is_optimal'].idxmax()
    optimal_price = revenue_curve.loc[optimal_idx, 'price']
    optimal_revenue = revenue_curve.loc[optimal_idx, 'monthly_revenue']

    fig.add_trace(
        go.Scatter(
            x=[optimal_price], y=[optimal_revenue],
            mode='markers',
            name='Optimal Price',
            marker=dict(size=15, color='green', symbol='star'),
            hovertemplate='Optimal: $%{x:.0f}/night<br>Max Revenue: $%{y:.0f}/month<extra></extra>'
        ),
        secondary_y=False
    )

    # Update axes
    fig.update_xaxes(title_text="Nightly Price ($)")
    fig.update_yaxes(title_text="Monthly Revenue ($)", secondary_y=False)
    fig.update_yaxes(title_text="Occupancy %", range=[0, 100], secondary_y=True)

    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Key insights
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Optimal Price", f"${optimization['optimal_price']:.0f}",
                 delta=f"{optimization['price_change_pct']:+.0f}% vs estimate")
    with col2:
        st.metric("Max Revenue", f"${optimization['optimal_revenue']:.0f}/mo",
                 delta=f"+{optimization['revenue_lift_pct']:.0f}% lift")
    with col3:
        safe_zone_text = f"${safe_prices.min():.0f} - ${safe_prices.max():.0f}" if len(safe_prices) > 0 else "None"
        st.metric("Safe Zone Range", safe_zone_text, help="Prices with ≥75% occupancy")

    st.markdown("---")

    # =========================================================================
    # SECTION 4: INTERACTIVE PRICE TESTER (SLIDER - NOW PERSISTS!)
    # =========================================================================
    st.markdown("## 🎚️ Interactive Price Tester")
    st.caption("Test different prices and see real-time predictions")

    min_slider = int(estimated_price * 0.5)
    max_slider = int(estimated_price * 2.0)

    # SLIDER IS NOW OUTSIDE THE CALCULATE BUTTON BLOCK!
    # Session state keeps it visible even after reruns
    test_price = st.slider(
        "Test Price ($/night)",
        min_value=min_slider,
        max_value=max_slider,
        value=int(optimization['optimal_price']),
        step=5,
        key='price_slider'
    )

    # Real-time prediction at test price
    test_occ = predict_occupancy('austin', property_data, test_price)
    test_revenue = test_price * test_occ * 30

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Test Price", f"${test_price}")
    with col2:
        occ_delta = (test_occ - optimization['current_occ']) * 100
        st.metric("Predicted Occupancy", f"{test_occ*100:.1f}%",
                 delta=f"{occ_delta:+.1f} ppts")
    with col3:
        rev_delta = ((test_revenue - optimization['current_revenue']) / optimization['current_revenue']) * 100
        st.metric("Monthly Revenue", f"${test_revenue:.0f}",
                 delta=f"{rev_delta:+.1f}%")

    # Occupancy gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=test_occ * 100,
        title={'text': "Predicted Occupancy"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#08519c"},
            'steps': [
                {'range': [0, 50], 'color': "#ffcccc"},
                {'range': [50, 75], 'color': "#ffffcc"},
                {'range': [75, 100], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))

    fig_gauge.update_layout(height=250)
    st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    # =========================================================================
    # SECTION 5: FINAL RECOMMENDATIONS
    # =========================================================================
    st.markdown("## 🎯 Final Recommendations")

    # Determine recommended range (within safe zone if possible)
    if len(safe_prices) > 0:
        recommended_low = safe_prices.min()
        recommended_high = safe_prices.max()

        if knn_result['success']:
            # Combine k-NN and safe zone
            knn_mid = knn_result['price_mid']
            if recommended_low <= knn_mid <= recommended_high:
                st.success(f"""
                **✅ Strong Consensus:**
                - k-NN Market Rate: **${knn_mid:.0f}**
                - XGBoost Optimal: **${optimization['optimal_price']:.0f}**
                - Safe Zone: **${recommended_low:.0f} - ${recommended_high:.0f}** (≥75% occupancy)

                **Recommended Price: ${knn_mid:.0f}** (within safe zone and matches market)
                """)
            else:
                st.info(f"""
                **📊 Consider These Options:**
                - Market-Based (k-NN): **${knn_mid:.0f}**
                - Revenue-Optimized: **${optimization['optimal_price']:.0f}**
                - Safe Zone: **${recommended_low:.0f} - ${recommended_high:.0f}** (≥75% occupancy)

                We recommend staying within the safe zone for consistent bookings.
                """)
        else:
            st.success(f"""
            **Recommended Price Range:** **${recommended_low:.0f} - ${recommended_high:.0f}**

            This range maintains ≥75% occupancy while maximizing revenue.
            """)
    else:
        st.warning("""
        ⚠️ **No safe zone found** - All tested prices fall below 75% occupancy threshold.

        Consider:
        - Lowering your price expectation
        - Adding more amenities to increase appeal
        - Improving property listing quality
        """)

    # Action items
    st.markdown("### 📝 Next Steps:")

    # Smart vibe recommendation based on score
    vibe_dimensions = {
        'Walkability': vibe_data['walkability_score'],
        'Safety': vibe_data['safety_score'],
        'Nightlife': vibe_data['nightlife_score'],
        'Quietness': vibe_data['quietness_score'],
        'Family-Friendly': vibe_data['family_friendly_score'],
        'Local Authentic': vibe_data['local_authentic_score'],
        'Convenience': vibe_data['convenience_score'],
        'Food Scene': vibe_data['food_scene_score'],
        'Liveliness': vibe_data['liveliness_score'],
        'Charm': vibe_data['charm_score']
    }

    if vibe_data['vibe_score'] >= 50:
        # Medium/high vibe - leverage overall vibe
        vibe_tip = f"**Leverage your neighborhood vibe** ({vibe_data['vibe_score']:.0f}/100) in your listing description"
    else:
        # Low vibe - highlight top 2 specific strengths
        top_2_vibes = sorted(vibe_dimensions.items(), key=lambda x: x[1], reverse=True)[:2]
        vibe_names = ' and '.join([f"{name} ({score:.0f})" for name, score in top_2_vibes])
        vibe_tip = f"**Highlight your neighborhood's strengths**: {vibe_names} in your listing description"

    st.markdown(f"""
    1. **Set your base price** within the recommended range
    2. **Monitor occupancy** for the first 2-4 weeks and adjust
    3. {vibe_tip}
    4. **Highlight key amenities** in photos and description
    5. **Adjust seasonally** - increase during high-demand periods (SXSW, ACL, etc.)
    """)

# =============================================================================
# FOOTER NAVIGATION
# =============================================================================
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🗺️ View Vibe Maps", use_container_width=True):
        st.switch_page("pages/4_🗺️_Vibe_Maps.py")

with col2:
    if st.button("🎡 Try London", use_container_width=True):
        st.switch_page("pages/1_🎡_London.py")

with col3:
    if st.button("🗽 Try NYC", use_container_width=True):
        st.switch_page("pages/3_🗽_NYC.py")
