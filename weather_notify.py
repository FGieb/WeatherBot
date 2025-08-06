import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Built-in timezone support
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

# Target hours we want in the graph
TARGET_HOURS = [9, 12, 15, 18, 21, 0]
TZ = ZoneInfo("Europe/Paris")  # Paris timezone (also Brussels/Amsterdam)

# --- FETCH FUNCTIONS ---

def get_openweather_forecast(lat, lon):
    """Fetch tomorrow's forecast (3-hour intervals) from OpenWeather"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    data = requests.get(url).json()

    if "list" not in data:
        print("OpenWeather API error:", data)
        return []

    tomorrow = (datetime.now(TZ) + timedelta(days=1)).date()
    forecasts = []

    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"], TZ)
        if dt.date() == tomorrow and (dt.hour in TARGET_HOURS):
            temp = item["main"]["temp"]
            rain = item.get("pop", 0) * 100
            forecasts.append((dt, temp, rain))

    return forecasts


def get_weatherapi_forecast(city_name):
    """Fetch tomorrow's forecast (hourly) from WeatherAPI, sampling every 3 hours to match OWM"""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city_name}&days=2&aqi=no&alerts=no"
    data = requests.get(url).json()

    if "forecast" not in data:
        print("WeatherAPI error:", data)
        return []

    tomorrow = (datetime.now(TZ) + timedelta(days=1)).date()
    forecasts = []

    for i, hour in enumerate(data["forecast"]["forecastday"][1]["hour"]):
        dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
        if dt.date() == tomorrow and (dt.hour in TARGET_HOURS):
            temp = hour["temp_c"]
            rain = hour["chance_of_rain"]
            forecasts.append((dt, temp, rain))

    return forecasts

# --- MIDNIGHT FALLBACK FIX ---

def ensure_midnight_point(owm_data, wa_data):
    """Ensure midnight (00:00) point is present, fallback if missing"""
    midnight_dt = datetime.combine((datetime.now(TZ) + timedelta(days=1)).date(), datetime.min.time()).replace(tzinfo=TZ)

    # Check if 00:00 present
    owm_has_midnight = any(pt[0].hour == 0 for pt in owm_data)
    wa_has_midnight = any(pt[0].hour == 0 for pt in wa_data)

    if not owm_has_midnight and wa_has_midnight:
        # Copy WA midnight value to OWM
        wa_midnight = next(pt for pt in wa_data if pt[0].hour == 0)
        owm_data.append((midnight_dt, wa_midnight[1], wa_midnight[2]))
    elif not wa_has_midnight and owm_has_midnight:
        # Copy OWM midnight value to WA
        owm_midnight = next(pt for pt in owm_data if pt[0].hour == 0)
        wa_data.append((midnight_dt, owm_midnight[1], owm_midnight[2]))
    elif not owm_has_midnight and not wa_has_midnight:
        # Remove midnight from target if neither provides it
        owm_data = [pt for pt in owm_data if pt[0].hour != 0]
        wa_data = [pt for pt in wa_data if pt[0].hour != 0]

    # Sort by datetime to keep order
    owm_data.sort(key=lambda x: x[0])
    wa_data.sort(key=lambda x: x[0])

    return owm_data, wa_data

# --- GRAPHING & NOTIFICATIONS ---

def plot_comparison(city, owm_data, wa_data):
    """Plot accurate comparison graph for temps and rain probabilities"""
    import matplotlib.dates as mdates

    # Ensure midnight consistency
    owm_data, wa_data = ensure_midnight_point(owm_data, wa_data)

    # Separate fields
    times = [t[0] for t in owm_data]  # use OWM times as base
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [max(0, t[2]) for t in owm_data]  # clamp to 0
    temps_wa = [t[1] for t in wa_data]
    rains_wa = [max(0, t[2]) for t in wa_data]    # clamp to 0

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
    ax2.plot(times, rains_owm, label="Rain% OWM", color="cyan", linestyle="-.", marker='.')
    ax2.plot(times, rains_wa, label="Rain% WeatherAPI", color="blue", linestyle=":", marker='.')
    ax2.set_ylabel("Rain Probability (%)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")
    ax2.set_ylim(0, 100)  # force 0–100%

    # X-axis formatting (ensure fixed spacing)
    tick_hours = [9, 12, 15, 18, 21, 0]
    tick_labels = ["9", "12", "15", "18", "21", "00"]
    ax1.set_xticks([t for t in times if t.hour in tick_hours])
    ax1.set_xticklabels([tick_labels[tick_hours.index(t.hour)] for t in times if t.hour in tick_hours])

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

# --- SUMMARY + PUSH ---

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

        # Ensure midnight consistency
        owm_data, wa_data = ensure_midnight_point(owm_data, wa_data)

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
