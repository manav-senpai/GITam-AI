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

        # Common bug keywords
        all_labels = []
        for bug in bugs:
            all_labels.extend(bug.get("labels", []))
        label_counts = Counter(all_labels).most_common(10)

        return {
            "total_issues": len(issues),
            "total_bugs": len(bugs),
            "total_feature_requests": len(non_bugs),
            "open_bugs": len([b for b in bugs if b["state"] == "open"]),
            "closed_bugs": len([b for b in bugs if b["state"] == "closed"]),
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
