import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--city', type=str, default='mumbai', choices=['mumbai', 'delhi'])
args, unknown = parser.parse_known_args()
CITY = args.city.lower()

if CITY == 'mumbai':
    INPUT_FILE = Path("data/processed/training_dataset.csv")
    OUTPUT_FILE = Path("data/processed/training_features.csv")
else:
    INPUT_FILE = Path(f"data/processed/{CITY}_training_dataset.csv")
    OUTPUT_FILE = Path(f"data/processed/{CITY}_training_features.csv")


def main():
    logger.info("Starting feature engineering...")
    
    if not INPUT_FILE.exists():
        logger.error(f"Input file {INPUT_FILE} not found.")
        return
        
    df = pd.read_csv(INPUT_FILE)
    initial_rows = len(df)
    original_cols = df.columns.tolist()
    logger.info(f"Loaded input dataset with {initial_rows} rows and {df.shape[1]} columns.")
    
    # 1. Sort data by station (location) and date
    df['date'] = pd.to_datetime(df['date'])
    
    # Check if 'location' or 'station' exists to sort by
    sort_col = 'location' if 'location' in df.columns else 'station'
    df = df.sort_values([sort_col, 'date']).reset_index(drop=True)
    
    # 2. Create lag features for PM2.5
    logger.info("Creating lag features for PM2.5...")
    if 'pm25' in df.columns:
        for lag in [1, 2, 3, 7, 14]:
            df[f'pm25_lag_{lag}'] = df.groupby(sort_col)['pm25'].shift(lag)
            
        # 3. Create rolling features for PM2.5
        logger.info("Creating rolling features for PM2.5...")
        df['pm25_rolling_mean_7'] = df.groupby(sort_col)['pm25'].transform(lambda x: x.rolling(7, min_periods=1).mean())
        df['pm25_rolling_mean_14'] = df.groupby(sort_col)['pm25'].transform(lambda x: x.rolling(14, min_periods=1).mean())
        df['pm25_rolling_mean_30'] = df.groupby(sort_col)['pm25'].transform(lambda x: x.rolling(30, min_periods=1).mean())
        df['pm25_rolling_std_7'] = df.groupby(sort_col)['pm25'].transform(lambda x: x.rolling(7, min_periods=1).std())
        df['pm25_rolling_std_30'] = df.groupby(sort_col)['pm25'].transform(lambda x: x.rolling(30, min_periods=1).std())
    
    # 4. Create lag features for PM10, NO2, CO, and O3
    logger.info("Creating lag features for other pollutants...")
    pollutants = ['pm10', 'no2', 'co', 'o3']
    for p in pollutants:
        if p in df.columns:
            for lag in [1, 7]:
                df[f'{p}_lag_{lag}'] = df.groupby(sort_col)[p].shift(lag)
                
    # 5. Create lag features for weather
    logger.info("Creating lag features for weather variables...")
    weather_vars = {
        'temperature': 'temperature_2m_mean', 
        'humidity': 'relative_humidity_2m_mean', 
        'wind_speed': 'wind_speed_10m_mean', 
        'precipitation': 'precipitation_sum'
    }
    
    for var_name, col_name in weather_vars.items():
        if col_name in df.columns:
            # Create 1-day lag
            df[f'{var_name}_lag_1'] = df.groupby(sort_col)[col_name].shift(1)
            
    # 6. Create calendar features
    logger.info("Creating calendar features...")
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['day_of_year'] = df['date'].dt.dayofyear
    df['weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # 7. Create cyclical encodings
    logger.info("Creating cyclical encodings...")
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    
    df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    df['day_of_year_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
    df['day_of_year_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)
    
    # 8. Drop rows containing NaNs introduced by lag creation
    logger.info("Dropping NaNs introduced by feature engineering...")
    
    # Find the new lag/rolling columns to check for NaNs
    new_cols = [c for c in df.columns if c not in original_cols and ('lag' in c or 'rolling' in c)]
    if new_cols:
        df = df.dropna(subset=new_cols)
    
    final_shape = df.shape
    
    # 9. Save the engineered dataset
    logger.info(f"Saving engineered dataset to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    
    # 10. Print a report
    engineered_features = [c for c in df.columns if c not in original_cols]
    
    print("\n--- Feature Engineering Report ---")
    print(f"Input rows: {initial_rows}")
    print(f"Output rows: {final_shape[0]}")
    print(f"Number of engineered features: {len(engineered_features)}")
    print("Feature names:")
    for f in engineered_features:
        print(f" - {f}")
    print(f"Final shape: {final_shape}")
    print("----------------------------------\n")

if __name__ == "__main__":
    main()
