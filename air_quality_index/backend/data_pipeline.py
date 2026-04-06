"""
Data Pipeline: Loading, Cleaning, and Feature Engineering for AQI Dataset
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "air_quality.csv"


def load_and_clean(filepath=DATA_PATH):
    """Load and clean the air quality dataset."""
    df = pd.read_csv(filepath, parse_dates=["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    # Fill missing numeric values with forward fill then median
    numeric_cols = ["PM2.5", "PM10", "CO", "NO2", "SO2", "O3", "Temperature", "Humidity", "AQI"]
    df[numeric_cols] = df[numeric_cols].ffill()
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())

    # Clip negative values
    for col in ["PM2.5", "PM10", "CO", "NO2", "SO2", "O3"]:
        df[col] = df[col].clip(lower=0)

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create lag and rolling features for time-series prediction."""
    df = df.copy()

    # Lag features (previous day values)
    df["AQI_lag1"] = df["AQI"].shift(1)
    df["PM25_lag1"] = df["PM2.5"].shift(1)
    df["NO2_lag1"] = df["NO2"].shift(1)

    # Rolling averages
    df["AQI_roll3"] = df["AQI"].shift(1).rolling(window=3).mean()
    df["AQI_roll7"] = df["AQI"].shift(1).rolling(window=7).mean()
    df["PM25_roll3"] = df["PM2.5"].shift(1).rolling(window=3).mean()

    # Date features
    df["DayOfYear"] = df["Date"].dt.dayofyear
    df["Month"] = df["Date"].dt.month
    df["DayOfWeek"] = df["Date"].dt.dayofweek

    # Drop rows where lag features are NaN (first 7 rows)
    df = df.dropna().reset_index(drop=True)
    return df


FEATURE_COLS = [
    "PM2.5", "PM10", "CO", "NO2", "SO2", "O3",
    "Temperature", "Humidity",
    "AQI_lag1", "PM25_lag1", "NO2_lag1",
    "AQI_roll3", "AQI_roll7", "PM25_roll3",
    "DayOfYear", "Month", "DayOfWeek"
]
TARGET_COL = "AQI"


def get_features_and_target(df: pd.DataFrame):
    """Return X (features) and y (target) for modeling."""
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]
    return X, y


def get_historical_data(n_days: int = 5, filepath=DATA_PATH):
    """Return last n_days of cleaned data, mapped to current dates (ending today)."""
    df = load_and_clean(filepath)
    df = df.tail(n_days).reset_index(drop=True)
    
    # Map the last n rows to the actual last n days from 2026-04-06
    today = pd.Timestamp("2026-04-06")
    dates = [today - pd.Timedelta(days=i) for i in range(n_days)]
    dates.reverse() # Sort ascending
    
    df["Date"] = dates
    return df[["Date", "AQI", "PM2.5", "PM10", "NO2"]].to_dict(orient="records")


if __name__ == "__main__":
    df = load_and_clean()
    df = engineer_features(df)
    print(f"Dataset shape: {df.shape}")
    print(df.tail())
