"""
Report Generator Agent - Creates CEO-friendly business impact reports.
Translates technical metrics into business language.
"""

from .llm_client import ask_llm


class ReportGeneratorAgent:
    """Agent that generates business-impact reports for non-technical stakeholders."""

    def generate_report(
        self, repo_info: dict, health_scores: dict, predictions: dict, bug_analysis: dict
    ) -> dict:
        """Generate a comprehensive CEO report."""
        print("[ReportGenerator] Generating CEO report...")

        # Calculate business metrics
        total_risk_cost = sum(
            p.get("estimated_impact", {}).get("estimated_cost_90d", 0)
            for p in predictions.get("predictions", [])
        )
        total_risk_hours = sum(
            p.get("estimated_impact", {}).get("estimated_debug_hours_90d", 0)
            for p in predictions.get("predictions", [])
        )

        high_risk_components = predictions.get("summary", {}).get("high_risk_90d", 0)
        overall_health = health_scores.get("overall_score", {}).get("score", 0)
        grade = health_scores.get("grade", "N/A")

        # Build the prompt for LLM
        report_data = f"""
Repository: {repo_info.get('name', 'Unknown')}
Description: {repo_info.get('description', 'N/A')}
Overall Health Score: {overall_health}/100 (Grade: {grade})

Key Metrics:
- Total files analyzed: {health_scores.get('total_files_analyzed', 0)}
- Critical files: {health_scores.get('critical_count', 0)}
- Warning files: {health_scores.get('warning_count', 0)}
- Healthy files: {health_scores.get('healthy_count', 0)}
- Open bugs: {bug_analysis.get('open_bugs', 0)}
- Average bug resolution: {bug_analysis.get('avg_resolution_days', 'N/A')} days

90-Day Predictions:
- Components at high risk of failure: {high_risk_components}
- Estimated debugging hours (if not addressed): {total_risk_hours} hours
- Estimated cost of inaction: ${total_risk_cost:,.0f}

Top Risk Components:
"""
        for p in predictions.get("predictions", [])[:5]:
            report_data += f"- {p['filename']}: Health {p['current_health']} → {p['predicted_health_90d']} (90d). Risk: {p['risk_level_90d']}. Est. cost: ${p['estimated_impact']['estimated_cost_90d']:,.0f}\n"

        prompt = f"""You are writing an executive briefing for a non-technical CEO about the health of their software product's codebase.

Using the following data, write a professional, clear, and compelling business report. The CEO does not know what "git", "commits", or "code churn" mean. Translate EVERYTHING into business terms.

{report_data}

Structure the report EXACTLY like this (use markdown formatting):

# Engineering Health Report: [Repo Name]
## Executive Summary
(2-3 sentences: overall health, biggest risk, cost of inaction)

## Health Grade: [Grade] ([Score]/100)
(1 sentence explaining what this means in business terms)

## 🔴 Critical Risks
(Bullet points of the top 3-5 risks, written for a business person. Use money and time estimates.)

## 📊 90-Day Forecast
(What will happen if nothing is done in the next 90 days. Be specific about cost and impact.)

## 💡 Recommended Actions
(3-5 specific, prioritized actions. Each with estimated time and impact.)

## 💰 Cost of Inaction vs. Cost of Action
(A simple comparison: how much it costs to fix now vs. how much it will cost later)

Keep the tone professional but urgent. Use numbers. Make the CEO feel informed, not scared. Total length: ~400 words.
"""

        report_text = ask_llm(
            prompt,
            system_prompt="You are a senior engineering consultant writing executive briefings. You translate technical risk into business impact. Be precise, use numbers, and write for a CEO who has no technical background.",
            max_tokens=2048,
        )

        return {
            "report_text": report_text,
            "metrics": {
                "overall_health": overall_health,
                "grade": grade,
                "total_risk_cost": total_risk_cost,
                "total_risk_hours": total_risk_hours,
                "high_risk_components": high_risk_components,
                "critical_files": health_scores.get("critical_count", 0),
                "open_bugs": bug_analysis.get("open_bugs", 0),
            },
        }
