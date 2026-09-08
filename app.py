from flask import Flask, request, jsonify
import requests
import json
import time
import re
from functools import wraps
from datetime import datetime

app = Flask(__name__)

# ==============================================
# 🌤️ WEATHER API
# Made by @KINGFFAIAK47x · ANSH AFT
# ==============================================

# Authentication Keys
VALID_KEYS = {
    "LEAK": "full_access",
}

# Weather API Key (Hidden)
WEATHER_API_KEY = "fec68ebf3d3341e09f295825251712"

# ==============================================
# 🛡️ INPUT VALIDATION
# ==============================================

class AdvancedValidator:
    @staticmethod
    def validate_city(city):
        if not city:
            return False, "City name is required"
        
        city = str(city).strip()
        
        if len(city) < 2:
            return False, "City name must be at least 2 characters"
        
        if len(city) > 100:
            return False, "City name too long"
        
        city = re.sub(r'[<>"\']', '', city)
        
        return True, city
    
    @staticmethod
    def validate_api_key(api_key):
        if not api_key:
            return False, "API key is required"
        
        api_key = str(api_key).strip()
        
        if len(api_key) < 4:
            return False, "Invalid API key format"
        
        return True, None
    
    @staticmethod
    def sanitize_input(value):
        if value is None:
            return "N/A"
        
        value = str(value).strip()
        value = re.sub(r'[<>"\']', '', value)
        
        if len(value) > 1000:
            value = value[:1000] + "..."
        
        return value if value else "N/A"

# ==============================================
# 🔐 AUTHENTICATION
# ==============================================

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.args.get('key', '').strip()
        
        is_valid, error_msg = AdvancedValidator.validate_api_key(api_key)
        
        if not is_valid:
            return jsonify({
                "status": "error",
                "error_code": "INVALID_API_KEY",
                "message": error_msg,
                "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
            }), 401
        
        if api_key not in VALID_KEYS:
            return jsonify({
                "status": "error",
                "error_code": "UNAUTHORIZED",
                "message": "Invalid API key!",
                "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
            }), 403
        
        request.api_key = api_key
        request.access_level = VALID_KEYS[api_key]
        
        return f(*args, **kwargs)
    return decorated_function

# ==============================================
# 🌤️ WEATHER FUNCTIONS
# ==============================================

