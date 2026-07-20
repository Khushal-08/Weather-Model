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

CITY = st.sidebar.selectbox("Select City", ["Mumbai", "Delhi"]).lower()
st.session_state['city'] = CITY

# Load fast cached data for KPIs
df_hist, station_list = load_historical_data(city=CITY)
num_stations = len(station_list) if station_list else 8
worst_pm25 = f"{df_hist['pm25'].max():.1f}" if not df_hist.empty and 'pm25' in df_hist.columns else "N/A"

st.markdown(f"<h1>Urban Air Quality Intelligence Platform — {CITY.capitalize()}</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #475569; margin-bottom: 2rem;'>An AI-driven platform for proactive air quality management, predicting pollution hotspots and attributing sources using geospatial intelligence.</p>", unsafe_allow_html=True)

# 1. KPI Strip
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Active Monitoring Stations", value=num_stations)
with col2:
    st.metric(label="Forecast Horizons", value="24h / 48h / 72h")
with col3:
    st.metric(label="Supported Languages", value="English, Hindi, Marathi")
with col4:
    st.metric(label="Peak Historical PM2.5", value=worst_pm25, delta="µg/m³" if worst_pm25 != "N/A" else None, delta_color="off")

st.markdown("<br><br>", unsafe_allow_html=True)

# 2. View Cards
st.markdown("<h3 style='margin-bottom:1.5rem;'>Platform Modules</h3>", unsafe_allow_html=True)

col_admin, col_cit = st.columns(2)
with col_admin:
    st.markdown("""
        <div style="border-radius:12px; background:white; padding:2rem; border:1px solid #e2e8f0; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); height:100%;">
            <h3 style="margin-top:0;">🏢 Administrator View</h3>
            <p style="color:#64748b; font-weight:500;">For City Planners & Environmental Regulators</p>
            <p style="color:#475569;">Access deep geospatial diagnostics, actionable enforcement recommendations, Geospatial Source Risk Estimation, and multi-horizon PM2.5 forecasting.</p>
        </div>
    """, unsafe_allow_html=True)

with col_cit:
    st.markdown("""
        <div style="border-radius:12px; background:white; padding:2rem; border:1px solid #e2e8f0; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); height:100%;">
            <h3 style="margin-top:0;">👨‍👩‍👧‍👦 Citizen View</h3>
            <p style="color:#64748b; font-weight:500;">For General Public & Sensitive Groups</p>
            <p style="color:#475569;">Get hyperlocal AQI status, health risk alerts, and personalized advisories translated into regional languages with a minimalist interface.</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# 3. How it Works Strip
st.markdown("<h3>System Architecture</h3>", unsafe_allow_html=True)
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: stretch; text-align: center; margin-top: 1rem; gap: 1rem;">
    <div style="flex: 1; padding: 1.5rem; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📡</div>
        <div style="font-weight: 600; color: #0f172a;">1. Data Ingestion</div>
        <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">AQI & Weather APIs (Open-Meteo, OpenAQ)</div>
    </div>
    <div style="flex: 0.1; display:flex; align-items:center; justify-content:center; font-size: 1.5em; color: #94a3b8;">→</div>
    <div style="flex: 1; padding: 1.5rem; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🧠</div>
        <div style="font-weight: 600; color: #0f172a;">2. AI Forecasting</div>
        <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">Multi-Horizon XGBoost + SHAP Explainability</div>
    </div>
    <div style="flex: 0.1; display:flex; align-items:center; justify-content:center; font-size: 1.5em; color: #94a3b8;">→</div>
    <div style="flex: 1; padding: 1.5rem; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🌍</div>
        <div style="font-weight: 600; color: #0f172a;">3. Geospatial Engine</div>
        <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">OSMnx Heuristics (Traffic, Industry, Wind)</div>
    </div>
    <div style="flex: 0.1; display:flex; align-items:center; justify-content:center; font-size: 1.5em; color: #94a3b8;">→</div>
    <div style="flex: 1; padding: 1.5rem; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
        <div style="font-weight: 600; color: #0f172a;">4. GenAI Advisory</div>
        <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">LLM-powered recommendations & insights</div>
    </div>
</div>
""", unsafe_allow_html=True)
