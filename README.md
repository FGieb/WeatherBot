# 🌦️ WeatherBot Automation – Updated System Overview (August 2025)

## 1. 🎯 Goal
Automatically analyze and compare weather forecasts from multiple APIs and public sources, generate a clean, insightful summary with ChatGPT, and send it daily via Pushover — fully automated with GitHub Actions. Smart workarounds (like avoiding Zapier and using cookie-based GitHub deployments) make this efficient, affordable, and fun.

---

## 2. 🔁 Workflow Overview
The automation runs daily at 21:00 CET and consists of three main Python scripts:

### ✔ `weather_notify.py`
- **Purpose:** Fetch forecast data from:
  - OpenWeatherMap
  - WeatherAPI
- **Output:**
  - JSON summary → `docs/{city}_forecast.json`
  - PNG comparison chart → `docs/{city}_comparison.png`
- **Includes:**
  - Average temperature & rain probability
  - High/low temperatures
  - Comparison between both APIs

### ✅ `compare_and_analyze.py`
- **Purpose:**
  - Reads each city's forecast JSON
  - Scrapes forecast data from public sources:
    - YR.no
    - Meteoblue
    - (KNMI placeholder included)
  - Uses GPT-4 (OpenAI API) to:
    - Compare forecasts
    - Assess confidence in API predictions
    - Add a clear, natural-language `gpt_comment`
    - Classify alignment as: `full`, `partial`, or `divergent`
- **Output:**
  - Appends `gpt_comment` and `alignment` to each city's forecast JSON
  - Comments are short, optionally playful, and context-aware (e.g., "cozy Sunday", "good start to the week")

### ✅ `send_to_pushover.py`
- **Purpose:**
  - Reads enriched forecast JSON + PNG chart
  - Sends a clean and structured Pushover notification per city
  - Includes:
    - Summary (from JSON)
    - GPT insight comment
    - Attached PNG chart
    - Title includes alignment emoji (✅, ⚠️, ❌)
- **Multi-user support:** You can add multiple recipients by comma-separating user keys in the `PUSHOVER_USER_KEY` secret

---

## 3. ⚙️ Technical Setup

### GitHub Actions
- Trigger: Daily at **21:00 CET** (19:00 UTC)
- Uses `main.yml` workflow and `GH_PAT` secret to auto-commit outputs (not the default `GITHUB_TOKEN`)

### APIs Used
- OpenWeatherMap
- WeatherAPI
- OpenAI GPT-4 API

### Scraping
- HTML scraping of YR.no and Meteoblue using BeautifulSoup
- Limited by rate-limiting and content availability — gracefully handled

### Output Storage
- All outputs saved to `docs/` folder
- Publicly accessible via GitHub Pages for chart access if needed

### Notifications
- Uses Pushover for direct push alerts
- Image, text, and summaries are sent with rich formatting + emojis
- One message per city, combining summary + GPT insight + PNG chart

### Alignment Detection (new)
- GPT comment now includes implicit analysis type:
  - `alignment = "full"` → forecasts agree
  - `alignment = "partial"` → minor differences
  - `alignment = "divergent"` → major mismatch
- Useful for logic filters, alerts, or archiving

---

## 4. 🧠 No-Zapier Design
To avoid dependency on Zapier:
- GitHub Actions handles all automation
- Python scripts control scraping, analysis, and notification
- All logic runs in CI — self-contained, replicable, and cheap

---

## 5. ✅ Status
- ✔ Daily GitHub Action is live
- ✔ JSON & PNG generated for Paris and Brussels
- ✔ ChatGPT analysis integrated
- ✔ Alignment detection working
- ✔ Pushover notification now fully working 🎉

---

## 🗂 Directory Summary

```bash
scripts/
├── weather_notify.py         # Fetch APIs + generate chart
├── compare_and_analyze.py    # Scrapes + GPT + alignment tagging
├── send_to_pushover.py       # Push alert sender (final step)

docs/
├── paris_forecast.json       # JSON summary
├── paris_comparison.png      # Chart with annotated lines
├── brussels_forecast.json
├── brussels_comparison.png
```

---

## 📊 Graph Features
- Temperature lines:
  - 🔴 OpenWeatherMap
  - 🟠 WeatherAPI
  - ⚫ Average
- Rain lines (dotted):
  - 🔵 OWM
  - 🔹 WeatherAPI
- Labels at 12:00 & 18:00
- Chart title: `Paris Tomorrow – Day Forecast`

---

## ☁️ GitHub Actions (Daily Forecast)

### Schedule
- Daily at 10:00 CET (or 21:00 for latest data)

### Secrets (for CI)
Add these under GitHub → Settings → Actions → Secrets:
```env
GH_PAT=your_personal_token
OPENWEATHER_API_KEY=your_openweather_key
WEATHERAPI_API_KEY=your_weatherapi_key
OPENAI_API_KEY=your_openai_key
PUSHOVER_API_TOKEN=your_app_token
PUSHOVER_USER_KEY=your_user_key[,your_boyfriends_key]
```

You can add multiple user keys to `PUSHOVER_USER_KEY` by comma-separating them. No spaces.

---

## 🛠️ Local Setup

1. Create a file `weather.env`:
```env
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_API_TOKEN=your_pushover_token
OPENWEATHER_API_KEY=your_openweather_key
WEATHERAPI_API_KEY=your_weatherapi_key
OPENAI_API_KEY=your_openai_key
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run manually:
```bash
python scripts/weather_notify.py
python scripts/compare_and_analyze.py
python scripts/send_to_pushover.py
```

---

## 🧠 Smart Things (That Took Way Too Long to Get Right)
- Alignment categorization via GPT response parsing
- Friendly tone blending factual forecast + casual insights
- Flexible scraping with fallback text if blocked
- Full automation with no 3rd-party scheduler
- Single-message-per-city Pushover formatting with chart and GPT summary

---

## 🚀 Future Ideas
- Expand to more cities (e.g., Amsterdam, Berlin)
- Weekend trends or weekly summaries
- Archive via GitHub Pages
- UI dashboard for review

---

## ✅ Example Output

Pushover Message:
```txt
Paris: ☀️ Avg 27.1°C (0°C range), 0% rain
High 31°C / Low 22°C

🤖 GPT: Forecasts align well — looks like a warm, dry day. Perfect for a stroll by the Seine.

📊 Chart attached.
```

Graph:
- Clearly annotated
- Easily interpreted at a glance

---

## ❓ FAQ

**Q: Why isn’t `.env` in the repo?**  
A: To protect API keys — it's only for local use. GitHub Actions uses encrypted Secrets.

**Q: How do I run it manually?**  
A: Just run `python scripts/weather_notify.py` → `compare_and_analyze.py` → `send_to_pushover.py`

**Q: Can I add someone else to receive alerts?**  
A: Yes, just update your secret:
```env
PUSHOVER_USER_KEY=your_key,partner_key
```
Pushover will send to both recipients at once.

---

Built for curiosity, consistency, and comparing clouds ☁️
