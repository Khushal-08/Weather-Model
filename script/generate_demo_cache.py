import os
import json
import logging
from pathlib import Path
import pandas as pd

from predict_pipeline import generate_air_quality_intelligence
from train_multi_horizon import load_and_prepare_data_multi

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_FILE = Path("data/processed/training_features.csv")
DEMO_DIR = Path("data/demo")

def generate_cache():
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading dataset for cache generation...")
    df, features, targets = load_and_prepare_data_multi(DATA_FILE)
    
    stations = df['station'].unique()
    logger.info(f"Detected {len(stations)} stations: {stations}")
    
    for station in stations:
        logger.info(f"=========================================")
        logger.info(f"Generating cache for station: {station}")
        logger.info(f"=========================================")
        
        station_df = df[df['station'] == station].tail(1)
        if station_df.empty:
            logger.warning(f"No data found for {station}")
            continue
            
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

        try:
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
            
            output_file = DEMO_DIR / f"{station.replace(' ', '_').replace(',', '')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully cached {station} to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate cache for {station}: {e}", exc_info=True)

if __name__ == "__main__":
    generate_cache()
