# ⚡ PowerPulse — AI Energy Coach

**PowerPulse** is an **AI + IoT-powered platform** that predicts home energy usage, detects consumption spikes, and delivers *personalized, context-aware* energy-saving recommendations using **Google Gemini**.

It combines live weather data, simulated IoT sensor input, and predictive analytics to make sustainability *intuitive and actionable.*

---

## 🌍 Problem

Most households have no real-time awareness of when and how their energy costs spike.  
Smart thermostats and dashboards exist, but they:
- Require **expensive hardware**, and  
- Don’t provide **personalized insights** based on lifestyle, comfort, or behavior.

---

## 💡 Solution

PowerPulse uses AI to:

1. **Forecast short-term (12 h) energy usage** from weather, home size, and preferences.  
2. **Detect inefficiencies** or peak-hour patterns.  
3. **Quantify CO₂ and cost impact** of simple actions (e.g., raising thermostat by +2 °F).  
4. **Coach users in natural language** — with Gemini generating concise, friendly recommendations.

**Key differentiator:** behavioral optimization and tight feedback loops (predict → explain → coach) — no hardware required.

---

## 🧠 How It Works

### 🔹 Inputs
- **Weather API:** Temperature and humidity for the next 12 hours.
- **IoT or Simulated Data:** Household size, A/C power, thermostat settings.
- **User Preferences:** Comfort mode (Eco, Budget, Comfort).

### 🔹 AI Engine
- Predicts hourly consumption (`predicted_kwh`) vs baseline.
- Detects **spikes** and **peak tariff** hours.
- Calculates CO₂ and cost savings for each corrective action.
- Generates **personalized recommendations** using Google Gemini.

### 🔹 Outputs
- **Real-time energy metrics** (kWh, $, CO₂).
- **Forecast chart** for next 12 hours.
- **GEMINI CHAT recommendations**: short, data-driven nudges.
- **Weather widget** for contextual awareness.

---

## 🧩 Key Features

| Feature | Description |
|----------|-------------|
| 🔮 **Energy Forecasting** | Predicts hourly consumption using weather trends |
| 🚨 **Peak Detection** | Flags high-usage or peak-tariff hours |
| 💬 **AI Coach (Gemini)** | Generates contextual, human-like recommendations |
| 🌡️ **Weather-Aware Insights** | Integrates real outdoor temperature & humidity |
| ⚙️ **IoT-Ready** | Works with simulated or real smart device data |
| 💰 **Impact Metrics** | Quantifies CO₂ and dollar savings per suggestion |

---

## ⚙️ Setup & Run

### 🖥 Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 🖥 Frontend (Next.js)
```bash
cd frontend
npm run dev
```
---

## 🚀 Future Enhancements

### 🔹 Smart Integrations
- Connect with **smart thermostats** (Nest, Ecobee) for real-world automation.  
- Parse **utility bills** to auto-calibrate baseline and costs.

### 🔹 Community Features
- **Neighborhood leaderboard** to gamify sustainable energy habits.  
- Share achievements and compare CO₂ savings with local peers.

### 🔹 Data Insights
- Historical trend visualization using **PostgreSQL** + **Grafana**.  
- Predict weekly or seasonal energy spikes using extended weather data.

---

## 🏆 Impact

### 🔹 PowerPulse Helps Households:
- Cut **5–10%** of electricity use during peak hours.  
- Reduce **daily CO₂ emissions by up to 0.5 kg.**  
- Build awareness and actionable, sustainable habits through AI-driven coaching.  
- Translate real data into tangible actions — empowering users to save both **money and the planet.**
