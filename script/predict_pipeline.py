import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
import shap

# Import the existing pipeline modules
from geospatial_features import generate_dynamic_features
from attribution_agent import run_attribution_agent
from shap_explainer import explain_prediction
from citizen_advisory import generate_advisory

# Import multi-horizon loader
from train_multi_horizon import load_and_prepare_data_multi

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

def get_models_dir(city):
    if city == 'mumbai':
        return Path("models/mumbai")
    else:
        return Path(f"models/{city}")


def get_aqi_category(pm25):
    """Convert PM2.5 to Indian AQI category."""
    if pm25 <= 30:
        return "Good"
    elif pm25 <= 60:
        return "Satisfactory"
    elif pm25 <= 90:
        return "Moderately Polluted"
    elif pm25 <= 120:
        return "Poor"
    elif pm25 <= 250:
        return "Very Poor"
    else:
        return "Severe"

def generate_air_quality_intelligence(station, lat, lon, target_date, input_row, feature_names,
                                      wind_dir, wind_speed, no2=None, co=None, pm10=None, pm25=None, city='mumbai'):
    """
    End-to-End Inference Orchestration Pipeline.
    Combines Multi-Horizon Forecasting, SHAP, and Attribution Agent into a single unified JSON.
    """
    logger.info(f"Generating intelligence for {station} at {target_date} in {city}")
    
    # 1. Load Models & Forecast Multi-Horizon
    forecasts = {}
    models_dir = get_models_dir(city)
    primary_predicted_pm25 = None
    
    for horizon in ["24h", "48h", "72h"]:
        model_path = models_dir / f"xgboost_{horizon}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
            
        model = joblib.load(model_path)
        predicted_pm25 = float(model.predict(input_row)[0])
        aqi_category = get_aqi_category(predicted_pm25)
        
        forecasts[horizon] = {
            "pm25": round(predicted_pm25, 2),
            "aqi_category": aqi_category
        }
        
        # We use the 24h model as the primary anchor for SHAP and Attribution Agent
        if horizon == "24h":
            primary_predicted_pm25 = predicted_pm25
            primary_model = model
    
    # 2. Run SHAP Explanation (Anchored to 24h model)
    logger.info("Running SHAP model explanation on 24h model...")
    explainer = shap.TreeExplainer(primary_model)
    shap_result = explain_prediction(explainer, input_row, feature_names)
    
    # 3. Generate Geospatial Evidence
    logger.info("Running Geospatial Pipeline...")
    evidence_json = generate_dynamic_features(
        target_date=target_date,
        station_name=station,
        wind_dir=wind_dir,
        wind_speed=wind_speed,
        no2=no2,
        co=co,
        pm10=pm10,
        pm25=pm25,
        city=city
    )
    
    # 4. Run Attribution Agent
    logger.info("Running Source Attribution Engine...")
    attribution_result = run_attribution_agent(primary_predicted_pm25, evidence_json)
    
    # 5. Run Citizen Advisory Agent
    logger.info("Running Citizen Advisory Agent...")
    dominant_source = attribution_result["sources"][0]["name"] if attribution_result["sources"] else "Unknown"
    aqi_24h = forecasts["24h"]["aqi_category"]
    advisory_json = generate_advisory(station, "24h", aqi_24h, dominant_source)
    
    # 6. Compile Final Unified JSON
    final_intelligence = {
        "location": station,
        "latitude": lat,
        "longitude": lon,
        "timestamp": target_date,
        "forecast": forecasts,
        "model_explanation": {
            "top_increasing_factors": shap_result["top_increasing_factors"],
            "top_decreasing_factors": shap_result["top_decreasing_factors"],
            "main_drivers": shap_result["model_explanation"]["main_drivers"]
        },
        "source_influence": {
            "confidence": attribution_result["confidence"],
            "sources": attribution_result["sources"]
        },
        "recommendations": [s["recommendation"] for s in attribution_result["sources"] if s.get("recommendation")],
        "citizen_advisory": advisory_json
    }
    
    return final_intelligence

def validate_pipeline():
    """Test the orchestration pipeline on Sion, Mumbai."""
    logger.info("Starting End-to-End Orchestration Validation...")
    
    df, features, targets = load_and_prepare_data_multi(DATA_FILE)
    
    # Find Kurla, Mumbai station for our test case (different from Sion)
    sion_df = df[df['station'] == 'Kurla, Mumbai - MPCB'].tail(1)
    if sion_df.empty:
        sion_df = df[df['station'] != 'Sion, Mumbai - MPCB'].tail(1)
        
    input_row = sion_df[features]
    
    # Extract metadata
    station = sion_df['station'].iloc[0]
    lat = sion_df['latitude'].iloc[0] if 'latitude' in sion_df.columns else 19.047
    lon = sion_df['longitude'].iloc[0] if 'longitude' in sion_df.columns else 72.8746
    target_date = str(sion_df['date'].iloc[0])
    
    # Confirm dataset date range
    min_date = df['date'].min()
    max_date = df['date'].max()
    print(f"\n--- DATASET DATE RANGE CONFIRMATION ---")
    print(f"Training dataset date range: {min_date.date()} to {max_date.date()}")
    print(f"Selecting latest available record for validation: {target_date}")
    print("---------------------------------------\n")
    
    # Extract met and pollutant proxy
    wind_dir = float(sion_df['wind_speed_10m_mean'].iloc[0]) if 'wind_speed_10m_mean' in sion_df.columns else 270.0
    wind_speed = float(sion_df['wind_speed_10m_mean'].iloc[0]) if 'wind_speed_10m_mean' in sion_df.columns else 15.0
    no2 = float(sion_df['no2'].iloc[0]) if 'no2' in sion_df.columns else 55.0
    co = float(sion_df['co'].iloc[0]) if 'co' in sion_df.columns else 1.5
    pm10 = float(sion_df['pm10'].iloc[0]) if 'pm10' in sion_df.columns else 180.0
    pm25_val = float(sion_df['pm25'].iloc[0]) if 'pm25' in sion_df.columns else 50.0

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
    
    print("\n=======================================================")
    print("      URBAN AIR QUALITY INTELLIGENCE - DASHBOARD       ")
    print("=======================================================")
    print(json.dumps(result, indent=2, ensure_ascii=True))
    print("=======================================================\n")
    
    with open("reports/full_pipeline_test.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("Full JSON with native Unicode saved to reports/full_pipeline_test.json")

if __name__ == "__main__":
    validate_pipeline()
