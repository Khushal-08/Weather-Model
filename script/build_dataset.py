import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Safeguard logging as explicitly requested
print("\n" + "="*60)
print("SAFEGUARD: AQI DATA SOURCE")
print("Loading exclusively from: data/Maharasthra.xlsx")
print("Target Date Range: 2021-08-01 to 2023-07-31")
print("="*60 + "\n")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

AQI_RAW_PATH = Path("data/Maharasthra.xlsx")
WEATHER_RAW_PATH = Path("data/raw/weather_daily.csv")
PROCESSED_DIR = Path("data/processed")
OUTPUT_DATASET_PATH = PROCESSED_DIR / "training_dataset.csv"

def load_data():
    if not AQI_RAW_PATH.exists():
        raise FileNotFoundError(f"Missing {AQI_RAW_PATH}")
    if not WEATHER_RAW_PATH.exists():
        raise FileNotFoundError(f"Missing {WEATHER_RAW_PATH}")
        
    df_aqi = pd.read_excel(AQI_RAW_PATH)
    # Parse dates explicitly assuming Indian DD-MM-YYYY format
    df_aqi['date'] = pd.to_datetime(df_aqi['From Date'], format='%d-%m-%Y %H:%M', errors='coerce').dt.normalize()
    df_aqi = df_aqi.dropna(subset=['date'])
    
    # Restrict to the requested full range
    start_date = pd.to_datetime("2021-08-01")
    end_date = pd.to_datetime("2023-07-31")
    df_aqi = df_aqi[(df_aqi['date'] >= start_date) & (df_aqi['date'] <= end_date)].copy()
    
    # Negative handling
    for col in ['PM2.5', 'PM10', 'NO2', 'CO', 'Ozone', 'SO2']:
        if col in df_aqi.columns:
            df_aqi[col] = pd.to_numeric(df_aqi[col], errors='coerce')
            df_aqi.loc[df_aqi[col] < 0, col] = np.nan
            
    df_weather = pd.read_csv(WEATHER_RAW_PATH)
    df_weather['date'] = pd.to_datetime(df_weather['date']).dt.normalize()
    
    return df_aqi, df_weather

def select_stations(df_aqi):
    logger.info("Evaluating station completeness...")
    
    # The expected total days for 2021-08-01 to 2023-07-31 is 730 days
    total_days = 730
    
    # Daily aggregation first (mean)
    pollutants = ['PM2.5', 'PM10', 'NO2', 'CO', 'Ozone', 'SO2']
    df_daily = df_aqi.groupby(['Station', 'date'], as_index=False)[pollutants].mean()
    
    counts = df_daily.groupby('Station')['PM2.5'].count()
    completeness = (counts / total_days) * 100
    
    print("\n--- STATION COMPLETENESS REPORT ---")
    selected_stations = []
    
    # Pick the top 8 Mumbai stations that meet the >60% threshold
    mumbai_stations = [s for s in completeness.index if 'Mumbai' in s]
    
    for stat, comp in completeness.sort_values(ascending=False).items():
        if comp >= 60.0 and stat in mumbai_stations and len(selected_stations) < 8:
            status = "INCLUDED (Top 8 Mumbai)"
            selected_stations.append(stat)
        elif comp >= 60.0:
            status = "EXCLUDED (Not in top 8 Mumbai)"
        else:
            status = "EXCLUDED (<60% completeness)"
            
        print(f"{stat}: {comp:.2f}% -> {status}")
    print("-----------------------------------\n")
    
    if len(selected_stations) == 0:
        raise ValueError("No stations met the 60% threshold!")
        
    df_selected = df_daily[df_daily['Station'].isin(selected_stations)].copy()
    return df_selected

def reindex_and_interpolate(df_aqi):
    logger.info("Performing continuous date reindexing and forward interpolation...")
    start_date = pd.to_datetime("2021-08-01")
    end_date = pd.to_datetime("2023-07-31")
    full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    pollutants = ['PM2.5', 'PM10', 'NO2', 'CO', 'Ozone', 'SO2']
    
    final_dfs = []
    
    for stat, group in df_aqi.groupby('Station'):
        group = group.set_index('date')
        
        # Continuous reindexing
        group = group.reindex(full_date_range)
        group['Station'] = stat
        
        # Forward interpolation ONLY
        group[pollutants] = group[pollutants].ffill()
        
        # Log boundary bfills if any start NaNs exist
        boundary_nans = group[pollutants].isna().iloc[0].sum()
        if boundary_nans > 0:
            logger.warning(f"Station {stat} has NaNs at the start of the series. Applying boundary bfill for first valid observation.")
            group[pollutants] = group[pollutants].bfill()
            
        final_dfs.append(group.reset_index().rename(columns={'index': 'date'}))
        
    return pd.concat(final_dfs, ignore_index=True)

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    df_aqi, df_weather = load_data()
    df_aqi = select_stations(df_aqi)
    df_aqi = reindex_and_interpolate(df_aqi)
    
    # Rename columns to match expected downstream lowercase names
    df_aqi = df_aqi.rename(columns={
        'Station': 'station',
        'PM2.5': 'pm25',
        'PM10': 'pm10',
        'NO2': 'no2',
        'CO': 'co',
        'Ozone': 'o3',
        'SO2': 'so2'
    })
    
    logger.info("Merging with weather data...")
    df_merged = pd.merge(df_aqi, df_weather, on=['station', 'date'], how='inner')
    
    # Fill missing weather data using ffill
    weather_vars = ['temperature_2m_mean', 'relative_humidity_2m_mean', 'precipitation_sum', 'wind_speed_10m_mean']
    weather_vars = [v for v in weather_vars if v in df_merged.columns]
    for stat, group in df_merged.groupby('station'):
        df_merged.loc[group.index, weather_vars] = group[weather_vars].ffill().bfill()
        
    df_merged.to_csv(OUTPUT_DATASET_PATH, index=False)
    logger.info(f"Saved merged dataset to {OUTPUT_DATASET_PATH} with shape {df_merged.shape}")

if __name__ == "__main__":
    main()
