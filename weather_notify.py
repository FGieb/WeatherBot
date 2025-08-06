import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("weather.env")

# Get API keys
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHERAPI_API_KEY = os.getenv("WEATHERAPI_API_KEY")

# Locations: Brussels & Paris
CITIES = {
    "Brussels": {"lat": 50.8503, "lon": 4.3517},
    "Paris": {"lat": 48.8566, "lon": 2.3522}
}

# --- FETCH FUNCTIONS ---

def get_openweather_forecast(lat, lon):
    """Fetch tomorrow's forecast (3-hour intervals) from OpenWeather (free forecast API)"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    data = requests.get(url).json()

    # Handle errors
    if "list" not in data:
        print("OpenWeather API error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    forecasts = []

    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        if dt.date() == tomorrow:
            temp = item["main"]["temp"]
            rain = item.get("pop", 0) * 100  # Probability of precipitation
            forecasts.append((dt, temp, rain))

    return forecasts


def get_weatherapi_forecast(city_name):
    """Fetch tomorrow's forecast (hourly) from WeatherAPI"""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city_name}&days=2&aqi=no&alerts=no"
    data = requests.get(url).json()

    if "forecast" not in data:
        print("WeatherAPI error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    forecasts = []

    for hour in data["forecast"]["forecastday"][1]["hour"]:
        dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
        temp = hour["temp_c"]
        rain = hour["chance_of_rain"]
        forecasts.append((dt, temp, rain))

    return forecasts

# --- GRAPHING & NOTIFICATIONS ---

def plot_comparison(city, owm_data, wa_data):
    """Plot comparison graph for temps and rain probabilities"""
    plt.figure(figsize=(8, 4))
    plt.title(f"Weather Comparison - {city} (Tomorrow)")

    # OpenWeather
    times_owm = [t[0] for t in owm_data]
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [t[2] for t in owm_data]

    # WeatherAPI
    times_wa = [t[0] for t in wa_data]
    temps_wa = [t[1] for t in wa_data]
    rains_wa = [t[2] for t in wa_data]

    # Plot temperature
    plt.plot(times_owm, temps_owm, label="Temp OWM", linestyle="-")
    plt.plot(times_wa, temps_wa, label="Temp WeatherAPI", linestyle="--")

    # Plot rain
    plt.plot(times_owm, rains_owm, label="Rain% OWM", linestyle=":")
    plt.plot(times_wa, rains_wa, label="Rain% WeatherAPI", linestyle="-.")

    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"{city.lower()}_comparison.png"
    plt.savefig(filename)
    plt.close()
    return filename

def weather_to_emoji(condition):
    """Convert basic condition keywords to emoji"""
    condition = condition.lower()
    if "rain" in condition:
        return "🌧️"
    elif "snow" in condition:
        return "❄️"
    elif "cloud" in condition:
        return "☁️"
    elif "clear" in condition:
        return "☀️"
    else:
        return "🌤️"

def create_summary(city_name, avg_temp, avg_rain, condition):
    """Format summary line with emoji and key metrics"""
    emoji = weather_to_emoji(condition)
    return f"{city_name}: {emoji} {avg_temp:.1f}°C, {avg_rain:.0f}% rain"


def send_pushover(message, image_path=None):
    """Send Pushover notification with optional image"""
    files = {}
    if image_path:
        files['attachment'] = ('image.png', open(image_path, 'rb'), 'image/png')
    response = requests.post("https://api.pushover.net/1/messages.json", data={
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "priority": 1,        # High priority (forces alert)
        "sound": "pushover"   # Optional: choose alert sound
    }, files=files)
    return response.json()


# --- MAIN SCRIPT ---

def main():
    for city in CITIES:
        # Fetch data
        owm_data = get_openweather_forecast(CITIES[city]["lat"], CITIES[city]["lon"])
        wa_data = get_weatherapi_forecast(city)

        # If either API fails, skip city
        if not owm_data or not wa_data:
            send_pushover(f"{city}: Weather data unavailable.")
            continue

        # Consensus summary
        avg_temp = (sum(t[1] for t in owm_data) / len(owm_data) + sum(t[1] for t in wa_data) / len(wa_data)) / 2
        avg_rain = (sum(t[2] for t in owm_data) / len(owm_data) + sum(t[2] for t in wa_data) / len(wa_data)) / 2

        message = (f"{city} tomorrow:\n"
                   f"Avg Temp: {avg_temp:.1f}°C\n"
                   f"Avg Rain: {avg_rain:.0f}% chance\n"
                   "See graph for details.")

        # Create graph
        graph_file = plot_comparison(city, owm_data, wa_data)

        # Send notification
        send_pushover(message, graph_file)


if __name__ == "__main__":
    main()
