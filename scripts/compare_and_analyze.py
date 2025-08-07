import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

# --- Load environment and initialize OpenAI client ---
load_dotenv("weather.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

CITIES = ["Brussels", "Paris"]

def load_forecast(city):
    with open(f"docs/{city.lower()}_forecast.json") as f:
        return json.load(f)

# --- SCRAPERS ---

def scrape_forecast_yr(city):
    if city.lower() == "brussels":
        url = "https://www.yr.no/en/forecast/daily-table/2-2800866/Belgium/Brussels-Capital/Brussels"
    elif city.lower() == "paris":
        url = "https://www.yr.no/en/forecast/daily-table/2-2988507/France/Île-de-France/Paris"
    else:
        return "Unsupported city"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        forecast_block = soup.find("table")
        return forecast_block.text.strip()[:1000] if forecast_block else "Could not extract data from YR.no"
    except Exception as e:
        return f"Error scraping YR.no: {e}"

def scrape_forecast_knmi(city):
    if city.lower() in ["brussels", "paris"]:
        return f"KNMI does not cover {city}."
    url = "https://www.knmi.nl/nederland-nu/weer/verwachtingen"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        forecast_block = soup.find("div", class_="content")
        return forecast_block.text.strip()[:1000] if forecast_block else "Could not extract data from KNMI"
    except Exception as e:
        return f"Error scraping KNMI: {e}"

def scrape_forecast_meteoblue(city):
    if city.lower() == "brussels":
        url = "https://www.meteoblue.com/en/weather/week/brussels_belgium_2800866"
    elif city.lower() == "paris":
        url = "https://www.meteoblue.com/en/weather/week/paris_france_2988507"
    else:
        return "Unsupported city"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        text_block = soup.find("div", class_="tab-content")
        return text_block.text.strip()[:1000] if text_block else "Could not extract data from Meteoblue"
    except Exception as e:
        return f"Error scraping Meteoblue: {e}"

# --- GPT ANALYSIS ---

def analyze_with_chatgpt(city, summary, yr, knmi, meteoblue):
    prompt = f"""
You are a weather analyst AI assistant. You are given the forecast summary below for {city}, based on API data from OpenWeatherMap and WeatherAPI:

{summary}

You also have access to forecast data scraped from the following sites:
- YR.no: {yr}
- KNMI: {knmi}
- Meteoblue: {meteoblue}

Your task is to:
1. Compare the original forecast summary with the scraped forecasts.
2. Identify any major discrepancies (e.g., big differences in temperature or rain).
3. Comment on how confident we should be in the original forecast.
4. Keep the tone professional, but feel free to be playfully cautious if you spot something strange.
5. If the scraped data significantly disagrees with the original forecast, include a ⚠️ warning at the top.

Return only your final assessment paragraph.
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# --- MAIN ---

def main():
    for city in CITIES:
        try:
            forecast = load_forecast(city)
            summary = forecast.get("summary", "")

            yr = scrape_forecast_yr(city)
            knmi = scrape_forecast_knmi(city)
            meteoblue = scrape_forecast_meteoblue(city)

            gpt_comment = analyze_with_chatgpt(city, summary, yr, knmi, meteoblue)
            forecast["gpt_comment"] = gpt_comment

            with open(f"docs/{city.lower()}_forecast.json", "w") as f:
                json.dump(forecast, f, indent=2)

            print(f"✅ Updated {city} forecast with GPT comment.")
        except Exception as e:
            print(f"❌ Error updating {city}: {e}")

if __name__ == "__main__":
    main()