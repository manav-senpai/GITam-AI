"""
Predictor Agent - Predicts which components are likely to fail in the next 90 days.
Uses trend analysis on health metrics.
"""

from datetime import datetime
from collections import defaultdict


class PredictorAgent:
    """Agent that predicts future component failures based on trends."""

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

        # Estimated impact
        impact = self._estimate_impact(file_score, decay_rate)

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
            "estimated_impact": impact,
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

    def _estimate_impact(self, file_score: dict, decay_rate: float) -> dict:
        """Estimate business impact of not addressing this file."""
        # Simple heuristic-based estimation
        base_hours = file_score.get("change_count", 1) * 2  # hours spent changing
        risk_multiplier = 1 + (decay_rate * 0.5)

        estimated_debug_hours = round(base_hours * risk_multiplier, 1)
        estimated_cost = round(estimated_debug_hours * 75, 0)  # $75/hr dev rate

        return {
            "estimated_debug_hours_90d": estimated_debug_hours,
            "estimated_cost_90d": estimated_cost,
            "confidence": "medium" if decay_rate > 2 else "low",
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
