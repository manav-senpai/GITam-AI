"""
Health Scorer Agent - Assigns health scores to codebase components.
Combines signals from code analysis, bug patterns, and other metrics.
"""


class HealthScorerAgent:
    """Agent that calculates health scores for codebase components."""

    def calculate_scores(
        self, code_analysis: dict, bug_analysis: dict, repo_info: dict
    ) -> dict:
        """Calculate overall and per-component health scores."""
        print("[HealthScorer] Calculating health scores...")

        hotspot_files = code_analysis.get("hotspot_files", [])
        
        # Per-file health scores
        file_scores = []
        for f in hotspot_files:
            score = self._score_file(f, bug_analysis)
            file_scores.append(score)

        # Overall repo health score
        overall_score = self._calculate_overall_score(
            file_scores, code_analysis, bug_analysis, repo_info
        )

        # Categorize components
        critical = [f for f in file_scores if f["health_score"] < 40]
        warning = [f for f in file_scores if 40 <= f["health_score"] < 70]
        healthy = [f for f in file_scores if f["health_score"] >= 70]

        return {
            "overall_score": overall_score,
            "total_files_analyzed": len(file_scores),
            "critical_count": len(critical),
            "warning_count": len(warning),
            "healthy_count": len(healthy),
            "file_scores": sorted(file_scores, key=lambda x: x["health_score"]),
            "critical_files": critical,
            "warning_files": warning,
            "healthy_files": healthy,
            "grade": self._score_to_grade(overall_score["score"]),
        }

    def _score_file(self, file_data: dict, bug_analysis: dict) -> dict:
        """Calculate health score for a single file."""
        churn_score = file_data.get("churn_score", 0)

        # Check if file appears in bug-related commits
        bug_correlation_score = 0
        correlations = bug_analysis.get("bug_commit_correlations", [])
        for corr in correlations:
            if file_data["filename"] in corr.get("commit_message", ""):
                bug_correlation_score += 10

        # Invert churn score (high churn = low health)
        health = max(0, 100 - churn_score - min(bug_correlation_score, 30))

        # Determine risk factors
        risk_factors = []
        if churn_score > 50:
            risk_factors.append("High code churn")
        if file_data.get("unique_authors", 0) > 3:
            risk_factors.append("Many contributors (ownership diffusion)")
        if file_data.get("deletions", 0) > file_data.get("additions", 0):
            risk_factors.append("More deletions than additions (instability)")
        if bug_correlation_score > 0:
            risk_factors.append("Correlated with bug fixes")

        return {
            "filename": file_data["filename"],
            "health_score": round(health, 1),
            "churn_score": churn_score,
            "change_count": file_data["change_count"],
            "additions": file_data["additions"],
            "deletions": file_data["deletions"],
            "unique_authors": file_data["unique_authors"],
            "risk_factors": risk_factors,
            "status": self._score_to_status(health),
        }

    def _calculate_overall_score(
        self, file_scores: list, code_analysis: dict, bug_analysis: dict, repo_info: dict
    ) -> dict:
        """Calculate the overall repository health score."""
        if not file_scores:
            return {"score": 75, "breakdown": {}}

        # Component scores
        avg_file_health = sum(f["health_score"] for f in file_scores) / len(file_scores)
        
        # Bug density score (fewer bugs = higher score)
        total_bugs = bug_analysis.get("total_bugs", 0)
        open_bugs = bug_analysis.get("open_bugs", 0)
        bug_score = max(0, 100 - (open_bugs * 5) - (total_bugs * 0.5))

        # Activity score (regular commits = healthy)
        total_commits = code_analysis.get("total_commits", 0)
        activity_score = min(100, total_commits * 0.5)

        # Resolution speed score
        avg_resolution = bug_analysis.get("avg_resolution_days")
        resolution_score = 80
        if avg_resolution:
            if avg_resolution < 3:
                resolution_score = 95
            elif avg_resolution < 7:
                resolution_score = 80
            elif avg_resolution < 30:
                resolution_score = 60
            else:
                resolution_score = 40

        # Weighted overall score
        overall = (
            avg_file_health * 0.35
            + bug_score * 0.25
            + activity_score * 0.2
            + resolution_score * 0.2
        )

        return {
            "score": round(overall, 1),
            "breakdown": {
                "code_health": round(avg_file_health, 1),
                "bug_density": round(bug_score, 1),
                "development_activity": round(activity_score, 1),
                "bug_resolution_speed": round(resolution_score, 1),
            },
        }

    def _score_to_status(self, score: float) -> str:
        if score >= 70:
            return "healthy"
        elif score >= 40:
            return "warning"
        return "critical"

    def _score_to_grade(self, score: float) -> str:
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        return "F"
