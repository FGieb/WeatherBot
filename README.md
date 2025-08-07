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

