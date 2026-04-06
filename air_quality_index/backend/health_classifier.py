"""
Health Classifier: Converts AQI values into risk categories and health suggestions.
"""


def classify_aqi(aqi: float) -> dict:
    """
    Classify an AQI value into a risk category with health suggestions.

    AQI Ranges (India standard):
        0   – 50  : Good
        51  – 100 : Satisfactory
        101 – 200 : Moderate
        201 – 300 : Poor
        301 – 400 : Very Poor
        400+      : Severe / Hazardous
    """
    aqi = round(float(aqi), 1)

    if aqi <= 50:
        return {
            "aqi": aqi,
            "category": "Good",
            "risk_level": "Low Risk",
            "risk_code": "low",
            "asthma_alert": "No concern",
            "emoji": "✅",
            "color": "#00c853",
            "recommendation": "Air quality is excellent. Safe to go outside freely.",
            "outdoor_safe": True,
        }
    elif aqi <= 100:
        return {
            "aqi": aqi,
            "category": "Satisfactory",
            "risk_level": "Low Risk",
            "risk_code": "low",
            "asthma_alert": "Minimal concern",
            "emoji": "✅",
            "color": "#64dd17",
            "recommendation": "Air quality is acceptable. Safe to go outside.",
            "outdoor_safe": True,
        }
    elif aqi <= 200:
        return {
            "aqi": aqi,
            "category": "Moderate",
            "risk_level": "Moderate Risk",
            "risk_code": "moderate",
            "asthma_alert": "⚠️ Asthma / Lung patients should limit outdoor exposure",
            "emoji": "⚠️",
            "color": "#ffab00",
            "recommendation": "Limit prolonged outdoor activities. Sensitive groups should be cautious.",
            "outdoor_safe": False,
        }
    elif aqi <= 300:
        return {
            "aqi": aqi,
            "category": "Poor",
            "risk_level": "High Risk",
            "risk_code": "high",
            "asthma_alert": "🚨 HIGH ALERT for Asthma / Lung disease patients",
            "emoji": "❌",
            "color": "#ff6d00",
            "recommendation": "Attention: Do not go outside. High health risk.",
            "outdoor_safe": False,
        }
    elif aqi <= 400:
        return {
            "aqi": aqi,
            "category": "Very Poor",
            "risk_level": "High Risk",
            "risk_code": "high",
            "asthma_alert": "🚨 EMERGENCY ALERT for all respiratory patients",
            "emoji": "❌",
            "color": "#d50000",
            "recommendation": "Attention: Do not go outside. Stay indoors.",
            "outdoor_safe": False,
        }
    else:
        return {
            "aqi": aqi,
            "category": "Severe / Hazardous",
            "risk_level": "High Risk",
            "risk_code": "high",
            "asthma_alert": "🆘 CRITICAL — Immediate health risk for everyone",
            "emoji": "❌",
            "color": "#b71c1c",
            "recommendation": "Attention: Do not go outside. Critical risk.",
            "outdoor_safe": False,
        }
