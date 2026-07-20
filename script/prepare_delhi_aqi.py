import pandas as pd
import glob
import os

AQICN_DIR = r"C:\Weathermodel\data\delhi"
OUTPUT_DIR = r"C:\Weathermodel\data\raw"

STATION_MAP = {
    "alipur,-delhi": "Alipur",
    "anand-vihar, delhi": "Anand Vihar",
    "dite-okhla, delhi": "Okhla Phase II",
    "jawaharlal-nehru stadium, delhi": "Jawaharlal Nehru Stadium",
    "national-institute of malaria research, sector 8, dwarka, delhi": "Dwarka Sector 8",
    "punjabi-bagh, delhi": "Punjabi Bagh",
    "r.k.-puram, delhi": "RK Puram",
    "shaheed-sukhdev college of business studies, rohini, delhi": "Rohini"
}

def clean_aqicn_data():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    files = glob.glob(os.path.join(AQICN_DIR, "*air-quality.csv"))
    if not files:
        print("Error: No Delhi AQICN files found!")
        return
        
    all_dfs = []
    
    for f in files:
        base_name = os.path.basename(f).replace("-air-quality.csv", "")
        station_name = STATION_MAP.get(base_name, base_name.replace(",", "").title())
        
        try:
            df = pd.read_csv(f)
            df.columns = df.columns.str.strip()
            df.rename(columns={' pm25': 'pm25', ' pm10': 'pm10', ' o3': 'o3', 
                             ' no2': 'no2', ' so2': 'so2', ' co': 'co'}, inplace=True)
            
            df['date'] = pd.to_datetime(df['date'])
            df['station'] = station_name
            
            all_dfs.append(df)
            print(f"Processed {station_name}")
            
        except Exception as e:
            print(f"Failed to process {f}: {e}")
            
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    for col in ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
            
    final_df = final_df.sort_values(by=['station', 'date']).reset_index(drop=True)
    
    out_path = os.path.join(OUTPUT_DIR, "delhi_aqicn_consolidated.csv")
    final_df.to_csv(out_path, index=False)
    print(f"\nSaved consolidated data to {out_path} with shape {final_df.shape}")

if __name__ == "__main__":
    clean_aqicn_data()
