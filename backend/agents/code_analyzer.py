"""
Code Analyzer Agent - Analyzes code churn, complexity, and quality.
Identifies hotspot files and provides AI-powered code review.
"""

from collections import Counter, defaultdict
from .llm_client import ask_llm


class CodeAnalyzerAgent:
    """Agent that analyzes code change history and identifies hotspots."""

    def __init__(self):
        self.file_churn = Counter()
        self.file_additions = defaultdict(int)
        self.file_deletions = defaultdict(int)
        self.file_authors = defaultdict(set)
        self.file_last_modified = {}
        self.hotspot_files = []
        self.all_changed_files = set()

    def analyze_commits(self, commits: list, detailed_commits: list) -> dict:
        """Analyze commit history to find code churn and hotspots."""
        print("[CodeAnalyzer] Analyzing commit history...")

        # Analyze basic commits for frequency
        commit_dates = []
        for c in commits:
            commit_dates.append(c["date"])

        # Analyze detailed commits for file-level data
        for dc in detailed_commits:
            author = dc.get("author", "unknown")
            for f in dc.get("files", []):
                filename = f["filename"]
                self.all_changed_files.add(filename)
                self.file_churn[filename] += 1
                self.file_additions[filename] += f.get("additions", 0)
                self.file_deletions[filename] += f.get("deletions", 0)
                self.file_authors[filename].add(author)
                self.file_last_modified[filename] = dc["date"]

        # Identify hotspot files (most frequently changed)
        self.hotspot_files = self.file_churn.most_common(20)

        # Calculate churn rate per file
        file_analysis = []
        for filename, change_count in self.hotspot_files:
            related_tests = self._find_related_tests(filename)
            unique_authors = len(self.file_authors[filename])
            file_analysis.append({
                "filename": filename,
                "change_count": change_count,
                "additions": self.file_additions[filename],
                "deletions": self.file_deletions[filename],
                "unique_authors": unique_authors,
                "authors": list(self.file_authors[filename]),
                "last_modified": self.file_last_modified.get(filename),
                "commit_churn_rate": round((change_count / max(len(commits), 1)) * 100, 1),
                "test_related_files": related_tests,
                "has_test_signal": len(related_tests) > 0 or self._is_test_file(filename),
                "single_maintainer_risk": unique_authors <= 1,
                "churn_score": self._calculate_churn_score(
                    change_count,
                    self.file_additions[filename],
                    self.file_deletions[filename],
                    unique_authors,
                ),
            })

        return {
            "total_commits": len(commits),
            "total_files_changed": len(self.file_churn),
            "hotspot_files": file_analysis,
            "commit_frequency": self._calculate_commit_frequency(commits),
        }

    def _calculate_churn_score(
        self, changes: int, additions: int, deletions: int, authors: int
    ) -> float:
        """Calculate a normalized churn score (0-100). Higher = more risky."""
        # Weight factors
        change_weight = min(changes * 10, 40)  # Max 40 points for frequency
        size_weight = min((additions + deletions) / 50, 30)  # Max 30 for size
        author_weight = min(authors * 5, 15)  # Max 15 for author count
        delete_ratio = (
            (deletions / (additions + deletions) * 15)
            if (additions + deletions) > 0
            else 0
        )

        return min(round(change_weight + size_weight + author_weight + delete_ratio, 1), 100)

    def _is_test_file(self, filename: str) -> bool:
        lower = filename.lower()
        return (
            "/test" in lower
            or "tests/" in lower
            or lower.endswith("_test.py")
            or lower.endswith(".test.js")
            or lower.endswith(".spec.js")
            or lower.endswith(".test.ts")
            or lower.endswith(".spec.ts")
            or lower.endswith(".test.jsx")
            or lower.endswith(".test.tsx")
        )

    def _find_related_tests(self, filename: str) -> list:
        """Find test files that likely cover this file from changed-file history."""
        file_lower = filename.lower()
        base_name = file_lower.split("/")[-1].split(".")[0]
        related = []

        for candidate in self.all_changed_files:
            cand_lower = candidate.lower()
            if not self._is_test_file(cand_lower):
                continue
            if base_name and base_name in cand_lower:
                related.append(candidate)

        return sorted(set(related))[:5]

    def _calculate_commit_frequency(self, commits: list) -> dict:
        """Calculate commit frequency trends."""
        from datetime import datetime

        monthly = defaultdict(int)
        weekly = defaultdict(int)

        for c in commits:
            try:
                dt = datetime.fromisoformat(c["date"].replace("Z", "+00:00"))
                month_key = dt.strftime("%Y-%m")
                week_key = dt.strftime("%Y-W%W")
                monthly[month_key] += 1
                weekly[week_key] += 1
            except Exception:
                pass

        return {
            "monthly": dict(sorted(monthly.items())),
            "weekly": dict(sorted(weekly.items())),
        }

    def get_file_diffs(self, detailed_commits: list, filename: str) -> list:
        """Get all diffs for a specific file across commits."""
        diffs = []
        for dc in detailed_commits:
            for f in dc.get("files", []):
                if f["filename"] == filename:
                    diffs.append({
                        "sha": dc["sha"][:8],
                        "message": dc["message"][:100],
                        "author": dc["author"],
                        "date": dc["date"],
                        "status": f["status"],
                        "additions": f["additions"],
                        "deletions": f["deletions"],
                        "patch": f.get("patch", ""),
                    })
        return diffs

    async def ai_review_file(self, filename: str, file_content: str, diffs: list) -> str:
        """Use LLM to review a hotspot file and provide insights."""
        diff_text = ""
        for d in diffs[:5]:  # Limit to 5 most recent diffs
            diff_text += f"\n--- Commit {d['sha']} by {d['author']} ({d['date'][:10]}) ---\n"
            diff_text += f"Message: {d['message']}\n"
            diff_text += f"Patch:\n{d['patch'][:1000]}\n"

        prompt = f"""You are a senior software engineer reviewing code quality.

Analyze this file and its recent changes:

**File:** `{filename}`

**Current Code (first 3000 chars):**
```
{file_content[:3000]}
```

**Recent Changes (diffs):**
{diff_text[:3000]}

Provide a brief analysis (max 200 words):
1. **What this file does** (1 sentence)
2. **Key concerns** - code smells, complexity issues, anti-patterns
3. **Change pattern** - why is this file changing so often?
4. **Risk level** - Low/Medium/High and why
5. **Recommendation** - 1 specific actionable suggestion to improve it
"""

        return ask_llm(
            prompt,
            system_prompt="You are a senior software engineer specializing in code quality and technical debt analysis. Be concise and actionable.",
        )
