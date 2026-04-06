"""
Model Trainer: Train a Random Forest Regressor to predict AQI.
Saves the trained model and scaler to the models/ directory.
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent))
from data_pipeline import load_and_clean, engineer_features, get_features_and_target

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODELS_DIR / "aqi_predictor.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
STATS_PATH = MODELS_DIR / "model_stats.json"


def train_and_save():
    print("📦 Loading and processing data...")
    df = load_and_clean()
    df = engineer_features(df)

    X, y = get_features_and_target(df)

    # Time-based split (last 20% as test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Scale features
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)

    # --- Linear Regression (baseline) ---
    lr = LinearRegression()
    lr.fit(X_train_sc, y_train)
    lr_pred = lr.predict(X_test_sc)
    lr_mae = mean_absolute_error(y_test, lr_pred)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_pred))
    print(f"📊 Linear Regression  → MAE: {lr_mae:.2f} | RMSE: {lr_rmse:.2f}")

    # --- Random Forest (primary model) ---
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
    print(f"🌲 Random Forest      → MAE: {rf_mae:.2f} | RMSE: {rf_rmse:.2f}")

    # Save best model (Random Forest) and scaler
    joblib.dump(rf, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    stats = {
        "model": "Random Forest Regressor",
        "n_estimators": 200,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "mae": round(rf_mae, 2),
        "rmse": round(rf_rmse, 2),
        "baseline_mae": round(lr_mae, 2),
        "baseline_rmse": round(lr_rmse, 2),
        "features": list(X.columns),
    }
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n✅ Model saved → {MODEL_PATH}")
    print(f"✅ Scaler saved → {SCALER_PATH}")
    print(f"✅ Stats saved → {STATS_PATH}")
    return stats


if __name__ == "__main__":
    train_and_save()
