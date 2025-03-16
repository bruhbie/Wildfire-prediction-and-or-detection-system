def calculate_fire_risk(temperature, wind_speed):
    """Calculates fire risk based on temperature and wind speed."""
    risk = "Low"
    if temperature > 35 and wind_speed > 25:  # Increased thresholds for higher accuracy
        risk = "High"
    elif temperature > 30 and wind_speed > 20:
        risk = "Medium"
    return risk

def evaluate_fire_risk(forecast_data):
    """Evaluates fire risk for a list of weather data."""
    fire_risk_levels = []
    for data in forecast_data:
        temperature = data['temperature']
        wind_speed = data['wind_speed']
        risk_level = calculate_fire_risk(temperature, wind_speed)
        fire_risk_levels.append({'temperature': temperature, 'wind_speed': wind_speed, 'fire_risk': risk_level})
    return fire_risk_levels