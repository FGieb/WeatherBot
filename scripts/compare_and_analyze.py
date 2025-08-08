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
        url = "https://www.yr.no/en/forecast/daily-table/2-2988507/France/\u00cele-de-France/Paris"
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
You're a concise weather analyst AI helping to enrich a forecast summary for {city}, based on OpenWeatherMap and WeatherAPI:

Original forecast:
{summary}

You also have:
- YR.no: {yr}
- KNMI: {knmi}
- Meteoblue: {meteoblue}

Your job is to:
1. Compare the original forecast to the scraped data, but only for the period 09:00 to 21:00.
2. Describe notable similarities or differences in temperature, rain, or other conditions. Be concise when forecasts align, but add useful detail when there’s divergence or interesting patterns. If the context naturally lends itself to a playful metaphor or reference (e.g., involving monkeys), you may use it, but only if it fits without forcing it. Avoid repeating the source names unnecessarily; focus on the weather story. 
3. Say whether the other sources confirm, differ from, or add nuance to it — especially regarding temperature and rain.
4. If forecasts differ significantly, start with ⚠️ and highlight the main difference.
5. If they align, say so simply — no filler needed 
5. Use a neutral tone by default, but feel free to add a light, human remark *if it naturally fits*, like referencing the day (e.g., "a dry start to the week" or "perfect for a lazy Sunday"). Don’t force it.

Limit the response to a maximum of 3 short sentences — fewer if nothing notable. Return only your final text.
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    comment = response.choices[0].message.content.strip()
    comment_lower = comment.lower()

    # --- Improved alignment detection ---
    if "⚠️" in comment or "big mismatch" in comment_lower or "major difference" in comment_lower:
        alignment = "divergent"
    elif any(word in comment_lower for word in ["slightly off", "some sources", "partial", "nuance", "slightly lower", "adds nuance", "not all sources"]):
        alignment = "partial"
    elif any(word in comment_lower for word in ["align", "match", "agree", "consistent", "in line", "all sources"]):
        alignment = "full"
    else:
        alignment = "unknown"

    return comment, alignment


# --- MAIN ---

def main():
    for city in CITIES:
        try:
            forecast = load_forecast(city)
            summary = forecast.get("summary", "")

            yr = scrape_forecast_yr(city)
            knmi = scrape_forecast_knmi(city)
            meteoblue = scrape_forecast_meteoblue(city)

            gpt_comment, alignment = analyze_with_chatgpt(city, summary, yr, knmi, meteoblue)
            forecast["gpt_comment"] = gpt_comment
            forecast["alignment"] = alignment

            with open(f"docs/{city.lower()}_forecast.json", "w") as f:
                json.dump(forecast, f, indent=2)

            print(f"✅ Updated {city} forecast with GPT comment and alignment: {alignment.upper()}.")
        except Exception as e:
            print(f"❌ Error updating {city}: {e}")

if __name__ == "__main__":
    main()
