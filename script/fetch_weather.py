import pandas as pd
import requests
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from tqdm import tqdm
import os

# ==========================================
# CONFIGURATION & SETUP
# ==========================================

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Cache API requests to avoid redundant calls (expires in 30 days)
requests_cache.install_cache('open_meteo_cache', expire_after=2592000)

TARGET_STATIONS = [
    {"full_name": "Chhatrapati Shivaji Intl. Airport (T2), Mumbai - MPCB", "latitude": 19.0974, "longitude": 72.8743},
    {"full_name": "Sion, Mumbai - MPCB", "latitude": 19.0470, "longitude": 72.8746},
    {"full_name": "Worli, Mumbai - MPCB", "latitude": 19.0169, "longitude": 72.8169},
    {"full_name": "Borivali East, Mumbai - MPCB", "latitude": 19.2290, "longitude": 72.8649},
    {"full_name": "Kurla, Mumbai - MPCB", "latitude": 19.0728, "longitude": 72.8826},
    {"full_name": "Powai, Mumbai - MPCB", "latitude": 19.1176, "longitude": 72.9060},
    {"full_name": "Vasai West, Mumbai - MPCB", "latitude": 19.3800, "longitude": 72.8256},
    {"full_name": "Mulund West, Mumbai - MPCB", "latitude": 19.1718, "longitude": 72.9452}
]

AQI_DATA_PATH = "data/raw/aqi.csv"
OUTPUT_DIR = "data/raw"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "weather_daily.csv")

# Open-Meteo Archive API endpoint
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Define date range matching our AQI data fetch
START_DATE = "2021-08-01"
END_DATE = "2023-07-31"

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_session():
    """Configure a requests session with retries for transient failures."""
    session = requests_cache.CachedSession('open_meteo_cache', expire_after=2592000)
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def extract_station_coordinates():
    """Return hardcoded target stations."""
    for s in TARGET_STATIONS:
        logger.info(f" - {s['full_name']} (Lat: {s['latitude']}, Lon: {s['longitude']})")
    return TARGET_STATIONS

def fetch_weather_for_station(session, lat, lon):
    """Fetch hourly weather data from Open-Meteo Archive API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m,surface_pressure,cloud_cover,shortwave_radiation",
        "timezone": "Asia/Kolkata"
    }

    try:
        response = session.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "hourly" not in data:
            logger.warning(f"No hourly data returned for lat={lat}, lon={lon}")
            return None
            
        hourly_df = pd.DataFrame(data["hourly"])
        hourly_df["time"] = pd.to_datetime(hourly_df["time"])
        
        return hourly_df
        
    except Exception as e:
        logger.error(f"API request failed for lat={lat}, lon={lon}: {e}")
        return None

def aggregate_daily(hourly_df):
    """Aggregate hourly weather metrics into daily statistics."""
    if not pd.api.types.is_datetime64_any_dtype(hourly_df['time']):
        hourly_df['time'] = pd.to_datetime(hourly_df['time'])
    
    # Create a date column for daily grouping
    hourly_df['date'] = hourly_df['time'].dt.date
    
    # Define aggregation rules matching standard daily weather metrics
    agg_rules = {
        "temperature_2m": ["mean", "min", "max"],
        "relative_humidity_2m": ["mean", "min", "max"],
        "precipitation": ["sum"],
        "wind_speed_10m": ["mean", "max"],
        "wind_direction_10m": ["mean"],
        "surface_pressure": ["mean"],
        "cloud_cover": ["mean"],
        "shortwave_radiation": ["sum", "mean"]
    }
    
    # Filter rules to only columns that actually exist in the fetched data
    valid_rules = {k: v for k, v in agg_rules.items() if k in hourly_df.columns}
    
    daily_df = hourly_df.groupby("date").agg(valid_rules)
    
    # Flatten the MultiIndex columns (e.g., ('temperature_2m', 'mean') -> 'temperature_2m_mean')
    daily_df.columns = [f"{col}_{stat}" for col, stat in daily_df.columns]
    daily_df = daily_df.reset_index()
    
    return daily_df

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    logger.info("Starting Open-Meteo historical weather fetch.")
    
    stations = extract_station_coordinates()
    if not stations:
        logger.warning("No stations found to process. Exiting.")
        return

    session = get_session()
    all_daily_data = []

    for station in tqdm(stations, desc="Fetching Weather Data"):
        lat = station["latitude"]
        lon = station["longitude"]
        name = station["full_name"]
        
        hourly_df = fetch_weather_for_station(session, lat, lon)
        
        if hourly_df is not None and not hourly_df.empty:
            daily_df = aggregate_daily(hourly_df)
            
            # Add station metadata to the daily records
            daily_df.insert(0, "station", name)
            daily_df.insert(1, "latitude", lat)
            daily_df.insert(2, "longitude", lon)
            
            all_daily_data.append(daily_df)
        else:
            logger.error(f"Failed to fetch or parse data for {name}")

    if all_daily_data:
        final_df = pd.concat(all_daily_data, ignore_index=True)
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        final_df.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Successfully saved aggregated daily weather to {OUTPUT_FILE}")
        logger.info(f"Total rows generated: {len(final_df)}")
    else:
        logger.error("No data was successfully fetched for any station.")

if __name__ == "__main__":
    main()
