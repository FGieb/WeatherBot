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

    if "list" not in data:
        print("OpenWeather API error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    forecasts = []

    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        # Only include 10:00 - 22:00
        if dt.date() == tomorrow and 10 <= dt.hour <= 22:
            temp = item["main"]["temp"]
            rain = item.get("pop", 0) * 100  # Probability of precipitation
            forecasts.append((dt, temp, rain))

    return forecasts


def get_weatherapi_forecast(city_name):
    """Fetch tomorrow's forecast (hourly) from WeatherAPI and sample every 3 hours to match OpenWeather"""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city_name}&days=2&aqi=no&alerts=no"
    data = requests.get(url).json()

    if "forecast" not in data:
        print("WeatherAPI error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    forecasts = []

    for i, hour in enumerate(data["forecast"]["forecastday"][1]["hour"]):
        dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
        # Only include 10:00 - 22:00 and every 3rd hour (align with OpenWeather)
        if dt.date() == tomorrow and 10 <= dt.hour <= 22 and i % 3 == 0:
            temp = hour["temp_c"]
            rain = hour["chance_of_rain"]
            forecasts.append((dt, temp, rain))

    return forecasts

# --- GRAPHING & NOTIFICATIONS ---

def plot_comparison(city, owm_data, wa_data):
    """Improved graph: clear times, rain baseline, average temp line, annotations."""
    import numpy as np

    # Extract data
    times = [t[0] for t in owm_data]  # assuming both APIs return same time intervals
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [t[2] for t in owm_data]
    temps_wa = [t[1] for t in wa_data]
    rains_wa = [t[2] for t in wa_data]

    # Average line for temperature
    avg_temp_line = [(o + w) / 2 for o, w in zip(temps_owm, temps_wa)]

    # Convert times to hour labels
    hours = [t.strftime("%H:%M") for t in times]

    plt.figure(figsize=(8, 4))
    plt.title(f"{city} Tomorrow – Temp & Rain")

    # Temperature axis
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.set_xlabel("Time")
    ax1.set_ylabel("Temperature (°C)", color="red")
    ax1.plot(hours, temps_owm, label="Temp OWM", color="red")
    ax1.plot(hours, temps_wa, label="Temp WeatherAPI", color="orange", linestyle="--")
    ax1.plot(hours, avg_temp_line, label=f"Avg Temp", color="black", linestyle=":")

    # Annotate two points (midday & evening)
    mid_idx = len(avg_temp_line) // 3  # around 1/3 into day
    eve_idx = (2 * len(avg_temp_line)) // 3  # around 2/3 into day
    ax1.annotate(f"{avg_temp_line[mid_idx]:.1f}°C", (mid_idx, avg_temp_line[mid_idx]),
                 textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8)
    ax1.annotate(f"{avg_temp_line[eve_idx]:.1f}°C", (eve_idx, avg_temp_line[eve_idx]),
                 textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8)

    ax1.tick_params(axis="y", labelcolor="red")

    # Rain probability axis
    ax2 = ax1.twinx()
    ax2.set_ylabel("Rain Probability (%)", color="blue")
    ax2.set_ylim(0, 100)  # Force 0–100 range
    ax2.plot(hours, rains_owm, label="Rain% OWM", color="blue", linestyle=":")
    ax2.plot(hours, rains_wa, label="Rain% WeatherAPI", color="cyan", linestyle="-.")

    ax2.tick_params(axis="y", labelcolor="blue")

    # X-axis ticks: show only 12, 15, 18, 21, 00
    tick_positions = [i for i, h in enumerate(hours) if h in ["12:00", "15:00", "18:00", "21:00", "00:00"]]
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels([hours[i] for i in tick_positions])

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

    plt.tight_layout()

    filename = f"{city.lower()}_comparison.png"
    plt.savefig(filename, dpi=120)
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

def create_summary(city_name, avg_temp, avg_rain, high_temp, low_temp, temp_range, rain_range):
    """Format summary line with emoji, avg, range, high/low, uncertainty flag"""
    # Determine emoji condition (simple logic based on rain)
    if avg_rain > 30:
        condition = "rain"
    elif avg_rain > 5:
        condition = "cloud"
    else:
        condition = "clear"

    emoji = weather_to_emoji(condition)

    # Flag uncertainty if APIs disagree significantly
    uncertainty_flag = ""
    if temp_range > 3 or rain_range > 20:
        uncertainty_flag = "⚠️ Forecast uncertain"

    summary = (
        f"{city_name}: {emoji} Avg {avg_temp:.1f}°C ({temp_range:.0f}°C range), {avg_rain:.0f}% rain ({rain_range:.0f}% range)\n"
        f"High {high_temp:.0f}°C / Low {low_temp:.0f}°C\n"
        f"{uncertainty_flag}"
    ).strip()

    return summary

def send_pushover(message, image_path=None):
    """Send Pushover notification with optional image"""
    files = {}
    if image_path:
        files['attachment'] = ('image.png', open(image_path, 'rb'), 'image/png')
    response = requests.post("https://api.pushover.net/1/messages.json", data={
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "priority": 1,
        "sound": "pushover"
    }, files=files)
    return response.json()

# --- MAIN SCRIPT ---

def main():
    for city in CITIES:
        # Fetch data
        owm_data = get_openweather_forecast(CITIES[city]["lat"], CITIES[city]["lon"])
        wa_data = get_weatherapi_forecast(city)

        if not owm_data or not wa_data:
            send_pushover(f"{city}: Weather data unavailable.")
            continue

        # Separate temps/rain for calculations
        temps_owm = [t[1] for t in owm_data]
        temps_wa = [t[1] for t in wa_data]
        rain_owm = [t[2] for t in owm_data]
        rain_wa = [t[2] for t in wa_data]

        # Averages (consensus)
        avg_temp = (sum(temps_owm) / len(temps_owm) + sum(temps_wa) / len(temps_wa)) / 2
        avg_rain = (sum(rain_owm) / len(rain_owm) + sum(rain_wa) / len(rain_wa)) / 2

        # High/low (daytime)
        high_temp = max(max(temps_owm), max(temps_wa))
        low_temp = min(min(temps_owm), min(temps_wa))

        # Ranges (API disagreement)
        temp_range = abs((sum(temps_owm) / len(temps_owm)) - (sum(temps_wa) / len(temps_wa)))
        rain_range = abs((sum(rain_owm) / len(rain_owm)) - (sum(rain_wa) / len(rain_wa)))

        # Build summary
        message = create_summary(city, avg_temp, avg_rain, high_temp, low_temp, temp_range, rain_range)

        # Graph & push
        graph_file = plot_comparison(city, owm_data, wa_data)
        send_pushover(message, graph_file)

if __name__ == "__main__":
    main()
