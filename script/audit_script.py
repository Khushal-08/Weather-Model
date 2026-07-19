import pandas as pd
import numpy as np

def audit():
    df = pd.read_csv('c:/Weathermodel/data/processed/training_dataset.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    print("=== 1. DATASET STRUCTURE ===")
    print(df.info())
    print("\nColumns:", df.columns.tolist())
    print("\nStations:", df['station'].unique())
    
    print("\n=== 2. MISSING VALUES ===")
    print(df.isna().sum())
    
    print("\n=== 3. DUPLICATE RECORDS ===")
    print("Total duplicates:", df.duplicated().sum())
    print("Station-Date duplicates:", df.duplicated(subset=['station', 'date']).sum())
    
    print("\n=== 4. DATE VALIDATION ===")
    print("Min date:", df['date'].min())
    print("Max date:", df['date'].max())
    
    for station in df['station'].unique():
        st_df = df[df['station'] == station].sort_values('date')
        date_diff = st_df['date'].diff().dt.days
        missing_dates = (date_diff > 1).sum()
        print(f"Station {station}: {missing_dates} gaps in dates. Expected rows: {(st_df['date'].max() - st_df['date'].min()).days + 1}, Actual rows: {len(st_df)}")
        
    print("\n=== 5. AQI VALIDATION ===")
    pollutants = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3']
    for p in pollutants:
        if p in df.columns:
            print(f"{p}: Min={df[p].min()}, Max={df[p].max()}, Negatives={(df[p] < 0).sum()}")
            
    print("\n=== 6. WEATHER VALIDATION ===")
    weather_cols = [c for c in df.columns if any(x in c for x in ['temperature', 'humidity', 'wind', 'precipitation', 'pressure', 'cloud', 'radiation'])]
    for w in weather_cols:
        print(f"{w}: Min={df[w].min()}, Max={df[w].max()}, NaN={df[w].isna().sum()}")
        
    print("\n=== 7. MERGE VALIDATION ===")
    aqi_cols = [c for c in pollutants if c in df.columns]
    has_aqi = df[aqi_cols].notna().any(axis=1)
    has_weather = df[weather_cols].notna().any(axis=1)
    print(f"Rows with AQI: {has_aqi.sum()}, Rows with Weather: {has_weather.sum()}, Total Rows: {len(df)}")
    
    print("\n=== 8. TIME SERIES READINESS ===")
    # Fix for groupby error in pandas 2.x where we should avoid applying on group keys if not needed or specify include_groups=False if warning
    is_sorted = df.groupby('station', group_keys=False).apply(lambda x: x['date'].is_monotonic_increasing).all()
    print("Is chronologically sorted per station:", is_sorted)

if __name__ == '__main__':
    audit()
