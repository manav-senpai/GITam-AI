# 🔬 Gitam AI — Predictive Engineering Intelligence Platform

**Gitam AI** is a multi-agent AI system that connects to any public GitHub repository, analyzes its codebase health, predicts which components are most likely to cause failures in the next 90 days, and generates a business-impact report for non-technical stakeholders.

> Built for the Agentic AI Hackathon — a fully functional platform powered by 7 specialized AI agents.

---

## 🧬 Features

| Feature | Description |
|---------|-------------|
| **🔍 Multi-Agent Analysis** | 7 specialized agents (Data Collector, Code Analyzer, Bug Analyzer, Health Scorer, Predictor, Report Generator, Email Sender) |
| **📊 Health Dashboard** | Per-component health scores, commit frequency charts, bug statistics, risk timeline |
| **🧬 Deep Code Review** | Side-by-side diff viewer with AI-powered explanations of code changes and anti-patterns |
| **📈 90-Day Predictions** | Forecasts which components will degrade based on churn, bug correlations, and ownership diffusion |
| **📋 CEO Report** | AI-generated business-impact report translating technical risk into cost/time/revenue language |
| **📧 Email to CEO** | One-click email delivery of the report via Gmail SMTP |
| **💬 AI Chatbot** | Interactive assistant that answers questions about the analysis |
| **🌗 Light/Dark Mode** | Toggle between themes with persistent preference |

---

## 🏗 Architecture

```
Frontend (React + Vite)  ──REST API──▶  Backend (FastAPI)
                                          │
                         ┌────────────────┼────────────────┐
                         ▼                ▼                ▼
                    Agent 1-2         Agent 3-5         Agent 6-7
                  (Data + Code)    (Bugs + Health     (Report +
                                    + Predictor)      Email + Chat)
                         │                │                │
                    GitHub API       Analysis Engine      LLM (Groq)
```

### Agents
1. **Data Collector** → Pulls commits, issues, diffs, contributors from GitHub API
2. **Code Analyzer** → Tracks file churn, hotspots, and provides AI code review
3. **Bug Analyzer** → Categorizes bugs, correlates with code changes, tracks resolution time
4. **Health Scorer** → Computes per-component health scores (0-100) with weighted formula
5. **Predictor** → Forecasts 30/60/90-day risk using decay rate modeling
6. **Report Generator** → Creates CEO-friendly business impact report via LLM
7. **Email Sender** → Delivers report as styled HTML email via SMTP

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Groq API Key** (free at [console.groq.com](https://console.groq.com)) — or Ollama for local LLM

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/gitam-ai.git
cd gitam-ai
```

### 2. Setup Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Setup Frontend
```bash
cd frontend

# Install dependencies
npm install
```

### 4. Run
```bash
# Terminal 1 — Backend
cd backend
python main.py
# Runs on http://localhost:8000

# Terminal 2 — Frontend
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### 5. Use it
1. Open http://localhost:5173
2. Enter a GitHub repo URL (e.g., `https://github.com/pallets/flask`)
3. Click **🚀 Analyze** — watch the multi-agent progress
4. Explore: **Dashboard** → **Code Review** → **CEO Report**
5. Use the **💬 chatbot** to ask questions about the analysis

---

## ⚙️ Configuration

### `.env` file (backend)

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key (free tier) | ✅ |
| `GROQ_MODEL` | Model name (default: `llama-3.3-70b-versatile`) | No |
| `OLLAMA_BASE_URL` | Ollama server URL (default: `http://localhost:11434`) | No |
| `OLLAMA_MODEL` | Local model (default: `qwen2.5:3b`) | No |
| `SMTP_EMAIL` | Gmail address for sending CEO reports | Optional |
| `SMTP_PASSWORD` | Gmail App Password ([create here](https://myaccount.google.com/apppasswords)) | Optional |

---

## 📁 Project Structure

```
gitam-ai/
├── backend/
│   ├── main.py                 # FastAPI server + API routes
│   ├── agents/
│   │   ├── llm_client.py       # Groq/Ollama LLM abstraction
│   │   ├── data_collector.py   # GitHub API data collection
│   │   ├── code_analyzer.py    # Code churn + AI code review
│   │   ├── bug_analyzer.py     # Bug pattern analysis
│   │   ├── health_scorer.py    # Health scoring engine
│   │   ├── predictor.py        # 90-day failure prediction
│   │   ├── report_generator.py # CEO report generation
│   │   └── email_sender.py     # SMTP email delivery
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app + routing + theme
│   │   ├── index.css           # Full design system
│   │   ├── pages/
│   │   │   ├── Home.jsx        # Landing page
│   │   │   ├── Dashboard.jsx   # Health dashboard
│   │   │   ├── CodeReview.jsx  # Code diff viewer + AI review
│   │   │   └── Report.jsx      # CEO report + email
│   │   └── components/
│   │       └── Chatbot.jsx     # AI chatbot
│   └── package.json
└── README.md
```

---

## 🛡️ PS Requirements Checklist

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| Multi-agent AI system | ✅ | 7 specialized agents with distinct roles |
| Connect to GitHub/GitLab | ✅ | GitHub REST API (public repos, no auth needed) |
| Analyze code change history | ✅ | Commit frequency, file churn, actual diff analysis |
| Bug patterns | ✅ | Issue categorization, severity, resolution time, correlation |
| Test coverage trends | ✅ | Test file detection, coverage pattern analysis |
| Deployment frequency | ✅ | Release/tag analysis, CI pipeline indicators |
| Health score per component | ✅ | Weighted 0-100 score with letter grade |
| Predict failures (90 days) | ✅ | Decay rate modeling with 30/60/90 day forecasts |
| Business-impact report (CEO) | ✅ | AI-generated plain English report with cost estimates |
| Cost of inaction | ✅ | Dollar and hour estimates per component |

---

## 🧰 Tech Stack

- **Frontend:** React + Vite, Vanilla CSS (custom design system)
- **Backend:** Python FastAPI, Uvicorn
- **AI/LLM:** Groq (Llama 3.3 70B) with Ollama fallback
- **APIs:** GitHub REST API
- **Email:** Python smtplib + Gmail SMTP

---

## 📄 License

MIT License — built for the Agentic AI Hackathon.
