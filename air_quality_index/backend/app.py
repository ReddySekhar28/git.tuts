"""
Flask API Server for AQI Prediction System
Endpoints:
  POST /predict        - Predict AQI from pollutant inputs
  GET  /historical     - Get last N days of AQI data
  GET  /model-stats    - Return model MAE/RMSE stats
  POST /train          - Retrain the model on demand
"""

import json
import os
import sys
from pathlib import Path
import requests

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

# Ensure local imports work
sys.path.insert(0, str(Path(__file__).parent))
from data_pipeline import (
    FEATURE_COLS,
    engineer_features,
    get_features_and_target,
    get_historical_data,
    load_and_clean,
)
from health_classifier import classify_aqi
from model_trainer import train_and_save

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "aqi_predictor.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
STATS_PATH  = MODELS_DIR / "model_stats.json"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# ── App Setup ──────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path="",
)
CORS(app)

# ── Load or train model on startup ────────────────────────────────────────────
model, scaler, model_stats = None, None, {}

def load_model():
    global model, scaler, model_stats
    if MODEL_PATH.exists() and SCALER_PATH.exists():
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        if STATS_PATH.exists():
            with open(STATS_PATH) as f:
                model_stats = json.load(f)
        print("✅ Model loaded from disk.")
    else:
        print("⚙️  No saved model found — training now...")
        model_stats = train_and_save()
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        print("✅ Model trained and loaded.")


