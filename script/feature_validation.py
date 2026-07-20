import pandas as pd
import numpy as np
import os

INPUT_FILE = r"C:\Weathermodel\data\processed\training_features.csv"
OUTPUT_DIR = r"C:\Weathermodel\reports"

def generate_feature_validation():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.read_csv(INPUT_FILE)
    df['date'] = pd.to_datetime(df['date'])
    
    print("\n====================================================")
    print("PHASE 4 — FEATURE VALIDATION REPORT")
    print("====================================================\n")
    
    # Yearly PM2.5 Statistics
    print("### Yearly PM2.5 Statistics")
    df['year'] = df['date'].dt.year
    yearly_stats = []
    
    for year, group in df.groupby('year'):
        pm25 = group['pm25'].dropna()
        if not pm25.empty:
            yearly_stats.append({
                "Year": year,
                "Mean": pm25.mean(),
                "Median": pm25.median(),
                "Std": pm25.std(),
                "95th Percentile": pm25.quantile(0.95),
                "Maximum": pm25.max()
            })
            
    yearly_df = pd.DataFrame(yearly_stats)
    print(yearly_df.to_string(index=False, float_format="%.1f"))
    print("\n")
    
    # Feature Statistics
    print("### Feature Validation Flags")
    features = [c for c in df.columns if c not in ['station', 'date', 'year']]
    validation_data = []
    
    for f in features:
        data = df[f]
        missing_pct = data.isna().sum() / len(data) * 100
        
        flags = []
        if missing_pct == 100:
            flags.append("ALL-NULL")
            mean, std, min_val, max_val = np.nan, np.nan, np.nan, np.nan
        else:
            mean = data.mean()
            std = data.std()
            min_val = data.min()
            max_val = data.max()
            
            if std == 0:
                flags.append("CONSTANT")
                
            if 'pm25' in f and max_val > 1500:
                flags.append("SUSPICIOUS DISTRIBUTION (Max > 1500)")
                
        validation_data.append({
            "Feature": f,
            "Mean": mean,
            "Std": std,
            "Min": min_val,
            "Max": max_val,
            "Missing %": f"{missing_pct:.1f}%",
            "Flags": ", ".join(flags) if flags else "OK"
        })
        
        if flags:
            print(f"- {f}: {', '.join(flags)}")
            
    val_df = pd.DataFrame(validation_data)
    val_path = os.path.join(OUTPUT_DIR, "feature_validation.csv")
    val_df.to_csv(val_path, index=False)
    print(f"\nSaved feature validation report to {val_path}")
    
    print("\n====================================================\n")

if __name__ == "__main__":
    generate_feature_validation()
