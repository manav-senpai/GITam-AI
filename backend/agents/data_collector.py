"""
Data Collector Agent - Pulls data from GitHub API.
Fetches commits, issues, file changes, and diffs for a given repository.
"""

import httpx
from typing import Optional
from datetime import datetime, timedelta


GITHUB_API = "https://api.github.com"


class DataCollectorAgent:
    """Agent that connects to GitHub and collects repository data."""

    def __init__(self, repo_owner: str, repo_name: str, token: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"{GITHUB_API}/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HotspotAI/1.0",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"

    async def _get(self, url: str, params: dict = None) -> dict | list:
        """Make a GET request to GitHub API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def get_repo_info(self) -> dict:
        """Get basic repository information."""
        data = await self._get(self.base_url)
        return {
            "name": data.get("full_name"),
            "description": data.get("description"),
            "language": data.get("language"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "default_branch": data.get("default_branch"),
        }

    async def get_recent_commits(self, days: int = 180, per_page: int = 100) -> list:
        """Get recent commits from the repository."""
        since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        params = {"since": since, "per_page": min(per_page, 100), "page": 1}

        all_commits = []
        # Fetch up to 3 pages (300 commits max)
        for page in range(1, 4):
            params["page"] = page
            try:
                commits = await self._get(f"{self.base_url}/commits", params)
                if not commits:
                    break
                for c in commits:
                    all_commits.append({
                        "sha": c["sha"],
                        "message": c["commit"]["message"][:200],
                        "author": c["commit"]["author"]["name"],
                        "date": c["commit"]["author"]["date"],
                        "url": c["html_url"],
                    })
                if len(commits) < per_page:
                    break
            except Exception:
                break

        return all_commits

    async def get_commit_detail(self, sha: str) -> dict:
        """Get detailed commit info including files changed."""
        data = await self._get(f"{self.base_url}/commits/{sha}")
        files_changed = []
        for f in data.get("files", []):
            files_changed.append({
                "filename": f["filename"],
                "status": f["status"],  # added, modified, removed
                "additions": f["additions"],
                "deletions": f["deletions"],
                "changes": f["changes"],
                "patch": f.get("patch", "")[:3000],  # limit patch size
            })
        return {
            "sha": data["sha"],
            "message": data["commit"]["message"],
            "author": data["commit"]["author"]["name"],
            "date": data["commit"]["author"]["date"],
            "stats": data.get("stats", {}),
            "files": files_changed,
        }

    async def get_issues(self, state: str = "all", per_page: int = 100) -> list:
        """Get repository issues (bugs)."""
        params = {
            "state": state,
            "per_page": per_page,
            "sort": "updated",
            "direction": "desc",
        }

        all_issues = []
        for page in range(1, 3):
            params["page"] = page
            try:
                issues = await self._get(f"{self.base_url}/issues", params)
                if not issues:
                    break
                for issue in issues:
                    if "pull_request" in issue:
                        continue  # skip PRs
                    labels = [l["name"] for l in issue.get("labels", [])]
                    all_issues.append({
                        "number": issue["number"],
                        "title": issue["title"],
                        "state": issue["state"],
                        "labels": labels,
                        "created_at": issue["created_at"],
                        "closed_at": issue.get("closed_at"),
                        "body": (issue.get("body") or "")[:500],
                        "is_bug": any(
                            kw in " ".join(labels).lower()
                            for kw in ["bug", "defect", "error", "fix", "crash"]
                        ),
                    })
                if len(issues) < per_page:
                    break
            except Exception:
                break

        return all_issues

    async def get_file_content(self, path: str, ref: str = None) -> str:
        """Get file content from the repository."""
        params = {}
        if ref:
            params["ref"] = ref
        try:
            data = await self._get(f"{self.base_url}/contents/{path}", params)
            if data.get("encoding") == "base64":
                import base64
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return data.get("content", "")
        except Exception:
            return ""

    async def get_contributors(self) -> list:
        """Get repository contributors."""
        try:
            data = await self._get(f"{self.base_url}/contributors", {"per_page": 30})
            return [
                {
                    "login": c["login"],
                    "contributions": c["contributions"],
                    "avatar": c["avatar_url"],
                }
                for c in data
            ]
        except Exception:
            return []

    async def collect_all(self, days: int = 180) -> dict:
        """Run full data collection pipeline."""
        print("[DataCollector] Starting data collection...")

        repo_info = await self.get_repo_info()
        print(f"[DataCollector] Repo: {repo_info['name']}")

        commits = await self.get_recent_commits(days=days)
        print(f"[DataCollector] Collected {len(commits)} commits")

        issues = await self.get_issues()
        print(f"[DataCollector] Collected {len(issues)} issues")

        contributors = await self.get_contributors()
        print(f"[DataCollector] Collected {len(contributors)} contributors")

        # Get detailed diffs for the last 15 commits
        detailed_commits = []
        for commit in commits[:15]:
            try:
                detail = await self.get_commit_detail(commit["sha"])
                detailed_commits.append(detail)
            except Exception:
                pass
        print(f"[DataCollector] Fetched {len(detailed_commits)} detailed commit diffs")

        return {
            "repo_info": repo_info,
            "commits": commits,
            "detailed_commits": detailed_commits,
            "issues": issues,
            "contributors": contributors,
        }
