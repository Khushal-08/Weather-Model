import os
import math
import logging
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
from shapely.geometry import Point
from pyproj import Geod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Configure OSMnx
ox.settings.log_console = False
ox.settings.use_cache = True

STATIC_FEATURES_PATH = Path("data/geospatial/static_features.csv")
STATIC_FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = Path("reports/figures")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

geod = Geod(ellps='WGS84')

def get_bearing(lat1, lon1, lat2, lon2):
    """Calculate forward azimuth from point 1 to point 2."""
    forward_az, back_az, distance = geod.inv(lon1, lat1, lon2, lat2)
    return (forward_az + 360) % 360, distance

def get_sector(bearing):
    """Convert bearing (0-360) to one of 8 sectors."""
    sectors = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    idx = int(round(bearing / 45.0)) % 8
    return sectors[idx]

def extract_traffic_features(lat, lon):
    """Extract road lengths and density from OSM."""
    logger.info(f"Extracting traffic features for {lat}, {lon}")
    
    features = {}
    
    # Radii for road density
    for radius in [1000, 3000, 5000]:
        try:
            # We use features_from_point for highway to capture lengths without full graph topology
            roads = ox.features.features_from_point((lat, lon), tags={'highway': True}, dist=radius)
            if not roads.empty:
                # Filter to line strings
                roads = roads[roads.geometry.type == 'LineString']
                # Reproject to local UTM to calculate lengths in meters
                roads_proj = roads.to_crs(roads.estimate_utm_crs())
                total_length = roads_proj.length.sum()
                features[f'road_density_{radius//1000}km'] = total_length
            else:
                features[f'road_density_{radius//1000}km'] = 0.0
        except Exception as e:
            logger.warning(f"Error fetching roads for radius {radius}: {e}")
            features[f'road_density_{radius//1000}km'] = 0.0

    # Distance to major road
    try:
        major_roads = ox.features.features_from_point((lat, lon), tags={'highway': ['motorway', 'trunk', 'primary']}, dist=5000)
        if not major_roads.empty:
            target_pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
            # Reproject for accurate distance in meters
            local_crs = major_roads.estimate_utm_crs()
            major_roads_proj = major_roads.to_crs(local_crs)
            target_proj = target_pt.to_crs(local_crs)
            
            distances = major_roads_proj.geometry.distance(target_proj.iloc[0])
            features['major_road_distance'] = distances.min()
        else:
            features['major_road_distance'] = 5000.0
    except Exception as e:
        logger.warning(f"Error fetching major roads: {e}")
        features['major_road_distance'] = 5000.0

    return features

