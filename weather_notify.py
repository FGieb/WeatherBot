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

# Target hours for forecast
TARGET_HOURS = [9, 12, 15, 18, 21, 0]

# --- FETCH FUNCTIONS ---

def get_openweather_forecast(lat, lon):
    """Fetch tomorrow's forecast (3-hour intervals) from OpenWeather"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    data = requests.get(url).json()

    if "list" not in data:
        print("OpenWeather API error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    points = []

    # Extract 3-hourly forecast for tomorrow at target hours
    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        if dt.date() == tomorrow and (dt.hour in TARGET_HOURS):
            temp = item["main"]["temp"]
            rain = item.get("pop", 0) * 100  # pop is 0–1 → convert to %
            points.append((dt, temp, rain))

    return points


def get_weatherapi_forecast(city_name):
    """Fetch tomorrow's forecast (hourly) from WeatherAPI for 09–00 target hours"""
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city_name}&days=2&aqi=no&alerts=no"
    data = requests.get(url).json()

    if "forecast" not in data:
        print("WeatherAPI error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    points = []

    # Extract hourly forecast for tomorrow and filter target hours
    for hour in data["forecast"]["forecastday"][1]["hour"]:
        dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
        if dt.date() == tomorrow and (dt.hour in TARGET_HOURS):
            temp = hour["temp_c"]
            rain = float(hour["chance_of_rain"])  # already %
            points.append((dt, temp, rain))

    return points


# --- GRAPHING & NOTIFICATIONS ---

def plot_comparison(city, owm_data, wa_data):
    """
    Plot comparison graph with evenly spaced hours (09–00) and bold annotations at 15:00 and 21:00.
    """

    # Fixed target labels
    hours_labels = ["09", "12", "15", "18", "21", "00"]

    # Sort and ensure data only contains target hours
    owm_data = sorted([d for d in owm_data if d[0].hour in TARGET_HOURS], key=lambda x: x[0])
    wa_data = sorted([d for d in wa_data if d[0].hour in TARGET_HOURS], key=lambda x: x[0])

    # Extract temperatures and rain
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [t[2] for t in owm_data]

    temps_wa = [t[1] for t in wa_data]
    rains_wa = [t[2] for t in wa_data]

    # Average line
    avg_temp_line = [(a + b) / 2 for a, b in zip(temps_owm, temps_wa)]

    # Use simple indices for equal spacing
    x = range(len(hours_labels))  # 0 to 5

    # --- Plot ---
    fig, ax1 = plt.subplots(figsize=(8, 4))

    # Temperature lines
    ax1.plot(x, temps_owm, label="Temp OWM", color="red", linestyle="-", marker="o")
    ax1.plot(x, temps_wa, label="Temp WeatherAPI", color="orange", linestyle="--", marker="o")
    ax1.plot(x, avg_temp_line, label="Avg Temp", color="black", linestyle=":", marker="o")

    ax1.set_ylabel("Temperature (°C)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    # Rain probability lines (secondary axis)
    ax2 = ax1.twinx()
    ax2.plot(x, rains_owm, label="Rain% OWM", color="cyan", linestyle="-", marker="o")
    ax2.plot(x, rains_wa, label="Rain% WeatherAPI", color="blue", linestyle="-.", marker="o")
    ax2.set_ylabel("Rain Probability (%)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")
    ax2.set_ylim(0, 100)

    # X-axis: equal spacing with labels
    ax1.set_xticks(x)
    ax1.set_xticklabels(hours_labels)

    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="upper left")

    # Bold annotations at 15 (index 2) and 21 (index 4)
    for idx in [2, 4]:
        ax1.annotate(
            f"{avg_temp_line[idx]:.1f}°C",
            (x[idx], avg_temp_line[idx]),
            textcoords="offset points",
            xytext=(0, 12),
            ha='center',
            fontsize=11,
            fontweight='bold',
            color="black"
        )

    # Title and layout
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

        # --- DEBUG: Print timestamps and values to check alignment ---
        print(f"\n--- DEBUG: OpenWeather data for {city} ---")
        for t in owm_data:
            print(t[0], "Temp:", t[1], "Rain:", t[2])

        print(f"\n--- DEBUG: WeatherAPI data for {city} ---")
        for t in wa_data:
            print(t[0], "Temp:", t[1], "Rain:", t[2])
        # ------------------------------------------------------------

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
