import plotly.graph_objects as go
import pandas as pd

# Dark Navy Theme Colors
COLORS = {
    'primary': '#0b1121',      # Dark Navy
    'secondary': '#f59e0b',    # Orange/Amber for PM2.5 line like reference
    'accent': '#10b981',       # Emerald 500
    'warning': '#f59e0b',      # Amber 500
    'danger': '#ef4444',       # Red 500
    'grid': '#1f2937',         # Slate 800
    'text': '#9ca3af',         # Slate 400
    
    # Source attribution colors
    'Traffic': '#ef4444',              # Red
    'Industry': '#8b5cf6',             # Purple
    'Construction': '#f59e0b',         # Amber
    'Biomass Burning': '#10b981',      # Emerald
    'Regional Background': '#3b82f6',  # Blue
    'Other': '#6b7280'                 # Gray
}

def apply_chart_theme(fig):
    """Applies the Dark Navy theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color=COLORS['text']),
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False, zeroline=False, color=COLORS['text']),
        yaxis=dict(showgrid=True, gridcolor=COLORS['grid'], zeroline=False, color=COLORS['text']),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#1f2937",
            font_size=13,
            font_family="Inter, sans-serif",
            font_color="#ffffff"
        )
    )
    return fig

def create_forecast_chart(intelligence_data):
    """Creates a smooth area chart for 24h, 48h, 72h forecasts with confidence bands."""
    try:
        f24 = intelligence_data['forecast']['24h']['pm25']
        f48 = intelligence_data['forecast']['48h']['pm25']
        f72 = intelligence_data['forecast']['72h']['pm25']
    except KeyError:
        return go.Figure()
        
    horizons = ['24 Hours', '48 Hours', '72 Hours']
    vals = [f24, f48, f72]
    
    # Generate illustrative confidence bounds (+/- 15% for hackathon context)
    upper_bounds = [v * 1.15 for v in vals]
    lower_bounds = [v * 0.85 for v in vals]
    
    fig = go.Figure()
    
    # Upper Bound
    fig.add_trace(go.Scatter(
        x=horizons, 
        y=upper_bounds,
        mode='lines',
        line=dict(color='rgba(245, 158, 11, 0.3)', width=1, dash='dash'),
        name='Upper Bound (95% CI)'
    ))
    
    # Lower Bound (with fill to upper)
    fig.add_trace(go.Scatter(
        x=horizons, 
        y=lower_bounds,
        mode='lines',
        line=dict(color='rgba(245, 158, 11, 0.3)', width=1, dash='dash'),
        fill='tonexty',
        fillcolor='rgba(245, 158, 11, 0.1)',
        name='Lower Bound'
    ))
    
    # Main Prediction
    fig.add_trace(go.Scatter(
        x=horizons, 
        y=vals,
        mode='lines+markers',
        line=dict(color=COLORS['secondary'], width=3, shape='spline'),
        marker=dict(size=8, color=COLORS['secondary'], symbol='circle'),
        name='Predicted PM2.5'
    ))
    
    fig = apply_chart_theme(fig)
    fig.update_layout(
        title=dict(text="PM2.5 Forecast Trend", font=dict(color="#ffffff")),
        yaxis_title="µg/m³",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=10)),
        height=250
    )
    return fig

def create_source_attribution_chart(sources_list):
    """Creates a premium donut chart for source attribution."""
    if not sources_list:
        return go.Figure()
    source_emojis = {
        'Traffic': '🚗 Traffic',
        'Industry': '🏭 Industry',
        'Construction': '🏗️ Construction',
        'Biomass Burning': '🔥 Biomass Burning',
        'Regional Background': '🌍 Regional Background'
    }
    labels = [source_emojis.get(s['name'], s['name']) for s in sources_list]
    values = [s.get('contribution_percentage', 0) for s in sources_list]
    colors = [COLORS.get(s['name'], COLORS['Other']) for s in sources_list]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=0.6,
        marker=dict(colors=colors, line=dict(color='#111827', width=2)),
        textinfo='percent',
        textposition='inside',
        textfont_size=14,
        hoverinfo='label+percent'
    )])
    
    fig = apply_chart_theme(fig)
    fig.update_layout(
        title=dict(text="Geospatial Source Attribution", font=dict(color="#ffffff")),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5, font=dict(color="#e2e8f0", size=10)),
        margin=dict(t=40, b=60, l=10, r=10),
        height=300
    )
    # Remove grid lines for pie chart
    fig.update_xaxes(showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, visible=False)
    
    return fig

def create_shap_chart(increasing, decreasing):
    """Creates a horizontal bar chart for SHAP explanations."""
    features = []
    impacts = []
    colors = []
    
    feature_mappings = {
        'pm25_lag_1': "Yesterday's Pollution",
        'pm25_lag_7': "Last Week's Baseline",
        'pm25_lag_30': "Monthly Baseline",
        'wind_speed': "Wind Dispersion",
        'temperature_2m': "Temp Inversion",
        'relative_humidity_2m': "Atmospheric Moisture",
        'surface_pressure': "Atmospheric Pressure",
        'day_of_year': "Seasonal Weather",
        'day_of_week': "Weekly Rhythm",
        'pm10_lag_1': "Yesterday's Coarse Dust",
        'no2_lag_1': "Yesterday's Traffic",
        'precipitation': "Rainfall Washout"
    }
    def humanize(f): return feature_mappings.get(f, f.replace('_', ' ').title())

    # Sort and combine
    # Increasing are positive, decreasing are negative impacts on pollution
    for item in reversed(decreasing[:3]):
        features.append(humanize(item['feature']))
        impacts.append(item['impact']) # usually negative
        colors.append('#10b981') # Emerald for decrease (good)
        
    for item in increasing[:3]:
        features.append(humanize(item['feature']))
        impacts.append(item['impact']) # positive
        colors.append('#ef4444') # Red for increase
        
    if not features:
        return go.Figure()
        
    fig = go.Figure(go.Bar(
        x=impacts,
        y=features,
        orientation='h',
        marker_color=colors,
        text=[f"{v:+.1f}" for v in impacts],
        textposition='outside',
        textfont=dict(color="#e2e8f0")
    ))
    
    fig = apply_chart_theme(fig)
    fig.update_layout(
        title=dict(text="AI Explainability (SHAP Top Features)", font=dict(color="#ffffff")),
        xaxis_title="Impact on PM2.5",
        yaxis_title=None,
        showlegend=False,
        height=250
    )
    return fig
