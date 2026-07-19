import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import shap
from xgboost import plot_importance

# Add script directory to path to import train_xgboost
sys.path.append(str(Path(__file__).parent))
from train_xgboost import load_and_prepare_data, chronological_train_test_split, INPUT_FILE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports/figures")

def setup_directories():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def categorize_feature(feature_name):
    """Group feature into a category."""
    if 'pm25_lag' in feature_name:
        return 'PM2.5 Lag'
    elif 'rolling' in feature_name:
        return 'Rolling Statistics'
    elif any(poll in feature_name for poll in ['pm10', 'no2', 'co', 'o3']):
        return 'Pollutant Lag'
    elif any(wea in feature_name for wea in ['temperature', 'humidity', 'wind_speed', 'precipitation']):
        return 'Weather'
    elif 'sin' in feature_name or 'cos' in feature_name:
        return 'Cyclical'
    elif any(cal in feature_name for cal in ['day_of_week', 'month', 'day_of_year', 'weekend']):
        return 'Calendar'
    return 'Other'

def analyze_xgboost_importance(model, feature_names):
    """
    Compute, visualize, and group XGBoost feature importances (Gain and Weight).
    """
    logger.info("Computing XGBoost Feature Importances...")
    
    # 1. Gain (Contribution to loss reduction)
    gain_importance = model.get_booster().get_score(importance_type='gain')
    # 2. Weight (Number of times feature is used to split)
    weight_importance = model.get_booster().get_score(importance_type='weight')
    
    # Fill missing features with 0
    gain_dict = {f: gain_importance.get(f, 0.0) for f in feature_names}
    weight_dict = {f: weight_importance.get(f, 0.0) for f in feature_names}
    
    df_imp = pd.DataFrame({
        'Feature': feature_names,
        'Gain': [gain_dict[f] for f in feature_names],
        'Weight': [weight_dict[f] for f in feature_names]
    })
    
    df_imp['Category'] = df_imp['Feature'].apply(categorize_feature)
    
    # Sort by Gain
    df_imp = df_imp.sort_values(by='Gain', ascending=False).reset_index(drop=True)
    
    # Save Top 20 Table
    top_20 = df_imp.head(20)
    top_20.to_csv(REPORTS_DIR / "top_20_features_xgboost.csv", index=False)
    
    # Plot Gain Importance
    plt.figure(figsize=(10, 8))
    plt.barh(top_20['Feature'][::-1], top_20['Gain'][::-1], color='steelblue')
    plt.title('Top 20 Features by XGBoost Gain')
    plt.xlabel('Gain (Average Gain of Splits)')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "feature_importance_gain.png")
    plt.close()
    
    logger.info("XGBoost importance plots saved.")
    return df_imp

def generate_shap_global_explanations(model, X_test):
    """
    Generate global SHAP explanations (Summary Plot & Bar Plot).
    Returns the explainer and shap_values for local explanations.
    """
    logger.info("Generating SHAP Global Explanations...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)
    
    # 1. SHAP Bar Plot (Global magnitude)
    plt.figure()
    shap.plots.bar(shap_values, max_display=15, show=False)
    plt.title("SHAP Global Feature Importance (Bar)")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_bar_plot.png")
    plt.close()
    
    # 2. SHAP Summary Plot (Beeswarm)
    plt.figure()
    shap.plots.beeswarm(shap_values, max_display=15, show=False)
    plt.title("SHAP Summary Plot (Beeswarm)")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_summary_plot.png")
    plt.close()
    
    logger.info("SHAP global plots saved.")
    return explainer, shap_values

def generate_shap_local_explanations(shap_values, X_test, y_test, y_pred):
    """
    Generate local explanations (Waterfall plots) for representative cases.
    """
    logger.info("Generating SHAP Local Explanations...")
    
    # Find indices for low, medium, high PM2.5 predictions
    sorted_idx = np.argsort(y_pred)
    
    low_idx = sorted_idx[int(len(sorted_idx) * 0.1)]   # 10th percentile
    med_idx = sorted_idx[int(len(sorted_idx) * 0.5)]   # Median
    high_idx = sorted_idx[int(len(sorted_idx) * 0.9)]  # 90th percentile
    
    cases = {
        'Low': low_idx,
        'Medium': med_idx,
        'High': high_idx
    }
    
    for case_name, idx in cases.items():
        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(shap_values[idx], max_display=10, show=False)
        
        plt.title(f"SHAP Waterfall - {case_name} PM2.5 Prediction\n"
                  f"Actual: {y_test.iloc[idx]:.2f} | Predicted: {y_pred[idx]:.2f}")
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / f"shap_waterfall_{case_name.lower()}.png")
        plt.close()
        
    logger.info("SHAP local waterfall plots saved.")

def main():
    setup_directories()
    
    # 1. Load Data
    df, features, target = load_and_prepare_data(INPUT_FILE)
    _, test_df = chronological_train_test_split(df, test_size=0.2)
    
    X_test = test_df[features]
    y_test = test_df[target]
    
    # 2. Load Model
    model_path = MODELS_DIR / "xgboost_baseline.joblib"
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}. Please run train_xgboost.py first.")
        return
        
    model = joblib.load(model_path)
    y_pred = model.predict(X_test)
    
    # 3. XGBoost Feature Importance
    df_imp = analyze_xgboost_importance(model, features)
    
    # 4. SHAP Global Explanations
    explainer, shap_values = generate_shap_global_explanations(model, X_test)
    
    # 5. SHAP Local Explanations
    generate_shap_local_explanations(shap_values, X_test, y_test, y_pred)
    
    logger.info("Model interpretation complete.")

if __name__ == "__main__":
    main()
