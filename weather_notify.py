import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pytz import timezone, utc

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

# Fixed target hours
TARGET_HOURS = [9, 12, 15, 18, 21, 0]
paris_tz = timezone("Europe/Paris")

# --- FETCH FUNCTIONS ---

def get_openweather_forecast(lat, lon):
    """Fetch tomorrow's forecast (3-hour intervals) from OpenWeather, convert UTC→Paris, include midnight next day."""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    data = requests.get(url).json()

    if "list" not in data:
        print("OpenWeather API error:", data)
        return []

    tomorrow = (datetime.now(paris_tz) + timedelta(days=1)).date()
    day_after = tomorrow + timedelta(days=1)
    forecasts = []

    for item in data["list"]:
        # Convert UTC to Paris time
        dt_utc = datetime.utcfromtimestamp(item["dt"])
        dt_local = utc.localize(dt_utc).astimezone(paris_tz)

        # Include tomorrow’s data OR midnight of next day
        if (dt_local.date() == tomorrow and dt_local.hour in TARGET_HOURS) or (
            dt_local.date() == day_after and dt_local.hour == 0
        ):
            temp = item["main"]["temp"]
            rain = item.get("pop", 0) * 100  # Probability of precipitation
            forecasts.append((dt_local, temp, rain))

    # Debug
    print(f"\n--- DEBUG: OpenWeather data ---")
    for t in forecasts:
        print(f"{t[0]} Temp: {t[1]} Rain: {t[2]}")

    return forecasts


def get_weatherapi_forecast(city_name):
    """Fetch tomorrow's forecast (hourly) from WeatherAPI, include midnight next day, align with target hours."""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city_name}&days=2&aqi=no&alerts=no"
    data = requests.get(url).json()

    if "forecast" not in data:
        print("WeatherAPI error:", data)
        return []

    tomorrow = (datetime.now(paris_tz) + timedelta(days=1)).date()
    day_after = tomorrow + timedelta(days=1)
    forecasts = []

    # Process tomorrow
    for hour in data["forecast"]["forecastday"][1]["hour"]:
        dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
        dt = paris_tz.localize(dt)

        # Include tomorrow’s hours or midnight of next day
        if (dt.date() == tomorrow and dt.hour in TARGET_HOURS) or (
            dt.date() == day_after and dt.hour == 0
        ):
            temp = hour["temp_c"]
            rain = hour["chance_of_rain"]
            forecasts.append((dt, temp, rain))

    # Debug
    print(f"\n--- DEBUG: WeatherAPI data ---")
    for t in forecasts:
        print(f"{t[0]} Temp: {t[1]} Rain: {t[2]}")

    return forecasts

# --- GRAPHING & NOTIFICATIONS ---

def plot_comparison(city, owm_data, wa_data):
    """Plot comparison graph for temps and rain probabilities with fixed tick spacing and bold avg annotations."""
    # Extract fields
    times = [t[0] for t in owm_data]  # aligned hours
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [max(0, t[2]) for t in owm_data]
    temps_wa = [t[1] for t in wa_data]
    rains_wa = [max(0, t[2]) for t in wa_data]

    # Average temp line
    avg_temp_line = [(a + b) / 2 for a, b in zip(temps_owm, temps_wa)]

    # Plot
    fig, ax1 = plt.subplots(figsize=(8, 4))

    # Temperature lines
    ax1.plot(times, temps_owm, label="Temp OWM", color="red", marker='o')
    ax1.plot(times, temps_wa, label="Temp WeatherAPI", color="orange", linestyle="--", marker='o')
    ax1.plot(times, avg_temp_line, label="Avg Temp", color="black", linestyle=":", marker='o')

    ax1.set_ylabel("Temperature (°C)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    # Rain probability lines (secondary axis)
    ax2 = ax1.twinx()
    ax2.plot(times, rains_owm, label="Rain% OWM", color="cyan", linestyle="-.", marker='o')
    ax2.plot(times, rains_wa, label="Rain% WeatherAPI", color="blue", linestyle=":", marker='o')
    ax2.set_ylabel("Rain Probability (%)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")
    ax2.set_ylim(0, 100)  # fixed 0–100%

    # X-axis fixed labels
    ax1.set_xticks(times)
    ax1.set_xticklabels(["09", "12", "15", "18", "21", "00"])

    # Bold annotations at 15 & 21
    for target_hour in [15, 21]:
        if any(t.hour == target_hour for t in times):
            idx = next(i for i, t in enumerate(times) if t.hour == target_hour)
            ax1.annotate(
                f"{avg_temp_line[idx]:.1f}°C",
                (times[idx], avg_temp_line[idx]),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center',
                fontsize=12,
                fontweight='bold',
                color="black"
            )

    # Title & layout
    fig.suptitle(f"{city} Tomorrow – Temp & Rain", fontsize=12)
    fig.tight_layout()

    filename = f"{city.lower()}_comparison.png"
    plt.savefig(filename)
    plt.close()
    return filename

# --- Summary + Pushover ---

def weather_to_emoji(condition):
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
    if avg_rain > 30:
        condition = "rain"
    elif avg_rain > 5:
        condition = "cloud"
    else:
        condition = "clear"

    emoji = weather_to_emoji(condition)

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

        # Averages
        avg_temp = (sum(temps_owm) / len(temps_owm) + sum(temps_wa) / len(temps_wa)) / 2
        avg_rain = (sum(rain_owm) / len(rain_owm) + sum(rain_wa) / len(rain_wa)) / 2

        # High/low
        high_temp = max(max(temps_owm), max(temps_wa))
        low_temp = min(min(temps_owm), min(temps_wa))

        # Ranges
        temp_range = abs((sum(temps_owm) / len(temps_owm)) - (sum(temps_wa) / len(temps_wa)))
        rain_range = abs((sum(rain_owm) / len(rain_owm)) - (sum(rain_wa) / len(rain_wa)))

        # Build summary
        message = create_summary(city, avg_temp, avg_rain, high_temp, low_temp, temp_range, rain_range)

        # Graph & push
        graph_file = plot_comparison(city, owm_data, wa_data)
        send_pushover(message, graph_file)

if __name__ == "__main__":
    main()
