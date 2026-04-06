import streamlit as st
import pandas as pd
import numpy as np
import joblib
import requests
import json
from pathlib import Path
import sys
import pydeck as pdk
from datetime import datetime

# Ensure local imports from 'backend' folder work
# Note: When deploying to Streamlit Cloud, we need to handle paths correctly.
sys.path.insert(0, str(Path(__file__).parent / "backend"))
from data_pipeline import (
    FEATURE_COLS,
    engineer_features,
    load_and_clean,
)
from health_classifier import classify_aqi

# --- Page Config ---
st.set_page_config(
    page_title="AQI Predictor | AI Air Quality Analysis",
    page_icon="🌍",
    layout="wide",
)

# --- Custom Styles ---
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 3.5rem; font-weight: 700; color: #f8fafc; }
    .health-card { 
        background: rgba(20, 25, 41, 0.4); 
        padding: 1.2rem; 
        border-radius: 16px; 
        border: 1px solid rgba(255, 255, 255, 0.08); 
        margin-bottom: 1rem;
    }
    .risk-badge { 
        display: inline-block; 
        padding: 0.2rem 0.6rem; 
        border-radius: 4px; 
        font-weight: 700; 
        font-size: 0.65rem; 
        text-transform: uppercase; 
        margin-bottom: 0.5rem;
        color: white;
    }
    .stApp { background: #0b0f19; }
</style>
""", unsafe_allow_html=True)

# --- Model Loading ---
@st.cache_resource
def load_assets():
    base_path = Path(__file__).parent / "backend" / "models"
    model = joblib.load(base_path / "aqi_predictor.pkl")
    scaler = joblib.load(base_path / "scaler.pkl")
    stats_path = base_path / "model_stats.json"
    stats = {}
    if stats_path.exists():
        with open(stats_path) as f:
            stats = json.load(f)
    return model, scaler, stats

try:
    model, scaler, model_stats = load_assets()
except Exception as e:
    st.error(f"Error loading model: {e}")
    st.stop()

# --- Helpers ---
def fetch_live_aqi(lat, lon):
    try:
        url_aqi = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone"
        url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        aqi_res = requests.get(url_aqi, timeout=5).json()
        weather_res = requests.get(url_weather, timeout=5).json()
        curr_aqi = aqi_res.get("current", {})
        curr_wx = weather_res.get("current", {})
        co_mg = (curr_aqi.get("carbon_monoxide") or 500) / 1000.0
        return {
            "PM2.5": curr_aqi.get("pm2_5") or 50.0,
            "PM10": curr_aqi.get("pm10") or 80.0,
            "CO": co_mg,
            "NO2": curr_aqi.get("nitrogen_dioxide") or 20.0,
            "SO2": curr_aqi.get("sulphur_dioxide") or 10.0,
            "O3": curr_aqi.get("ozone") or 40.0,
            "Temperature": curr_wx.get("temperature_2m") or 25.0,
            "Humidity": curr_wx.get("relative_humidity_2m") or 50.0
        }
    except:
        return {"PM2.5": 65, "PM10": 110, "CO": 0.8, "NO2": 25, "SO2": 15, "O3": 35, "Temperature": 28, "Humidity": 45}

def predict_aqi(inputs):
    df = load_and_clean()
    df = engineer_features(df)
    last_row = df.iloc[-1]
    feature_row = {
        "PM2.5": inputs.get("PM2.5"), "PM10": inputs.get("PM10"), "CO": inputs.get("CO"),
        "NO2": inputs.get("NO2"), "SO2": inputs.get("SO2"), "O3": inputs.get("O3"),
        "Temperature": inputs.get("Temperature"), "Humidity": inputs.get("Humidity"),
        "AQI_lag1": last_row["AQI"], "PM25_lag1": last_row["PM2.5"], "NO2_lag1": last_row["NO2"],
        "AQI_roll3": last_row["AQI_roll3"], "AQI_roll7": last_row["AQI_roll7"], "PM25_roll3": last_row["PM25_roll3"],
        "DayOfYear": datetime.now().timetuple().tm_yday, "Month": datetime.now().month, "DayOfWeek": datetime.now().weekday()
    }
    X = pd.DataFrame([feature_row])[FEATURE_COLS]
    pred = max(0, round(float(model.predict(X)[0]), 1))
    return classify_aqi(pred)

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3222/3222800.png", width=80)
    st.title("Settings")
    
    city_input = st.text_input("Enter City", "New Delhi")
    if st.button("Sync Location", use_container_width=True):
        res = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city_input}&count=1").json()
        if res.get("results"):
            st.session_state.lat = res["results"][0]["latitude"]
            st.session_state.lon = res["results"][0]["longitude"]
            st.session_state.city = f"{res['results'][0]['name']}, {res['results'][0].get('country', '')}"
        else:
            st.error("City not found")

    if "lat" not in st.session_state:
        st.session_state.lat, st.session_state.lon, st.session_state.city = 28.6139, 77.2090, "New Delhi"

    st.markdown("---")
    st.subheader("🧪 Simulation Scenarios")
    pm25 = st.slider("PM2.5", 0.0, 400.0, 65.0)
    pm10 = st.slider("PM10", 0.0, 500.0, 110.0)
    co = st.slider("CO (mg/m³)", 0.0, 10.0, 0.8)
    no2 = st.slider("NO2", 0.0, 200.0, 25.0)
    so2 = st.slider("SO2", 0.0, 100.0, 15.0)
    o3 = st.slider("O3", 0.0, 200.0, 35.0)
    temp = st.slider("Temp (°C)", -10.0, 50.0, 25.0)
    hum = st.slider("Humidity (%)", 0, 100, 50)

sim_inputs = {"PM2.5": pm25, "PM10": pm10, "CO": co, "NO2": no2, "SO2": so2, "O3": o3, "Temperature": temp, "Humidity": hum}

# --- Dashboard ---
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title(f"🌍 Live Dashboard: {st.session_state.city}")
with header_col2:
    st.write("")
    st.button("🔄 Refresh Data")

live_data = fetch_live_aqi(st.session_state.lat, st.session_state.lon)
today_aqi = int(live_data["PM2.5"] * 1.6 + live_data["NO2"] * 0.4)
today_class = classify_aqi(today_aqi)
tomorrow_class = predict_aqi(sim_inputs)

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    st.metric("TODAY (LIVE)", today_aqi)
    st.markdown(f"""
        <div class="health-card">
            <span class="risk-badge" style="background:{today_class['color']}">{today_class['risk_level']}</span><br>
            <b style="font-size:1.4rem; color:{today_class['color']}">{today_class['category']}</b>
            <p style="font-size:0.9rem; color:#94a3b8; margin-top:0.5rem">{today_class['recommendation']}</p>
        </div>
    """, unsafe_allow_html=True)

with row1_col2:
    st.metric("TOMORROW (PREDICTED)", tomorrow_class['aqi'], delta=int(tomorrow_class['aqi'] - today_aqi), delta_color="inverse")
    st.markdown(f"""
        <div class="health-card">
            <span class="risk-badge" style="background:{tomorrow_class['color']}">{tomorrow_class['risk_level']}</span><br>
            <b style="font-size:1.4rem; color:{tomorrow_class['color']}">{tomorrow_class['category']}</b>
            <p style="font-size:0.9rem; color:#94a3b8; margin-top:0.5rem">{tomorrow_class['recommendation']}</p>
        </div>
    """, unsafe_allow_html=True)

with row1_col3:
    st.markdown("### Health & Safety Indicators")
    if not tomorrow_class['outdoor_safe']:
        st.error(f"🏠 **High Health Risk Advice**\n\n- {tomorrow_class['recommendation']}")
    else:
        st.success(f"🍃 **Safe for Outdoor Activities**\n\n- {tomorrow_class['recommendation']}")
    
    if tomorrow_class.get('asthma_alert'):
        st.warning(f"🫁 **Respiratory Alert**\n\n{tomorrow_class['asthma_alert']}")

st.markdown("---")
aqi_col, chart_col = st.columns([1, 2])

with aqi_col:
    st.subheader("Sensor Map")
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v9',
        initial_view_state=pdk.ViewState(latitude=st.session_state.lat, longitude=st.session_state.lon, zoom=11, pitch=45),
        layers=[pdk.Layer('ScatterplotLayer', data=[{'lat': st.session_state.lat, 'lon': st.session_state.lon}], get_position='[lon, lat]', get_color='[59, 130, 246, 200]', get_radius=500)]
    ))

with chart_col:
    st.subheader("Historical Trends (New Delhi Base)")
    hist_data = get_historical_data(10)
    pdf = pd.DataFrame(hist_data)
    if not pdf.empty:
        st.area_chart(pdf.set_index('Date')['AQI'])
    else:
        st.info("Historical data unavailable for this location.")

# --- Chat ---
st.markdown("---")
st.subheader("💬 AI Air Quality Assistant")
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm your AI air quality assistant. How can I help you today?"}]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask about pollutants, health risks..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Generic AI response (can be expanded)
    aqi = tomorrow_class['aqi']
    res_text = f"Based on the predicted AQI of {aqi} ({tomorrow_class['category']}), "
    if aqi > 150: res_text += "it's definitely safer to stay indoors. PM2.5 levels are significant."
    else: res_text += "conditions look relatively stable. Enjoy your time!"
    
    st.session_state.messages.append({"role": "assistant", "content": res_text})
    with st.chat_message("assistant"):
        st.write(res_text)
