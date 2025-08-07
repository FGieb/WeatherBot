# scripts/compare_and_analyze.py

import json
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv("weather.env")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Helper: Load forecast JSON
def load_forecast(city):
    path = f"docs/{city.lower()}_forecast.json"
    with open(path, "r") as f:
        return json.load(f)

# Helper: Scrape forecast from external site (example: YR.no)
def scrape_forecast_yr(city):
    if city.lower() == "brussels":
        url = "https://www.yr.no/en/forecast/daily-table/2-2800866/Belgium/Brussels-Capital/Brussels"
    elif city.lower() == "paris":
        url = "https://www.yr.no/en/forecast/daily-table/2-2988507/France/Île-de-France/Paris"
    else:
        return "Unsupported city"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    forecast_block = soup.find("table")
    if not forecast_block:
        return "Could not extract data from YR.no"
    return forecast_block.text.strip()[:1000]  # Return partial raw forecast

# Helper: Generate comparison summary with OpenAI
def generate_analysis(city, internal_data, external_forecast):
    prompt = f"""
Compare this API-based weather forecast:

{json.dumps(internal_data, indent=2)}

With the website forecast text:

{external_forecast}

Write a short analysis (1–2 paragraphs) summarizing similarities, discrepancies, and reliability concerns, if any.
"""
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Main process
def main():
    for city in ["Brussels", "Paris"]:
        try:
            forecast_data = load_forecast(city)
            external_forecast = scrape_forecast_yr(city)
            analysis = generate_analysis(city, forecast_data, external_forecast)
            forecast_data["analysis"] = analysis

            # Overwrite JSON with enriched data
            with open(f"docs/{city.lower()}_forecast.json", "w") as f:
                json.dump(forecast_data, f, indent=2)

            print(f"Updated forecast for {city} with analysis.")
        except Exception as e:
            print(f"Error processing {city}: {e}")

if __name__ == "__main__":
    main()
