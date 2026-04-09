"""
Hotspot AI - Predictive Engineering Intelligence Platform
Main FastAPI Server — orchestrates multi-agent pipeline.
"""

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from agents.data_collector import DataCollectorAgent
from agents.code_analyzer import CodeAnalyzerAgent
from agents.bug_analyzer import BugAnalyzerAgent
from agents.health_scorer import HealthScorerAgent
from agents.predictor import PredictorAgent
from agents.report_generator import ReportGeneratorAgent
from agents.email_sender import EmailSenderAgent

app = FastAPI(
    title="Hotspot AI",
    description="Predictive Engineering Intelligence Platform",
    version="1.0.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory store for analysis results ──
analysis_store = {}


# ── Request/Response Models ──
class AnalyzeRequest(BaseModel):
    repo_url: str  # e.g., "https://github.com/pallets/flask"
    days: int = 180


class CodeReviewRequest(BaseModel):
    filename: str


class EmailRequest(BaseModel):
    to_email: str
    repo_url: str


# ── Helper ──
def parse_repo_url(url: str) -> tuple:
    """Parse GitHub URL to (owner, repo)."""
    url = url.strip().rstrip("/")
    parts = url.replace("https://github.com/", "").replace("http://github.com/", "").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    raise ValueError(f"Invalid GitHub URL: {url}")


# ── SSE Progress Streaming ──
from fastapi.responses import StreamingResponse
import json


async def analysis_generator(repo_owner: str, repo_name: str, days: int):
    """Generator that yields SSE events during analysis."""
    repo_key = f"{repo_owner}/{repo_name}"

    try:
        # Step 1: Data Collection
        yield f"data: {json.dumps({'step': 1, 'total': 6, 'agent': 'Data Collector', 'status': 'Connecting to GitHub and collecting repository data...', 'progress': 10})}\n\n"

        collector = DataCollectorAgent(repo_owner, repo_name)
        raw_data = await collector.collect_all(days=days)

        commit_count = len(raw_data.get('commits', []))
        yield f"data: {json.dumps({'step': 2, 'total': 6, 'agent': 'Code Analyzer', 'status': 'Analyzing code churn across ' + str(commit_count) + ' commits...', 'progress': 30})}\n\n"

        # Step 2: Code Analysis
        code_analyzer = CodeAnalyzerAgent()
        code_analysis = code_analyzer.analyze_commits(
            raw_data["commits"], raw_data["detailed_commits"]
        )

        issue_count = len(raw_data.get('issues', []))
        yield f"data: {json.dumps({'step': 3, 'total': 6, 'agent': 'Bug Analyzer', 'status': 'Analyzing ' + str(issue_count) + ' issues for bug patterns...', 'progress': 50})}\n\n"

        # Step 3: Bug Analysis
        bug_analyzer = BugAnalyzerAgent()
        bug_analysis = bug_analyzer.analyze_issues(raw_data["issues"], raw_data["commits"])

        yield f"data: {json.dumps({'step': 4, 'total': 6, 'agent': 'Health Scorer', 'status': 'Computing health scores for all components...', 'progress': 65})}\n\n"

        # Step 4: Health Scoring
        health_scorer = HealthScorerAgent()
        health_scores = health_scorer.calculate_scores(
            code_analysis, bug_analysis, raw_data["repo_info"]
        )

        yield f"data: {json.dumps({'step': 5, 'total': 6, 'agent': 'Predictor', 'status': 'Predicting failures for the next 90 days...', 'progress': 80})}\n\n"

        # Step 5: Predictions
        predictor = PredictorAgent()
        predictions = predictor.predict(health_scores, code_analysis, bug_analysis)

        yield f"data: {json.dumps({'step': 6, 'total': 6, 'agent': 'Report Generator', 'status': 'Generating CEO business impact report...', 'progress': 90})}\n\n"

        # Step 6: CEO Report
        report_gen = ReportGeneratorAgent()
        report = report_gen.generate_report(
            raw_data["repo_info"], health_scores, predictions, bug_analysis
        )

        # Store results
        analysis_store[repo_key] = {
            "repo_info": raw_data["repo_info"],
            "code_analysis": code_analysis,
            "bug_analysis": bug_analysis,
            "health_scores": health_scores,
            "predictions": predictions,
            "report": report,
            "raw_data": raw_data,
            "code_analyzer": code_analyzer,
        }

        yield f"data: {json.dumps({'step': 6, 'total': 6, 'agent': 'Complete', 'status': 'Analysis complete!', 'progress': 100, 'done': True})}\n\n"

    except Exception as e:
        err_msg = str(e)
        yield f"data: {json.dumps({'error': err_msg, 'step': 0, 'status': 'Error: ' + err_msg})}\n\n"


@app.post("/api/analyze")
async def analyze_repo(req: AnalyzeRequest):
    """Start analysis of a GitHub repository (SSE stream)."""
    try:
        owner, name = parse_repo_url(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StreamingResponse(
        analysis_generator(owner, name, req.days),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/dashboard/{owner}/{repo}")
async def get_dashboard(owner: str, repo: str):
    """Get dashboard data for an analyzed repo."""
    repo_key = f"{owner}/{repo}"
    if repo_key not in analysis_store:
        raise HTTPException(status_code=404, detail="Repository not analyzed yet. Run /api/analyze first.")

    data = analysis_store[repo_key]
    return {
        "repo_info": data["repo_info"],
        "health_scores": data["health_scores"],
        "predictions": data["predictions"],
        "code_analysis": {
            "total_commits": data["code_analysis"]["total_commits"],
            "total_files_changed": data["code_analysis"]["total_files_changed"],
            "hotspot_files": data["code_analysis"]["hotspot_files"][:15],
            "commit_frequency": data["code_analysis"]["commit_frequency"],
        },
        "bug_analysis": {
            "total_bugs": data["bug_analysis"]["total_bugs"],
            "open_bugs": data["bug_analysis"]["open_bugs"],
            "severity": data["bug_analysis"]["severity"],
            "monthly_trend": data["bug_analysis"]["monthly_trend"],
            "avg_resolution_days": data["bug_analysis"]["avg_resolution_days"],
            "recent_bugs": data["bug_analysis"]["recent_bugs"][:5],
        },
    }


@app.post("/api/code-review/{owner}/{repo}")
async def get_code_review(owner: str, repo: str, req: CodeReviewRequest):
    """Get code review for a specific file."""
    repo_key = f"{owner}/{repo}"
    if repo_key not in analysis_store:
        raise HTTPException(status_code=404, detail="Repository not analyzed yet.")

    data = analysis_store[repo_key]
    code_analyzer: CodeAnalyzerAgent = data.get("code_analyzer")

    if not code_analyzer:
        raise HTTPException(status_code=500, detail="Code analyzer not available.")

    # Get diffs for this file
    diffs = code_analyzer.get_file_diffs(data["raw_data"]["detailed_commits"], req.filename)

    # Get current file content
    collector = DataCollectorAgent(owner, repo)
    file_content = await collector.get_file_content(req.filename)

    # Get AI review
    ai_review = await code_analyzer.ai_review_file(req.filename, file_content, diffs)

    return {
        "filename": req.filename,
        "current_content": file_content[:10000],
        "diffs": diffs,
        "ai_review": ai_review,
    }


@app.get("/api/report/{owner}/{repo}")
async def get_report(owner: str, repo: str):
    """Get the CEO report for an analyzed repo."""
    repo_key = f"{owner}/{repo}"
    if repo_key not in analysis_store:
        raise HTTPException(status_code=404, detail="Repository not analyzed yet.")

    return analysis_store[repo_key]["report"]


@app.post("/api/send-email")
async def send_email(req: EmailRequest):
    """Send the CEO report via email."""
    try:
        owner, name = parse_repo_url(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    repo_key = f"{owner}/{name}"
    if repo_key not in analysis_store:
        raise HTTPException(status_code=404, detail="Repository not analyzed yet.")

    report = analysis_store[repo_key]["report"]
    email_sender = EmailSenderAgent()
    result = email_sender.send_report(
        req.to_email, report["report_text"], repo_key
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return result


class ChatRequest(BaseModel):
    question: str
    repo_url: str


@app.post("/api/chat")
async def chat_with_analysis(req: ChatRequest):
    """Chatbot — answers questions about the analysis."""
    from agents.llm_client import ask_llm

    try:
        owner, name = parse_repo_url(req.repo_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    repo_key = f"{owner}/{name}"
    if repo_key not in analysis_store:
        raise HTTPException(status_code=404, detail="Repository not analyzed yet.")

    data = analysis_store[repo_key]
    hs = data["health_scores"]
    ba = data["bug_analysis"]
    pred = data["predictions"]
    overall = hs.get("overall_score", {})

    # Build context for the LLM
    context = f"""Repository: {data['repo_info'].get('name', repo_key)}
Overall Health Score: {overall.get('score', 'N/A')}/100 (Grade: {hs.get('grade', 'N/A')})
Critical Files: {hs.get('critical_count', 0)}
Warning Files: {hs.get('warning_count', 0)}
Healthy Files: {hs.get('healthy_count', 0)}
Open Bugs: {ba.get('open_bugs', 0)}
Total Bugs: {ba.get('total_bugs', 0)}
Avg Bug Resolution: {ba.get('avg_resolution_days', 'N/A')} days
High Risk (90d): {pred.get('summary', {}).get('high_risk_90d', 0)} components

Top Risk Files:
"""
    for fs in hs.get("file_scores", [])[:8]:
        context += f"- {fs['filename']}: health={fs['health_score']}, changes={fs['change_count']}, risk_factors={fs.get('risk_factors', [])}\n"

    answer = ask_llm(
        f"""You are Gitam AI, an intelligent assistant that helps users understand their codebase health analysis.

Context about the analyzed repository:
{context}

User's question: {req.question}

Answer concisely (max 150 words). Be specific with numbers from the data. If the user asks for recommendations, prioritize by impact.""",
        system_prompt="You are Gitam AI, a helpful codebase health assistant. Be concise, friendly, and data-driven.",
        max_tokens=512,
    )

    return {"answer": answer}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "Gitam AI", "analyzed_repos": list(analysis_store.keys())}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

