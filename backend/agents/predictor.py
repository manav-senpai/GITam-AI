"""
Predictor Agent - Predicts which components are likely to fail in the next 90 days.
Uses COCOMO II model for cost estimation + decay rate trend analysis.
"""

import math
from datetime import datetime
from collections import defaultdict


class PredictorAgent:
    """Agent that predicts future component failures based on trends."""

    # COCOMO II coefficients (Semi-Detached mode — typical for most projects)
    COCOMO_A = 3.0        # Effort multiplier
    COCOMO_B = 1.12       # Scale exponent
    COCOMO_C = 2.5        # Schedule multiplier
    COCOMO_D = 0.35       # Schedule exponent
    DEV_HOURLY_RATE = 75  # Average developer rate ($/hr)
    HOURS_PER_PM = 152    # Working hours per person-month

    def predict(
        self, health_scores: dict, code_analysis: dict, bug_analysis: dict
    ) -> dict:
        """Generate predictions for the next 30/60/90 days."""
        print("[Predictor] Generating failure predictions...")

        file_scores = health_scores.get("file_scores", [])
        predictions = []

        for fs in file_scores:
            prediction = self._predict_file_risk(fs, code_analysis, bug_analysis)
            if prediction:
                predictions.append(prediction)

        # Sort by risk (highest first)
        predictions.sort(key=lambda x: x["risk_score_90d"], reverse=True)

        # Summary statistics
        high_risk_30d = [p for p in predictions if p["risk_level_30d"] == "high"]
        high_risk_60d = [p for p in predictions if p["risk_level_60d"] == "high"]
        high_risk_90d = [p for p in predictions if p["risk_level_90d"] == "high"]

        # Aggregate COCOMO cost breakdown
        cocomo_breakdown = self._aggregate_cocomo(predictions)

        return {
            "predictions": predictions,
            "summary": {
                "total_components_analyzed": len(predictions),
                "high_risk_30d": len(high_risk_30d),
                "high_risk_60d": len(high_risk_60d),
                "high_risk_90d": len(high_risk_90d),
                "top_risk_component": predictions[0]["filename"] if predictions else None,
            },
            "timeline": self._generate_timeline(predictions),
            "cocomo_breakdown": cocomo_breakdown,
        }

    def _estimate_kloc(self, file_score: dict) -> float:
        """Estimate KLOC (thousands of lines of code) from change metrics."""
        # Rough estimation: additions + deletions gives volume of code touched
        additions = file_score.get("additions", 0)
        deletions = file_score.get("deletions", 0)
        total_lines = additions + deletions
        # Assume changed code is ~30% of total file size for hotspot files
        estimated_file_size = max(total_lines * 3.3, 100)
        return estimated_file_size / 1000.0  # Convert to KLOC

    def _cocomo_effort(self, kloc: float, complexity: str = "medium") -> dict:
        """
        COCOMO II effort/cost estimation.
        
        Formula: Effort (PM) = A × (KLOC)^B × EAF
        Cost = Effort × Hours_per_PM × Hourly_Rate
        Schedule = C × (Effort)^D
        
        EAF (Effort Adjustment Factor) based on complexity:
          - low:    0.75 (simple, well-understood code)
          - medium: 1.00 (typical complexity)
          - high:   1.40 (complex, poorly documented)
          - critical: 1.80 (very complex, high coupling)
        """
        eaf_map = {"low": 0.75, "medium": 1.00, "high": 1.40, "critical": 1.80}
        eaf = eaf_map.get(complexity, 1.0)

        if kloc <= 0:
            kloc = 0.1

        effort_pm = self.COCOMO_A * math.pow(kloc, self.COCOMO_B) * eaf
        schedule_months = self.COCOMO_C * math.pow(effort_pm, self.COCOMO_D) if effort_pm > 0 else 0
        cost = effort_pm * self.HOURS_PER_PM * self.DEV_HOURLY_RATE

        # Break down cost components
        development_cost = cost * 0.40
        testing_cost = cost * 0.25
        review_cost = cost * 0.15
        deployment_cost = cost * 0.10
        overhead_cost = cost * 0.10

        return {
            "kloc": round(kloc, 3),
            "effort_person_months": round(effort_pm, 2),
            "schedule_months": round(schedule_months, 2),
            "total_cost": round(cost, 0),
            "effort_hours": round(effort_pm * self.HOURS_PER_PM, 1),
            "complexity": complexity,
            "eaf": eaf,
            "breakdown": {
                "development": round(development_cost, 0),
                "testing": round(testing_cost, 0),
                "code_review": round(review_cost, 0),
                "deployment": round(deployment_cost, 0),
                "overhead": round(overhead_cost, 0),
            },
        }

    def _predict_file_risk(
        self, file_score: dict, code_analysis: dict, bug_analysis: dict
    ) -> dict:
        """Predict risk for a single file over 30/60/90 days."""
        current_health = file_score["health_score"]
        churn = file_score["churn_score"]
        risk_factors = file_score.get("risk_factors", [])

        # Calculate decay rate based on current metrics
        decay_rate = 0

        # High churn files degrade faster
        if churn > 60:
            decay_rate += 3
        elif churn > 40:
            decay_rate += 2
        elif churn > 20:
            decay_rate += 1

        # Many risk factors accelerate decay
        decay_rate += len(risk_factors) * 0.5

        # Files with many authors have ownership issues
        if file_score.get("unique_authors", 0) > 3:
            decay_rate += 1

        # Predict future scores
        score_30d = max(0, current_health - (decay_rate * 3))
        score_60d = max(0, current_health - (decay_rate * 6))
        score_90d = max(0, current_health - (decay_rate * 9))

        # Calculate risk levels
        risk_30d = self._score_to_risk(score_30d)
        risk_60d = self._score_to_risk(score_60d)
        risk_90d = self._score_to_risk(score_90d)

        # Determine complexity from risk factors
        if current_health < 30:
            complexity = "critical"
        elif current_health < 50:
            complexity = "high"
        elif current_health < 70:
            complexity = "medium"
        else:
            complexity = "low"

        # COCOMO-based cost estimation
        kloc = self._estimate_kloc(file_score)
        cocomo = self._cocomo_effort(kloc, complexity)

        return {
            "filename": file_score["filename"],
            "current_health": current_health,
            "predicted_health_30d": round(score_30d, 1),
            "predicted_health_60d": round(score_60d, 1),
            "predicted_health_90d": round(score_90d, 1),
            "risk_score_90d": round(100 - score_90d, 1),
            "risk_level_30d": risk_30d,
            "risk_level_60d": risk_60d,
            "risk_level_90d": risk_90d,
            "decay_rate": round(decay_rate, 2),
            "risk_factors": risk_factors,
            "estimated_impact": {
                "estimated_debug_hours_90d": cocomo["effort_hours"],
                "estimated_cost_90d": cocomo["total_cost"],
                "confidence": "high" if decay_rate > 3 else "medium" if decay_rate > 1.5 else "low",
            },
            "cocomo": cocomo,
            "recommendation": self._generate_recommendation(
                file_score, decay_rate, risk_90d
            ),
        }

    def _score_to_risk(self, score: float) -> str:
        if score >= 70:
            return "low"
        elif score >= 40:
            return "medium"
        return "high"

    def _aggregate_cocomo(self, predictions: list) -> dict:
        """Aggregate COCOMO metrics across all components."""
        total_cost = sum(p.get("cocomo", {}).get("total_cost", 0) for p in predictions)
        total_hours = sum(p.get("cocomo", {}).get("effort_hours", 0) for p in predictions)
        total_pm = sum(p.get("cocomo", {}).get("effort_person_months", 0) for p in predictions)

        # Aggregate breakdown
        dev = sum(p.get("cocomo", {}).get("breakdown", {}).get("development", 0) for p in predictions)
        test = sum(p.get("cocomo", {}).get("breakdown", {}).get("testing", 0) for p in predictions)
        review = sum(p.get("cocomo", {}).get("breakdown", {}).get("code_review", 0) for p in predictions)
        deploy = sum(p.get("cocomo", {}).get("breakdown", {}).get("deployment", 0) for p in predictions)
        overhead = sum(p.get("cocomo", {}).get("breakdown", {}).get("overhead", 0) for p in predictions)

        return {
            "model": "COCOMO II (Semi-Detached)",
            "dev_rate_per_hour": self.DEV_HOURLY_RATE,
            "total_cost": round(total_cost, 0),
            "total_effort_hours": round(total_hours, 1),
            "total_effort_person_months": round(total_pm, 2),
            "breakdown": {
                "development": round(dev, 0),
                "testing": round(test, 0),
                "code_review": round(review, 0),
                "deployment": round(deploy, 0),
                "overhead_management": round(overhead, 0),
            },
        }

    def _generate_recommendation(
        self, file_score: dict, decay_rate: float, risk_90d: str
    ) -> str:
        """Generate a brief recommendation for this file."""
        if risk_90d == "high":
            return f"URGENT: Refactor '{file_score['filename']}' immediately. High churn and multiple risk factors suggest imminent failure."
        elif risk_90d == "medium":
            return f"PLAN: Schedule review of '{file_score['filename']}' within 30 days. Increasing instability detected."
        else:
            return f"MONITOR: '{file_score['filename']}' is stable but should be monitored for changes."

    def _generate_timeline(self, predictions: list) -> list:
        """Generate a risk timeline for visualization."""
        timeline = []
        for period, days_label in [("30d", "risk_level_30d"), ("60d", "risk_level_60d"), ("90d", "risk_level_90d")]:
            high = len([p for p in predictions if p[days_label] == "high"])
            medium = len([p for p in predictions if p[days_label] == "medium"])
            low = len([p for p in predictions if p[days_label] == "low"])
            timeline.append({
                "period": period,
                "high_risk": high,
                "medium_risk": medium,
                "low_risk": low,
            })
        return timeline
