from flask import Flask, request, jsonify, render_template
import requests
import sys

# --- Flask & Open-Meteo Configuration ---
app = Flask(__name__)
AIR_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast" # For temperature

def get_single_location_data(lat, lon):
    """Fetches Air Quality and Temperature data for a single point."""
    
    # 1. AIR QUALITY PARAMETERS (CO, NO2, O3)
    air_params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["carbon_monoxide", "nitrogen_dioxide", "ozone"], 
        "domains": "cams_global",
        "timezone": "auto"
    }
    
    # 2. TEMPERATURE PARAMETERS
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m"],
        "temperature_unit": "fahrenheit",
        "timezone": "auto"
    }

    try:
        # Fetch Air Quality
        air_response = requests.get(AIR_API_URL, params=air_params)
        air_response.raise_for_status()
        air_data = air_response.json()

        # Fetch Temperature
        weather_response = requests.get(WEATHER_API_URL, params=weather_params)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        # Combine results
        air_current = air_data["current"]
        air_units = air_data["current_units"]
        weather_current = weather_data["current"]
        weather_units = weather_data["current_units"]

        return {
            'success': True,
            'latitude': lat,
            'longitude': lon,
            'timezone': air_data.get("timezone", "N/A"),
            # Gas Data
            'co': f"{air_current.get('carbon_monoxide')} {air_units.get('carbon_monoxide', 'N/A')}",
            'no2': f"{air_current.get('nitrogen_dioxide')} {air_units.get('nitrogen_dioxide', 'N/A')}",
            'o3': f"{air_current.get('ozone')} {air_units.get('ozone', 'N/A')}",
            # Temp Data
            'temp': f"{weather_current.get('temperature_2m')} {weather_units.get('temperature_2m', 'N/A')}",
        }

    except Exception as e:
        return {
            'success': False,
            'latitude': lat,
            'longitude': lon,
            'error': f"Failed to fetch data: {e}"
        }


@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/get_data', methods=['POST'])
def get_data_endpoint():
    """Endpoint to handle AJAX calls from the webpage for multiple points."""
    data = request.json
    coordinates_str = data.get('coordinates_str', '')
    
    # Example Input: "34.05,-118.24;40.71,-74.01"
    
    location_results = []
    
    try:
        # Parse the string of coordinates
        location_pairs = coordinates_str.split(';')
        for pair in location_pairs:
            if not pair.strip(): continue # Skip empty strings
            
            lat_str, lon_str = pair.split(',')
            lat = float(lat_str.strip())
            lon = float(lon_str.strip())
            
            # Fetch data for this specific location
            result = get_single_location_data(lat, lon)
            location_results.append(result)
            
        return jsonify({'success': True, 'results': location_results})

    except Exception as e:
        return jsonify({'success': False, 'error': f'Invalid coordinate format or processing error: {e}'}), 400

if __name__ == '__main__':
    # You must install Flask and requests: pip install flask requests
    # NOTE: Mapbox requires a token, but the globe will work without it.
    print("Running Flask app. Navigate to http://127.0.0.1:5000/")
    app.run(debug=True)