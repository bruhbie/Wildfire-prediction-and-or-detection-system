import smtplib
from email.mime.text import MIMEText
import requests
import json
import logging
from fire_risk_calculator import evaluate_fire_risk  # Corrected import
from flask import Flask, request, jsonify  # Corrected Flask import

# Creates diary/memory
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

NO_REPLY_EMAIL = "emergancyfireriskalert@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_PASSWORD = "2016551585D"

app = Flask(__name__)  # Initialize Flask app

def send_email_alert(message, recipient_email):
    try:
        msg = MIMEText(message)
        msg['Subject'] = "Emergency Fire Risk Alert"  # Corrected subject
        msg['From'] = NO_REPLY_EMAIL  # Corrected variable name
        msg['To'] = recipient_email

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(NO_REPLY_EMAIL, SMTP_PASSWORD)
            server.sendmail(NO_REPLY_EMAIL, recipient_email, msg.as_string())
            logging.info(f"Alert email sent successfully to {recipient_email}.")
    except Exception as e:
        logging.error(f"Error sending alert email: {e}")

def get_noaa_forecast_data(latitude, longitude):
    try:
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        points_response = requests.get(points_url)
        points_response.raise_for_status()
        points_data = points_response.json()

        forecast_hourly_url = points_data['properties']['forecastHourly']
        forecast_hourly_data = requests.get(forecast_hourly_url).json()

        relevant_data = []
        for period in forecast_hourly_data['properties']['periods'][0:12]:
            temp = period.get('temperature')
            wind_speed = period.get('windSpeed')
            humidity = period.get('relativeHumidity', {}).get('value')
            if temp is not None and wind_speed is not None and humidity is not None:
                relevant_data.append({
                    'temperature': temp,
                    'wind_speed': wind_speed,
                    'humidity': humidity
                })
        return relevant_data

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching NOAA data: {e}")
        return None
    except KeyError as e:
        logging.error(f"Error parsing NOAA data: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return None

def check_and_alert(latitude, longitude, user_email):
    """Checks fire risk, sends alerts, and provides safety advice."""

    if latitude is None or longitude is None:
        logging.error("Latitude or Longitude not provided. Alerts cannot be sent.")
        return

    forecast_data = get_noaa_forecast_data(latitude, longitude)
    if forecast_data:
        risk_levels = evaluate_fire_risk(forecast_data)
        extreme_risk_found = False
        alert_message = "Emergency Fire Risk Alert:\n"

        for risk_data in risk_levels:
            if risk_data['fire_risk'] == "Extreme":
                extreme_risk_found = True
                alert_message += (f"Temperature: {risk_data['temperature']}, Wind Speed: {risk_data['wind_speed']}, Humidity: {risk_data['humidity']}%, Risk: Extreme\n")

        if extreme_risk_found:
            alert_message += "\nExtreme fire risk detected in your area. Immediate action is advised:\n"
            alert_message += "- Activate home sprinkler systems.\n"
            alert_message += "- Deploy firefighting foam if available.\n"
            alert_message += "- Evacuate the premises and proceed to a safer location.\n"
            alert_message += "- Stay informed about local emergency broadcasts.\n"
            send_email_alert(alert_message, user_email)
        else:
            logging.info("No extreme fire risk detected.")
    else:
        logging.error("Failed to retrieve forecast data. Alerts cannot be sent.")

@app.route('/send_fire_alert', methods=['POST'])
def send_fire_alert():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    user_email = data.get('user_email')

    if latitude is None or longitude is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400

    check_and_alert(latitude, longitude, user_email)
    return jsonify({'message': 'Alert process started'}), 200

@app.route('/weather', methods=['GET'])
def get_weather():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    data = get_noaa_forecast_data(lat, lon)
    if data and len(data) > 0:
        return jsonify({
            'temperature': data[0]['temperature'],
            'humidity': data[0]['humidity'],
            'wind_speed': data[0]['wind_speed']
        })
    else:
        return jsonify({'error': 'Could not fetch weather data'}), 500

@app.route('/calculate_fire_risk', methods=['POST'])
def calculate_fire_risk_endpoint():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    temp = data.get('temperature')
    humidity = data.get('humidity')
    wind_speed = data.get('wind_speed')

    weather_data = [{'temperature': temp, 'humidity': humidity, 'wind_speed': wind_speed}]
    risk_levels = evaluate_fire_risk(weather_data)

    if risk_levels and len(risk_levels) > 0:
        return jsonify({'fire_risk': risk_levels[0]['fire_risk']})
    else:
        return jsonify({'error': 'Could not calculate fire risk'}), 500

if __name__ == '__main__':
    app.run(debug=True)