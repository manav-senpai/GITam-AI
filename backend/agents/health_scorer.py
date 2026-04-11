"""
Health Scorer Agent - Assigns health scores to codebase components.
Combines signals from code analysis, bug patterns, and other metrics.
"""


class HealthScorerAgent:
    """Agent that calculates health scores for codebase components."""

    WEIGHTS = {
        "code_quality": 0.30,
        "bug_density": 0.25,
        "test_coverage": 0.20,
        "commit_stability": 0.15,
        "ownership_risk": 0.10,
    }

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
        has_test_signal = file_data.get("has_test_signal", False)
        commit_churn_rate = file_data.get("commit_churn_rate", 0)
        unique_authors = file_data.get("unique_authors", 0)
        total_issues = max(1, bug_analysis.get("total_issues", 0))
        open_bug_rate = bug_analysis.get("open_bugs", 0) / total_issues

        # Check if file appears in bug-related commits
        bug_correlation_score = 0
        correlations = bug_analysis.get("bug_commit_correlations", [])
        for corr in correlations:
            if file_data["filename"] in corr.get("commit_message", ""):
                bug_correlation_score += 10

        code_quality_score = max(35, 100 - min(65, (churn_score * 0.55)))
        bug_density_score = max(55, 100 - min(45, bug_correlation_score * 1.6 + open_bug_rate * 25))
        # Missing direct test signal does not always mean poor coverage in mature repos.
        test_coverage_score = 90 if has_test_signal else 52
        commit_stability_score = max(50, 100 - min(50, churn_score * 0.6 + commit_churn_rate * 0.35))

        if unique_authors <= 1:
            ownership_score = 62
        elif unique_authors <= 3:
            ownership_score = 90
        elif unique_authors <= 8:
            ownership_score = 93
        else:
            ownership_score = 88

        health = (
            code_quality_score * self.WEIGHTS["code_quality"]
            + bug_density_score * self.WEIGHTS["bug_density"]
            + test_coverage_score * self.WEIGHTS["test_coverage"]
            + commit_stability_score * self.WEIGHTS["commit_stability"]
            + ownership_score * self.WEIGHTS["ownership_risk"]
        )

        # Determine risk factors
        risk_factors = []
        if churn_score > 50:
            risk_factors.append("High code churn")
        if unique_authors > 12:
            risk_factors.append("Many contributors (ownership diffusion)")
        if file_data.get("deletions", 0) > file_data.get("additions", 0):
            risk_factors.append("More deletions than additions (instability)")
        if bug_correlation_score > 0:
            risk_factors.append("Correlated with bug fixes")
        if not has_test_signal:
            risk_factors.append("Low test coverage signal")
        if unique_authors <= 1:
            risk_factors.append("Single contributor risk")

        risk_drivers = []
        if churn_score > 50:
            risk_drivers.append({
                "driver": "High commit churn",
                "impact": round(min(30, churn_score * 0.35), 1),
                "evidence": f"Churn score {round(churn_score, 1)} from {file_data.get('change_count', 0)} recent changes",
            })
        if not has_test_signal:
            risk_drivers.append({
                "driver": "Low test coverage",
                "impact": 14.0,
                "evidence": "No related test file found in recent changed files",
            })
        if bug_correlation_score > 0:
            risk_drivers.append({
                "driver": "High bug density",
                "impact": round(min(24, bug_correlation_score * 0.9), 1),
                "evidence": "File appears in bug-fix correlated commit patterns",
            })
        if unique_authors <= 1:
            risk_drivers.append({
                "driver": "Single contributor risk",
                "impact": 14.0,
                "evidence": "Only one active maintainer touched this hotspot recently",
            })

        risk_tags = []
        if churn_score > 50:
            risk_tags.append("high-churn")
        if unique_authors <= 1:
            risk_tags.append("single-maintainer")
        if not has_test_signal:
            risk_tags.append("low-test-coverage")
        if bug_correlation_score > 0:
            risk_tags.append("bug-prone")

        return {
            "filename": file_data["filename"],
            "health_score": round(health, 1),
            "churn_score": churn_score,
            "commit_churn_rate": commit_churn_rate,
            "change_count": file_data["change_count"],
            "additions": file_data["additions"],
            "deletions": file_data["deletions"],
            "unique_authors": unique_authors,
            "has_test_signal": has_test_signal,
            "test_related_files": file_data.get("test_related_files", []),
            "score_breakdown": {
                "code_quality": round(code_quality_score, 1),
                "bug_density": round(bug_density_score, 1),
                "test_coverage": round(test_coverage_score, 1),
                "commit_stability": round(commit_stability_score, 1),
                "ownership_risk": round(ownership_score, 1),
            },
            "risk_factors": risk_factors,
            "risk_drivers": risk_drivers,
            "risk_tags": risk_tags,
            "status": self._score_to_status(health),
        }

    def _calculate_overall_score(
        self, file_scores: list, code_analysis: dict, bug_analysis: dict, repo_info: dict
    ) -> dict:
        """Calculate the overall repository health score."""
        if not file_scores:
            return {"score": 75, "breakdown": {}}

        avg_code_quality = sum(f.get("score_breakdown", {}).get("code_quality", 70) for f in file_scores) / len(file_scores)
        avg_test_coverage = sum(f.get("score_breakdown", {}).get("test_coverage", 50) for f in file_scores) / len(file_scores)
        avg_ownership = sum(f.get("score_breakdown", {}).get("ownership_risk", 60) for f in file_scores) / len(file_scores)

        total_bugs = bug_analysis.get("total_bugs", 0)
        open_bugs = bug_analysis.get("open_bugs", 0)
        total_issues = max(1, bug_analysis.get("total_issues", 0))
        bug_rate = total_bugs / total_issues
        open_bug_rate = open_bugs / total_issues
        total_commits = code_analysis.get("total_commits", 0)
        open_bugs_per_100_commits = (open_bugs / max(1, total_commits)) * 100
        # Normalize by issue volume so large active repos are not unfairly punished.
        if total_issues < 5:
            bug_density_score = 68
        else:
            bug_density_score = max(
                70,
                100 - min(30, open_bugs_per_100_commits * 1.2 + bug_rate * 6),
            )

        avg_churn = sum(f.get("churn_score", 0) for f in file_scores) / len(file_scores)
        monthly_commits = list(code_analysis.get("commit_frequency", {}).get("monthly", {}).values())
        if len(monthly_commits) >= 2:
            avg_commits = sum(monthly_commits) / len(monthly_commits)
            variance = sum((x - avg_commits) ** 2 for x in monthly_commits) / len(monthly_commits)
            volatility = (variance ** 0.5)
            normalized_volatility = min(40, volatility * 4)
        else:
            normalized_volatility = 12
        if total_commits < 20:
            commit_stability_score = max(42, 100 - min(58, avg_churn * 0.6 + normalized_volatility * 1.15))
        else:
            commit_stability_score = max(60, 100 - min(40, avg_churn * 0.42 + normalized_volatility * 0.75))

        critical_ratio = len([f for f in file_scores if f.get("health_score", 100) < 40]) / max(1, len(file_scores))
        low_test_ratio = len([f for f in file_scores if not f.get("has_test_signal", False)]) / max(1, len(file_scores))
        maturity_bonus = 0
        if total_commits >= 40:
            maturity_bonus += 4
        if total_commits >= 80:
            maturity_bonus += 2
        if open_bug_rate < 0.2:
            maturity_bonus += 3
        if critical_ratio < 0.25:
            maturity_bonus += 3
        if avg_code_quality >= 85 and bug_density_score >= 72:
            maturity_bonus += 4

        low_maturity_penalty = 0
        if total_commits < 20:
            low_maturity_penalty += 10
        elif total_commits < 40:
            low_maturity_penalty += 5
        if total_issues == 0 and total_commits < 30:
            low_maturity_penalty += 5
        if low_test_ratio > 0.6:
            low_maturity_penalty += 4
        if critical_ratio > 0.35:
            low_maturity_penalty += 4

        weighted = (
            avg_code_quality * self.WEIGHTS["code_quality"]
            + bug_density_score * self.WEIGHTS["bug_density"]
            + avg_test_coverage * self.WEIGHTS["test_coverage"]
            + commit_stability_score * self.WEIGHTS["commit_stability"]
            + avg_ownership * self.WEIGHTS["ownership_risk"]
        )
        overall = min(97, max(25, weighted + maturity_bonus - low_maturity_penalty))

        return {
            "score": round(overall, 1),
            "breakdown": {
                "code_quality": round(avg_code_quality, 1),
                "bug_density": round(bug_density_score, 1),
                "test_coverage": round(avg_test_coverage, 1),
                "commit_stability": round(commit_stability_score, 1),
                "ownership_risk": round(avg_ownership, 1),
            },
            "weights": {
                "code_quality": 30,
                "bug_density": 25,
                "test_coverage": 20,
                "commit_stability": 15,
                "ownership_risk": 10,
            },
            "calibration": {
                "maturity_bonus": round(maturity_bonus, 1),
                "low_maturity_penalty": round(low_maturity_penalty, 1),
                "open_bug_rate": round(open_bug_rate, 3),
                "open_bugs_per_100_commits": round(open_bugs_per_100_commits, 2),
                "critical_file_ratio": round(critical_ratio, 3),
                "low_test_ratio": round(low_test_ratio, 3),
            },
            "formula": "Weighted health model with normalized bug rates and maturity bonus",
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