def extract_landuse_features(lat, lon):
    """Extract industrial and construction POIs and bin their areas into 8 directional sectors."""
    logger.info(f"Extracting landuse features for {lat}, {lon}")
    
    features = {f'industry_area_{sec}': 0.0 for sec in ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']}
    features.update({f'construction_area_{sec}': 0.0 for sec in ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']})
    features['industrial_poi_count'] = 0
    features['construction_site_count'] = 0
    
    # Fetch Industry
    try:
        industry = ox.features.features_from_point((lat, lon), tags={'landuse': 'industrial', 'man_made': 'works'}, dist=5000)
        if not industry.empty:
            features['industrial_poi_count'] = len(industry)
            # Use projected CRS for area calculation in sq meters
            industry_proj = industry.to_crs(industry.estimate_utm_crs())
            
            for idx, row in industry_proj.iterrows():
                poly_area = row.geometry.area
                poly_centroid = row.geometry.centroid
                
                # Convert centroid back to lat/lon to get bearing
                centroid_wgs = gpd.GeoSeries([poly_centroid], crs=industry_proj.crs).to_crs("EPSG:4326").iloc[0]
                poly_lat, poly_lon = centroid_wgs.y, centroid_wgs.x
                
                bearing, _ = get_bearing(lat, lon, poly_lat, poly_lon)
                sector = get_sector(bearing)
                features[f'industry_area_{sector}'] += poly_area
    except Exception as e:
        logger.warning(f"Error fetching industry: {e}")

    # Fetch Construction
    try:
        construction = ox.features.features_from_point((lat, lon), tags={'landuse': ['construction', 'brownfield', 'quarry']}, dist=5000)
        if not construction.empty:
            features['construction_site_count'] = len(construction)
            construction_proj = construction.to_crs(construction.estimate_utm_crs())
            
            for idx, row in construction_proj.iterrows():
                poly_area = row.geometry.area
                poly_centroid = row.geometry.centroid
                
                centroid_wgs = gpd.GeoSeries([poly_centroid], crs=construction_proj.crs).to_crs("EPSG:4326").iloc[0]
                poly_lat, poly_lon = centroid_wgs.y, centroid_wgs.x
                
                bearing, _ = get_bearing(lat, lon, poly_lat, poly_lon)
                sector = get_sector(bearing)
                features[f'construction_area_{sector}'] += poly_area
    except Exception as e:
        logger.warning(f"Error fetching construction: {e}")

    return features

def generate_static_features(target_station=None):
    """Generate and cache static features for Mumbai stations."""
    if STATIC_FEATURES_PATH.exists():
        static_df = pd.read_csv(STATIC_FEATURES_PATH)
        if target_station is None or target_station in static_df['station'].values:
            logger.info(f"Static features found in cache for {target_station}.")
            return static_df
    else:
        static_df = pd.DataFrame()
    
    logger.info(f"Static features cache missing for {target_station}. Generating...")
    
    training_data_path = "data/processed/training_features.csv"
    if not os.path.exists(training_data_path):
        raise FileNotFoundError(f"Could not find {training_data_path} to identify stations.")
    
    df = pd.read_csv(training_data_path)
    stations = df[['station', 'latitude', 'longitude']].drop_duplicates()
    
    if target_station:
        stations = stations[stations['station'] == target_station]
    
    results = []
    for _, row in stations.iterrows():
        station_name = row['station']
        lat, lon = row['latitude'], row['longitude']
        
        stat_feats = {
            'station': station_name,
            'latitude': lat,
            'longitude': lon
        }
        
        traffic = extract_traffic_features(lat, lon)
        landuse = extract_landuse_features(lat, lon)
        
        stat_feats.update(traffic)
        stat_feats.update(landuse)
        results.append(stat_feats)
        
    if results:
        new_static_df = pd.DataFrame(results)
        if not static_df.empty:
            static_df = pd.concat([static_df, new_static_df], ignore_index=True)
        else:
            static_df = new_static_df
        static_df.to_csv(STATIC_FEATURES_PATH, index=False)
        logger.info(f"Successfully cached static features to {STATIC_FEATURES_PATH}")
    
    return static_df

def fetch_nasa_firms_data():
    """Fetch 24h rolling NASA FIRMS active fire data for South Asia."""
    url = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_South_Asia_24h.csv"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        logger.warning(f"Failed to fetch FIRMS data: {e}")
        return pd.DataFrame()

def calculate_upwind_factor(source_lat, source_lon, target_lat, target_lon, wind_dir, wind_speed):
    """
    Calculate the transport influence of a source on the target.
    wind_dir is meteorological (direction wind blows FROM).
    Target to Source bearing is compared to wind_dir.
    """
    bearing, distance_m = get_bearing(target_lat, target_lon, source_lat, source_lon)
    distance_km = distance_m / 1000.0
    
    # Handle circular angle differences
    delta = abs(bearing - wind_dir)
    angle_diff = min(delta, 360 - delta)
    
    # If the source is more than 90 degrees away from the upwind vector, it's downwind (no transport)
    if angle_diff > 90:
        return 0.0
        
    # Cosine decay for angle. Source exactly upwind (angle_diff=0) -> cos(0)=1
    angular_factor = math.cos(math.radians(angle_diff))
    
    # Score decays with distance, increases with wind_speed
    score = (angular_factor * max(1, wind_speed)) / (distance_km + 1)
    return score

def generate_dynamic_features(target_date, station_name, wind_dir, wind_speed, no2=None, co=None, pm10=None, pm25=None):
    """
    Generate the evidence layer JSON dynamically using weather, fires, pollutants, and cached static data.
    """
    static_df = generate_static_features(target_station=station_name)
    station_static = static_df[static_df['station'] == station_name]
    
    if station_static.empty:
        raise ValueError(f"Station {station_name} not found in static features cache.")
        
    station_static = station_static.iloc[0]
    target_lat = station_static['latitude']
    target_lon = station_static['longitude']
    
    # --- 1. Compute Traffic Score ---
    # Max road density in 5km buffer in our dataset is around 100000m (100km). We normalize roughly.
    rd_5km = station_static.get('road_density_5km', 0)
    major_dist = station_static.get('major_road_distance', 5000)
    
    # Heuristic traffic score 0-1
    traffic_density_score = min(1.0, rd_5km / 100000.0) 
    traffic_proximity_score = max(0.0, 1.0 - (major_dist / 2000.0))
    traffic_score = 0.6 * traffic_density_score + 0.4 * traffic_proximity_score
    
    traffic_evidence = [
        f"Road density within 5km is {rd_5km/1000:.1f} km.",
        f"Nearest major road is {major_dist:.0f} meters away."
    ]
    if no2 is not None and co is not None:
        if no2 > 40 and co > 1.0:
            traffic_evidence.append("Pollutant signature (High NO2 and CO) strongly indicates heavy vehicular combustion.")
            traffic_score = min(1.0, traffic_score + 0.2)
            
    # --- 2. Compute Upwind Industrial & Construction Scores ---
    wind_sector = get_sector(wind_dir)
    upwind_industry_area = station_static.get(f'industry_area_{wind_sector}', 0)
    upwind_construction_area = station_static.get(f'construction_area_{wind_sector}', 0)
    
    # Max area roughly 1e6 sq meters (1 sq km)
    industrial_score = min(1.0, upwind_industry_area / 1000000.0)
    construction_score = min(1.0, upwind_construction_area / 500000.0)
    
    industrial_evidence = [f"Upwind sector ({wind_sector}) contains {upwind_industry_area/1000000:.2f} sq km of industrial land use."]
    construction_evidence = [f"Upwind sector ({wind_sector}) contains {upwind_construction_area/1000000:.2f} sq km of construction/brownfield."]
    
    if industrial_score == 0:
        industrial_evidence.append("No industrial activity located in the direct upwind path.")
        
    if pm10 is not None and pm25 is not None:
        if pm25 > 0 and (pm10 / pm25) > 2.5:
            construction_evidence.append("Pollutant signature (High PM10 vs PM2.5 ratio) strongly indicates coarse dust suspension.")
            construction_score = min(1.0, construction_score + 0.2)

    # --- 3. Compute Upwind Fire Score ---
    firms_df = fetch_nasa_firms_data()
    upwind_fire_score = 0.0
    fire_evidence = []
    
    if not firms_df.empty:
        firms_df['dist_bearing'] = firms_df.apply(
            lambda row: get_bearing(target_lat, target_lon, row['latitude'], row['longitude']), axis=1
        )
        firms_df[['bearing', 'distance_m']] = pd.DataFrame(firms_df['dist_bearing'].tolist(), index=firms_df.index)
        firms_df['distance_km'] = firms_df['distance_m'] / 1000.0
        
        fires_50km = firms_df[firms_df['distance_km'] <= 50]
        
        fire_evidence.append(f"Detected {len(fires_50km)} active fires within 50km radius.")
        
        # Calculate scores
        scores = fires_50km.apply(
            lambda row: calculate_upwind_factor(row['latitude'], row['longitude'], target_lat, target_lon, wind_dir, wind_speed), axis=1
        )
        if not scores.empty:
            upwind_fire_score = min(1.0, scores.sum())
            if upwind_fire_score > 0.5:
                fire_evidence.append(f"Significant active fires located directly upwind (Transport Score: {upwind_fire_score:.2f}).")
            elif upwind_fire_score > 0:
                fire_evidence.append("Minor upwind fire influence detected.")
            else:
                fire_evidence.append("Fires detected, but they are entirely downwind of the target.")
    else:
        fire_evidence.append("NASA FIRMS fire data currently unavailable or empty.")

    # --- 4. JSON Generation ---
    attribution_json = {
        "timestamp": target_date,
        "station": station_name,
        "latitude": target_lat,
        "longitude": target_lon,
        "meteorology": {
            "wind_direction": wind_dir,
            "wind_speed_kmh": wind_speed
        },
        "raw_scores": {
            "traffic_score": round(traffic_score, 3),
            "industrial_score": round(industrial_score, 3),
            "construction_score": round(construction_score, 3),
            "upwind_fire_score": round(upwind_fire_score, 3)
        },
        "evidence": {
            "traffic": traffic_evidence,
            "industry": industrial_evidence,
            "construction": construction_evidence,
            "biomass": fire_evidence
        }
    }
    
    return attribution_json

def validate_pipeline():
    """Run a validation test on Sion, Mumbai and plot spatial relationships."""
    logger.info("Running geospatial pipeline validation...")
    
    # Sion station coordinates
    target_station = "Sion, Mumbai - MPCB"
    
    # 1. Fetch static (will generate if first time)
    logger.info("Triggering static generation...")
    generate_static_features()
    
    # 2. Mock dynamic conditions (Wind from West 270 deg at 15 km/h, some trace pollutants)
    logger.info("Executing dynamic feature generation...")
    import json
    result = generate_dynamic_features(
        target_date="2026-07-20T08:00:00",
        station_name=target_station,
        wind_dir=270, # West wind
        wind_speed=15, 
        no2=55, # High NO2
        co=1.5,
        pm10=180,
        pm25=50 # Ratio > 3
    )
    
    print("\n--- GENERATED ATTRIBUTION EVIDENCE JSON ---")
    print(json.dumps(result, indent=2))
    print("-------------------------------------------\n")
    
    # 3. Create Map (Task 8)
    lat, lon = result['latitude'], result['longitude']
    logger.info("Plotting validation map...")
    
    try:
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # Plot buffer
        target_pt = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
        target_utm = target_pt.to_crs(target_pt.estimate_utm_crs())
        buffer_utm = target_utm.buffer(5000) # 5km
        buffer = buffer_utm.to_crs("EPSG:4326")
        buffer.plot(ax=ax, facecolor='none', edgecolor='black', linestyle='--', linewidth=2, label="5km Buffer")
        
        # Plot roads
        roads = ox.features.features_from_point((lat, lon), tags={'highway': ['primary', 'trunk', 'motorway']}, dist=5000)
        if not roads.empty:
            roads[roads.geometry.type == 'LineString'].plot(ax=ax, color='gray', linewidth=1, alpha=0.6, label="Major Roads")
            
        # Plot industry
        industry = ox.features.features_from_point((lat, lon), tags={'landuse': 'industrial', 'man_made': 'works'}, dist=5000)
        if not industry.empty:
            industry.plot(ax=ax, color='purple', alpha=0.4, label="Industrial Zones")
            
        # Target Point
        target_pt.plot(ax=ax, color='red', markersize=100, marker='*', label="Monitoring Station")
        
        # NASA FIRMS Fires
        firms = fetch_nasa_firms_data()
        if not firms.empty:
            gdf_fires = gpd.GeoDataFrame(firms, geometry=gpd.points_from_xy(firms.longitude, firms.latitude), crs="EPSG:4326")
            gdf_fires.plot(ax=ax, color='orange', markersize=30, alpha=0.8, label="Active Fires (VIIRS)")
        
        # Add basemap
        ctx.add_basemap(ax, crs="EPSG:4326", source=ctx.providers.OpenStreetMap.Mapnik)
        
        plt.title(f"Geospatial Validation Map: {target_station}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "mumbai_spatial_validation.png", dpi=150)
        plt.close()
        logger.info(f"Map saved to {REPORTS_DIR}/mumbai_spatial_validation.png")
        
    except Exception as e:
        logger.error(f"Failed to generate map: {e}")

if __name__ == "__main__":
    validate_pipeline()
