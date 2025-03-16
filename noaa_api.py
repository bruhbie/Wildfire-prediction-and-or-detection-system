import requests
import json
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_noaa_forecast_data(latitude, longitude):
    """Retrieves relevant NOAA forecast data (temperature and wind speed)."""
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
            wind_speed = period.get('windSpeed', "0 mph")
            wind_speed_value = int(wind_speed.split()[0]) if wind_speed.split()[0].isdigit() else 0

            if temp is not None:
                relevant_data.append({
                    'temperature': temp,
                    'wind_speed': wind_speed_value,
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
    
    
def get_noaa_forecast(latitude, longitude):
    """ Retrieves and displays the NOAA forecast with humidity, oxygen, and other weather aspects """
    try:
        points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        points_response = requests.get(points_url)
        points_response.raise_for_status()
        points_data = points_response.json()

        forecast_url = points_data['properties']['forecast']
        forecast_hourly_url = points_data['properties']['forecastHourly']
        observation_stations_url = points_data['properties']['observationStations']

        forecast_data = requests.get(forecast_url).json()
        forecast_hourly_data = requests.get(forecast_hourly_url).json()
        observation_stations_data = requests.get(observation_stations_url).json()

        latest_observation_url = observation_stations_data['features'][0]['id'] + '/observations/latest'
        latest_observation_data = requests.get(latest_observation_url).json()

        display_forecast(forecast_data)
        display_hourly_forecast(forecast_hourly_data)
        display_latest_observations(latest_observation_data)

        relevant_data = get_noaa_forecast_data(latitude, longitude)
        if relevant_data:
            print("\nRelevant NOAA Data (Next 12 Hours):")
            for item in relevant_data:
                print(f"  Temperature: {item['temperature']}, Wind Speed: {item['wind_speed']}, Humidity: {item['humidity']}%")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching NOAA data: {e}")
    except KeyError as e:
        logging.error(f"Error parsing NOAA data: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


def display_forecast(forecast_data):
    print("\nHourly NOAA Forecast:")
    for period in forecast_data['properties']['periods']:
        print(f"  {period['name']}: {period['shortForecast']}")
        print(f"    Temperature: {period['temperature']} {period['temperatureUnit']}")
        print(f"    Wind: {period['windSpeed']} {period['windDirection']}")
        if 'relativeHumidity' in period:
            print(f"    Humidity: {period['relativeHumidity']['value']}%")
        print("-" * 20)

def display_hourly_forecast(forecast_hourly_data):
    print("\nHourly NOAA Forecast:")
    for period in forecast_hourly_data['properties']['periods'][0:12]:
        start_time = datetime.datetime.fromisoformat(period['startTime'].replace('Z', '+00:00'))
        print(f"  {start_time.strftime('%Y-%m-%d %H:%M')}: {period['shortForecast']}")
        print(f"    Temperature: {period['temperature']} {period['temperatureUnit']}")
        print(f"    Wind: {period['windSpeed']} {period['windDirection']}")
        if 'relativeHumidity' in period:
            print(f"    Humidity: {period['relativeHumidity']['value']}%")
        print("-" * 20)


def display_latest_observations(latest_observation_data):
    print("\nLatest Observations:")
    if 'properties' in latest_observation_data and latest_observation_data['properties']:
        properties = latest_observation_data['properties']
        if 'temperature' in properties and properties['temperature']:
            print(f"  Temperature: {properties['temperature']['value']} {properties['temperature']['unitCode']}")
        if 'relativeHumidity' in properties and properties['relativeHumidity']:
            print(f"  Humidity: {properties['relativeHumidity']['value']}%")
        if 'windSpeed' in properties and properties['windSpeed']:
            print(f"  Wind Speed: {properties['windSpeed']['value']} {properties['windSpeed']['unitCode']}")
        if 'windDirection' in properties and properties['windDirection']:
            print(f"  Wind Direction: {properties['windDirection']['value']} degrees")
        if 'barometricPressure' in properties and properties['barometricPressure']:
            print(f"  Barometric Pressure: {properties['barometricPressure']['value']} {properties['barometricPressure']['unitCode']}")
        if 'dewpoint' in properties and properties['dewpoint']:
            print(f"  Dewpoint: {properties['dewpoint']['value']} {properties['dewpoint']['unitCode']}")
    else:
        print("No latest observation data available.")