def fetch_weather_data(city):
    is_valid, error_msg = AdvancedValidator.validate_city(city)
    if not is_valid:
        return None, error_msg
    
    base_url = "https://api.weatherapi.com/v1/forecast.json"
    
    params = {
        "key": WEATHER_API_KEY,
        "q": city,
        "days": 3,
        "aqi": "yes"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data:
            return data, None
        else:
            return None, "No weather data found"
            
    except requests.exceptions.Timeout:
        return None, "Request timeout"
    except requests.exceptions.ConnectionError:
        return None, "Connection error"
    except requests.exceptions.RequestException as e:
        return None, f"Network error: {str(e)}"
    except json.JSONDecodeError:
        return None, "Invalid response format"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def get_air_quality_category(aqi):
    aqi_categories = {
        1: "Good",
        2: "Moderate",
        3: "Unhealthy for Sensitive Groups",
        4: "Unhealthy",
        5: "Very Unhealthy",
        6: "Hazardous"
    }
    return aqi_categories.get(aqi, "N/A")

def get_weather_emoji(condition_text):
    condition = condition_text.lower()
    if "sunny" in condition or "clear" in condition:
        return "☀️"
    elif "cloud" in condition:
        return "☁️"
    elif "rain" in condition or "drizzle" in condition:
        return "🌧️"
    elif "thunder" in condition or "storm" in condition:
        return "⛈️"
    elif "snow" in condition:
        return "❄️"
    elif "fog" in condition or "mist" in condition:
        return "🌫️"
    elif "wind" in condition:
        return "💨"
    else:
        return "🌤️"

def format_complete_weather(data, city):
    if not data:
        return None
    
    try:
        current = data.get("current", {})
        location = data.get("location", {})
        forecast = data.get("forecast", {})
        
        # Location
        location_name = location.get("name", "N/A")
        location_region = location.get("region", "N/A")
        location_country = location.get("country", "N/A")
        location_lat = location.get("lat", "N/A")
        location_lon = location.get("lon", "N/A")
        location_time = location.get("localtime", "N/A")
        
        # Current weather
        temp_c = current.get("temp_c", "N/A")
        temp_f = current.get("temp_f", "N/A")
        feels_like_c = current.get("feelslike_c", "N/A")
        feels_like_f = current.get("feelslike_f", "N/A")
        
        condition = current.get("condition", {})
        condition_text = condition.get("text", "N/A")
        condition_emoji = get_weather_emoji(condition_text)
        
        humidity = current.get("humidity", "N/A")
        wind_kph = current.get("wind_kph", "N/A")
        wind_dir = current.get("wind_dir", "N/A")
        pressure_mb = current.get("pressure_mb", "N/A")
        precip_mm = current.get("precip_mm", "N/A")
        uv = current.get("uv", "N/A")
        visibility_km = current.get("vis_km", "N/A")
        cloud = current.get("cloud", "N/A")
        
        # Air Quality
        air_quality = current.get("air_quality", {})
        aqi_us = air_quality.get("us-epa-index", "N/A")
        aqi_category = get_air_quality_category(aqi_us) if aqi_us != "N/A" else "N/A"
        pm25 = air_quality.get("pm2_5", "N/A")
        pm10 = air_quality.get("pm10", "N/A")
        
        # Forecast - 3 days
        forecast_days = []
        forecast_data = forecast.get("forecastday", [])
        
        for day in forecast_data:
            day_data = day.get("day", {})
            astro = day.get("astro", {})
            date = day.get("date", "N/A")
            
            day_condition = day_data.get("condition", {})
            day_condition_text = day_condition.get("text", "N/A")
            day_condition_emoji = get_weather_emoji(day_condition_text)
            
            forecast_days.append({
                "date": date,
                "day": datetime.strptime(date, "%Y-%m-%d").strftime("%A") if date != "N/A" else "N/A",
                "max_temp": f"{day_data.get('maxtemp_c', 'N/A')}°C",
                "min_temp": f"{day_data.get('mintemp_c', 'N/A')}°C",
                "condition": day_condition_text,
                "emoji": day_condition_emoji,
                "humidity": f"{day_data.get('avghumidity', 'N/A')}%",
                "wind": f"{day_data.get('maxwind_kph', 'N/A')} km/h",
                "precip": f"{day_data.get('totalprecip_mm', 'N/A')} mm",
                "sunrise": astro.get("sunrise", "N/A"),
                "sunset": astro.get("sunset", "N/A")
            })
        
        return {
            "status": "success",
            "location": {
                "name": location_name,
                "region": location_region,
                "country": location_country,
                "latitude": location_lat,
                "longitude": location_lon,
                "local_time": location_time
            },
            "current": {
                "temperature": f"{temp_c}°C ({temp_f}°F)",
                "feels_like": f"{feels_like_c}°C ({feels_like_f}°F)",
                "condition": f"{condition_emoji} {condition_text}",
                "humidity": f"{humidity}%",
                "wind": f"{wind_kph} km/h {wind_dir}",
                "pressure": f"{pressure_mb} mb",
                "precipitation": f"{precip_mm} mm",
                "uv_index": uv,
                "visibility": f"{visibility_km} km",
                "cloud_cover": f"{cloud}%"
            },
            "air_quality": {
                "aqi": aqi_us,
                "category": aqi_category,
                "pm2.5": pm25,
                "pm10": pm10
            },
            "forecast": forecast_days,
            "credit": {
                "username": "@KINGFFAIAK47x",
                "made_by": "ANSH AFT"
            }
        }
        
    except Exception as e:
        return None

def format_current_weather(data, city):
    if not data:
        return None
    
    try:
        current = data.get("current", {})
        location = data.get("location", {})
        condition = current.get("condition", {})
        air_quality = current.get("air_quality", {})
        
        aqi_us = air_quality.get("us-epa-index", "N/A")
        aqi_category = get_air_quality_category(aqi_us) if aqi_us != "N/A" else "N/A"
        condition_emoji = get_weather_emoji(condition.get("text", ""))
        
        return {
            "status": "success",
            "location": {
                "name": location.get("name", "N/A"),
                "region": location.get("region", "N/A"),
                "country": location.get("country", "N/A"),
                "local_time": location.get("localtime", "N/A")
            },
            "current": {
                "temperature": f"{current.get('temp_c', 'N/A')}°C ({current.get('temp_f', 'N/A')}°F)",
                "feels_like": f"{current.get('feelslike_c', 'N/A')}°C ({current.get('feelslike_f', 'N/A')}°F)",
                "condition": f"{condition_emoji} {condition.get('text', 'N/A')}",
                "humidity": f"{current.get('humidity', 'N/A')}%",
                "wind": f"{current.get('wind_kph', 'N/A')} km/h {current.get('wind_dir', 'N/A')}",
                "uv_index": current.get("uv", "N/A"),
                "cloud_cover": f"{current.get('cloud', 'N/A')}%",
                "precipitation": f"{current.get('precip_mm', 'N/A')} mm",
                "pressure": f"{current.get('pressure_mb', 'N/A')} mb",
                "visibility": f"{current.get('vis_km', 'N/A')} km"
            },
            "air_quality": {
                "aqi": aqi_us,
                "category": aqi_category,
                "pm2.5": air_quality.get("pm2_5", "N/A"),
                "pm10": air_quality.get("pm10", "N/A")
            },
            "credit": {
                "username": "@KINGFFAIAK47x",
                "made_by": "ANSH AFT"
            }
        }
        
    except Exception as e:
        return None

# ==============================================
# 🏠 HOME
# ==============================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "name": "🌤️ WEATHER API",
        "version": "3.0",
        "description": "Get weather data with 3-day forecast",
        "endpoints": {
            "/weather": {
                "method": "GET",
                "description": "Complete weather + 3-day forecast + AQI",
                "example": "/weather?key=YOUR_KEY&city=Delhi"
            },
            "/weather/current": {
                "method": "GET",
                "description": "Current weather only",
                "example": "/weather/current?key=YOUR_KEY&city=Mumbai"
            }
        },
        "credit": {
            "username": "@KINGFFAIAK47x",
            "made_by": "ANSH AFT"
        }
    })

