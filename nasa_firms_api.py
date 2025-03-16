import requests
import folium
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

satellite = request.args.get('satellite', 'SV-C2')

# FIRMS API endpoint (for live fire data)
url = f'https://firms.modaps.eosdis.nasa.gov/api/fire/active?date={date}&satellite={satellite}&apiKey=93dbf5d44f179fcb7fba2f7cb38832be'

def fetch_live_fire_data():
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@app.route('/api/livefires', methods=['GET'])
def livefires():
    fire_data = fetch_live_fire_data(date, satellite)
    if fire_data is None:
        return jsonify({"error": "Failed to fetch live fire data"}), 400
    
    # Generate map with live fire data
    fire_map = generate_fire_map(fire_data['fires'])
    
    # Return the map as an HTML response
    return render_template_string(fire_map)


def generate_fire_map(fires):
    # Initialize the map (centered on the US)
    m = folium.Map(location=[37.0902, -95.7129], zoom_start=5)

    # Add markers for each fire
    for fire in fires:
        latitude = fire.get('latitude')
        longitude = fire.get('longitude')
        
        if latitude and longitude:
            folium.Marker(
                location=[latitude, longitude],
                popup=f"Brightness: {fire.get('brightness')}\nDate: {fire.get('acq_date')}",
                icon=folium.Icon(color='red', icon='fire')
            ).add_to(m)
    
    # Generate the HTML for the map
    return m._repr_html_()

# Run the app
if __name__ == '__main__':
    app.run(debug=True)