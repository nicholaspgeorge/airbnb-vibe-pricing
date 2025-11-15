"""
TASK 6: INTERACTIVE REVENUE CURVE EXPLORER

Creates interactive visualization of revenue optimization curves for diverse listings.
Users can explore different listings, hover for exact values, and understand optimization opportunities.

Author: Vibe-Aware Pricing Team
Date: 2025-11-07
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# Configuration
CITY = 'london'
N_EXAMPLES = 6  # Number of diverse examples to show

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / f'data/{CITY}'
CURVES_PATH = DATA_DIR / 'outputs/recommendations/revenue_curves.parquet'
RECS_PATH = DATA_DIR / 'outputs/recommendations/revenue_recommendations.parquet'
VIZ_DIR = DATA_DIR / 'outputs/visualizations'

print("=" * 80)
print("INTERACTIVE REVENUE CURVE EXPLORER")
print("=" * 80)
print()

# ============================================================================
# Load Data
# ============================================================================

print("[1/3] Loading revenue curves and recommendations...")

curves = pd.read_parquet(CURVES_PATH)
recommendations = pd.read_parquet(RECS_PATH)

print(f"  ✓ Loaded curves: {len(curves):,} price points across {recommendations.shape[0]} listings")
print(f"  ✓ Loaded recommendations: {recommendations.shape[0]} listings")
print()

# ============================================================================
# Select Diverse Examples
# ============================================================================

print("[2/3] Selecting diverse example listings...")

# Selection criteria: diverse room types, vibe scores, revenue lift potential
examples = []

# Example 1: Highest revenue lift
high_lift = recommendations.nlargest(1, 'revenue_lift_pct')
if len(high_lift) > 0:
    examples.append(('Highest Lift', high_lift.iloc[0]))

# Example 2: High vibe area
high_vibe = recommendations.nlargest(1, 'vibe_score')
if len(high_vibe) > 0:
    examples.append(('High Vibe Area', high_vibe.iloc[0]))

# Example 3: Low vibe area
low_vibe = recommendations.nsmallest(1, 'vibe_score')
if len(low_vibe) > 0:
    examples.append(('Low Vibe Area', low_vibe.iloc[0]))

# Example 4: Private room
private_room = recommendations[recommendations['room_type'] == 'Private room'].sample(1, random_state=42)
if len(private_room) > 0:
    examples.append(('Private Room', private_room.iloc[0]))

# Example 5: Budget listing
budget = recommendations.nsmallest(1, 'current_price')
if len(budget) > 0:
    examples.append(('Budget Listing', budget.iloc[0]))

# Example 6: Luxury listing
luxury = recommendations.nlargest(1, 'current_price')
if len(luxury) > 0:
    examples.append(('Luxury Listing', luxury.iloc[0]))

print(f"  ✓ Selected {len(examples)} diverse listings")
for label, rec in examples:
    print(f"     • {label}: {rec['property_type']} in {rec['neighbourhood']}")
print()

# ============================================================================
# Create Interactive Revenue Curves
# ============================================================================

print("[3/3] Creating interactive revenue curve visualization...")

# Create subplots
fig = make_subplots(
    rows=2, cols=3,
    subplot_titles=[f"{label}<br>{rec['room_type']}, {rec['neighbourhood']}"
                    for label, rec in examples],
    vertical_spacing=0.12,
    horizontal_spacing=0.10
)

colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for idx, ((label, rec), color) in enumerate(zip(examples, colors)):
    row = (idx // 3) + 1
    col = (idx % 3) + 1

    # Get curve for this listing
    curve = curves[curves['listing_id'] == rec['listing_id']].copy()

    # Plot revenue curve
    fig.add_trace(
        go.Scatter(
            x=curve['price'],
            y=curve['monthly_revenue'],
            mode='lines',
            name=label,
            line=dict(color=color, width=2),
            hovertemplate='<b>Price: £%{x:.0f}</b><br>' +
                          'Occupancy: %{customdata[0]:.1%}<br>' +
                          'Revenue: £%{y:,.0f}/mo<br>' +
                          '<extra></extra>',
            customdata=curve[['predicted_occ_90']].values,
            showlegend=False
        ),
        row=row, col=col
    )

    # Mark current price
    current_idx = (curve['price'] - rec['current_price']).abs().idxmin()
    current_revenue = curve.loc[current_idx, 'monthly_revenue']

    fig.add_trace(
        go.Scatter(
            x=[rec['current_price']],
            y=[current_revenue],
            mode='markers',
            marker=dict(size=10, color='gray', symbol='circle'),
            name='Current',
            hovertemplate=f'<b>Current Price</b><br>£{rec["current_price"]:.0f}/night<br>' +
                          f'Revenue: £{rec["current_revenue"]:.0f}/mo<extra></extra>',
            showlegend=(idx == 0)
        ),
        row=row, col=col
    )

    # Mark optimal price
    fig.add_trace(
        go.Scatter(
            x=[rec['optimal_price']],
            y=[rec['optimal_revenue']],
            mode='markers',
            marker=dict(size=15, color='green', symbol='star'),
            name='Optimal',
            hovertemplate=f'<b>Optimal Price</b><br>£{rec["optimal_price"]:.0f}/night<br>' +
                          f'Revenue: £{rec["optimal_revenue"]:.0f}/mo<br>' +
                          f'Lift: {rec["revenue_lift_pct"]:.1f}%<extra></extra>',
            showlegend=(idx == 0)
        ),
        row=row, col=col
    )

    # Add annotations
    fig.add_annotation(
        text=f"Lift: {rec['revenue_lift_pct']:.0f}%<br>Current: £{rec['current_price']:.0f} → Optimal: £{rec['optimal_price']:.0f}",
        xref=f'x{idx+1}' if idx > 0 else 'x',
        yref=f'y{idx+1}' if idx > 0 else 'y',
        x=rec['optimal_price'],
        y=rec['optimal_revenue'] * 0.85,
        showarrow=False,
        font=dict(size=9, color='#333'),
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='#ccc',
        borderwidth=1,
        row=row, col=col
    )

# Update layout
fig.update_layout(
    title=dict(
        text='Revenue Optimization Curves: Interactive Explorer<br>' +
             '<sub>Hover for details | Gray dot = Current price | Green star = Optimal price</sub>',
        font=dict(size=18),
        x=0.5,
        xanchor='center'
    ),
    height=800,
    showlegend=True,
    legend=dict(
        orientation='h',
        yanchor='bottom',
        y=1.02,
        xanchor='center',
        x=0.5,
        font=dict(size=11)
    ),
    hovermode='closest'
)

# Update axes
fig.update_xaxes(title_text='Nightly Price (£)', title_font=dict(size=10))
fig.update_yaxes(title_text='Monthly Revenue (£)', title_font=dict(size=10))

# Save
output_path = VIZ_DIR / 'revenue_curves_interactive.html'
fig.write_html(output_path)
print(f"  ✓ Saved interactive revenue curves: {output_path.name}")

print()

# ============================================================================
# Summary Statistics
# ============================================================================

print("=" * 80)
print("REVENUE CURVE INSIGHTS")
print("=" * 80)

for label, rec in examples:
    print(f"\n{label}:")
    print(f"  Property: {rec['property_type']}")
    print(f"  Location: {rec['neighbourhood']} (vibe={rec['vibe_score']:.1f})")
    print(f"  Current: £{rec['current_price']:.0f}/night → £{rec['current_revenue']:.0f}/month")
    print(f"  Optimal: £{rec['optimal_price']:.0f}/night → £{rec['optimal_revenue']:.0f}/month")
    print(f"  Revenue Lift: {rec['revenue_lift_pct']:.1f}% (£{rec['optimal_revenue'] - rec['current_revenue']:.0f}/month gain)")

    if rec['has_safe_band']:
        print(f"  Safe Band: £{rec['safe_low']:.0f} - £{rec['safe_high']:.0f} (occ ≥75%)")
    else:
        print(f"  Safe Band: None (current price already at or above 75% occ threshold)")

print("\n" + "=" * 80)
print("INTERACTIVE REVENUE CURVES COMPLETE ✅")
print("=" * 80)
print(f"\nOutput: {output_path}")
print("\nTo view: Open the HTML file in any web browser")
print("  • Hover over curves for exact price/revenue/occupancy values")
print("  • Compare optimization opportunities across different listing types")
print("  • Gray dots show current pricing, green stars show optimal pricing")
print("=" * 80)
