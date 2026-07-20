import pandas as pd
import glob
import os

files = glob.glob(r"C:\Weathermodel\data\*air-quality.csv")

print("# Phase 0: Standalone Dataset Audit Report (AQICN Station Files)\n")

for file_path in files:
    filename = os.path.basename(file_path)
    print(f"## Auditing: {filename}")
    try:
        df = pd.read_csv(file_path, skipinitialspace=True)
    except Exception as e:
        print(f"Failed to read: {e}\n")
        continue
        
    print(f"- **Row count:** {len(df)}")
    
    date_col = 'date' if 'date' in df.columns else None
    if date_col:
        df['parsed_date'] = pd.to_datetime(df[date_col], errors='coerce').dt.date
        dates = df['parsed_date'].dropna().sort_values().unique()
        if len(dates) > 0:
            print(f"- **Date Range:** {dates[0]} to {dates[-1]} ({len(dates)} unique days)")
            today = pd.to_datetime("2026-07-20").date()
            if dates[-1] > today:
                print(f"- [RED FLAG]: Dataset contains dates past today ({dates[-1]}). Impossible for real historical data.")
        else:
            print("- No valid dates found.")
    else:
        print("- No date column identified.")
        
    pm25_col = 'pm25' if 'pm25' in df.columns else None
    if pm25_col and date_col and len(dates) > 0:
        total_days_in_range = (dates[-1] - dates[0]).days + 1
        df[pm25_col] = pd.to_numeric(df[pm25_col], errors='coerce')
        valid_days = df.dropna(subset=[pm25_col])['parsed_date'].nunique()
        pct = (valid_days / total_days_in_range) * 100
        print(f"- **Completeness (PM2.5):** {valid_days}/{total_days_in_range} days ({pct:.1f}%)")
        if pct >= 99.9:
            print(f"  - [RED FLAG]: Suspiciously gap-free data ({pct:.1f}%).")
        if pct < 60.0:
            print(f"  - [RED FLAG]: Thin coverage ({pct:.1f}%).")
            
        valid_pm25 = df[pm25_col].dropna()
        if not valid_pm25.empty:
             print(f"- **Stats (PM2.5):** Mean={valid_pm25.mean():.1f}, Min={valid_pm25.min():.1f}, Max={valid_pm25.max():.1f}")
             if valid_pm25.max() > 1000 or valid_pm25.min() < 0:
                  print("  - [RED FLAG]: Out of realistic PM2.5 bounds.")
    print("\n---\n")
