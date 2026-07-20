import pandas as pd
import glob
import os
import numpy as np

AQICN_DIR = r"C:\Weathermodel\data"
OUTPUT_DIR = r"C:\Weathermodel\data\raw"
REPORT_DIR = r"C:\Weathermodel\reports"

# Mappings to standardize station names with the dashboard's expected names
# The user's target stations are: "Sion, Borivali East, Colaba, Chembur, Powai, Kurla, Bandra Kurla Complex, Worli"
STATION_MAP = {
    "borivali-east, mumbai, india": "Borivali East, Mumbai - MPCB",
    "chhatrapati-shivaji intl. airport (t2), mumbai, india": "Chhatrapati Shivaji Intl. Airport (T2), Mumbai - MPCB",
    "kurla,-mumbai": "Kurla, Mumbai - MPCB",
    "powai,-mumbai, india": "Powai, Mumbai - MPCB",
    "sion,-mumbai, india": "Sion, Mumbai - MPCB",
    "vasai-west, mumbai, india": "Vasai West, Mumbai - MPCB",
    "worli,-mumbai, india": "Worli, Mumbai - MPCB"
}

def clean_aqicn_data():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    files = glob.glob(os.path.join(AQICN_DIR, "*air-quality.csv"))
    if not files:
        print("Error: No AQICN files found!")
        return
        
    all_dfs = []
    report_data = []
    
    global_min_date = pd.to_datetime('2100-01-01').date()
    global_max_date = pd.to_datetime('1900-01-01').date()
    
    for f in files:
        base_name = os.path.basename(f).replace("-air-quality.csv", "")
        station_name = STATION_MAP.get(base_name, base_name.replace(",", "").title())
        
        try:
            df = pd.read_csv(f, skipinitialspace=True)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue
            
        df['station'] = station_name
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
        df = df.dropna(subset=['date'])
        df = df.sort_values('date').drop_duplicates(subset=['date']) # Ensure uniqueness per station
        
        # Convert numeric cols
        pollutants = ['pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
        for p in pollutants:
            if p in df.columns:
                df[p] = pd.to_numeric(df[p], errors='coerce')
                
        all_dfs.append(df)
        
        # Data Quality calculations
        dates = df['date'].sort_values()
        min_date = dates.min()
        max_date = dates.max()
        
        if min_date < global_min_date: global_min_date = min_date
        if max_date > global_max_date: global_max_date = max_date
        
        total_rows = len(df)
        total_days_range = (max_date - min_date).days + 1
        
        pm25_comp = df['pm25'].notna().sum() / total_days_range * 100
        pm10_comp = df['pm10'].notna().sum() / total_days_range * 100 if 'pm10' in df.columns else 0
        
        # Longest gap
        df_full_date = df.set_index('date').reindex(pd.date_range(min_date, max_date).date)
        is_missing = df_full_date['pm25'].isna()
        longest_gap = is_missing.groupby((~is_missing).cumsum()).sum().max()
        
        # Missing percentages
        missing_pcts = {p: (df[p].isna().sum() / total_rows * 100) if p in df.columns else 100 for p in pollutants}
        
        # Negatives
        negatives = {p: (df[p] < 0).sum() if p in df.columns else 0 for p in pollutants}
        has_negs = sum(negatives.values()) > 0
        
        report_data.append({
            "Station Name": station_name,
            "Date Range": f"{min_date} to {max_date}",
            "Total Rows": total_rows,
            "PM2.5 Completeness %": f"{pm25_comp:.1f}%",
            "PM10 Completeness %": f"{pm10_comp:.1f}%",
            "Weather Completeness %": "N/A (Phase 2)",
            "Duplicate Dates": total_rows - dates.nunique(),
            "Negative Values": "Yes" if has_negs else "No",
            "Longest Gap (Days)": int(longest_gap),
            "PM2.5 Missing %": f"{missing_pcts['pm25']:.1f}%",
            "PM10 Missing %": f"{missing_pcts['pm10']:.1f}%",
            "NO2 Missing %": f"{missing_pcts['no2']:.1f}%"
        })
        
    consolidated_df = pd.concat(all_dfs, ignore_index=True)
    out_path = os.path.join(OUTPUT_DIR, "aqicn_consolidated.csv")
    consolidated_df.to_csv(out_path, index=False)
    
    report_df = pd.DataFrame(report_data)
    report_path = os.path.join(REPORT_DIR, "data_quality_report.csv")
    report_df.to_csv(report_path, index=False)
    
    print("====================================================")
    print("PHASE 1 — DATA INGESTION & AUDIT COMPLETE")
    print("====================================================")
    print(f"Earliest Available Date: {global_min_date}")
    print(f"Latest Available Date: {global_max_date}")
    print(f"Consolidated dataset saved to: {out_path}\n")
    
    print("DATA QUALITY SUMMARY:")
    print(report_df.to_string(index=False))
    print("====================================================\n")
    
    # Save a config file with dates so Phase 2 can read them without hardcoding
    with open(os.path.join(OUTPUT_DIR, "date_range.txt"), "w") as f:
        f.write(f"{global_min_date},{global_max_date}")

if __name__ == "__main__":
    clean_aqicn_data()
