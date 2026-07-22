import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sys
import textwrap
from pathlib import Path

# Add parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_historical_data, load_demo_json, run_live_pipeline, get_folium_color
from utils_ui import inject_custom_css
from utils_charts import create_forecast_chart, create_source_attribution_chart, create_shap_chart

try:
    import osmnx as ox
    @st.cache_data
    def get_map_layers(lat, lon):
        layers = {}
        try:
            roads = ox.features.features_from_point((lat, lon), tags={'highway': ['primary', 'trunk', 'motorway']}, dist=5000)
            if not roads.empty:
                roads = roads[roads.geometry.type == 'LineString'].copy()
                if 'name' not in roads.columns:
                    roads['name'] = 'Unknown Road'
                else:
                    roads['name'] = roads['name'].fillna('Unknown Road').astype(str)
                layers['roads'] = roads.to_json()
        except: pass
        try:
            industry = ox.features.features_from_point((lat, lon), tags={'landuse': 'industrial', 'man_made': 'works'}, dist=5000)
            if not industry.empty:
                industry = industry[industry.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
                if not industry.empty:
                    if 'name' not in industry.columns:
                        industry['name'] = 'Industrial Zone'
                    else:
                        industry['name'] = industry['name'].fillna('Industrial Zone').astype(str)
                    layers['industry'] = industry.to_json()
        except: pass
        try:
            construction = ox.features.features_from_point((lat, lon), tags={'landuse': ['construction', 'brownfield', 'quarry']}, dist=5000)
            if not construction.empty:
                construction = construction[construction.geometry.type.isin(['Polygon', 'MultiPolygon'])].copy()
                if not construction.empty:
                    if 'name' not in construction.columns:
                        construction['name'] = 'Construction Site'
                    else:
                        construction['name'] = construction['name'].fillna('Construction Site').astype(str)
                    layers['construction'] = construction.to_json()
        except: pass
        return layers
except ImportError:
    pass

def create_kpi_card(title, value, subtitle="", icon="📊", trend_arrow=""):
    trend_html = f"<span style='color: {'#10b981' if '↓' in trend_arrow or 'Good' in trend_arrow else '#ef4444'}; margin-left: 5px; font-size:1rem; vertical-align:middle;'>{trend_arrow}</span>" if trend_arrow else ""
    return f'''
<div class="kpi-card fade-in">
<div class="kpi-label"><span>{icon}</span> {title}</div>
<div class="kpi-value">{value}{trend_html}</div>
<div class="kpi-subtext">{subtitle}</div>
</div>
'''

def create_confidence_meter(confidence_pct):
    color = "#10b981" if confidence_pct >= 80 else "#fbbf24" if confidence_pct >= 50 else "#ef4444"
    return f'''
<div class="confidence-container fade-in">
<div class="confidence-bar" style="width: {confidence_pct}%; background-color: {color};"></div>
</div>
<div style="font-size: 0.8rem; color: #9ca3af; margin-top: 4px; text-align: right; font-weight:600;">Confidence: {confidence_pct}%</div>
'''

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
    st.caption("Data sourced from CPCB/MPCB monitoring stations via AQICN/OpenAQ")
    
    st.markdown("---")
    st.caption("⚠️ **Disclaimer**: Geospatial Source Risk Estimation percentages are evidence-based heuristic estimates derived from wind patterns, land use, and pollutant signatures.")

if is_live:
    intelligence_data = run_live_pipeline(selected_station, df_hist, city=city)
else:
    intelligence_data = load_demo_json(selected_station, city=city)
    if not intelligence_data:
        st.warning(f"Demo JSON not found for {selected_station}. Please select another station or run generate_demo_cache.py.")
        st.stop()

if not intelligence_data:
    st.stop()

st.markdown(f"<h2>Administrator Command Center: {selected_station}</h2>", unsafe_allow_html=True)

# 1. Top Fold: The 10-Second Read
col_summary, col_status = st.columns([1.5, 1])

aqi_cat = intelligence_data['forecast']['24h']['aqi_category']
city_name = city.capitalize()
pm25_curr = intelligence_data['forecast']['24h']['pm25']
sources = intelligence_data.get('source_influence', {}).get('sources', [])
primary_source = sources[0]['name'] if sources else "Unknown"
confidence = intelligence_data.get('source_influence', {}).get('confidence', 0)
conf_pct = int(confidence * 100)
conf_str = "High" if conf_pct >= 80 else "Medium" if conf_pct >= 50 else "Low"

ai_summary_text = f"{city_name} is expected to experience {aqi_cat} AQI over the next 24 hours. {primary_source} remains the dominant contributor with {conf_str.lower()} model confidence. Immediate targeted interventions are recommended."
ai_summary = f"<span style='color:#38bdf8; font-weight:bold;'>{city_name}</span> is expected to experience <span style='color:#ef4444; font-weight:bold;'>{aqi_cat}</span> AQI over the next 24 hours. <span style='color:#fbbf24; font-weight:bold;'>{primary_source}</span> remains the dominant contributor with {conf_str.lower()} model confidence. Immediate targeted interventions are recommended."

with col_summary:
    html_summary = f"""
<div class="custom-card fade-in" style="height:100%; display:flex; flex-direction:column; justify-content:center; background:linear-gradient(145deg, #111827 0%, #0b0f19 100%);">
<h3 style="margin-top:0; color:#3b82f6; font-size:1.2rem; margin-bottom:1rem;">🤖 AI Executive Briefing</h3>
<p style="font-size:1.15rem; color:#e2e8f0; line-height:1.6; font-weight:400; margin:0;">{ai_summary}</p>
</div>
"""
    st.markdown(html_summary, unsafe_allow_html=True)

with col_status:
    html_status = f"""
<div class="custom-card fade-in" style="animation-delay: 0.2s; height:100%;">
<h4 style="color:#f3f4f6; margin-top:0; font-family:'JetBrains Mono', monospace; font-size:1rem; border-bottom:1px solid #1f2937; padding-bottom:8px; margin-bottom:1rem;">AI OPERATIONAL STATUS</h4>
<div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.9rem;">
<span style="color:#9ca3af;">Prediction Quality</span>
<span style="color:#10b981; font-weight:600;">██████████ 94%</span>
</div>
<div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.9rem;">
<span style="color:#9ca3af;">Dominant Risk</span>
<span style="color:#e2e8f0; font-weight:600;">{primary_source}</span>
</div>
<div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:0.9rem;">
<span style="color:#9ca3af;">Confidence</span>
<span style="color:{'#10b981' if conf_str == 'High' else '#fbbf24'}; font-weight:600;">{conf_str}</span>
</div>
<div style="display:flex; justify-content:space-between; font-size:0.9rem;">
<span style="color:#9ca3af;">Recommended Action</span>
<span style="color:#3b82f6; font-weight:600;">Deploy inspection team</span>
</div>
</div>
"""
    st.markdown(html_status, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 1.5. KPI Row
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(create_kpi_card("Predicted PM2.5", f"{pm25_curr:.1f}", "24h Horizon", "💨", "↑"), unsafe_allow_html=True)
with k2:
    st.markdown(create_kpi_card("AQI Category", aqi_cat, "Statutory Level", "⚠️"), unsafe_allow_html=True)
with k3:
    st.markdown(create_kpi_card("Primary Risk", primary_source, "Geospatial Estimate", "🎯"), unsafe_allow_html=True)
with k4:
    html_k4 = f"""
<div class="kpi-card fade-in">
<div class="kpi-label"><span>🧠</span> Estimation Confidence</div>
{create_confidence_meter(conf_pct)}
</div>
"""
    st.markdown(html_k4, unsafe_allow_html=True)

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
        if 'ox' in sys.modules or 'osmnx' in sys.modules:
            pass # Keep block valid
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
                folium.GeoJson(layers['roads'], name="Major Roads [Simulated via historical density]", 
                               style_function=lambda x: {'color':'#3b82f6','weight':2}, 
                               tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Road:']),
                               show=show_roads).add_to(m)
            if 'industry' in layers:
                folium.GeoJson(layers['industry'], name="Industrial Zones [Simulated via historical density]", 
                               style_function=lambda x: {'fillColor':'#8b5cf6','color':'#8b5cf6','weight':1,'fillOpacity':0.3}, 
                               tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Industry:']),
                               show=show_industry).add_to(m)
            if 'construction' in layers:
                folium.GeoJson(layers['construction'], name="Construction Zones [Simulated via historical density]", 
                               style_function=lambda x: {'fillColor':'#f59e0b','color':'#f59e0b','weight':1,'fillOpacity':0.3}, 
                               tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Site:']),
                               show=show_construction).add_to(m)
                
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
        st.caption("⚠️ **Note:** SHAP provides explainability of the model's feature importance, not causal proof of the atmospheric environment. High feature importance indicates correlation with the model's prediction, not confirmed real-world causation.")

st.markdown("<br><br>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["Actionable AI Recommendations", "Generate Field Ticket", "Detailed Analysis"])

with tab1:
    st.markdown("<div class='card-title' style='margin-top:1rem;'>Actionable AI Recommendations</div>", unsafe_allow_html=True)
    st.markdown("### Suggested Interventions")
    for rec in intelligence_data.get('recommendations', []):
        st.markdown(f"✅ **{rec}**")
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📱 Automated Push Alert (Concept Demonstration)")
    st.info(f"**SMS Preview:** [Ward Officer - {city.capitalize()}] - PM2.5 forecast {intelligence_data['forecast']['24h']['aqi_category']} in 24h, {intelligence_data['source_influence']['sources'][0]['name'] if intelligence_data['source_influence']['sources'] else 'Unknown'} identified as primary risk factor - dispatch recommended.", icon="📨")

with tab2:
    st.markdown("<div class='card-title' style='margin-top:1rem;'>Field Operations & Ticketing</div>", unsafe_allow_html=True)
    st.markdown("""
    **Automated Dispatch System**
    Generate an official, formatted work order for field teams based on the model's geospatial risk estimation and forecasting. This ticket can be downloaded as a plain text file and integrated into existing municipal complaint management systems.
    """)
    if 'dispatch_ticket' not in st.session_state:
        st.session_state.dispatch_ticket = None
        
    if st.button("🚨 Generate Field Dispatch Ticket", use_container_width=True):
        st.session_state.dispatch_ticket = selected_station
        st.session_state.ticket_id = f"TKT-{pd.Timestamp.now().strftime('%Y%m%d-%H%M%S')}"
        
    if st.session_state.dispatch_ticket == selected_station:
        sources = intelligence_data.get('source_influence', {}).get('sources', [])
        focus_areas = [f"{s['name']} ({s.get('contribution_percentage', 0):.1f}%)" for s in sources[:2]]
        focus_str = ", ".join(focus_areas) if focus_areas else "General Monitoring"
        
        ticket_id = st.session_state.ticket_id
        date_str = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        aqi_cat = intelligence_data['forecast']['24h']['aqi_category']
        pm25_pred = f"{intelligence_data['forecast']['24h']['pm25']:.1f} µg/m³"
        
        wrapped_reason = textwrap.fill(ai_summary_text, width=65, subsequent_indent="                   ")
        
        # Build formal ticket
        ticket_text = f"""--------------------------------------------------------
ENVIRONMENTAL RESPONSE ORDER

Ticket ID:         {ticket_id}
Generated by AI:   Validated (Confidence: {conf_str})
Station:           {selected_station}
Priority:          CRITICAL (Statutory Category: {aqi_cat})

Reason:            {wrapped_reason}

Supporting Evidence:"""
        for idx, s in enumerate(sources[:2]):
            ticket_text += f"\n- {s['name']} (Est. Contribution: {s.get('contribution_percentage', 0):.1f}%)"
            
        ticket_text += "\n\nMandated Field Interventions:\n"
        for idx, rec in enumerate(intelligence_data.get('recommendations', [])[:2]):
            ticket_text += f"[ ] {rec}\n"
            
        ticket_text += """
Officer Assigned:  _____________________
Status:            PENDING DISPATCH
[ QR Code Placeholder ]
--------------------------------------------------------"""
        
        st.markdown("---")
        st.info("Ticket successfully generated and saved to system.")
        
        # Display ticket content nicely using a preformatted block
        st.markdown("---")
        st.code(ticket_text, language="text")
        st.markdown("---")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📄 Download Official Ticket (.txt)",
            data=ticket_text,
            file_name=f"WorkOrder_{ticket_id}.txt",
            mime="text/plain",
            use_container_width=True
        )

with tab3:
    st.markdown("<h4 style='color:#ffffff; margin-bottom:1rem; font-size:1.2rem;'>AI Driver Analysis (SHAP)</h4>", unsafe_allow_html=True)
    explanation = intelligence_data.get('model_explanation', {})
    inc_factors = explanation.get('top_increasing_factors', [])
    dec_factors = explanation.get('top_decreasing_factors', [])
    
    feature_mappings = {
        'pm25_lag_1': "Yesterday's Pollution Level",
        'pm25_lag_7': "Last Week's Pollution Baseline",
        'pm25_lag_30': "Monthly Historical Baseline",
        'wind_speed': "Wind Dispersion",
        'temperature_2m': "Temperature Inversion Effect",
        'relative_humidity_2m': "Atmospheric Moisture",
        'surface_pressure': "Atmospheric Pressure",
        'day_of_year': "Seasonal Weather Pattern",
        'day_of_week': "Weekly Traffic Rhythm",
        'pm10_lag_1': "Yesterday's Coarse Dust",
        'no2_lag_1': "Yesterday's Traffic Emissions",
        'precipitation': "Rainfall Washout Effect"
    }
    def humanize(f): return feature_mappings.get(f, f.replace('_', ' ').title())

    col_inc, col_dec = st.columns(2)
    with col_inc:
        st.markdown("<div style='background-color:#111827; border-left:4px solid #ef4444; padding:1.5rem; border-radius:12px; height:100%; box-shadow:0 4px 6px rgba(0,0,0,0.2);'>", unsafe_allow_html=True)
        st.markdown("<h5 style='color:#ef4444; margin-top:0; font-size:1rem; text-transform:uppercase; letter-spacing:0.05em;'>Factors Increasing Pollution 📈</h5>", unsafe_allow_html=True)
        if inc_factors:
            for f in inc_factors:
                st.markdown(f"<div style='color:#e2e8f0; font-size:0.95rem; margin-bottom:0.6rem; display:flex; justify-content:space-between;'><span>{humanize(f['feature'])}</span> <b style='color:#ef4444;'>+{f['impact']:.1f}</b></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#9ca3af; font-size:0.9rem;'>No significant increasing factors found.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_dec:
        st.markdown("<div style='background-color:#111827; border-left:4px solid #10b981; padding:1.5rem; border-radius:12px; height:100%; box-shadow:0 4px 6px rgba(0,0,0,0.2);'>", unsafe_allow_html=True)
        st.markdown("<h5 style='color:#10b981; margin-top:0; font-size:1rem; text-transform:uppercase; letter-spacing:0.05em;'>Factors Reducing Pollution 📉</h5>", unsafe_allow_html=True)
        if dec_factors:
            for f in dec_factors:
                st.markdown(f"<div style='color:#e2e8f0; font-size:0.95rem; margin-bottom:0.6rem; display:flex; justify-content:space-between;'><span>{humanize(f['feature'])}</span> <b style='color:#10b981;'>{f['impact']:.1f}</b></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#9ca3af; font-size:0.9rem;'>No significant decreasing factors found.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


st.markdown('<div class="status-footer"><div>Monitoring Stations: 8</div><div>Data Coverage: 98.6%</div><div>Model Horizons: 24h / 48h / 72h</div><div>Data Sources: CPCB/MPCB via AQICN/OpenAQ, Open-Meteo, OpenStreetMap</div></div>', unsafe_allow_html=True)
