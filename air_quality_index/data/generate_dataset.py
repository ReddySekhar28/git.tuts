"""
Generate a synthetic but realistic 2-year air quality dataset for India.
Run this once: python generate_dataset.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

DATA_DIR = Path(__file__).parent
DATA_DIR.mkdir(exist_ok=True)

# Generate 2 years of daily data
dates = pd.date_range("2022-01-01", "2023-12-31", freq="D")
n = len(dates)

# Seasonal pattern (winter = worse AQI)
month = dates.month
season_factor = np.where(
    (month >= 11) | (month <= 2), 1.8,   # Winter: high pollution
    np.where((month >= 6) & (month <= 9), 0.7, 1.0)  # Monsoon: cleaner
)

base_aqi = 120 * season_factor + np.random.normal(0, 25, n)
base_aqi = np.clip(base_aqi, 10, 500)

# Pollutant columns correlated with AQI
pm25   = base_aqi * 0.6 + np.random.normal(0, 10, n)
pm10   = base_aqi * 0.9 + np.random.normal(0, 15, n)
co     = (base_aqi / 100) * 1.2 + np.random.normal(0, 0.3, n)  # mg/m3
no2    = base_aqi * 0.4 + np.random.normal(0, 12, n)
so2    = base_aqi * 0.15 + np.random.normal(0, 5, n)
o3     = 60 + np.random.normal(0, 20, n) - base_aqi * 0.05  # inversely related
temp   = 25 + 10 * np.sin(2 * np.pi * (dates.dayofyear - 60) / 365) + np.random.normal(0, 3, n)
humid  = 60 + 20 * np.sin(2 * np.pi * (dates.dayofyear - 180) / 365) + np.random.normal(0, 10, n)

# Clip all to realistic ranges
pm25  = np.clip(pm25, 5, 500)
pm10  = np.clip(pm10, 10, 600)
co    = np.clip(co, 0.1, 10)
no2   = np.clip(no2, 5, 200)
so2   = np.clip(so2, 2, 100)
o3    = np.clip(o3, 10, 120)
temp  = np.clip(temp, 2, 45)
humid = np.clip(humid, 20, 100)
aqi   = np.clip(base_aqi, 10, 500).round(1)

df = pd.DataFrame({
    "Date":        dates.strftime("%Y-%m-%d"),
    "PM2.5":       pm25.round(1),
    "PM10":        pm10.round(1),
    "CO":          co.round(3),
    "NO2":         no2.round(1),
    "SO2":         so2.round(1),
    "O3":          o3.round(1),
    "Temperature": temp.round(1),
    "Humidity":    humid.round(1),
    "AQI":         aqi,
})

# Introduce 3% missing values randomly
for col in ["PM2.5", "PM10", "NO2", "SO2"]:
    mask = np.random.random(n) < 0.03
    df.loc[mask, col] = np.nan

out_path = DATA_DIR / "air_quality.csv"
df.to_csv(out_path, index=False)
print(f"✅ Dataset saved to {out_path} ({len(df)} rows)")
print(df.describe())
