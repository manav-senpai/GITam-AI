"""
Bug Analyzer Agent - Analyzes bug patterns from GitHub issues.
Correlates bugs with code changes to find root causes.
"""

from collections import Counter, defaultdict
from datetime import datetime


class BugAnalyzerAgent:
    """Agent that analyzes bug patterns and correlates them with code changes."""

    def analyze_issues(self, issues: list, commits: list) -> dict:
        """Analyze bugs and their patterns."""
        print("[BugAnalyzer] Analyzing bug patterns...")

        bugs = [i for i in issues if i.get("is_bug")]
        non_bugs = [i for i in issues if not i.get("is_bug")]

        # Bug severity analysis
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for bug in bugs:
            labels_str = " ".join(bug.get("labels", [])).lower()
            if any(kw in labels_str for kw in ["critical", "urgent", "blocker", "crash"]):
                severity_counts["critical"] += 1
            elif any(kw in labels_str for kw in ["high", "major", "important"]):
                severity_counts["high"] += 1
            elif any(kw in labels_str for kw in ["low", "minor", "trivial"]):
                severity_counts["low"] += 1
            else:
                severity_counts["medium"] += 1

        # Bug timeline analysis
        monthly_bugs = defaultdict(int)
        for bug in bugs:
            try:
                dt = datetime.fromisoformat(bug["created_at"].replace("Z", "+00:00"))
                monthly_bugs[dt.strftime("%Y-%m")] += 1
            except Exception:
                pass

        # Resolution time analysis
        resolution_times = []
        for bug in bugs:
            if bug.get("closed_at") and bug.get("created_at"):
                try:
                    created = datetime.fromisoformat(bug["created_at"].replace("Z", "+00:00"))
                    closed = datetime.fromisoformat(bug["closed_at"].replace("Z", "+00:00"))
                    days = (closed - created).days
                    resolution_times.append(days)
                except Exception:
                    pass

        avg_resolution = (
            round(sum(resolution_times) / len(resolution_times), 1)
            if resolution_times
            else None
        )

        # Bug-commit correlation
        bug_commit_correlations = self._correlate_bugs_with_commits(bugs, commits)
        commit_bug_signals = len(bug_commit_correlations)

        estimated_from_commits = False
        signal_source = "issues"

        total_bugs_value = len(bugs)
        open_bugs_value = len([b for b in bugs if b["state"] == "open"])
        closed_bugs_value = len([b for b in bugs if b["state"] == "closed"])

        # Some repositories don't use issue labels consistently; infer a conservative bug count from commit signals.
        if total_bugs_value == 0:
            estimated_from_commits = True
            if commit_bug_signals > 0:
                signal_source = "commit-signals"
                total_bugs_value = max(1, round(commit_bug_signals * 0.6))
            else:
                # Fallback: tiny conservative estimate from activity for repos that don't use issues.
                signal_source = "activity-inference"
                total_bugs_value = max(1, round(len(commits) * 0.1))

            open_bugs_value = max(0, round(total_bugs_value * 0.35))
            closed_bugs_value = max(0, total_bugs_value - open_bugs_value)

        # Common bug keywords
        all_labels = []
        for bug in bugs:
            all_labels.extend(bug.get("labels", []))
        label_counts = Counter(all_labels).most_common(10)

        return {
            "total_issues": len(issues),
            "total_bugs": total_bugs_value,
            "total_feature_requests": len(non_bugs),
            "open_bugs": open_bugs_value,
            "closed_bugs": closed_bugs_value,
            "estimated_from_commits": estimated_from_commits,
            "bug_signal_source": signal_source,
            "commit_bug_signals": commit_bug_signals,
            "severity": severity_counts,
            "monthly_trend": dict(sorted(monthly_bugs.items())),
            "avg_resolution_days": avg_resolution,
            "fastest_resolution_days": min(resolution_times) if resolution_times else None,
            "slowest_resolution_days": max(resolution_times) if resolution_times else None,
            "top_labels": label_counts,
            "bug_commit_correlations": bug_commit_correlations[:10],
            "recent_bugs": [
                {
                    "number": b["number"],
                    "title": b["title"],
                    "state": b["state"],
                    "labels": b["labels"],
                    "created_at": b["created_at"],
                }
                for b in bugs[:10]
            ],
        }

    def _correlate_bugs_with_commits(self, bugs: list, commits: list) -> list:
        """Find commits that might be related to bug fixes."""
        correlations = []
        bug_fix_keywords = ["fix", "bug", "patch", "resolve", "close", "issue", "error", "crash"]

        for commit in commits:
            msg = commit.get("message", "").lower()
            if any(kw in msg for kw in bug_fix_keywords):
                # Try to find related bug number
                import re
                issue_refs = re.findall(r"#(\d+)", commit["message"])
                correlations.append({
                    "commit_sha": commit["sha"][:8],
                    "commit_message": commit["message"][:100],
                    "commit_date": commit["date"],
                    "referenced_issues": [int(ref) for ref in issue_refs],
                    "author": commit["author"],
                })

        return correlations
