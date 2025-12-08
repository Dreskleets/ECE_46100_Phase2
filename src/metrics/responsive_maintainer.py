from __future__ import annotations
import time
from datetime import datetime
from src.utils.github_api import GitHubAPI

def metric(resource: dict) -> tuple[float, int]:
    """
    Responsive Maintainer metric:
    - Check average time to close issues via GitHub API.
    - Return (score ∈ [0,1], latency_ms).
    """
    start = time.perf_counter()
    url = resource.get("url", "")
    score = 0.0
    
    if "github.com" in url:
        try:
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[-2], parts[-1]
                api = GitHubAPI()
                
                # Get closed issues to measure resolution time
                # Limit to 100 latest closed issues
                issues = api.get_issues(owner, repo, state="closed")
                if issues:
                    total_time = 0
                    count = 0
                    for issue in issues:
                        # Skip pull requests (which are also issues in API)
                        if "pull_request" in issue:
                            continue
                            
                        if issue.get("created_at") and issue.get("closed_at"):
                            try:
                                created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                                closed = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
                                diff = (closed - created).total_seconds()
                                total_time += diff
                                count += 1
                            except ValueError:
                                continue
                    
                    if count > 0:
                        avg_time = total_time / count
                        # Score: < 24h (86400s) = 1.0, < 3 days = 0.8, < 7 days = 0.6, < 30 days = 0.4, else 0.2
                        if avg_time < 86400: score = 1.0
                        elif avg_time < 3 * 86400: score = 0.8
                        elif avg_time < 7 * 86400: score = 0.6
                        elif avg_time < 30 * 86400: score = 0.4
                        else: score = 0.2
                    else:
                        score = 0.5 # No closed issues (excluding PRs) found
                else:
                    score = 0.0 # API returned empty list or failed
        except Exception:
            score = 0.0

    latency_ms = int((time.perf_counter() - start) * 1000)
    return float(score), latency_ms
