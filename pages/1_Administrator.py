import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sys
from pathlib import Path

# Add parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_historical_data, load_demo_json, run_live_pipeline, get_folium_color
from utils_ui import inject_custom_css
from utils_charts import create_forecast_chart, create_source_attribution_chart, create_shap_chart

st.set_page_config(page_title="Administrator View", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()

with st.sidebar:
    city = st.session_state.get('city', 'mumbai')
    st.title(f"{city.capitalize()} Air Quality")
    st.markdown("---")
    data_mode = st.radio("Data Mode", ["Demo Mode (Precomputed)", "Live Mode (Real-time)"], index=0)
    is_live = "Live" in data_mode
    
    # Load Station List
    df_hist, station_list = load_historical_data(city=city)
    
    if not station_list:
        st.error("No station data found.")
        st.stop()
        
    selected_station = st.selectbox("Select Monitoring Station", station_list)
    
    st.markdown("---")
    st.caption("⚠️ **Disclaimer**: Geospatial Source Risk Estimation percentages are evidence-based heuristic estimates derived from wind patterns, land use, and pollutant signatures.")

if is_live:
    intelligence_data = run_live_pipeline(selected_station, df_hist)
else:
    intelligence_data = load_demo_json(selected_station, city=city)
    if not intelligence_data:
        st.warning(f"Demo JSON not found for {selected_station}. Please select another station or run generate_demo_cache.py.")
        st.stop()

if not intelligence_data:
    st.stop()

st.markdown(f"<h2>Administrator Diagnostics: {selected_station}</h2>", unsafe_allow_html=True)

# 1. Top KPI Summary Cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Predicted PM2.5 (24h)", f"{intelligence_data['forecast']['24h']['pm25']:.1f}", delta="µg/m³", delta_color="off")
with col2:
    st.metric("AQI Category", intelligence_data['forecast']['24h']['aqi_category'])
with col3:
    st.metric("Primary Geospatial Risk", intelligence_data['source_influence']['sources'][0]['name'] if intelligence_data['source_influence']['sources'] else "Unknown")
with col4:
    conf = intelligence_data['source_influence'].get('confidence', 0)
    st.metric("Estimation Confidence", f"{conf * 100:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# 2. Main Macro Layout (Map vs Analytics)
macro_col_map, macro_col_charts = st.columns([1.3, 1])

with macro_col_map:
    st.markdown("<div class='card-title'>Geospatial Intelligence Map</div>", unsafe_allow_html=True)
    if not df_hist.empty:
        min_lat = df_hist['latitude'].min()
        max_lat = df_hist['latitude'].max()
        min_lon = df_hist['longitude'].min()
        max_lon = df_hist['longitude'].max()
    else:
        min_lat, max_lat, min_lon, max_lon = 18.9, 19.3, 72.7, 73.0

    # Using light tile for Enterprise Light Mode
    m = folium.Map(tiles="CartoDB positron")
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    try:
        import osmnx as ox
        @st.cache_data
        def get_map_layers(lat, lon):
            layers = {}
            try:
                roads = ox.features.features_from_point((lat, lon), tags={'highway': ['primary', 'trunk', 'motorway']}, dist=5000)
                if not roads.empty:
                    layers['roads'] = roads[roads.geometry.type == 'LineString'].to_json()
            except: pass
            try:
                industry = ox.features.features_from_point((lat, lon), tags={'landuse': 'industrial', 'man_made': 'works'}, dist=5000)
                if not industry.empty:
                    industry = industry[industry.geometry.type.isin(['Polygon', 'MultiPolygon'])]
                    if not industry.empty:
                        layers['industry'] = industry.to_json()
            except: pass
            try:
                construction = ox.features.features_from_point((lat, lon), tags={'landuse': ['construction', 'brownfield', 'quarry']}, dist=5000)
                if not construction.empty:
                    construction = construction[construction.geometry.type.isin(['Polygon', 'MultiPolygon'])]
                    if not construction.empty:
                        layers['construction'] = construction.to_json()
            except: pass
            return layers
            
        if not df_hist.empty:
            stat_lat = df_hist[df_hist['station'] == selected_station]['latitude'].iloc[0] if 'latitude' in df_hist.columns else 19.0
            stat_lon = df_hist[df_hist['station'] == selected_station]['longitude'].iloc[0] if 'longitude' in df_hist.columns else 72.8
            layers = get_map_layers(stat_lat, stat_lon)
            
            # Determine which source layers to show based on >15% contribution
            sources = intelligence_data.get('source_influence', {}).get('sources', [])
            show_roads = any("traffic" in s.get('name', '').lower() and s.get('contribution_percentage', 0) > 15 for s in sources)
            show_industry = any("industry" in s.get('name', '').lower() and s.get('contribution_percentage', 0) > 15 for s in sources)
            show_construction = any("construction" in s.get('name', '').lower() and s.get('contribution_percentage', 0) > 15 for s in sources)
            show_fires = any("biomass" in s.get('name', '').lower() and s.get('contribution_percentage', 0) > 15 for s in sources)
            
            if 'roads' in layers:
                folium.GeoJson(layers['roads'], name="Major Roads", style_function=lambda x: {'color':'#3b82f6','weight':2}, show=show_roads).add_to(m)
            if 'industry' in layers:
                folium.GeoJson(layers['industry'], name="Industrial Zones", style_function=lambda x: {'fillColor':'#8b5cf6','color':'#8b5cf6','weight':1,'fillOpacity':0.3}, show=show_industry).add_to(m)
            if 'construction' in layers:
                folium.GeoJson(layers['construction'], name="Construction Zones", style_function=lambda x: {'fillColor':'#f59e0b','color':'#f59e0b','weight':1,'fillOpacity':0.3}, show=show_construction).add_to(m)
                
            try:
                from geospatial_features import fetch_nasa_firms_data
                firms = fetch_nasa_firms_data()
                if not firms.empty:
                    fire_group = folium.FeatureGroup(name="Active Fires (FIRMS)", show=show_fires)
                    for _, r in firms.iterrows():
                        folium.CircleMarker([r['latitude'], r['longitude']], radius=4, color='#ef4444', fill=True, popup="Active Fire").add_to(fire_group)
                    fire_group.add_to(m)
            except: pass
    except Exception as e:
        pass 
        
    if not df_hist.empty:
        for stat in station_list:
            stat_df = df_hist[df_hist['station'] == stat].tail(1)
            if not stat_df.empty:
                s_lat = stat_df['latitude'].iloc[0] if 'latitude' in stat_df.columns else 19.0
                s_lon = stat_df['longitude'].iloc[0] if 'longitude' in stat_df.columns else 72.8
                
                is_selected = (stat == selected_station)
                
                if is_selected:
                    color = get_folium_color(intelligence_data['forecast']['24h']['aqi_category'])
                    # Convert dark map colors to modern Hex variants if needed, or just use folium defaults
                    radius = 12
                    popup_text = f"<b>{stat}</b><br>PM2.5: {intelligence_data['forecast']['24h']['pm25']}<br>AQI: {intelligence_data['forecast']['24h']['aqi_category']}"
                else:
                    color = "#94a3b8"
                    radius = 6
                    popup_text = stat
                    
                folium.CircleMarker(
                    location=[s_lat, s_lon],
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9 if is_selected else 0.5,
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=stat
                ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, height=700, width="100%", returned_objects=[])

with macro_col_charts:
    st.markdown("<div class='card-title'>Analytics & Explainability</div>", unsafe_allow_html=True)
    
    # Render Plotly Charts
    fig_forecast = create_forecast_chart(intelligence_data)
    st.plotly_chart(fig_forecast, use_container_width=True, config={'displayModeBar': False})
    
    sources_data = intelligence_data.get('source_influence', {}).get('sources', [])
    if sources_data:
        fig_donut = create_source_attribution_chart(sources_data)
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        
    inc = intelligence_data.get('model_explanation', {}).get('top_increasing_factors', [])
    dec = intelligence_data.get('model_explanation', {}).get('top_decreasing_factors', [])
    if inc or dec:
        fig_shap = create_shap_chart(inc, dec)
        st.plotly_chart(fig_shap, use_container_width=True, config={'displayModeBar': False})

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<div class='card-title'>Actionable AI Recommendations</div>", unsafe_allow_html=True)

col_rec1, col_rec2 = st.columns(2)
with col_rec1:
    st.markdown("### Suggested Interventions")
    for rec in intelligence_data.get('recommendations', []):
        st.markdown(f"✅ **{rec}**")
        
with col_rec2:
    st.markdown("### Confidence Rationale")
    rationale = intelligence_data.get('source_influence', {}).get('rationale', 'No rationale provided.')
    st.info(rationale)
