"""
Predictor Agent - Predicts which components are likely to fail in the next 90 days.
Uses COCOMO II model for cost estimation + decay rate trend analysis.
"""

import math
from datetime import datetime


class PredictorAgent:
    """Agent that predicts future component failures based on trends."""

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

        failure_simulation = self._simulate_failures(predictions, code_analysis)

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
            "failure_simulation": failure_simulation,
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
        risk_drivers = file_score.get("risk_drivers", [])

        driver_impact = sum(d.get("impact", 0) for d in risk_drivers)

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

        # Risk drivers create measurable confidence in trend direction
        decay_rate += min(3.0, driver_impact / 25.0)

        # Files with many authors have ownership issues
        if file_score.get("unique_authors", 0) > 3:
            decay_rate += 1

        if file_score.get("unique_authors", 0) <= 1:
            decay_rate += 1.2

        if not file_score.get("has_test_signal", True):
            decay_rate += 1.0

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
            "risk_score_30d": round(100 - score_30d, 1),
            "risk_score_60d": round(100 - score_60d, 1),
            "risk_score_90d": round(100 - score_90d, 1),
            "risk_delta_30_to_90": round((100 - score_90d) - (100 - score_30d), 1),
            "risk_level_30d": risk_30d,
            "risk_level_60d": risk_60d,
            "risk_level_90d": risk_90d,
            "decay_rate": round(decay_rate, 2),
            "risk_factors": risk_factors,
            "risk_drivers": risk_drivers,
            "explanation": self._build_explanation(file_score["filename"], risk_drivers, risk_30d, risk_90d),
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

    def _build_explanation(self, filename: str, drivers: list, risk_30d: str, risk_90d: str) -> str:
        if not drivers:
            return f"{filename} is currently stable with limited risk signals in recent engineering activity."

        top = sorted(drivers, key=lambda d: d.get("impact", 0), reverse=True)[:3]
        why = ", ".join(d.get("driver", "Unknown driver") for d in top)
        return (
            f"Risk trend for {filename} moves from {risk_30d} in 30d to {risk_90d} in 90d "
            f"mainly due to: {why}."
        )

    def _simulate_failures(self, predictions: list, code_analysis: dict) -> dict:
        """Simulate blast radius for top risky components (wow feature)."""
        hotspot_meta = {
            f.get("filename"): f
            for f in code_analysis.get("hotspot_files", [])
            if f.get("filename")
        }
        hotspot_files = list(hotspot_meta.keys())
        simulation_items = []

        ranked_predictions = sorted(
            predictions,
            key=lambda p: (
                self._component_priority(p.get("filename", "")),
                p.get("risk_score_90d", 0),
            ),
            reverse=True,
        )

        for p in ranked_predictions[:5]:
            filename = p.get("filename", "")
            top_dir = filename.split("/")[0] if "/" in filename else "root"

            candidates = [f for f in hotspot_files if f != filename]
            candidates = sorted(
                candidates,
                key=lambda f: (
                    self._shared_subsystem_score(filename, f, top_dir),
                    self._component_priority(f),
                ),
                reverse=True,
            )

            impacted = [
                f for f in candidates
                if self._component_priority(f) >= 0
            ][:5]

            if not impacted:
                impacted = candidates[:3]

            risk_90 = p.get("risk_score_90d", 0)
            trigger_priority = self._component_priority(filename)
            impact_priority = sum(max(0, self._component_priority(f)) for f in impacted)

            estimated_downtime = round(
                1.2
                + (risk_90 / 20.0)
                + (len(impacted) * 0.85)
                + max(0, trigger_priority * 0.7)
                + (impact_priority * 0.2),
                1,
            )
            cascading = max(1, int(round(len(impacted) * 1.2)))

            trigger_info = hotspot_meta.get(filename, {})

            simulation_items.append({
                "trigger_file": filename,
                "risk_level": p.get("risk_level_90d"),
                "trigger_type": self._component_type(filename),
                "impacted_modules": impacted,
                "estimated_downtime_hours": estimated_downtime,
                "cascading_failures": cascading,
                "blast_radius": "high" if len(impacted) >= 4 else "medium" if len(impacted) >= 2 else "low",
                "reason": self._simulation_reason(filename, trigger_info, impacted),
            })

        portfolio_downtime = round(sum(item["estimated_downtime_hours"] for item in simulation_items), 1)
        return {
            "scenarios": simulation_items,
            "portfolio_estimated_downtime_hours": portfolio_downtime,
            "summary": "Simulation is prioritized toward runtime-critical modules; CI/config files are down-weighted for realistic production impact.",
        }

    def _component_priority(self, filename: str) -> int:
        """Higher score means more production-impactful component."""
        f = filename.lower()
        score = 0

        if any(seg in f for seg in ["src/", "backend/", "app/", "core/", "service", "api/"]):
            score += 4
        if any(seg in f for seg in [".github/", "workflow", "docs/", "readme", "changelog", "example"]):
            score -= 4
        if any(seg in f for seg in ["test", "spec", "fixtures/"]):
            score -= 2
        if any(seg in f for seg in ["lock", "package-lock", "yarn.lock", "pnpm-lock", ".env", "docker-compose"]):
            score -= 3

        if f.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".php", ".cs")):
            score += 2
        if f.endswith((".yaml", ".yml", ".toml", ".json", ".md")):
            score -= 1

        return score

    def _component_type(self, filename: str) -> str:
        f = filename.lower()
        if self._component_priority(filename) >= 4:
            return "runtime-core"
        if any(seg in f for seg in [".github/", "workflow", "ci", "pipeline"]):
            return "ci-config"
        if any(seg in f for seg in ["test", "spec"]):
            return "test-suite"
        return "supporting"

    def _shared_subsystem_score(self, root: str, candidate: str, top_dir: str) -> int:
        score = 0
        root_base = root.split("/")[-1].split(".")[0]
        cand_base = candidate.split("/")[-1]

        if candidate.startswith(top_dir + "/"):
            score += 4
        if root_base and root_base in candidate.lower():
            score += 2
        if cand_base.split(".")[0] == root_base:
            score += 2
        return score

    def _simulation_reason(self, trigger: str, trigger_info: dict, impacted: list) -> str:
        change_count = trigger_info.get("change_count", 0)
        additions = trigger_info.get("additions", 0)
        deletions = trigger_info.get("deletions", 0)
        return (
            f"{trigger} is a high-volatility hotspot ({change_count} changes, +{additions}/-{deletions}) "
            f"with dependency adjacency to {len(impacted)} nearby modules."
        )
