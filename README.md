# 🌦️ Daily Weather Forecast Bot

This project sends a **daily weather summary and forecast graph** for **Paris** and **Brussels**, comparing data from **OpenWeatherMap** and **WeatherAPI**, directly to your phone using [Pushover](https://pushover.net/).

It was built to:
- Compare forecasts across services
- Spot disagreement or uncertainty
- Give a beautiful and readable snapshot of tomorrow’s weather

---

## 🔍 What It Does

Every day, the bot:

1. Fetches **tomorrow’s forecast** (09:00–21:00) for Paris and Brussels
2. Pulls **temperature** and **rain probability** from:
   - OpenWeatherMap (3-hour intervals)
   - WeatherAPI (hourly, filtered to every 3rd hour)
3. Calculates:
   - Avg temp + rain
   - High / Low temp
   - Forecast uncertainty (range between APIs)
4. Generates a chart with:
   - 🔴 Red, 🟠 orange & ⚫ black lines for temps and their average
   - 🔵 Blue / 🔹 cyan rain lines (no legend)
   - Bold annotations for average temps at 12:00 & 18:00
   - Clean title (e.g., `Paris Tomorrow – Day Forecast`)
5. Sends a **notification and the graph** to your phone via Pushover

---



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

### 📲 `send_to_pushover.py` (in progress)
- **Purpose:**
  - Reads enriched forecast JSON + chart
  - Sends:
    - Title + summary
    - PNG chart
    - GPT comment
  - Via Pushover API

---

## 3. ⚙️ Technical Setup

### GitHub Actions
- Trigger: Daily at **21:00 CET** (19:00 UTC)
- Uses `main.yml` workflow and `GITHUB_TOKEN` to auto-commit outputs

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
- 🚧 Pushover notification script in progress

---

## 🗂 Directory Summary

```bash
scripts/
├── weather_notify.py         # Fetch APIs + generate chart
├── compare_and_analyze.py    # Scrapes + GPT + alignment tagging
├── send_to_pushover.py       # Push alert sender (in development)

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
PUSHOVER_USER_KEY=...
PUSHOVER_API_TOKEN=...
OPENWEATHER_API_KEY=...
WEATHERAPI_API_KEY=...
OPENAI_API_KEY=...
```

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
```

---

## 🧠 Smart Things (That Took Way Too Long to Get Right)
- Alignment categorization via GPT response parsing
- Friendly tone blending factual forecast + casual insights
- Flexible scraping with fallback text if blocked
- Full automation with no 3rd-party scheduler

---

## 🚀 Future Ideas
- Add `send_to_pushover.py` integration
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

🤖 GPT: Forecasts line up well, with minor variations. Should be smooth sailing for your Monday. ☀️
```

Graph:
- Clearly annotated
- Easily interpreted at a glance

---

## ❓ FAQ

**Q: Why isn’t `.env` in the repo?**  
A: To protect API keys — it's only for local use. GitHub Actions uses encrypted Secrets.

**Q: How do I run it manually?**  
A: Just run `python scripts/weather_notify.py` and then `compare_and_analyze.py`

**Q: Can I add someone else to receive alerts?**  
A: Yes, Pushover supports multiple user keys:  
```env
PUSHOVER_USER_KEY=key1,key2
```

---

Built for curiosity, consistency, and comparing clouds ☁️


# 🌦️ WeatherBot Automation – System Overview

## 1. 🎯 Goal

Automatically compare weather forecasts from two APIs with forecasts from public weather websites, generate a clean summary using ChatGPT, and send it daily via Pushover.

---

## 2. 🔁 Current Workflow

The automation runs **daily via GitHub Actions** and consists of three main Python scripts located in the `scripts/` folder:

### ✔ `weather_notify.py`
- **Purpose**: Fetches forecast data from:
  - OpenWeatherMap
  - WeatherAPI
- **Output**:
  - JSON summary → `docs/{city}_forecast.json`
  - Chart image → `docs/{city}_comparison.png`
- **Includes**:
  - Average temperature & rain probability
  - High/low temps
  - Comparison between APIs

### ⏳ `compare_and_analyze.py` *(to be developed)*
- **Purpose**:
  - Reads the JSON files created by `weather_notify.py`
  - Scrapes weather forecasts from specific websites (e.g., **KNMI**, **YR.no**)
  - Compares scraped data with API-based forecasts
  - Uses **OpenAI GPT API** to generate:
    - Natural language summary
    - Alerts or comments if forecasts significantly diverge
- **Output**:
  - Appends enriched analysis to the original JSON

### 📲 `send_to_pushover.py` *(to be developed)*
- **Purpose**:
  - Sends:
    - The enriched `.json` summary
    - The `.png` chart
  - Delivered via **Pushover API**

---

## 3. ⚙️ Technical Setup

- **GitHub Actions**:
  - Triggers daily using cron (`19:00 UTC`)
  - Uses the default `GITHUB_TOKEN` for commits
- **APIs Used**:
  - `OpenWeatherMap`
  - `WeatherAPI`
- **Output Storage**:
  - All files saved in the `docs/` directory for public access
- **Notification**:
  - Uses **Pushover** for direct push alerts
- **ChatGPT API**:
  - Used in `compare_and_analyze.py` to create human-readable summaries

---

## 4. 🧠 No-Zapier Design

Zapier is **not used** to avoid subscription fees. Instead:

- GitHub Actions handles scheduling
- Pushover and OpenAI API are triggered from Python scripts
- All logic is internal and runs inside GitHub CI

---

## 5. 🚧 What’s Next

- [ ] Build `compare_and_analyze.py` to scrape KNMI/YR.no and use GPT to generate insights
- [ ] Build `send_to_pushover.py` to package JSON + image into one daily notification
- [ ] (Optional) Add exception handling & logs
- [ ] (Optional) Add more cities or forecast types

---

## 🗂 Directory Summary

```
scripts/
├── weather_notify.py           # Main fetch + image/chart generator
├── compare_and_analyze.py      # Scrapes & uses ChatGPT (todo)
├── send_to_pushover.py         # Sends enriched output (todo)

docs/
├── brussels_forecast.json      # Daily summary
├── brussels_comparison.png     # Daily chart
├── paris_forecast.json
├── paris_comparison.png
```

---

## ✅ Status

- ✔ Fully automated GitHub Actions run
- ✔ JSON + PNG forecasts generated daily
- 🚧 GPT-based analysis & external site comparison pending
- 🚧 Final notification message in development

---

*Built with ❤️ and a lot of debugging.*


## 🗂️ Project Structure

\`\`\`
.
├── weather_notify.py         # Main script
├── weather.env               # Local file for API keys (excluded from repo)
├── requirements.txt          # Python dependencies
└── .github/
    └── workflows/
        └── main.yml          # GitHub Actions schedule (daily at 10:00 CET)
\`\`\`

---

## 🛠️ Local Setup

1. **Create a `.env` file named `weather.env`** with your API keys:
\`\`\`env
PUSHOVER_USER_KEY=your_user_key
PUSHOVER_API_TOKEN=your_pushover_token
OPENWEATHER_API_KEY=your_openweather_key
WEATHERAPI_API_KEY=your_weatherapi_key
\`\`\`

2. **Install Python dependencies**:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

3. **Run the script locally**:
\`\`\`bash
python weather_notify.py
\`\`\`

---

## ☁️ GitHub Actions (Daily Forecast)

The forecast runs **automatically every day at 10:00 (CET)** via GitHub Actions.

To make this work:

1. Go to your GitHub repo:
   - **Settings → Secrets and variables → Actions**
2. Add the following secrets:
   - `PUSHOVER_USER_KEY`
   - `PUSHOVER_API_TOKEN`
   - `OPENWEATHER_API_KEY`
   - `WEATHERAPI_API_KEY`

These are used during automated runs and replace the local `.env` file.

---

## ✅ Example Output

**Pushover Message**:
\`\`\`
Paris: ☀️ Avg 25.3°C (2°C range), 10% rain (5% range)
High 28°C / Low 22°C
\`\`\`

**Graph Includes**:
- Temp lines:  
  🔴 OWM | 🟠 WeatherAPI | ⚫ Average  
- Rain lines (no legend):  
  🔵 OWM | 🔹 WeatherAPI  
- Bold °C annotations at 12:00 & 18:00  
- Title like: `Paris Tomorrow – Day Forecast`

---

## 🚀 Future Ideas

- Weekend weather summaries
- Multi-day trend comparison
- Add more cities or toggle destinations
- Link to a shared webpage for archiving graphs
- Sound/theme customization in Pushover

---

## ❓ FAQ

**Q: Why isn’t `.env` in the repo?**  
To protect your API keys — it's used only for local testing.  
In production, GitHub Actions uses **Secrets** instead.

**Q: How do I run it manually?**  
Just execute:
\`\`\`bash
python weather_notify.py
\`\`\`

**Q: Can I add someone else to receive the alerts?**  
Yes — you can add multiple Pushover recipients by comma-separating the keys:
\`\`\`env
PUSHOVER_USER_KEY=your_key,partner_key
\`\`\`

---

Built for clarity, curiosity, and comparing clouds. ☁️

