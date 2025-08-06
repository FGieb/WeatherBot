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
    """Fetch tomorrow's forecast (interpolated hourly for 09–00) from OpenWeather"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    data = requests.get(url).json()

    if "list" not in data:
        print("OpenWeather API error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    points = []

    # Extract 3-hourly forecast for tomorrow
    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        if dt.date() == tomorrow:
            temp = item["main"]["temp"]
            rain = item.get("pop", 0) * 100
            points.append((dt, temp, rain))

    if not points:
        return []

    # Interpolate to desired hours: 09, 12, 15, 18, 21, 00
    target_hours = [9, 12, 15, 18, 21, 0]
    interpolated = []
    for h in target_hours:
        target_time = datetime.combine(tomorrow, datetime.min.time()) + timedelta(hours=h)
        # If direct match
        for pt in points:
            if pt[0].hour == h:
                interpolated.append((target_time, pt[1], pt[2]))
                break
        else:
            # Interpolate between closest 3-hour points
            before = max((p for p in points if p[0] <= target_time), default=points[0])
            after = min((p for p in points if p[0] >= target_time), default=points[-1])
            if before == after:
                temp = before[1]
                rain = before[2]
            else:
                ratio = (target_time - before[0]).total_seconds() / (after[0] - before[0]).total_seconds()
                temp = before[1] + (after[1] - before[1]) * ratio
                rain = before[2] + (after[2] - before[2]) * ratio
            interpolated.append((target_time, temp, rain))

    return interpolated


def get_weatherapi_forecast(city_name):
    """Fetch tomorrow's forecast (hourly) from WeatherAPI for 09–00"""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city_name}&days=2&aqi=no&alerts=no"
    data = requests.get(url).json()

    if "forecast" not in data:
        print("WeatherAPI error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    points = []

    # Extract hourly forecast for tomorrow
    for hour in data["forecast"]["forecastday"][1]["hour"]:
        dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
        if dt.date() == tomorrow and (dt.hour >= 9 or dt.hour == 0):
            points.append((dt, hour["temp_c"], hour["chance_of_rain"]))

    # Filter for target hours
    target_hours = [9, 12, 15, 18, 21, 0]
    filtered = [p for p in points if p[0].hour in target_hours]

    return filtered


# --- GRAPHING & NOTIFICATIONS ---

ddef plot_comparison(city, owm_data, wa_data):
    """Plot comparison graph with accurate times, 09–00, bold temps at 15 & 21"""
    import matplotlib.dates as mdates

    # Extract times & values
    times = [t[0] for t in owm_data]  # aligned to 09–00 already
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [max(0, t[2]) for t in owm_data]  # clamp negatives
    temps_wa = [t[1] for t in wa_data]
    rains_wa = [max(0, t[2]) for t in wa_data]

    avg_temp_line = [(a + b) / 2 for a, b in zip(temps_owm, temps_wa)]

    # Plot
    fig, ax1 = plt.subplots(figsize=(8, 4))

    # Temp lines
    ax1.plot(times, temps_owm, label="Temp OWM", color="red")
    ax1.plot(times, temps_wa, label="Temp WeatherAPI", color="orange", linestyle="--")
    ax1.plot(times, avg_temp_line, label="Avg Temp", color="black", linestyle=":")

    ax1.set_ylabel("Temperature (°C)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    # Rain lines (bottom axis)
    ax2 = ax1.twinx()
    ax2.plot(times, rains_owm, label="Rain% OWM", color="blue", linestyle="-.")
    ax2.plot(times, rains_wa, label="Rain% WeatherAPI", color="cyan", linestyle=":")
    ax2.set_ylabel("Rain Probability (%)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")
    ax2.set_ylim(0, 100)

    # X-axis formatting: fixed labels
    ax1.set_xticks(times)
    ax1.set_xticklabels(["9", "12", "15", "18", "21", "00"])

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
