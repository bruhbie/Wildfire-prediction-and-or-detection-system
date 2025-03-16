from flask import Flask, request, jsonify, render_template
from noaa_api import get_noaa_forecast_data
from fire_risk_calculator import calculate_fire_risk, evaluate_fire_risk
import requests
from datetime import datetime
from google.cloud import translate_v2 as translate
import os
from language_api import language_bp
import pandas as pd
import folium


app = Flask(__name__)


app.config['GOOGLE_APPLICATION_CREDENTIALS'] = "credentials.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = app.config['GOOGLE_APPLICATION_CREDENTIALS']
app.translate_client = translate.Client()

app.register_blueprint(language_bp)

MAPS_FOLDER = os.getcwd()


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/weather', methods=['GET'])
def get_weather():
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    if not latitude or not longitude:
        return jsonify({'error': 'Missing latitude or longitude'}), 400

    weather_data = get_noaa_forecast_data(latitude, longitude)

    if not weather_data:
        return jsonify({'error': 'Failed to fetch weather data'}), 500

    return jsonify({
        'temperature': weather_data[0]['temperature'],
        'wind_speed': weather_data[0]['wind_speed']
    })

@app.route('/calculate_fire_risk', methods=['POST'])
def calculate_fire_risk_endpoint():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not latitude or not longitude:
        return jsonify({'Error': 'Latitude or longitude missing'}), 400

    fire_data = fetch_fires_from_nasa_firms(latitude, longitude)

    if fire_data:
        if fire_data:
            confidence_levels = []
            for fire in fire_data:
                confidence_levels.append(fire.get('confidence', 'No Confidence Data'))
            return jsonify({'confidence_levels': confidence_levels})
    else:
        return jsonify({'confidence_levels': ['No data']}), 500
        


#US Bounding Box coordinates
min_lon = -125.0 #Pacific Ocean
max_lat = 49.5  #Alaska
max_lon = -66.96  #Atlantic Ocean
min_lat = 25.0 #Florida

def generate_map(fire_data):
    m = folium.Map(location=[fire_data[0]['latitude'], fire_data[0]['longitude']], zoom_start=8)

    for fire in fire_data:
        folium.Marker(
            location=[fire['latitude'], fire['longitude']],
            popup=fire['location']
        ).add_to(m)

    map_file = 'live_fire_map.html'
    m.save(map_file)
    return map_file

@app.route('/index')
def index():

    date = datetime.today().strftime('%Y-%m-%d')  # Current device date
    response = requests.get(f'http://localhost:5000/api/livefires?date={date}')

    if response.status_code == 200:
        fire_data = response.json()['fire_data']
        live_map_html = generate_map(fire_data)  # Generate map for live fire data
    else:
        live_map_html = "Error fetching live fire data."

    return render_template('index.html', live_map_html=live_map_html)

# Route for past fires page
@app.route('/pastfires', methods=['GET', 'POST'])
def past_fires():
    if request.method == 'POST':
        # User-selected state and date for past fire data
        state = request.form['state']
        date = request.form['date']
    else:
     
        state = 'Massachusetts'  # Example default state
        date = datetime.today().strftime('%Y-%m-%d')

   
    past_fires_df = pd.read_csv('pastfiredata.csv')

    # Filter past fire data based on the selected date and state
    filtered_past_fires = past_fires_df[(past_fires_df['state'] == state) & (past_fires_df['date'] == date)]

    # Generate map for past fire data
    past_fire_data = []
    for _, row in filtered_past_fires.iterrows():
        past_fire_data.append({
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'location': row['location']
        })
    
    past_map_html = generate_map(past_fire_data)

    return render_template('past_fires.html', past_map_html=past_map_html, state=state, date=date)

# Categorize fire risk based on confidence level
def categorize_fire_risk(confidence):
    if confidence == 'high':
        return 'High'
    elif confidence == 'nominal':
        return 'Medium'
    else:
        return 'Low'


def get_weather_data_from_api(latitude, longitude):
    # Example: Replace with actual weather API call (like OpenWeatherMap)
    return {
        'temp': 30,  # in Celsius
        'humidity': 60,
        'wind_speed': 15  # km/h
    }


if __name__ == '__main__':
    app.run(debug=True)