def make_prediction_from_inputs(inputs: dict) -> dict:
    """
    Build a feature row from raw pollutant inputs and predict AQI.
    Uses historical rolling stats from the real dataset as context.
    """
    df = load_and_clean()
    df = engineer_features(df)

    # Use the last row's lag/rolling values as context for "tomorrow"
    last_row = df.iloc[-1]

    pm25 = float(inputs.get("PM2.5", last_row["PM2.5"]))
    pm10 = float(inputs.get("PM10", last_row["PM10"]))
    co   = float(inputs.get("CO",   last_row["CO"]))
    no2  = float(inputs.get("NO2",  last_row["NO2"]))
    so2  = float(inputs.get("SO2",  last_row["SO2"]))
    o3   = float(inputs.get("O3",   last_row["O3"]))
    temp = float(inputs.get("Temperature", last_row["Temperature"]))
    hum  = float(inputs.get("Humidity",    last_row["Humidity"]))

    # Approximate current AQI from PM2.5 for lag features (if not given)
    curr_aqi_est = pm25 * 1.6 + no2 * 0.4

    feature_row = {
        "PM2.5":       pm25,
        "PM10":        pm10,
        "CO":          co,
        "NO2":         no2,
        "SO2":         so2,
        "O3":          o3,
        "Temperature": temp,
        "Humidity":    hum,
        "AQI_lag1":    float(inputs.get("AQI_lag1", last_row["AQI"])),
        "PM25_lag1":   float(inputs.get("PM25_lag1", last_row["PM2.5"])),
        "NO2_lag1":    float(inputs.get("NO2_lag1",  last_row["NO2"])),
        "AQI_roll3":   float(inputs.get("AQI_roll3", last_row["AQI_roll3"])),
        "AQI_roll7":   float(inputs.get("AQI_roll7", last_row["AQI_roll7"])),
        "PM25_roll3":  float(inputs.get("PM25_roll3", last_row["PM25_roll3"])),
        "DayOfYear":   pd.Timestamp.now().dayofyear,
        "Month":       pd.Timestamp.now().month,
        "DayOfWeek":   pd.Timestamp.now().dayofweek,
    }

    X = pd.DataFrame([feature_row])[FEATURE_COLS]
    predicted_aqi = float(model.predict(X)[0])
    predicted_aqi = max(0, round(predicted_aqi, 1))

    result = classify_aqi(predicted_aqi)
    result["input_values"] = inputs
    return result


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 503
    try:
        data = request.get_json(force=True)
        result = make_prediction_from_inputs(data)
        return jsonify({"success": True, "prediction": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/historical", methods=["GET"])
def historical():
    try:
        n = int(request.args.get("days", 30))
        n = min(max(n, 5), 365)
        records = get_historical_data(n)
        # Convert dates to strings for JSON
        for r in records:
            if hasattr(r.get("Date"), "strftime"):
                r["Date"] = r["Date"].strftime("%Y-%m-%d")
            
            # Predict Hazard Category for historical records
            res = classify_aqi(r.get("AQI", 50))
            r["Category"] = res["category"]
            r["HazardMessage"] = res.get("recommendation", "")
            
        return jsonify({"success": True, "data": records})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/model-stats", methods=["GET"])
def get_model_stats():
    return jsonify({"success": True, "stats": model_stats})


@app.route("/train", methods=["POST"])
def retrain():
    try:
        global model, scaler, model_stats
        model_stats = train_and_save()
        model  = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        return jsonify({"success": True, "stats": model_stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def fetch_live_aqi(lat=28.6139, lon=77.2090):
    try:
        url_aqi = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone"
        url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        
        aqi_res = requests.get(url_aqi, timeout=5).json()
        weather_res = requests.get(url_weather, timeout=5).json()
        
        curr_aqi = aqi_res.get("current", {})
        curr_wx = weather_res.get("current", {})
        
        # Open-Meteo returns CO in μg/m³, our model expects mg/m³. 
        co_mg = (curr_aqi.get("carbon_monoxide") or 500) / 1000.0
        
        data = {
            "PM2.5": curr_aqi.get("pm2_5") or 50.0,
            "PM10": curr_aqi.get("pm10") or 80.0,
            "CO": co_mg,
            "NO2": curr_aqi.get("nitrogen_dioxide") or 20.0,
            "SO2": curr_aqi.get("sulphur_dioxide") or 10.0,
            "O3": curr_aqi.get("ozone") or 40.0,
            "Temperature": curr_wx.get("temperature_2m") or 25.0,
            "Humidity": curr_wx.get("relative_humidity_2m") or 50.0
        }
        return data
    except Exception as e:
        print("Error fetching live API:", e)
        # Fallback dummy data if API fails
        return {"PM2.5": 65, "PM10": 110, "CO": 0.8, "NO2": 25, "SO2": 15, "O3": 35, "Temperature": 28, "Humidity": 45}

@app.route("/live-forecast", methods=["GET"])
def live_forecast():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 503
    try:
        lat = float(request.args.get("lat", 28.6139))
        lon = float(request.args.get("lon", 77.2090))
        
        # 1. Fetch live data for "Today"
        live_data = fetch_live_aqi(lat, lon)
        
        # 2. Predict "Tomorrow" using the live data as input
        prediction_result = make_prediction_from_inputs(live_data)
        
        # 3. Predict "Day After Tomorrow" using "Tomorrow" prediction as lag context
        day_after_data = live_data.copy()
        day_after_data["AQI_lag1"] = prediction_result["aqi"]
        day_after_result = make_prediction_from_inputs(day_after_data)
        
        # 4. Calculate "Today" approximate AQI (Weighted proxy for UI)
        pm25 = live_data.get("PM2.5", 50)
        no2 = live_data.get("NO2", 20)
        today_aqi_approx = int(pm25 * 1.6 + no2 * 0.4)
        today_class = classify_aqi(today_aqi_approx)
        
        # 5. Build enriched response
        today_data = today_class.copy()
        today_data["inputs"] = live_data
        
        return jsonify({
            "success": True,
            "today": today_data,
            "tomorrow": prediction_result,
            "day_after_tomorrow": day_after_result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        query = data.get("message", "").lower()
        context = data.get("context", {})
        
        # Simple rule-based AI logic (can be replaced with LLM API)
        aqi = context.get("aqi", 0)
        location = context.get("location", "your area")
        
        response = ""
        if "aqi" in query or "quality" in query:
            response = f"The current AQI in {location} is {aqi}. "
            if aqi <= 50: response += "It's a great day for outdoor activities!"
            elif aqi <= 100: response += "Air quality is satisfactory."
            else: response += "I recommend staying indoors if possible."
        elif "help" in query or "how" in query:
            response = "I can help you understand air quality levels, health risks, and the pollutant forecasts on this dashboard. Just ask!"
        elif "pm2.5" in query or "pollutant" in query:
            response = "PM2.5 are tiny particles that can enter your lungs. Today's levels are shown on the left panel."
        else:
            response = "That's a good question! As an AI focused on air quality, I'd say it's always best to check the forecast rings before heading out."

        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")
        if email and password:
            return jsonify({"success": True, "token": "mock-jwt-token-123", "name": email.split('@')[0]})
        return jsonify({"success": False, "error": "Invalid email or password"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    load_model()
    print("\n🌍  AQI Prediction System running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
