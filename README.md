# GITam AI

GITam AI is a full-stack engineering intelligence platform that analyzes GitHub repositories, identifies risky code hotspots, predicts future failures, and generates executive-friendly business reports.

It is built for public GitHub repositories and combines repository history, issue signals, code churn, and AI-generated analysis into a single workflow.

## What it does

- Analyzes GitHub repositories from a repo URL
- Collects commits, issues, file-level history, and repository metadata
- Scores code health across files and the repository overall
- Detects hotspot files with high churn, weak ownership, or bug signals
- Predicts likely failures over the next 30, 60, and 90 days
- Generates a CEO-style business impact report
- Supports file-level AI code review for hotspot files
- Can email the report through SMTP
- Includes a chatbot for asking questions about the analyzed repository

## Tech Stack

### Frontend
- React 19
- Vite
- React Router
- Plain CSS with a custom dashboard-style UI

### Backend
- FastAPI
- Uvicorn
- Pydantic
- Python-dotenv

### AI and data services
- Groq API as the primary LLM provider
- Ollama as a local fallback LLM provider
- GitHub API for repository data
- SMTP email delivery for report sharing
- ReportLab for PDF report attachments

## Project Structure

```text
.
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── agents/
│       ├── data_collector.py
│       ├── code_analyzer.py
│       ├── bug_analyzer.py
│       ├── health_scorer.py
│       ├── predictor.py
│       ├── report_generator.py
│       ├── email_sender.py
│       └── llm_client.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   └── Chatbot.jsx
│   │   └── pages/
│   │       ├── Home.jsx
│   │       ├── Dashboard.jsx
│   │       ├── CodeReview.jsx
│   │       ├── Report.jsx
│   │       └── About.jsx
│   └── package.json
└── README.md
```

## Key Features

### Home
- Paste a GitHub repo URL and start analysis
- Quick access cards for code review, dashboard, and CEO report
- Shows the workflow after a repository has been analyzed

### Dashboard
- Overall health score and grade
- Critical, warning, and healthy file counts
- Health score formula breakdown
- Commit frequency chart
- Bug summary
- Risk forecast timeline
- Top hotspot files
- Failure simulation summaries

### Code Review
- File-by-file hotspot review
- Commit diff history for the selected file
- AI-generated review of the file
- Risk metrics such as churn, contributor count, bug history, and test signal

### CEO Report
- Executive summary with business impact language
- Risk cost calculator
- Printable report view
- Email sending with optional PDF attachment

### About
- Simple overview of the product and why it exists

## How It Works

1. The user submits a public GitHub repository URL.
2. The backend parses the owner and repo name.
3. Data collection gathers repository metadata, commits, issues, and file history.
4. Code analysis measures churn, hotspots, ownership spread, and file risk.
5. Bug analysis extracts bug-related patterns from issues and commit signals.
6. Health scoring combines the signals into file and repository scores.
7. The predictor estimates short-term failure risk.
8. The report generator turns the analysis into executive-friendly language.
9. The frontend displays the dashboard, code review, report, and chatbot views.

## Prerequisites

- Python 3.10+ 
- Node.js 18+ and npm
- A GitHub token for stronger API access, especially for larger or rate-limited repositories
- A Groq API key for primary AI inference
- Optional: Ollama if you want a local AI fallback
- Optional: SMTP credentials if you want to email reports

## Environment Variables

Create a `backend/.env` file from `backend/.env.example`.

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
GITHUB_TOKEN=your_github_token_here

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Notes
- `GROQ_API_KEY` is required for cloud AI inference.
- If Groq is unavailable, the backend falls back to Ollama.
- `GITHUB_TOKEN` is optional but recommended to avoid rate limits.
- `SMTP_EMAIL` and `SMTP_PASSWORD` are required only if you want email sending to work.
- Gmail users should use an App Password, not their normal account password.

## Install and Run

### 1. Backend

From the project root:

```powershell
cd backend
python -m pip install -r requirements.txt
```

If you want to use the conda environment already configured in this workspace, activate it first or run the backend with the configured interpreter:

```powershell
C:\Users\ahire\anaconda3\envs\gitam-ai\python.exe main.py
```

The backend runs on:

- `http://localhost:8000`

### 2. Frontend

From the project root:

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

The frontend runs on:

- `http://localhost:5173`

## Running the Full App

Start both services in separate terminals:

```powershell
# Terminal 1
cd backend
C:\Users\ahire\anaconda3\envs\gitam-ai\python.exe main.py
```

```powershell
# Terminal 2
cd frontend
npm run dev -- --host 0.0.0.0
```

Then open:

- `http://localhost:5173`

## API Endpoints

### `GET /api/health`
Checks whether the backend is up.

### `POST /api/analyze`
Starts repository analysis and streams progress via SSE.

Request body:

```json
{
  "repo_url": "https://github.com/pallets/flask",
  "days": 180
}
```

### `GET /api/dashboard/{owner}/{repo}`
Returns the cached dashboard data for an analyzed repository.

### `POST /api/code-review/{owner}/{repo}`
Returns file-level diffs, metrics, and AI review for a selected hotspot file.

Request body:

```json
{
  "filename": "path/to/file.py"
}
```

### `GET /api/report/{owner}/{repo}`
Returns the generated executive report.

### `POST /api/send-email`
Sends the report by email.

Request body:

```json
{
  "to_email": "ceo@example.com",
  "repo_url": "https://github.com/pallets/flask",
  "report_text": "optional report override"
}
```

### `POST /api/chat`
Answers questions about the latest analyzed repository.

Request body:

```json
{
  "question": "Which files are the highest risk?",
  "repo_url": "https://github.com/pallets/flask"
}
```

## Important Behavior

- Analysis results are stored in memory on the backend.
- If the backend restarts, previously analyzed repositories are lost.
- The app currently works best with public GitHub repositories.
- Email sending will fail gracefully if SMTP is not configured.
- The UI uses the latest analysis data to show dashboard, code review, report, and chatbot views.

## Troubleshooting

### Backend fails on startup
Check that the Python environment has all requirements installed, especially `reportlab`, `fastapi`, `uvicorn`, `openai`, and `python-dotenv`.

### No analysis results appear
Make sure you analyzed a repository first, then wait for the SSE progress stream to complete.

### Email sending does not work
Confirm `SMTP_EMAIL` and `SMTP_PASSWORD` are set in `backend/.env`.

### Groq requests fail
Set a valid `GROQ_API_KEY`, or start Ollama locally so the fallback can work.

### GitHub rate limits
Add `GITHUB_TOKEN` to `backend/.env` to increase API limits and improve reliability.

## Development Notes

- Backend entry point: `backend/main.py`
- Frontend entry point: `frontend/src/main.jsx`
- Main app shell and navbar logic: `frontend/src/App.jsx`
- The frontend route order keeps About at the end of the navbar, before the theme toggle.

## License

No license file is currently included in the repository.

## Status

This project is functional as a hackathon-style full-stack prototype and can be extended into a production-grade internal engineering intelligence tool with persistent storage, auth, and richer analytics.
