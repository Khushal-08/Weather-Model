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
    intelligence_data = run_live_pipeline(selected_station, df_hist)
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
    st.markdown(f"""
        <div style="border-radius:16px; background:white; padding:3rem; border:1px solid #e2e8f0; box-shadow:0 10px 15px -3px rgba(0,0,0,0.05); text-align:center;">
            <p style="color:#64748b; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:0;">Current PM2.5</p>
            <p class="aqi-giant {color_class}">{pm25_val:.0f}</p>
            <p style="font-size:1.5rem; font-weight:700; margin-top:10px; color:#334155;">{aqi_cat}</p>
        </div>
    """, unsafe_allow_html=True)

with col_metrics:
    st.markdown("<h3 style='margin-bottom:1rem;'>Forecast Outlook</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
            <div style="border-radius:12px; background:white; padding:1.5rem; border:1px solid #e2e8f0; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
                <p style="color:#64748b; font-weight:600; margin-bottom:0;">Tomorrow (48h)</p>
                <p style="font-size:2rem; font-weight:700; color:#0f172a; margin:0;">{intelligence_data['forecast']['48h']['pm25']:.0f} <span style="font-size:1rem; color:#64748b;">µg/m³</span></p>
                <p style="color:#334155; margin-top:5px; margin-bottom:0;">{intelligence_data['forecast']['48h']['aqi_category']}</p>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div style="border-radius:12px; background:white; padding:1.5rem; border:1px solid #e2e8f0; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
                <p style="color:#64748b; font-weight:600; margin-bottom:0;">Day After (72h)</p>
                <p style="font-size:2rem; font-weight:700; color:#0f172a; margin:0;">{intelligence_data['forecast']['72h']['pm25']:.0f} <span style="font-size:1rem; color:#64748b;">µg/m³</span></p>
                <p style="color:#334155; margin-top:5px; margin-bottom:0;">{intelligence_data['forecast']['72h']['aqi_category']}</p>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    lang = st.selectbox("Advisory Language / भाषा", ["english", "hindi", "marathi"])
    group = st.radio("Who is this for?", ["General Public", "Sensitive Groups (Children, Elderly, Asthmatics)"])

st.markdown("---")
st.markdown("<h3>Personalized Health Advisory</h3>", unsafe_allow_html=True)

group_key = "general_public" if group == "General Public" else "sensitive_groups"
advisory_text = intelligence_data['citizen_advisory']['advisories'].get(lang, {}).get(group_key, "Advisory not available in this language.")
current_time = datetime.datetime.now().strftime("%I:%M %p")

# Light mode Whatsapp preview
whatsapp_html = f"""
<div style="background-color: #f0f2f5; padding: 20px; border-radius: 12px; max-width: 600px; margin: 10px auto; font-family: 'Inter', sans-serif; border: 1px solid #e2e8f0;">
    <div style="background-color: #ffffff; color: #1e293b; padding: 16px 20px; border-radius: 0px 12px 12px 12px; display: inline-block; max-width: 100%; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
        <div style="color: #25D366; font-size: 0.85em; font-weight: 600; margin-bottom: 8px;">{city.capitalize()} Gov AQI Alerts ✓</div>
        <div style="font-size: 1.05em; line-height: 1.5; white-space: pre-wrap;">{advisory_text}</div>
        <div style="color: #94a3b8; font-size: 0.75em; text-align: right; margin-top: 8px;">{current_time}</div>
    </div>
</div>
"""
st.markdown(whatsapp_html, unsafe_allow_html=True)

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
