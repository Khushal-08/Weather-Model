import streamlit as st
import pandas as pd
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

@st.cache_data
def load_historical_data(city='mumbai'):
    """Load the historical dataset to extract stations and recent history."""
    print("DEBUG: load_historical_data CACHE MISS")
    if city == 'mumbai':
        data_file = Path("data/processed/training_features.csv")
    else:
        data_file = Path(f"data/processed/{city}_training_features.csv")
        
    if not data_file.exists():
        return pd.DataFrame(), []
    df = pd.read_csv(data_file)
    df['date'] = pd.to_datetime(df['date'])
    
    sort_col = 'location' if 'location' in df.columns else 'station'
    df = df.sort_values([sort_col, 'date']).reset_index(drop=True)
    
    rolling_cols = [c for c in df.columns if 'rolling' in c]
    for col in rolling_cols:
        df[f"{col}_shifted"] = df.groupby(sort_col)[col].shift(1)
        
    stations = sorted(df['station'].unique())
    return df, stations

@st.cache_data
def load_demo_json(station_name, city='mumbai'):
    """Load the precomputed demo JSON for a station."""
    print(f"DEBUG: load_demo_json CACHE MISS for {station_name}")
    if city == 'mumbai':
        demo_dir = Path("data/demo/mumbai")
    else:
        demo_dir = Path(f"data/demo/{city}")
        
    file_name = f"{station_name.replace(' ', '_').replace(',', '')}.json"
    file_path = demo_dir / file_name
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def run_live_pipeline(station, df, city='mumbai'):
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
                pm25=pm25_val,
                city=city
            )
            status.update(label="Live Intelligence Generated Successfully!", state="complete", expanded=False)
            return result
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        st.info("Live mode encountered an error (e.g., API timeout or cache miss). Switching to Demo Mode is recommended.")
        return None
