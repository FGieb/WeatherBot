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
    """Improved plot: simplified times (10,13,16), avg line, high/low markers"""
    import matplotlib.dates as mdates
    import numpy as np

    # --- Filter 10:00–16:00 ---
    valid_hours = [10, 13, 16]
    owm_data = [d for d in owm_data if d[0].hour in valid_hours]
    wa_data = [d for d in wa_data if d[0].hour in valid_hours]

    # --- Extract data ---
    times_owm = [t[0] for t in owm_data]
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [min(100, max(0, t[2])) for t in owm_data]

    times_wa = [t[0] for t in wa_data]
    temps_wa = [t[1] for t in wa_data]
    rains_wa = [min(100, max(0, t[2])) for t in wa_data]

    # --- Create figure ---
    fig, ax1 = plt.subplots(figsize=(7, 3))

    # Temperature lines
    ax1.plot(times_owm, temps_owm, label="Temp OWM", color="red", linewidth=2)
    ax1.plot(times_wa, temps_wa, label="Temp WeatherAPI", color="orange", linestyle="--", linewidth=2)
    ax1.set_ylabel("Temperature (°C)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    # Average temperature line
    all_temps = temps_owm + temps_wa
    if all_temps:
        avg_temp = np.mean(all_temps)
        ax1.axhline(avg_temp, color="black", linestyle=":", linewidth=1)
        ax1.text(times_owm[0], avg_temp + 0.5, f"Avg {avg_temp:.1f}°C", color="black", fontsize=8)

        # Highlight high & low
        max_temp = max(all_temps)
        min_temp = min(all_temps)
        max_time = (times_owm + times_wa)[all_temps.index(max_temp)]
        min_time = (times_owm + times_wa)[all_temps.index(min_temp)]
        ax1.scatter(max_time, max_temp, color="red")
        ax1.text(max_time, max_temp + 0.5, f"{max_temp:.0f}°C", fontsize=8, color="red")
        ax1.scatter(min_time, min_temp, color="blue")
        ax1.text(min_time, min_temp - 1, f"{min_temp:.0f}°C", fontsize=8, color="blue")

        ax1.set_ylim(min_temp - 2, max_temp + 2)

    # Rain bars (right axis)
    ax2 = ax1.twinx()
    width = 0.04
    ax2.bar([t - timedelta(minutes=20) for t in times_owm], rains_owm, width=0.04,
            label="Rain% OWM", color="blue", alpha=0.3)
    ax2.bar([t + timedelta(minutes=20) for t in times_wa], rains_wa, width=0.04,
            label="Rain% WeatherAPI", color="cyan", alpha=0.3)
    ax2.set_ylabel("Rain Probability (%)", color="blue")
    ax2.set_ylim(0, 100)
    ax2.tick_params(axis="y", labelcolor="blue")

    # X-axis formatting (only 10, 13, 16)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.set_xticks(times_owm)  # Will only have 3 ticks
    plt.xticks(rotation=0)

    # Title & layout
    plt.title(f"{city} Tomorrow – Temp & Rain")
    fig.tight_layout(pad=0.5)

    # Combine legends
    lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    ax1.legend(lines, labels, loc="upper left", fontsize=8)

    filename = f"{city.lower()}_comparison.png"
    plt.savefig(filename)
    plt.close(fig)

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
