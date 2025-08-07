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
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={OPENWEATHER_API_KEY}"
    data = requests.get(url).json()

    if "list" not in data:
        print("OpenWeather API error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    forecasts = []
    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        if dt.date() == tomorrow and 9 <= dt.hour <= 21:
            temp = item["main"]["temp"]
            rain = item.get("pop", 0) * 100
            forecasts.append((dt, temp, rain))
    return forecasts

def get_weatherapi_forecast(city_name):
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHERAPI_API_KEY}&q={city_name}&days=2&aqi=no&alerts=no"
    data = requests.get(url).json()

    if "forecast" not in data:
        print("WeatherAPI error:", data)
        return []

    tomorrow = (datetime.now() + timedelta(days=1)).date()
    forecasts = []
    for i, hour in enumerate(data["forecast"]["forecastday"][1]["hour"]):
        dt = datetime.strptime(hour["time"], "%Y-%m-%d %H:%M")
        if dt.date() == tomorrow and 9 <= dt.hour <= 21 and i % 3 == 0:
            temp = hour["temp_c"]
            rain = hour["chance_of_rain"]
            forecasts.append((dt, temp, rain))
    return forecasts

# --- GRAPHING & NOTIFICATIONS ---

def plot_comparison(city, owm_data, wa_data):
    def filter_data(data):
        return [(t[0], t[1], t[2]) for t in data if 9 <= t[0].hour <= 21]

    owm_data = filter_data(owm_data)
    wa_data = filter_data(wa_data)

    times = [t[0] for t in owm_data]
    temps_owm = [t[1] for t in owm_data]
    rains_owm = [max(0, t[2]) for t in owm_data]
    temps_wa = [t[1] for t in wa_data]
    rains_wa = [max(0, t[2]) for t in wa_data]

    avg_temp_line = [(a + b) / 2 for a, b in zip(temps_owm, temps_wa)]

    fig, ax1 = plt.subplots(figsize=(8, 4))
    line_owm, = ax1.plot(times, temps_owm, label="Temp OWM", color="red")
    line_wa, = ax1.plot(times, temps_wa, label="Temp WeatherAPI", color="orange", linestyle="--")
    line_avg, = ax1.plot(times, avg_temp_line, label="Avg Temp", color="black", linestyle=":")

    ax1.set_ylabel("Temperature (°C)", color="red")
    ax1.tick_params(axis="y", labelcolor="red")

    ax2 = ax1.twinx()
    ax2.plot(times, rains_owm, color="blue", linestyle="-.")
    ax2.plot(times, rains_wa, color="cyan", linestyle=":")
    ax2.set_ylabel("Rain Probability (%)", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")
    ax2.set_ylim(0, 100)

    ax1.legend([line_owm, line_wa, line_avg], ["Temp OWM", "Temp WeatherAPI", "Avg Temp"], loc="upper left", fontsize=9)

    tick_hours = [9, 12, 15, 18, 21]
    tick_labels = ["9", "12", "15", "18", "21"]
    ax1.set_xticks([t for t in times if t.hour in tick_hours])
    ax1.set_xticklabels([tick_labels[tick_hours.index(t.hour)] for t in times if t.hour in tick_hours])

    for target_hour in [12, 18]:
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

    fig.suptitle(f"{city} Tomorrow – Day Forecast", fontsize=12)
    fig.tight_layout()

    filename = f"{city.lower()}_comparison.png"
    plt.savefig(filename)
    plt.close()
    return filename

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


def main():
    for city in CITIES:
        owm_data = get_openweather_forecast(CITIES[city]["lat"], CITIES[city]["lon"])
        wa_data = get_weatherapi_forecast(city)

        if not owm_data or not wa_data:
            print(f"{city}: Weather data unavailable.")
            continue

        temps_owm = [t[1] for t in owm_data]
        temps_wa = [t[1] for t in wa_data]
        rain_owm = [t[2] for t in owm_data]
        rain_wa = [t[2] for t in wa_data]

        avg_temp = (sum(temps_owm) / len(temps_owm) + sum(temps_wa) / len(temps_wa)) / 2
        avg_rain = (sum(rain_owm) / len(rain_owm) + sum(rain_wa) / len(rain_wa)) / 2
        high_temp = max(max(temps_owm), max(temps_wa))
        low_temp = min(min(temps_owm), min(temps_wa))
        temp_range = abs((sum(temps_owm) / len(temps_owm)) - (sum(temps_wa) / len(temps_wa)))
        rain_range = abs((sum(rain_owm) / len(rain_owm)) - (sum(rain_wa) / len(rain_wa)))

        message = create_summary(city, avg_temp, avg_rain, high_temp, low_temp, temp_range, rain_range)
        graph_file = plot_comparison(city, owm_data, wa_data)

               # Create summary and graph
        message = create_summary(city, avg_temp, avg_rain, high_temp, low_temp, temp_range, rain_range)
        graph_file = plot_comparison(city, owm_data, wa_data)

        # Prepare output JSON
        import json
        output = {
            "city": city,
            "avg_temp": avg_temp,
            "avg_rain": avg_rain,
            "high_temp": high_temp,
            "low_temp": low_temp,
            "temp_range": temp_range,
            "rain_range": rain_range,
            "summary": message,
            "graph_file": graph_file
        }

        # Save JSON to the 'docs' folder
        with open(f"docs/{city.lower()}_forecast.json", "w") as f:
            json.dump(output, f)

if __name__ == "__main__":
    main()

