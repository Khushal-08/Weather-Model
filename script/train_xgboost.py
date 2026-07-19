import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import joblib
import time

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

INPUT_FILE = Path("data/processed/training_features.csv")
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports/figures")

def setup_directories():
    """Ensure output directories exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def load_and_prepare_data(filepath):
    """
    Load data, fix rolling features for data leakage, and extract predictors/target.
    
    Time-series forecasting best practice: 
    When predicting next-day (or target at time t using features from time t-1),
    we must strictly ensure NO current-day variables (time t) are used in the features.
    """
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort chronologically as a best practice for time-series splits
    df = df.sort_values('date').reset_index(drop=True)
    
    sort_col = 'location' if 'location' in df.columns else 'station'
    
    # Fix rolling features to prevent data leakage:
    # In feature_engineering.py, rolling features included the current day. 
    # We must shift them by 1 day per station so they represent rolling stats UP TO yesterday.
    rolling_cols = [c for c in df.columns if 'rolling' in c]
    for col in rolling_cols:
        df[f"{col}_shifted"] = df.groupby(sort_col)[col].shift(1)
        
    # Drop rows with NaNs introduced by the shift
    df = df.dropna(subset=[f"{col}_shifted" for col in rolling_cols]).reset_index(drop=True)
    
    # Define features
    lag_cols = [c for c in df.columns if 'lag' in c]
    shifted_rolling_cols = [f"{c}_shifted" for c in rolling_cols]
    calendar_cols = ['day_of_week', 'month', 'day_of_year', 'weekend', 
                     'month_sin', 'month_cos', 'day_of_week_sin', 'day_of_week_cos', 
                     'day_of_year_sin', 'day_of_year_cos']
                     
    features = lag_cols + shifted_rolling_cols + calendar_cols
    target = 'pm25'

    # Drop rows with NaNs in features or target
    df = df.dropna(subset=features + [target]).reset_index(drop=True)
    
    logger.info(f"Selected {len(features)} features. Target is {target}.")
    return df, features, target

def chronological_train_test_split(df, test_size=0.2):
    """
    Split data chronologically into train and test sets.
    
    Time-series forecasting best practice:
    Never shuffle time-series data. Future data cannot be used to predict past data.
    A chronological split maintains the temporal order and simulates real-world forecasting.
    """
    split_idx = int(len(df) * (1 - test_size))
    
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    return train_df, test_df

def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error."""
    # Avoid division by zero
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

def evaluate_model(y_true, y_pred, split_name="Test"):
    """Calculate and log evaluation metrics."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = calculate_mape(y_true.values, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    logger.info(f"--- {split_name} Evaluation ---")
    logger.info(f"MAE:  {mae:.4f}")
    logger.info(f"RMSE: {rmse:.4f}")
    logger.info(f"MAPE: {mape:.2f}%")
    logger.info(f"R²:   {r2:.4f}")
    
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'R2': r2}

def plot_results(train_df, test_df, y_test_pred):
    """Generate Actual vs Predicted and Residual plots."""
    logger.info("Generating evaluation plots...")
    
    # 1. Actual vs Predicted (Time-Series)
    plt.figure(figsize=(14, 6))
    
    # Plotting last 20% of train to provide context, then test actuals vs predictions
    plt.plot(train_df['date'].tail(200), train_df['pm25'].tail(200), label='Train Actuals', color='blue', alpha=0.5)
    plt.plot(test_df['date'], test_df['pm25'], label='Test Actuals', color='black', alpha=0.7)
    plt.plot(test_df['date'], y_test_pred, label='Test Predictions (XGBoost)', color='red', alpha=0.8)
    
    plt.title('PM2.5 Forecasting: Actual vs Predicted')
    plt.xlabel('Date')
    plt.ylabel('PM2.5')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.savefig(REPORTS_DIR / "baseline_xgboost_actual_vs_predicted.png")
    plt.close()
    
    # 2. Residuals Plot
    residuals = test_df['pm25'] - y_test_pred
    plt.figure(figsize=(10, 5))
    plt.scatter(test_df['date'], residuals, color='purple', alpha=0.5)
    plt.axhline(0, color='black', linestyle='--')
    plt.title('Residuals Over Time (Actual - Predicted)')
    plt.xlabel('Date')
    plt.ylabel('Error (PM2.5)')
    plt.grid(True, alpha=0.3)
    
    plt.savefig(REPORTS_DIR / "baseline_xgboost_residuals.png")
    plt.close()
    
    logger.info(f"Plots saved to {REPORTS_DIR}")

def main():
    setup_directories()
    
    # 1. Load & Prepare
    df, features, target = load_and_prepare_data(INPUT_FILE)
    
    # 2. Chronological Split
    train_df, test_df = chronological_train_test_split(df, test_size=0.2)
    
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    # 3. Train XGBoost Baseline
    logger.info("Training XGBoost Regressor baseline...")
    # Baseline hyperparameters, no tuning yet
    model = XGBRegressor(
        n_estimators=100, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42,
        objective='reg:squarederror'
    )
    
    start_time = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_time
    logger.info(f"Training complete in {train_time:.4f} seconds.")
    
    # 4. Evaluate
    start_time = time.time()
    y_test_pred = model.predict(X_test)
    pred_time = time.time() - start_time
    logger.info(f"Prediction complete in {pred_time:.4f} seconds.")
    
    metrics = evaluate_model(y_test, y_test_pred, split_name="Test")
    metrics['Train_Time'] = train_time
    metrics['Predict_Time'] = pred_time
    pd.DataFrame([metrics]).to_csv(REPORTS_DIR / "xgboost_metrics.csv", index=False)
    
    # 5. Plotting
    plot_results(train_df, test_df, y_test_pred)
    
    # 6. Save Model
    model_path = MODELS_DIR / "xgboost_baseline.joblib"
    joblib.dump(model, model_path)
    logger.info(f"Model successfully saved to {model_path}")

if __name__ == "__main__":
    main()
