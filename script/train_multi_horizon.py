import logging
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import mean_squared_error, r2_score
from xgboost import XGBRegressor

print("\n" + "="*60)
print("SAFEGUARD: TRAINING DATASET")
print("Loading exclusively from: data/processed/training_features.csv")
print("Target Date Range: 2021-08-01 to 2023-07-31")
print("="*60 + "\n")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

INPUT_FILE = Path("data/processed/training_features.csv")
MODELS_DIR = Path("models")
REPORTS_DIR = Path("reports/figures")

def load_and_prepare_data_multi(filepath):
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
                     
    # Add current-day features to ensure XGBoost has actual values
    current_cols = ['pm25', 'pm10', 'no2', 'co', 'o3', 'temperature_2m_mean', 'relative_humidity_2m_mean', 'precipitation_sum', 'wind_speed_10m_mean']
    current_cols = [c for c in current_cols if c in df.columns]
    
    # pm25_rolling_mean_14_shifted and pm25_rolling_mean_30_shifted are inherently in shifted_rolling_cols
    features = current_cols + lag_cols + shifted_rolling_cols + calendar_cols
    
    # Create target columns using STATION-WISE grouping
    df["pm25_target_24h"] = df.groupby(sort_col)["pm25"].shift(-1)
    df["pm25_target_48h"] = df.groupby(sort_col)["pm25"].shift(-2)
    df["pm25_target_72h"] = df.groupby(sort_col)["pm25"].shift(-3)
    
    targets = ["pm25_target_24h", "pm25_target_48h", "pm25_target_72h"]
    df = df.dropna(subset=features + targets).reset_index(drop=True)
    
    return df, features, targets

def chronological_train_val_test_split(df):
    """Creates a chronological split for Train, Validation, and Test using explicit dates."""
    
    # Train: start to 2022-09-30
    train_end = pd.to_datetime('2022-09-30')
    # Val: 2022-10-01 to 2022-12-31
    val_end = pd.to_datetime('2022-12-31')
    
    train_df = df[df['date'] <= train_end].copy()
    val_df = df[(df['date'] > train_end) & (df['date'] <= val_end)].copy()
    test_df = df[df['date'] > val_end].copy()
    
    return train_df, val_df, test_df

def tune_and_train(train_df, val_df, test_df, features, target_col, baseline_val_col, horizon, tuned_params):
    X_train, y_train = train_df[features], train_df[target_col]
    X_val, y_val = val_df[features], val_df[target_col]
    X_test, y_test = test_df[features], test_df[target_col]
    
    baseline_preds_test = test_df[baseline_val_col]
    
    best_params = tuned_params.copy()
    
    # Only sweep for 48h and 72h
    if horizon in ["48h", "72h"]:
        logger.info(f"Sweeping hyperparameters for {horizon} on validation set...")
        sweep_params = [
            {'n_estimators': 300, 'max_depth': 4, 'learning_rate': 0.05, 'min_child_weight': 5, 'reg_lambda': 5},
            {'n_estimators': 300, 'max_depth': 3, 'learning_rate': 0.05, 'min_child_weight': 10, 'reg_lambda': 10},
            {'n_estimators': 300, 'max_depth': 3, 'learning_rate': 0.01, 'min_child_weight': 15, 'reg_lambda': 20},
            {'n_estimators': 300, 'max_depth': 2, 'learning_rate': 0.05, 'min_child_weight': 20, 'reg_lambda': 50}
        ]
        
        baseline_preds_val = val_df[baseline_val_col]
        baseline_rmse_val = np.sqrt(mean_squared_error(y_val, baseline_preds_val))
        
        best_imp = -float("inf")
        best_p = sweep_params[0]
        
        for p in sweep_params:
            m = XGBRegressor(**p, random_state=42, early_stopping_rounds=15)
            m.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
            preds_val = m.predict(X_val)
            rmse_val = np.sqrt(mean_squared_error(y_val, preds_val))
            imp = ((baseline_rmse_val - rmse_val) / baseline_rmse_val) * 100
            
            if imp > best_imp:
                best_imp = imp
                best_p = p
                
        logger.info(f"Best sweep params for {horizon}: {best_p} (Val Imp: {best_imp:.2f}%)")
        best_params.update(best_p)
        
        # Train final model using the best params and early stopping
        model = XGBRegressor(**best_params, early_stopping_rounds=15)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    else:
        # 24h model uses original logic: train on train+val combined, no early stopping
        X_train_full = pd.concat([X_train, X_val])
        y_train_full = pd.concat([y_train, y_val])
        model = XGBRegressor(**best_params)
        model.fit(X_train_full, y_train_full, verbose=False)
    
    y_pred = model.predict(X_test)
    
    xgboost_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    persistence_rmse = np.sqrt(mean_squared_error(y_test, baseline_preds_test))
    improvement = ((persistence_rmse - xgboost_rmse) / persistence_rmse) * 100
    xgboost_r2 = r2_score(y_test, y_pred)
    
    # Calculate Winter-only subset metrics
    winter_mask = test_df['date'].dt.month.isin([12, 1, 2])
    if winter_mask.sum() > 0:
        y_test_w = y_test[winter_mask]
        y_pred_w = y_pred[winter_mask]
        baseline_w = baseline_preds_test[winter_mask]
        
        xb_rmse_w = np.sqrt(mean_squared_error(y_test_w, y_pred_w))
        per_rmse_w = np.sqrt(mean_squared_error(y_test_w, baseline_w))
        imp_w = ((per_rmse_w - xb_rmse_w) / per_rmse_w) * 100
    else:
        xb_rmse_w, per_rmse_w, imp_w = np.nan, np.nan, np.nan
    
    return model, xgboost_rmse, persistence_rmse, improvement, xgboost_r2, xb_rmse_w, per_rmse_w, imp_w

