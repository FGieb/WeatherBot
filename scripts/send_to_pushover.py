import os
import json
import requests

# Load your Pushover credentials (use secrets or GitHub Actions env vars!)
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")

# Paths to the files (adjust if needed)
JSON_PATH = "docs/forecast.json"
PNG_PATH = "docs/forecast_chart.png"

# Optional: load forecast summary from JSON
def load_forecast_summary(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    # Simplified message – adapt to your needs
    message = (
        f"📍 Paris vs Brussels – Tomorrow\n"
        f"Paris: {data['Paris']['summary']}\n"
        f"Brussels: {data['Brussels']['summary']}"
    )
    return message

def send_notification(message, image_path=None):
    url = "https://api.pushover.net/1/messages.json"

    data = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "message": message,
        "title": "☀️ Daily Weather Update",
        "priority": 0,
    }

    files = {"attachment": open(image_path, "rb")} if image_path else None

    response = requests.post(url, data=data, files=files)
    if response.status_code == 200:
        print("✅ Notification sent!")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    summary = load_forecast_summary(JSON_PATH)
    send_notification(summary, PNG_PATH)
