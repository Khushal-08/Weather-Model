import plotly.graph_objects as go
import pandas as pd

# Enterprise Light Theme Colors
COLORS = {
    'primary': '#0f172a',      # Slate 900
    'secondary': '#3b82f6',    # Blue 500
    'accent': '#10b981',       # Emerald 500
    'warning': '#f59e0b',      # Amber 500
    'danger': '#ef4444',       # Red 500
    'grid': '#e2e8f0',         # Slate 200
    'text': '#475569',         # Slate 600
    
    # Source attribution colors
    'Traffic': '#3b82f6',
    'Industrial Area': '#8b5cf6',
    'Dust/Construction': '#f59e0b',
    'Biomass Burning': '#ef4444',
    'Other': '#94a3b8'
}

def apply_chart_theme(fig):
    """Applies the Enterprise Light theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color=COLORS['text']),
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False, zeroline=False, color=COLORS['text']),
        yaxis=dict(showgrid=True, gridcolor=COLORS['grid'], zeroline=False, color=COLORS['text']),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Inter, sans-serif"
        )
    )
    return fig

def create_forecast_chart(intelligence_data):
    """Creates a smooth area chart for 24h, 48h, 72h forecasts."""
    try:
        f24 = intelligence_data['forecast']['24h']['pm25']
        f48 = intelligence_data['forecast']['48h']['pm25']
        f72 = intelligence_data['forecast']['72h']['pm25']
    except KeyError:
        return go.Figure()
        
    horizons = ['24 Hours', '48 Hours', '72 Hours']
    vals = [f24, f48, f72]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=horizons, 
        y=vals,
        mode='lines+markers',
        line=dict(color=COLORS['secondary'], width=3, shape='spline'),
        marker=dict(size=8, color=COLORS['secondary'], symbol='circle'),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
        name='Predicted PM2.5'
    ))
    
    fig = apply_chart_theme(fig)
    fig.update_layout(
        title="PM2.5 Multi-Horizon Forecast",
        yaxis_title="µg/m³",
        showlegend=False
    )
    return fig

def create_source_attribution_chart(sources_list):
    """Creates a premium donut chart for source attribution."""
    if not sources_list:
        return go.Figure()
        
    labels = [s['name'] for s in sources_list]
    values = [s['contribution'] for s in sources_list]
    colors = [COLORS.get(l, COLORS['Other']) for l in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values, 
        hole=0.6,
        marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
        textinfo='percent',
        textfont_size=14,
        hoverinfo='label+percent'
    )])
    
    fig = apply_chart_theme(fig)
    fig.update_layout(
        title="Geospatial Source Attribution",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=40, b=40, l=10, r=10)
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
    
    # Sort and combine
    # Increasing are positive, decreasing are negative impacts on pollution
    for item in reversed(decreasing[:3]):
        features.append(item['feature'])
        impacts.append(item['impact']) # Usually negative
        colors.append(COLORS['accent']) # Green (reduces pollution)
        
    for item in increasing[:3]:
        features.append(item['feature'])
        impacts.append(item['impact']) # Positive
        colors.append(COLORS['danger']) # Red (increases pollution)
        
    if not features:
        return go.Figure()
        
    fig = go.Figure(go.Bar(
        x=impacts,
        y=features,
        orientation='h',
        marker_color=colors,
        text=[f"{v:+.1f}" for v in impacts],
        textposition='outside'
    ))
    
    fig = apply_chart_theme(fig)
    fig.update_layout(
        title="AI Explainability (Top Features)",
        xaxis_title="SHAP Value Impact on PM2.5",
        yaxis_title=None,
        showlegend=False
    )
    return fig