def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    df, features, targets = load_and_prepare_data_multi(INPUT_FILE)
    train_df, val_df, test_df = chronological_train_val_test_split(df)
    
    print("\n--- SPLIT DISTRIBUTION VALIDATION ---")
    for name, split_df in zip(['Train', 'Validation', 'Test'], [train_df, val_df, test_df]):
        d_min = split_df['date'].min().date()
        d_max = split_df['date'].max().date()
        mean_val = split_df['pm25'].mean()
        std_val = split_df['pm25'].std()
        print(f"\n{name} Split: Dates {d_min} to {d_max} | OVERALL PM2.5 Mean: {mean_val:.2f} | PM2.5 Std: {std_val:.2f}")
        
        print(f"  Monthly Breakdown:")
        monthly = split_df.groupby(split_df['date'].dt.month)['pm25'].agg(['mean', 'std', 'count']).round(2)
        for m, row in monthly.iterrows():
            print(f"    Month {m:02d}: Mean {row['mean']:<6.2f} | Std {row['std']:<6.2f} | N={int(row['count'])}")
    print("\n-------------------------------------\n")
    
    params_path = REPORTS_DIR / "xgboost_tuned_params.csv"
    if params_path.exists():
        tuned_params = pd.read_csv(params_path).iloc[0].to_dict()
        tuned_params['objective'] = 'reg:squarederror'
        tuned_params['random_state'] = 42
        for k, v in tuned_params.items():
            if isinstance(v, float) and v.is_integer():
                tuned_params[k] = int(v)
    else:
        tuned_params = {
            'n_estimators': 300,
            'max_depth': 6,
            'learning_rate': 0.05,
            'random_state': 42,
            'objective': 'reg:squarederror'
        }
    
    baseline_col = 'pm25'
    results = {}
    
    for horizon, target_col in zip(["24h", "48h", "72h"], targets):
        logger.info(f"Training {horizon} model on target {target_col}...")
        model, xb_rmse, per_rmse, imp, r2, xb_rmse_w, per_rmse_w, imp_w = tune_and_train(
            train_df, val_df, test_df, features, target_col, baseline_col, horizon, tuned_params
        )
        
        results[horizon] = {
            "xb_rmse": xb_rmse,
            "per_rmse": per_rmse,
            "imp": imp,
            "r2": r2,
            "xb_rmse_w": xb_rmse_w,
            "per_rmse_w": per_rmse_w,
            "imp_w": imp_w
        }
        
        joblib.dump(model, MODELS_DIR / f"xgboost_{horizon}.joblib")
        
    print("\n================= OVERALL TEST PERFORMANCE =================")
    print("Horizon | XGBoost RMSE | Persistence RMSE | Improvement % | XGBoost R²")
    for hor in ["24h", "48h", "72h"]:
        r = results[hor]
        print(f"{hor:<7} | {r['xb_rmse']:<12.2f} | {r['per_rmse']:<16.2f} | {r['imp']:<13.2f} | {r['r2']:.4f}")

    print("\n=============== WINTER-ONLY TEST PERFORMANCE ===============")
    print("Horizon | XGBoost RMSE | Persistence RMSE | Improvement %")
    for hor in ["24h", "48h", "72h"]:
        r = results[hor]
        if np.isnan(r['xb_rmse_w']):
            print(f"{hor:<7} | No Winter Data | No Winter Data   | N/A")
        else:
            print(f"{hor:<7} | {r['xb_rmse_w']:<12.2f} | {r['per_rmse_w']:<16.2f} | {r['imp_w']:<13.2f}")

    print("\n--- PERFORMANCE SUMMARY NOTE ---")
    for hor in ["24h", "48h", "72h"]:
        overall_imp = results[hor]['imp']
        winter_imp = results[hor]['imp_w']
        
        if overall_imp > 0 and (np.isnan(winter_imp) or winter_imp > 0):
            print(f"[{hor}] BEATS persistence overall (+{overall_imp:.2f}%) and in winter (+{winter_imp:.2f}%).")
        elif overall_imp > 0 and winter_imp <= 0:
            print(f"[{hor}] BEATS persistence overall (+{overall_imp:.2f}%), BUT FAILS IN WINTER ({winter_imp:.2f}%).")
        else:
            print(f"[{hor}] FAILS to beat persistence overall ({overall_imp:.2f}%).")

if __name__ == "__main__":
    main()
