import os
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("weather.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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
    except:
        return "Error scraping YR.no"

def scrape_forecast_knmi(city):
    if city.lower() == "brussels":
        return "KNMI does not cover Brussels."
    elif city.lower() == "paris":
        return "KNMI does not cover Paris."
    url = "https://www.knmi.nl/nederland-nu/weer/verwachtingen"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        forecast_block = soup.find("div", class_="content")
        return forecast_block.text.strip()[:1000] if forecast_block else "Could not extract data from KNMI"
    except:
        return "Error scraping KNMI"

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
    except:
        return "Error scraping Meteoblue"

# --- GPT ANALYSIS ---

def analyze_with_chatgpt(city, summary, yr, knmi, meteoblue):
    prompt = f"""
You are a weather analyst AI assistant. You are given the forecast summary below for {city}, based on API data from OpenWeatherMap and WeatherAPI:

SUMMARY:
{summary}

You are also given scraped textual forecasts for the same city from three external websites (YR.no, KNMI, Meteoblue). These sites may describe the forecast differently, in words rather than numbers.

EXTERNAL SOURCES:
- YR.no: {yr_forecast[:1000]}
- KNMI: {knmi_forecast[:1000]}
- Meteoblue: {meteoblue_forecast[:1000]}

Your task is to briefly assess how well the original forecast matches what the websites say. If the differences are small, just acknowledge and confirm the forecast is consistent. If there are *significant discrepancies* (e.g. APIs say 10% rain but websites talk about heavy showers), then flag this clearly using an appropriate emoji like 🚨 or ⚠️, and briefly explain why.

Be precise, human-readable, keep it to 1-3 sentences maximum — but allow for a slightly playful touch (like you're a smart assistant giving a daily weather vibe check, but have some cheeky humor sometimes). Keep it to 2–3 sentences max.
"""
   
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful weather analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

# --- MAIN ---

def main():
    for city in CITIES:
        forecast = load_forecast(city)
        summary = forecast.get("summary", "")

        yr = scrape_forecast_yr(city)
        knmi = scrape_forecast_knmi(city)
        meteoblue = scrape_forecast_meteoblue(city)

        gpt_comment = analyze_with_chatgpt(city, summary, yr, knmi, meteoblue)
        forecast["gpt_comment"] = gpt_comment

        with open(f"docs/{city.lower()}_forecast.json", "w") as f:
            json.dump(forecast, f, indent=2)
        print(f"Updated {city} forecast with GPT comment.")

if __name__ == "__main__":
    main()
