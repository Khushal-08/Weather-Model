import streamlit as st
import datetime
import sys
from pathlib import Path

# Add parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_historical_data, load_demo_json, run_live_pipeline
from utils_ui import inject_custom_css

st.set_page_config(page_title="Citizen View", layout="wide", initial_sidebar_state="expanded")
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
        
    selected_station = st.selectbox("Select Neighborhood / Station", station_list)
    
if is_live:
    intelligence_data = run_live_pipeline(selected_station, df_hist, city=city)
else:
    intelligence_data = load_demo_json(selected_station, city=city)
    if not intelligence_data:
        st.warning(f"Demo JSON not found for {selected_station}. Please select another station or run generate_demo_cache.py.")
        st.stop()

if not intelligence_data:
    st.stop()

st.markdown(f"<h2>Hyperlocal Air Quality: {selected_station}</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; font-size:1.1rem; margin-top:-10px; margin-bottom:2rem;'>Real-time health advisories powered by AI.</p>", unsafe_allow_html=True)

aqi_cat = intelligence_data['forecast']['24h']['aqi_category']
pm25_val = intelligence_data['forecast']['24h']['pm25']

color_class = "aqi-good"
if aqi_cat == "Satisfactory": color_class = "aqi-satisfactory"
elif aqi_cat == "Moderately Polluted": color_class = "aqi-moderate"
elif aqi_cat == "Poor": color_class = "aqi-poor"
elif aqi_cat == "Very Poor": color_class = "aqi-verypoor"
elif aqi_cat == "Severe": color_class = "aqi-severe"

# Massive AQI Card
col_giant, col_metrics = st.columns([1, 1])

with col_giant:
    st.markdown("<h3 style='margin-bottom:1rem; color:#f3f4f6;'>Current Status</h3>", unsafe_allow_html=True)
    html_giant = f"""
<div class="custom-card fade-in" style="text-align:center; padding:3rem 2rem;">
<p style="color:#9ca3af; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:0;">Current PM2.5</p>
<p class="aqi-giant {color_class}" style="margin: 0.5rem 0;">{pm25_val:.0f}</p>
<p style="font-size:1.5rem; font-weight:700; margin-top:0; color:#ffffff;">{aqi_cat}</p>
</div>
"""
    st.markdown(html_giant, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    lang = st.selectbox("Advisory Language / भाषा", ["english", "hindi", "marathi"])
    group = st.radio("Who is this for?", ["General Public", "Sensitive Groups (Children, Elderly, Asthmatics)"])

with col_metrics:
    st.markdown("<h3 style='margin-bottom:1rem; color:#ffffff;'>Forecast Outlook</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        html_c1 = f"""
<div class="custom-card fade-in" style="animation-delay: 0.1s;">
<p style="color:#9ca3af; font-weight:600; margin-bottom:0; text-transform:uppercase; letter-spacing:0.05em;">Tomorrow (48h)</p>
<p style="font-family:'JetBrains Mono', monospace; font-size:2rem; font-weight:700; color:#ffffff; margin:0.5rem 0;">{intelligence_data['forecast']['48h']['pm25']:.0f} <span style="font-size:1rem; color:#9ca3af;">µg/m³</span></p>
<p style="color:#e2e8f0; margin-bottom:0; font-weight:500;">{intelligence_data['forecast']['48h']['aqi_category']}</p>
</div>
"""
        st.markdown(html_c1, unsafe_allow_html=True)
    with c2:
        html_c2 = f"""
<div class="custom-card fade-in" style="animation-delay: 0.2s;">
<p style="color:#9ca3af; font-weight:600; margin-bottom:0; text-transform:uppercase; letter-spacing:0.05em;">Day After (72h)</p>
<p style="font-family:'JetBrains Mono', monospace; font-size:2rem; font-weight:700; color:#ffffff; margin:0.5rem 0;">{intelligence_data['forecast']['72h']['pm25']:.0f} <span style="font-size:1rem; color:#9ca3af;">µg/m³</span></p>
<p style="color:#e2e8f0; margin-bottom:0; font-weight:500;">{intelligence_data['forecast']['72h']['aqi_category']}</p>
</div>
"""
        st.markdown(html_c2, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<h3 style='color:#ffffff;'>Personalized Health Advisory</h3>", unsafe_allow_html=True)

group_key = "general_public" if group == "General Public" else "sensitive_groups"
advisory_text = intelligence_data['citizen_advisory']['advisories'].get(lang, {}).get(group_key, "Advisory not available in this language.")
current_time = datetime.datetime.now().strftime("%I:%M %p")

# Generate Dynamic Quick Action Tags
tags_html = ""
if aqi_cat in ["Poor", "Very Poor", "Severe"]:
    tags_html += '<div class="action-tag">😷 Wear Mask</div>'
    tags_html += '<div class="action-tag">🏃 Avoid Outdoor Exercise</div>'
    tags_html += '<div class="action-tag">🪟 Keep Windows Closed</div>'
elif aqi_cat == "Moderately Polluted":
    tags_html += '<div class="action-tag">😷 Mask for Sensitive Groups</div>'
    tags_html += '<div class="action-tag">⏱️ Reduce Prolonged Exertion</div>'
else:
    tags_html += '<div class="action-tag">✅ Safe for Outdoor Activities</div>'
    tags_html += '<div class="action-tag">🪟 Open Windows for Ventilation</div>'

# Dark mode Whatsapp/Advisory preview
whatsapp_html = f"""
<div style="margin-bottom: 15px;">
    {tags_html}
</div>
<div style="background-color: #111827; padding: 20px; border-radius: 12px; max-width: 600px; margin: 10px 0; font-family: 'Inter', sans-serif; border: 1px solid #1f2937;">
    <div style="background-color: #1f2937; color: #f3f4f6; padding: 16px 20px; border-radius: 0px 12px 12px 12px; display: inline-block; max-width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <div style="color: #10b981; font-size: 0.85em; font-weight: 600; margin-bottom: 8px;">{city.capitalize()} Gov AQI Alerts ✓</div>
        <div style="font-size: 1.05em; line-height: 1.5; white-space: pre-wrap;">{advisory_text}</div>
        <div style="color: #9ca3af; font-size: 0.75em; text-align: right; margin-top: 8px;">{current_time}</div>
    </div>
</div>
"""
st.markdown(whatsapp_html, unsafe_allow_html=True)
st.caption("Air quality data sourced from CPCB/MPCB monitoring networks via AQICN.")

st.markdown("<br>", unsafe_allow_html=True)
col_sub1, col_sub2, col_sub3 = st.columns([1,2,1])
with col_sub2:
    st.markdown("<div style='text-align:center;'><h4>Subscribe to SMS/WhatsApp Alerts</h4></div>", unsafe_allow_html=True)
    phone_input = st.text_input("Mobile Number", placeholder="+91 98765 43210", label_visibility="collapsed")
    if st.button("Subscribe 🔔", use_container_width=True):
        if phone_input:
            st.toast(f"Success! Alerts for {selected_station} subscribed to {phone_input}.", icon="✅")
        else:
            st.toast("Please enter a mobile number first.", icon="⚠️")

st.markdown('<div class="status-footer"><div style="display:flex; align-items:center;"><span class="live-badge-dot"></span><span class="live-badge-text">LIVE</span></div><div>Monitoring Stations: 16</div><div>Models: XGBoost 24h/48h/72h</div><div>Data Sources: CPCB, Open-Meteo, OSM</div></div>', unsafe_allow_html=True)
