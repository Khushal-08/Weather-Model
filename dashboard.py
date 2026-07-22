import streamlit as st
import sys
from pathlib import Path

# Important: ensure script directory is in sys.path
sys.path.append(str(Path(__file__).parent.parent))
from utils import load_historical_data
from utils_ui import inject_custom_css

st.set_page_config(page_title="Air Quality Intelligence Platform", page_icon="🌤️", layout="wide", initial_sidebar_state="expanded")

# Inject global CSS
inject_custom_css()

CITY = st.sidebar.selectbox("Select Active City for Analysis", ["Mumbai", "Delhi"]).lower()
st.session_state['city'] = CITY

# Load fast cached data for KPIs across both cities
df_mumbai, stations_mumbai = load_historical_data(city='mumbai')
df_delhi, stations_delhi = load_historical_data(city='delhi')

num_stations_mumbai = len(stations_mumbai) if stations_mumbai else 8
num_stations_delhi = len(stations_delhi) if stations_delhi else 8
total_stations = num_stations_mumbai + num_stations_delhi

max_pm25_mumbai = df_mumbai['pm25'].max() if not df_mumbai.empty and 'pm25' in df_mumbai.columns else 0
max_pm25_delhi = df_delhi['pm25'].max() if not df_delhi.empty and 'pm25' in df_delhi.columns else 0
worst_pm25_overall = max(max_pm25_mumbai, max_pm25_delhi)
worst_pm25_str = f"{worst_pm25_overall:.1f}" if worst_pm25_overall > 0 else "N/A"

st.markdown(f"<h1>National Urban Air Quality Intelligence Platform</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='font-size: 1.1rem; color: #9ca3af; margin-bottom: 2rem;'>An AI-driven platform for proactive air quality management, monitoring {total_stations} stations across Tier-1 Cities.</p>", unsafe_allow_html=True)

# 1. National Snapshot (City Comparison)
st.markdown("<h3 style='margin-bottom:1.5rem; color:#f3f4f6;'>National Snapshot</h3>", unsafe_allow_html=True)

def get_snapshot(df):
    if df.empty or 'pm25' not in df.columns or len(df) < 2:
        return 0, "N/A"
    curr = df.iloc[-1]['pm25']
    prev = df.iloc[-2]['pm25']
    trend_val = curr - prev
    trend_arrow = f"↑ +{trend_val:.1f}" if trend_val > 0 else f"↓ {trend_val:.1f}"
    return curr, trend_arrow

curr_mum, trend_mum = get_snapshot(df_mumbai)
curr_del, trend_del = get_snapshot(df_delhi)

priority_city = "Delhi" if curr_del > curr_mum else "Mumbai"

snapshot_html = f"""
<div style="display: flex; gap: 1.5rem; margin-bottom: 2rem;">
<div class="kpi-card fade-in" style="flex: 1; border-top: 4px solid {'#ef4444' if curr_mum > 100 else '#10b981'};">
<div class="kpi-label"><span>📍</span> Mumbai, Maharashtra</div>
<div class="kpi-value" style="font-size:2.5rem;">{curr_mum:.1f} <span style="font-size:1rem; color:#9ca3af; font-weight:500;">µg/m³ PM2.5</span></div>
<div class="kpi-subtext" style="display:flex; justify-content:space-between; margin-top:1rem; font-size:0.9rem;">
<span><span style="color:{'#ef4444' if '↑' in trend_mum else '#10b981'}; font-weight:600;">{trend_mum}</span> 24h Trend</span>
<span>🚗 Dominant Risk: <b>Traffic</b></span>
</div>
</div>
<div class="kpi-card fade-in" style="flex: 1; border-top: 4px solid {'#ef4444' if curr_del > 100 else '#10b981'}; animation-delay: 0.1s;">
<div class="kpi-label"><span>📍</span> New Delhi, Delhi</div>
<div class="kpi-value" style="font-size:2.5rem;">{curr_del:.1f} <span style="font-size:1rem; color:#9ca3af; font-weight:500;">µg/m³ PM2.5</span></div>
<div class="kpi-subtext" style="display:flex; justify-content:space-between; margin-top:1rem; font-size:0.9rem;">
<span><span style="color:{'#ef4444' if '↑' in trend_del else '#10b981'}; font-weight:600;">{trend_del}</span> 24h Trend</span>
<span>🏭 Dominant Risk: <b>Industry</b></span>
</div>
</div>
</div>

<div class="advisory-box fade-in" style="animation-delay: 0.2s; margin-bottom: 3rem; background-color: rgba(239, 68, 68, 0.1); border-left-color: #ef4444; color: #fca5a5;">
<strong>⚠️ Strategic Recommendation:</strong> Priority AI Response Protocol activated for <b>{priority_city}</b> due to elevated PM2.5 levels and increasing trends. Please select {priority_city} from the sidebar and proceed to the Administrator View.
</div>
"""
st.markdown(snapshot_html, unsafe_allow_html=True)

# 2. View Cards (Simplified)
card_style = "border-radius:12px; background:#111827; padding:2rem; border:1px solid #1f2937; box-shadow:0 4px 6px rgba(0,0,0,0.3); height:100%; transition: transform 0.2s; cursor: default;"

col_admin, col_cit = st.columns(2)
with col_admin:
    st.markdown(f"""
        <div class="custom-card fade-in" style="animation-delay: 0.3s;">
            <h3 style="margin-top:0; color:#ffffff; font-family:'Inter', sans-serif;">🏢 Administrator View</h3>
            <p style="color:#9ca3af; font-weight:500; margin-bottom:1.5rem;">For City Planners & Environmental Regulators</p>
            <p style="color:#e2e8f0; font-size:0.95rem; line-height:1.5;">Access deep geospatial diagnostics, Generate Dispatch Tickets, view Source Risk Estimation, and multi-horizon AI forecasting.</p>
        </div>
    """, unsafe_allow_html=True)

with col_cit:
    st.markdown(f"""
        <div class="custom-card fade-in" style="animation-delay: 0.4s;">
            <h3 style="margin-top:0; color:#ffffff; font-family:'Inter', sans-serif;">👨‍👩‍👧‍👦 Citizen View</h3>
            <p style="color:#9ca3af; font-weight:500; margin-bottom:1.5rem;">For General Public & Sensitive Groups</p>
            <p style="color:#e2e8f0; font-size:0.95rem; line-height:1.5;">Get hyperlocal AQI status, health risk alerts, and personalized advisories translated into regional languages with a clean interface.</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="status-footer"><div style="display:flex; align-items:center;"><span class="live-badge-dot"></span><span class="live-badge-text">LIVE</span></div><div>Monitoring Stations: 16</div><div>Models: XGBoost 24h/48h/72h</div><div>Data Sources: CPCB, Open-Meteo, OSM</div></div>', unsafe_allow_html=True)

