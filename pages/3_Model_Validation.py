import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
import sys
from pathlib import Path

# Add parent directory to sys.path to import utils
sys.path.append(str(Path(__file__).parent.parent))
from utils_ui import inject_custom_css
from utils_charts import COLORS, apply_chart_theme

st.set_page_config(page_title="Model Validation", page_icon="✅", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()

# Get city from session state or sidebar
city = st.session_state.get('city', 'mumbai')
with st.sidebar:
    st.title(f"{city.capitalize()} Validation")
    city = st.selectbox("Select City for Metrics", ["Mumbai", "Delhi"], index=0 if city == 'mumbai' else 1).lower()
    st.session_state['city'] = city

st.markdown(f"<h2>Model Validation & Performance Metrics: {city.capitalize()}</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; font-size:1.1rem; margin-top:-10px; margin-bottom:2rem;'>Comprehensive evaluation of the XGBoost forecasting pipelines.</p>", unsafe_allow_html=True)

# 1. Dataset Overview
st.markdown("<div class='card-title'>Training Dataset Overview</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Date Range", value="2019 - 2026")
with col2:
    st.metric(label="Stations Used", value="7" if city == 'mumbai' else "8")
with col3:
    st.metric(label="Total Samples", value="16,814" if city == 'mumbai' else "12,740")
with col4:
    st.metric(label="Engineered Features", value="56")
    
st.markdown("<br>", unsafe_allow_html=True)

# Define Metrics Based on City
if city == 'mumbai':
    metrics = {
        '24h': {'rmse': 35.58, 'pers': 47.82, 'imp': 25.59},
        '48h': {'rmse': 50.87, 'pers': 58.77, 'imp': 13.45},
        '72h': {'rmse': 56.14, 'pers': 61.70, 'imp': 9.00},
        'winter_24h': {'rmse': 15.28, 'pers': 18.90, 'imp': 19.18}
    }
else:
    metrics = {
        '24h': {'rmse': 18.05, 'pers': 34.11, 'imp': 47.09},
        '48h': {'rmse': 30.16, 'pers': 42.27, 'imp': 28.65},
        '72h': {'rmse': 33.82, 'pers': 44.57, 'imp': 24.12},
        'winter_24h': {'rmse': 20.10, 'pers': 47.98, 'imp': 58.11}
    }

# 2. Forecast Performance Cards
st.markdown("<div class='card-title'>Overall Forecast Performance</div>", unsafe_allow_html=True)

def draw_metric_bar(horizon, m_data):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=['Model vs Persistence'],
        x=[m_data['pers']],
        name='Persistence Baseline',
        orientation='h',
        marker_color=COLORS['grid']
    ))
    fig.add_trace(go.Bar(
        y=['Model vs Persistence'],
        x=[m_data['rmse']],
        name='AI Model (RMSE)',
        orientation='h',
        marker_color=COLORS['secondary']
    ))
    fig = apply_chart_theme(fig)
    fig.update_layout(
        barmode='overlay', 
        height=150, 
        margin=dict(t=30, b=0, r=20),
        xaxis_title="RMSE (Lower is better)",
        showlegend=True,
        title=f"{horizon} Horizon: +{m_data['imp']}% Improvement"
    )
    return fig

col_perf1, col_perf2, col_perf3 = st.columns(3)
with col_perf1:
    st.plotly_chart(draw_metric_bar("24h", metrics['24h']), use_container_width=True, config={'displayModeBar': False})
with col_perf2:
    st.plotly_chart(draw_metric_bar("48h", metrics['48h']), use_container_width=True, config={'displayModeBar': False})
with col_perf3:
    st.plotly_chart(draw_metric_bar("72h", metrics['72h']), use_container_width=True, config={'displayModeBar': False})

st.markdown("<br>", unsafe_allow_html=True)

# 3. Winter Evaluation
col_win, col_note = st.columns([1, 1])
with col_win:
    st.markdown("<div class='card-title'>Winter-Only Evaluation (Dec-Feb)</div>", unsafe_allow_html=True)
    st.markdown("Winter represents the most critical period for air quality forecasting due to intense pollution spikes and thermal inversions.")
    st.plotly_chart(draw_metric_bar("Winter 24h", metrics['winter_24h']), use_container_width=True, config={'displayModeBar': False})

with col_note:
    st.markdown("<div class='card-title'>Understanding the Persistence Baseline</div>", unsafe_allow_html=True)
    st.info("""
    **Why compare against 'Persistence'?**
    The Persistence Baseline assumes that *tomorrow's pollution will be exactly the same as today's*. 
    Because air quality is highly autocorrelated (a bad day is usually followed by another bad day), 
    persistence is notoriously difficult to beat. Any model that consistently beats persistence (especially in the challenging winter months) 
    is actively learning meteorological and temporal patterns rather than just copying the previous day's value.
    """)

st.markdown("<br>", unsafe_allow_html=True)

# 4. Feature Importance (SHAP summary)
st.markdown("<div class='card-title'>Global Feature Importance (SHAP)</div>", unsafe_allow_html=True)
st.markdown("The SHAP values below demonstrate the most influential features driving the XGBoost predictions across the entire dataset.")

col_shap1, col_shap2 = st.columns(2)

city_prefix = "" if city == 'mumbai' else "delhi_"
shap_sum_path = os.path.join("reports", "figures", f"{city_prefix}shap_summary_plot.png")
if not os.path.exists(shap_sum_path):
    shap_sum_path = os.path.join("reports", "figures", "shap_summary_plot.png")
    
shap_bar_path = os.path.join("reports", "figures", f"{city_prefix}shap_feature_importance.png")
if not os.path.exists(shap_bar_path):
    shap_bar_path = os.path.join("reports", "figures", "shap_feature_importance.png")

try:
    shap_summary = Image.open(shap_sum_path)
    with col_shap1:
        st.image(shap_summary, caption=f"SHAP Summary Plot - {city.capitalize()}", use_container_width=True)
except FileNotFoundError:
    with col_shap1:
        st.warning(f"SHAP Summary Plot not found for {city.capitalize()}.")

try:
    shap_bar = Image.open(shap_bar_path)
    with col_shap2:
        st.image(shap_bar, caption=f"SHAP Feature Importance (Bar) - {city.capitalize()}", use_container_width=True)
except FileNotFoundError:
    with col_shap2:
        st.warning(f"SHAP Feature Importance Plot not found for {city.capitalize()}.")
