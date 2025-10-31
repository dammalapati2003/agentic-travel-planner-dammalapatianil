#  AI Agent Challenge: Multi-Agent Travel Planning System

### **Tech Stack:**  
**Python • LangGraph • LLM (Groq Llama-3.1-8B-Instant)**

---

##  Overview

This project implements a **multi-agent travel planning system** that intelligently combines **live data**, **tool-driven reasoning** and **LangGraph orchestration** to generate realistic travel itineraries.

Given a user query like  
> “Plan a 2-day trip to New Delhi starting tomorrow,”  
the system automatically:
1. Extracts travel intent, city and dates.  
2. Fetches live **weather** data for each day.  
3. Finds **points of interest (POIs)** in the target city.  
4. Creates a **day-by-day itinerary** optimized for the weather.  

The solution integrates **LLM-based reasoning**, **Prompt Engineering** and **ReAct logic** for fully autonomous planning — without hard-coded if-else rules.

---

##  Features

| Agent | Function | Data Source |
|--------|-----------|--------------|
|  **Input Handler** | Parses user query into structured fields | LLM → LangGraph parser node |
|  **Weather Agent** | Fetches daily summaries | [Open-Meteo API](https://open-meteo.com) |
|  **POI Agent** | Gets nearby attractions / restaurants / nature spots | [OpenTripMap API](https://opentripmap.io) |
|  **Planner Agent** | Builds itineraries combining weather + POIs | Custom LLM logic |
|  **Router / LLM Brain** | Chooses which agent(s) to invoke | Groq Llama-3.1 (ReAct prompt) |

---

##  LangGraph Design

```
┌──────────────┐
│ Input Node   │
└──────┬───────┘
       ▼
┌──────────────┐
│ Router Node  │
└──────┬───────┘
   ┌────┴──────┬─────────────┐
   ▼            ▼             ▼
Weather Agent  POI Agent   Planner Agent
   │            │            │
   └───────┬────┴───────┬────┘
           ▼            ▼
        Synthesizer → Final Output
```

> The LLM dynamically selects which tools to call (weather, POI, or both) and merges results into a coherent itinerary.

---

##  Setup Instructions

```bash
# 1️ Environment
python -m venv .venv
# Windows
.venv\Scripts\activate

# 2  Dependencies
pip install -r requirements.txt

# 3️  API Keys
cp .env.example .env
# then set:
# GROQ_API_KEY=<your_groq_key>
# OPENTRIPMAP_API_KEY=<your_opentripmap_key>

# 4️  Run
python -m app.main "Plan a 2 day trip to Delhi next week"
```

> 🕒 Default timezone: Asia/Kolkata (for relative phrases like “today”, “tomorrow”).  

---

##  Example Run

**Input**
```
Plan a 2-day trip to New Delhi starting tomorrow.
```

**Output**

**Weather Info**
```
• Day 1 (Sep 24 2025): Sunny 34 °C
• Day 2 (Sep 25 2025): Cloudy 31 °C
```

**Points of Interest**
```
• Red Fort – Historic site
• India Gate – Landmark
• Qutub Minar – UNESCO monument
• Lotus Temple – Modern temple
• Connaught Place – Food & shopping
```

**Travel Itinerary**

| Day | Morning | Afternoon | Evening | Notes |
|-----|----------|------------|----------|--------|
| 1 | Red Fort | India Gate | Connaught Place | Sunny, good for walking |
| 2 | Qutub Minar | Lotus Temple | Free exploration | Cloudy, less heat |

---

##  Metrics of Success

| Metric | Goal |
|---------|------|
| POIs per day | 3–5 recommended stops |
| Weather alignment | Outdoor plans on clear days |
| Runtime | < 5 seconds per query |
| Graceful Fallbacks | If API fails, LLM summary still valid |

---

##  Future Improvements

- **Budget optimization** (auto-suggest low-cost plans)  
- **Multi-city planning** across routes  
- **Preference tuning** (food / culture / nature filters)  
- **“Re-plan” feature** if weather changes  
- **Map visualization + distance matrix**

---

##  Evaluation Summary 

| Criterion | Weight | Fulfilled |
|------------|--------|------------|
| Business Design | 40 % |  Design doc + metrics + future scope |
| Technical Implementation | 60 % |  LangGraph nodes + live tools + ReAct reasoning |

---

##  Repository Structure

```
 agentic-travel-planner-kranthi/
 ├── app/
 │   ├── agents/
 │   │   ├── router.py
 │   │   ├── weather_agent.py
 │   │   ├── poi_agent.py
 │   │   └── planner_agent.py
 │   ├── tools/
 │   │   ├── weather.py
 │   │   └── poi.py
 │   ├── llm.py
 │   ├── config.py
 │   ├── utils/
 │   │   └── date_utils.py
 │   ├── io/input_handler.py
 │   └── main.py
 ├── docs/design.md
 ├── .env.example
 ├── requirements.txt
 └── README.md
```

---

##  Submission Checklist

 Private GitHub Repo → `agentic-travel-planner-kranthi`  
 Add `wintechservices12@gmail.com` as a collaborator  
 Include these files:  
- `README.md` (this file)  
- `docs/design.md` (design document 3–5 pages)  
- Working code + `.env.example`  
 Short demo video (3–4 min) showing prompt → tools → final itinerary  
 At least one error handling example (fallback mode)

---
##  Short Demo vedio 
# vedio link : https://drive.google.com/file/d/1qPuocx6-f2FW-Wyvm8IjHxxmLr8FMke_/view?usp=sharing

