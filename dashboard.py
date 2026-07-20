import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import json
import time
from pathlib import Path

# Try to import pipeline functions for Live Mode
try:
    import sys
    sys.path.append(str(Path(__file__).parent / "script"))
    from predict_pipeline import generate_air_quality_intelligence
    from train_multi_horizon import load_and_prepare_data_multi
    LIVE_MODE_AVAILABLE = True
except ImportError:
    LIVE_MODE_AVAILABLE = False

# --- CONFIG & CONSTANTS ---
st.set_page_config(page_title="Air Quality Intelligence Dashboard", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = Path("data/processed/training_features.csv")
DEMO_DIR = Path("data/demo")

def get_folium_color(aqi_category):
    mapping = {
        "Good": "green",
        "Satisfactory": "lightgreen",
        "Moderately Polluted": "orange",
        "Poor": "lightred",
        "Very Poor": "red",
        "Severe": "darkred"
    }
    return mapping.get(aqi_category, "gray")

# --- CACHING FUNCTIONS ---
@st.cache_data
def load_historical_data():
    """Load the historical dataset to extract stations and recent history."""
    if not DATA_FILE.exists():
        return pd.DataFrame(), []
    df = pd.read_csv(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    
    sort_col = 'location' if 'location' in df.columns else 'station'
    df = df.sort_values([sort_col, 'date']).reset_index(drop=True)
    
    rolling_cols = [c for c in df.columns if 'rolling' in c]
    for col in rolling_cols:
        df[f"{col}_shifted"] = df.groupby(sort_col)[col].shift(1)
        
    stations = sorted(df['station'].unique())
    return df, stations

@st.cache_data
def load_demo_json(station_name):
    """Load the precomputed demo JSON for a station."""
    file_name = f"{station_name.replace(' ', '_').replace(',', '')}.json"
    file_path = DEMO_DIR / file_name
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def run_live_pipeline(station, df):
    """Run the actual Python pipeline with progress indicators."""
    if not LIVE_MODE_AVAILABLE:
        st.error("Live mode dependencies not found. Please switch to Demo Mode.")
        return None
        
    station_df = df[df['station'] == station].tail(1)
    if station_df.empty:
        st.error("No historical data found for this station to use as input.")
        return None
        
    try:
        with st.status(f"Generating live intelligence for {station}...", expanded=True) as status:
            st.write("Loading XGBoost models and multi-horizon forecasting...")
            time.sleep(0.5) 
            
            st.write("Running SHAP explainer...")
            time.sleep(0.5)
            
            st.write("Extracting geospatial features and executing Source Attribution Agent...")
            
            rolling_cols = [c for c in df.columns if 'rolling' in c and not c.endswith('_shifted')]
            lag_cols = [c for c in df.columns if 'lag' in c]
            shifted_rolling_cols = [f"{c}_shifted" for c in rolling_cols]
            calendar_cols = ['day_of_week', 'month', 'day_of_year', 'weekend', 
                             'month_sin', 'month_cos', 'day_of_week_sin', 'day_of_week_cos', 
                             'day_of_year_sin', 'day_of_year_cos']
                             
            current_cols = ['pm25', 'pm10', 'no2', 'co', 'o3', 'temperature_2m_mean', 'relative_humidity_2m_mean', 'precipitation_sum', 'wind_speed_10m_mean']
            current_cols = [c for c in current_cols if c in df.columns]
            
            features = current_cols + lag_cols + shifted_rolling_cols + calendar_cols
            input_row = station_df[features]
            
            lat = station_df['latitude'].iloc[0] if 'latitude' in station_df.columns else 19.047
            lon = station_df['longitude'].iloc[0] if 'longitude' in station_df.columns else 72.8746
            target_date = str(station_df['date'].iloc[0])
            
            wind_dir = float(station_df['wind_speed_10m_mean'].iloc[0]) if 'wind_speed_10m_mean' in station_df.columns else 270.0
            wind_speed = float(station_df['wind_speed_10m_mean'].iloc[0]) if 'wind_speed_10m_mean' in station_df.columns else 15.0
            no2 = float(station_df['no2'].iloc[0]) if 'no2' in station_df.columns else 55.0
            co = float(station_df['co'].iloc[0]) if 'co' in station_df.columns else 1.5
            pm10 = float(station_df['pm10'].iloc[0]) if 'pm10' in station_df.columns else 180.0
            pm25_val = float(station_df['pm25'].iloc[0]) if 'pm25' in station_df.columns else 50.0
            
            st.write("Querying Gemini API for Citizen Advisory...")
            result = generate_air_quality_intelligence(
                station=station,
                lat=lat,
                lon=lon,
                target_date=target_date,
                input_row=input_row,
                feature_names=features,
                wind_dir=wind_dir,
                wind_speed=wind_speed,
                no2=no2,
                co=co,
                pm10=pm10,
                pm25=pm25_val
            )
            status.update(label="Live Intelligence Generated Successfully!", state="complete", expanded=False)
            return result
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.info("Live mode encountered an error (e.g., API timeout or cache miss). Switching to Demo Mode is recommended.")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("Mumbai Urban Air Quality")
    
    # State Toggles
    view_mode = st.radio("View Mode", ["Citizen", "Administrator"], index=1)
    
    st.markdown("---")
    data_mode = st.radio("Data Mode", ["Demo Mode (Precomputed)", "Live Mode (Real-time)"], index=0)
    is_live = "Live" in data_mode
    
    # Load Station List
    df_hist, station_list = load_historical_data()
    
    if not station_list:
        st.error("No station data found.")
        st.stop()
        
    selected_station = st.selectbox("Select Monitoring Station", station_list)
    
    st.markdown("---")
    st.caption("⚠️ **Disclaimer**: Source contribution percentages are evidence-based estimates derived from geospatial features, weather transport, and pollutant signatures. They are not direct emission measurements.")
    
# --- FETCH DATA ---
if is_live:
    intelligence_data = run_live_pipeline(selected_station, df_hist)
else:
    intelligence_data = load_demo_json(selected_station)
    if not intelligence_data:
        st.warning(f"Demo JSON not found for {selected_station}. Please select another station or run generate_demo_cache.py.")
        st.stop()

if not intelligence_data:
    st.stop()

# --- MAIN LAYOUT ---

if view_mode == "Administrator":
    # 1. Top KPI Summary Cards
    st.markdown("### Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Predicted PM2.5 (24h)", f"{intelligence_data['forecast']['24h']['pm25']} µg/m³")
    with col2:
        st.metric("AQI Category", intelligence_data['forecast']['24h']['aqi_category'])
    with col3:
        st.metric("Primary Source", intelligence_data['source_influence']['sources'][0]['name'] if intelligence_data['source_influence']['sources'] else "Unknown")
    with col4:
        conf = intelligence_data['source_influence'].get('confidence', 0)
        st.metric("Attribution Confidence", f"{conf * 100:.1f}%")

    st.markdown("---")

    # 2. Main Map
    st.markdown("### Station Map")
    
    if not df_hist.empty:
        min_lat = df_hist['latitude'].min()
        max_lat = df_hist['latitude'].max()
        min_lon = df_hist['longitude'].min()
        max_lon = df_hist['longitude'].max()
    else:
        min_lat, max_lat, min_lon, max_lon = 18.9, 19.3, 72.7, 73.0

    m = folium.Map(tiles="CartoDB dark_matter")
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
                    layers['industry'] = industry.to_json()
            except: pass
            try:
                construction = ox.features.features_from_point((lat, lon), tags={'landuse': ['construction', 'brownfield', 'quarry']}, dist=5000)
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
                folium.GeoJson(layers['roads'], name="Major Roads", style_function=lambda x: {'color':'gray','weight':2}, tooltip="Major Road", show=show_roads).add_to(m)
            if 'industry' in layers:
                folium.GeoJson(layers['industry'], name="Industrial Zones", style_function=lambda x: {'fillColor':'purple','color':'purple','weight':1,'fillOpacity':0.4}, tooltip="Industrial Zone", show=show_industry).add_to(m)
            if 'construction' in layers:
                folium.GeoJson(layers['construction'], name="Construction Zones", style_function=lambda x: {'fillColor':'orange','color':'orange','weight':1,'fillOpacity':0.4}, tooltip="Construction Zone", show=show_construction).add_to(m)
                
            try:
                from geospatial_features import fetch_nasa_firms_data
                firms = fetch_nasa_firms_data()
                if not firms.empty:
                    fire_group = folium.FeatureGroup(name="Active Fires (FIRMS)", show=show_fires)
                    for _, r in firms.iterrows():
                        folium.CircleMarker([r['latitude'], r['longitude']], radius=3, color='red', fill=True, popup="Active Fire").add_to(fire_group)
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
                    radius = 12
                    popup_text = f"<b>{stat}</b><br>PM2.5: {intelligence_data['forecast']['24h']['pm25']}<br>AQI: {intelligence_data['forecast']['24h']['aqi_category']}"
                else:
                    color = "lightgray"
                    radius = 6
                    popup_text = stat
                    
                folium.CircleMarker(
                    location=[s_lat, s_lon],
                    radius=radius,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7 if is_selected else 0.4,
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=stat
                ).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, height=400, width=1200, returned_objects=[])

    st.markdown("---")

    st.header("Administrator Diagnostics")
    
    tab1, tab2, tab3 = st.tabs(["Forecast & Source Attribution", "SHAP Explainer", "Recommended Actions"])
    
    with tab1:
        col_chart, col_donut = st.columns([2, 1])
        with col_chart:
            st.subheader("PM2.5 Forecast (72h Horizon)")
            if not df_hist.empty:
                hist = df_hist[df_hist['station'] == selected_station].tail(30)[['date', 'pm25']]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=hist['date'], y=hist['pm25'], mode='lines+markers', name='Historical', line=dict(color='gray')))
                
                last_hist_date = hist['date'].iloc[-1]
                last_hist_val = hist['pm25'].iloc[-1]
                
                last_date = pd.to_datetime(intelligence_data['timestamp'])
                f_dates = [last_hist_date, last_date + pd.Timedelta(days=1), last_date + pd.Timedelta(days=2), last_date + pd.Timedelta(days=3)]
                f_vals = [
                    last_hist_val,
                    intelligence_data['forecast']['24h']['pm25'],
                    intelligence_data['forecast']['48h']['pm25'],
                    intelligence_data['forecast']['72h']['pm25']
                ]
                fig.add_trace(go.Scatter(x=f_dates, y=f_vals, mode='lines+markers', name='Forecast', line=dict(color='red', dash='dash')))
                
                fig.update_layout(title="Historical & Predicted PM2.5", xaxis_title="Date", yaxis_title="PM2.5", margin=dict(l=0, r=0, t=40, b=0), template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
        with col_donut:
            st.subheader("Source Attribution")
            sources = intelligence_data['source_influence']['sources']
            labels = [s['name'] for s in sources]
            values = [s['contribution_percentage'] for s in sources]
            hover_texts = [f"Confidence: {s.get('confidence', 0)*100:.0f}%" for s in sources]
            
            fig2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, hovertext=hover_texts, textinfo='label+percent', textposition='outside')])
            fig2.update_layout(margin=dict(l=40, r=40, t=40, b=40), showlegend=True, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
            
    with tab2:
        col_shap_inc, col_shap_dec = st.columns(2)
        with col_shap_inc:
            st.subheader("Top Factors Increasing Pollution")
            for factor in intelligence_data['model_explanation']['top_increasing_factors'][:5]:
                clean_name = factor['feature'].replace("_", " ").title()
                st.markdown(f"- **{clean_name}** (+{factor['impact']} impact)")
                
        with col_shap_dec:
            st.subheader("Top Factors Decreasing Pollution")
            for factor in intelligence_data['model_explanation']['top_decreasing_factors'][:5]:
                clean_name = factor['feature'].replace("_", " ").title()
                st.markdown(f"- **{clean_name}** ({factor['impact']} impact)")
                
    with tab3:
        st.subheader("Administrative Recommendations")
        for rec in intelligence_data['recommendations']:
            st.info(rec)
            
        with st.expander("System Architecture (How it works)"):
            st.code('''
            AQI + Weather Data 
                    ↓
            Feature Engineering 
                    ↓
            XGBoost Forecast 
                    ↓
            SHAP Explanation 
                    ↓
            Geospatial Evidence (OSMnx/FIRMS)
                    ↓
            Source Attribution Agent
                    ↓
            Citizen Advisory Agent
            ''')
            
    st.markdown("---")
    st.download_button(
        label="Download Full Intelligence Report (JSON)",
        data=json.dumps(intelligence_data, indent=2, ensure_ascii=False),
        file_name=f"intelligence_{selected_station.split(',')[0].replace(' ', '_')}.json",
        mime="application/json"
    )

elif view_mode == "Citizen":
    st.header("Citizen Air Quality Advisory")
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current PM2.5 Forecast (24h)", f"{intelligence_data['forecast']['24h']['pm25']} µg/m³")
    with col2:
        st.metric("48h Outlook", f"{intelligence_data['forecast']['48h']['pm25']} µg/m³")
    with col3:
        st.metric("72h Outlook", f"{intelligence_data['forecast']['72h']['pm25']} µg/m³")
        
    st.markdown(f"**Overall Status:** {intelligence_data['forecast']['24h']['aqi_category']}")
    st.markdown("---")
    
    lang = st.selectbox("Select Language / भाषा निवड / भाषा चुनें", ["english", "hindi", "marathi"])
    group = st.radio("Who is this for?", ["General Public", "Sensitive Groups (Children, Elderly, Asthmatics)"])
    group_key = "general_public" if group == "General Public" else "sensitive_groups"
    
    advisory_text = intelligence_data['citizen_advisory']['advisories'].get(lang, {}).get(group_key, "Advisory not available in this language.")
    
    st.success(advisory_text)
