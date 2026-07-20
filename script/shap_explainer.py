import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import joblib
import shap
import json

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
    INPUT_FILE = Path("data/processed/training_features.csv")
    MODELS_DIR = Path("models/mumbai")
    REPORTS_DIR = Path("reports/figures")
else:
    INPUT_FILE = Path(f"data/processed/{CITY}_training_features.csv")
    MODELS_DIR = Path(f"models/{CITY}")
    REPORTS_DIR = Path(f"reports/{CITY}")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def setup_directories():
    """Ensure output directories exist."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def load_and_prepare_data(filepath):
    """
    Identical data loading logic used in train_xgboost.py to guarantee feature parity.
    """
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    
    df = df.sort_values('date').reset_index(drop=True)
    sort_col = 'location' if 'location' in df.columns else 'station'
    
    rolling_cols = [c for c in df.columns if 'rolling' in c]
    for col in rolling_cols:
        df[f"{col}_shifted"] = df.groupby(sort_col)[col].shift(1)
        
    df = df.dropna(subset=[f"{col}_shifted" for col in rolling_cols]).reset_index(drop=True)
    
    lag_cols = [c for c in df.columns if 'lag' in c]
    shifted_rolling_cols = [f"{c}_shifted" for c in rolling_cols]
    calendar_cols = ['day_of_week', 'month', 'day_of_year', 'weekend', 
                     'month_sin', 'month_cos', 'day_of_week_sin', 'day_of_week_cos', 
                     'day_of_year_sin', 'day_of_year_cos']
                     
    df["pm25_target_24h"] = df.groupby(sort_col)["pm25"].shift(-1)
    current_cols = ['pm25', 'pm10', 'no2', 'co', 'o3', 'temperature_2m_mean', 'relative_humidity_2m_mean', 'precipitation_sum', 'wind_speed_10m_mean']
    current_cols = [c for c in current_cols if c in df.columns]
    
    features = current_cols + lag_cols + shifted_rolling_cols + calendar_cols
    target = 'pm25_target_24h'

    df = df.dropna(subset=features + [target]).reset_index(drop=True)
    
    return df, features, target

def categorize_feature(feature_name):
    """Categorize a feature into predefined macro drivers."""
    f = feature_name.lower()
    if any(x in f for x in ['pm25', 'pm10', 'no2', 'co', 'so2', 'o3', 'aqi']):
        return "Historical Pollution"
    elif any(x in f for x in ['temp', 'humid', 'wind', 'precip', 'pressure', 'sun']):
        return "Meteorology"
    elif any(x in f for x in ['month', 'day', 'week', 'year', 'sin', 'cos', 'weekend']):
        return "Calendar"
    else:
        return "Other Predictors"

def generate_global_explainability(model, X):
    """Generate and save global SHAP summary plots."""
    setup_directories()
    logger.info("Generating global SHAP explainability plots...")
    
    explainer = shap.TreeExplainer(model)
    
    # We sample if the dataset is large to ensure fast plotting, using ~1000 rows as standard.
    X_sample = shap.sample(X, 1000) if len(X) > 1000 else X
    shap_values = explainer.shap_values(X_sample)
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_summary_plot.png", dpi=150)
    plt.close()
    
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_feature_importance.png", dpi=150)
    plt.close()
    
    logger.info(f"Saved SHAP global plots to {REPORTS_DIR}")
    return explainer

def explain_prediction(explainer, input_row, feature_names):
    """Generate the structured local explanation JSON for a single prediction."""
    # SHAP values matrix shape handling (1, n_features)
    shap_vals = explainer.shap_values(input_row)[0]
    expected_value = explainer.expected_value
    
    if isinstance(expected_value, np.ndarray):
        expected_value = expected_value[0]
        
    predicted_pm25 = expected_value + np.sum(shap_vals)
    
    factors = []
    category_impacts = {
        "Historical Pollution": 0.0,
        "Meteorology": 0.0,
        "Calendar": 0.0,
        "Other Predictors": 0.0
    }
    
    for i, feature in enumerate(feature_names):
        val = shap_vals[i]
        category = categorize_feature(feature)
        category_impacts[category] += val
        
        direction = "increases pollution" if val > 0 else "reduces pollution"
        factors.append({
            "feature": feature,
            "impact": round(float(val), 2),
            "direction": direction,
            "abs_impact": abs(float(val))
        })
        
    # Sort by magnitude of impact
    factors.sort(key=lambda x: x['abs_impact'], reverse=True)
    
    top_increasing = [f for f in factors if f['impact'] > 0][:5]
    top_decreasing = [f for f in factors if f['impact'] < 0][:5]
    
    # Remove temporary sorting key
    for f in top_increasing + top_decreasing:
        f.pop('abs_impact', None)
        
    # Format main drivers grouping
    main_drivers = []
    for cat, impact in sorted(category_impacts.items(), key=lambda item: abs(item[1]), reverse=True):
        if abs(impact) > 0.05: # Only include meaningful drivers
            sign = "+" if impact > 0 else ""
            main_drivers.append({
                "category": cat,
                "impact": f"{sign}{round(float(impact), 2)}"
            })
            
    final_json = {
        "predicted_pm25": round(float(predicted_pm25), 2),
        "top_increasing_factors": top_increasing,
        "top_decreasing_factors": top_decreasing,
        "model_explanation": {
            "main_drivers": main_drivers
        },
        "source_attribution_reference": {
            "note": "Source influence is generated separately by Attribution Agent"
        }
    }
    
    return final_json

def validate_shap():
    """Run validation pipeline and test on a Mumbai Sion station row."""
    logger.info("Starting SHAP validation pipeline...")
    df, features, target = load_and_prepare_data(INPUT_FILE)
    
    # Find Sion, Mumbai station for our test case to align with attribution agent
    sion_df = df[df['station'] == 'Sion, Mumbai - MPCB'].tail(1)
    if sion_df.empty:
        sion_df = df.tail(1)
        
    X_sion = sion_df[features]
    
    model_path = MODELS_DIR / "xgboost_24h.joblib"
    if not model_path.exists():
        raise FileNotFoundError(f"Tuned model not found at {model_path}. Please train first.")
        
    logger.info(f"Loading tuned model from {model_path}")
    model = joblib.load(model_path)
    
    # 1. Generate Global Interpretability
    explainer = generate_global_explainability(model, df[features])
    
    # 2. Generate Local Explanability JSON for Sion
    result_json = explain_prediction(explainer, X_sion, features)
    
    print("\n--- SHAP LOCAL EXPLANATION JSON ---")
    print(json.dumps(result_json, indent=2))
    print("-----------------------------------\n")

if __name__ == "__main__":
    validate_shap()
