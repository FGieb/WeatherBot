import os
import json
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

CITIES = ["paris", "brussels"]

def load_forecast(city):
    path = f"docs/{city}_forecast.json"
    with open(path, "r") as f:
        return json.load(f)

def build_prompt(city, forecast_data):
    return f"""
You are a weather analyst. Compare forecasts from multiple APIs for {city.title()} and generate a short summary.

Here is the forecast data:

{json.dumps(forecast_data, indent=2)}

Provide:
- Overall summary of agreement/disagreement
- Rain/temperature conflict alerts if any
- Confidence level (High/Medium/Low)

Format:

🧠 AI Summary:
<One short paragraph>

⚠️ Forecast confidence: <High/Medium/Low>

Keep it under 5 lines. Don’t repeat city name. Start directly with the summary.
"""

def analyze_forecast(city):
    data = load_forecast(city)
    prompt = build_prompt(city, data)

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful weather analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    summary = response["choices"][0]["message"]["content"].strip()

    output_path = f"docs/{city}_message.txt"
    with open(output_path, "w") as f:
        f.write(summary)
    print(f"✅ Saved AI summary for {city} to {output_path}")

if __name__ == "__main__":
    for city in CITIES:
        analyze_forecast(city)
