import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import joblib
import time
import optuna

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
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
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    
    # Sort chronologically as a best practice for time-series splits
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
                     
    features = lag_cols + shifted_rolling_cols + calendar_cols
    target = 'pm25'

    df = df.dropna(subset=features + [target]).reset_index(drop=True)
    
    logger.info(f"Selected {len(features)} features. Target is {target}.")
    return df, features, target

def chronological_train_test_split(df, test_size=0.2):
    split_idx = int(len(df) * (1 - test_size))
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    return train_df, test_df

def calculate_mape(y_true, y_pred):
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

def evaluate_model(y_true, y_pred, split_name="Test"):
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

def objective(trial, X, y):
    param = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'gamma': trial.suggest_float('gamma', 0.0, 5.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 100.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 100.0, log=True),
        'objective': 'reg:squarederror',
        'random_state': 42,
        'n_jobs': -1
    }
    
    tscv = TimeSeriesSplit(n_splits=5)
    rmse_scores = []
    
    # We must convert to numpy for TimeSeriesSplit if they are pandas dataframes
    X_arr = X.values if isinstance(X, pd.DataFrame) else X
    y_arr = y.values if isinstance(y, pd.Series) else y
    
    for train_index, valid_index in tscv.split(X_arr):
        X_tr, X_va = X_arr[train_index], X_arr[valid_index]
        y_tr, y_va = y_arr[train_index], y_arr[valid_index]
        
        model = XGBRegressor(**param)
        model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], verbose=False)
        preds = model.predict(X_va)
        rmse = np.sqrt(mean_squared_error(y_va, preds))
        rmse_scores.append(rmse)
        
    return np.mean(rmse_scores)

def main():
    setup_directories()
    
    df, features, target = load_and_prepare_data(INPUT_FILE)
    train_df, test_df = chronological_train_test_split(df, test_size=0.2)
    
    X_train, y_train = train_df[features], train_df[target]
    X_test, y_test = test_df[features], test_df[target]
    
    logger.info("Starting hyperparameter tuning using Optuna and TimeSeriesSplit...")
    
    # Optimize
    study = optuna.create_study(direction='minimize')
    study.optimize(lambda trial: objective(trial, X_train, y_train), n_trials=30)
    
    logger.info("Number of finished trials: {}".format(len(study.trials)))
    logger.info("Best trial:")
    trial = study.best_trial
    logger.info("  Value (RMSE): {}".format(trial.value))
    logger.info("  Params: ")
    for key, value in trial.params.items():
        logger.info("    {}: {}".format(key, value))
        
    # Retrain on full train data with best params
    best_params = trial.params
    best_params['objective'] = 'reg:squarederror'
    best_params['random_state'] = 42
    best_params['n_jobs'] = -1
    
    logger.info("Retraining best model on full training set...")
    best_model = XGBRegressor(**best_params)
    
    start_time = time.time()
    best_model.fit(X_train, y_train)
    train_time = time.time() - start_time
    logger.info(f"Training of best model complete in {train_time:.4f} seconds.")
    
    # Evaluate
    start_time = time.time()
    y_test_pred = best_model.predict(X_test)
    pred_time = time.time() - start_time
    logger.info(f"Prediction complete in {pred_time:.4f} seconds.")
    
    metrics = evaluate_model(y_test, y_test_pred, split_name="Test (Tuned)")
    metrics['Train_Time'] = train_time
    metrics['Predict_Time'] = pred_time
    
    pd.DataFrame([metrics]).to_csv(REPORTS_DIR / "xgboost_tuned_metrics.csv", index=False)
    pd.DataFrame([best_params]).to_csv(REPORTS_DIR / "xgboost_tuned_params.csv", index=False)
    
    model_path = MODELS_DIR / "xgboost_tuned.joblib"
    joblib.dump(best_model, model_path)
    logger.info(f"Tuned model successfully saved to {model_path}")

if __name__ == "__main__":
    main()