# ==============================================
# 🌤️ COMPLETE WEATHER
# ==============================================

@app.route('/weather', methods=['GET'])
@require_api_key
def get_complete_weather():
    city = request.args.get('city', '').strip()
    city = AdvancedValidator.sanitize_input(city)
    
    if not city:
        return jsonify({
            "status": "error",
            "error_code": "MISSING_CITY",
            "message": "Please provide a city name",
            "usage": "/weather?key=YOUR_KEY&city=Delhi",
            "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
        }), 400
    
    is_valid, error_msg = AdvancedValidator.validate_city(city)
    
    if not is_valid:
        return jsonify({
            "status": "error",
            "error_code": "INVALID_CITY",
            "message": error_msg,
            "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
        }), 400
    
    start_time = time.time()
    data, error = fetch_weather_data(city)
    response_time = round((time.time() - start_time) * 1000, 2)
    
    if error:
        return jsonify({
            "status": "error",
            "error_code": "WEATHER_FETCH_ERROR",
            "message": error,
            "city": city,
            "response_time": f"{response_time}ms",
            "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
        }), 404
    
    if data:
        formatted_data = format_complete_weather(data, city)
        if formatted_data:
            formatted_data["response_time"] = f"{response_time}ms"
            return jsonify(formatted_data), 200
    
    return jsonify({
        "status": "error",
        "message": "No weather data found",
        "city": city,
        "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
    }), 404

# ==============================================
# 🌤️ CURRENT WEATHER
# ==============================================

@app.route('/weather/current', methods=['GET'])
@require_api_key
def get_current_weather():
    city = request.args.get('city', '').strip()
    city = AdvancedValidator.sanitize_input(city)
    
    if not city:
        return jsonify({
            "status": "error",
            "error_code": "MISSING_CITY",
            "message": "Please provide a city name",
            "usage": "/weather/current?key=YOUR_KEY&city=Mumbai",
            "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
        }), 400
    
    is_valid, error_msg = AdvancedValidator.validate_city(city)
    
    if not is_valid:
        return jsonify({
            "status": "error",
            "error_code": "INVALID_CITY",
            "message": error_msg,
            "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
        }), 400
    
    start_time = time.time()
    data, error = fetch_weather_data(city)
    response_time = round((time.time() - start_time) * 1000, 2)
    
    if error:
        return jsonify({
            "status": "error",
            "error_code": "WEATHER_FETCH_ERROR",
            "message": error,
            "city": city,
            "response_time": f"{response_time}ms",
            "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
        }), 404
    
    if data:
        formatted_data = format_current_weather(data, city)
        if formatted_data:
            formatted_data["response_time"] = f"{response_time}ms"
            return jsonify(formatted_data), 200
    
    return jsonify({
        "status": "error",
        "message": "No weather data found",
        "city": city,
        "credit": {"username": "@KINGFFAIAK47x", "made_by": "ANSH AFT"}
    }), 404

# ==============================================
# 🚀 MAIN
# ==============================================

if __name__ == "__main__":
    print("🌤️ WEATHER API STARTED")
    print("=" * 40)
    print("📌 Server: http://localhost:5000")
    print("📌 /weather?key=LEAK&city=Delhi")
    print("📌 /weather/current?key=LEAK&city=Mumbai")
    print("=" * 40)
    app.run(debug=True, host='0.0.0.0', port=5000)
