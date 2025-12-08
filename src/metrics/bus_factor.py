from __future__ import annotations

import math
import time
from collections import Counter

try:
    from git import Repo
except ImportError:
    Repo = None  # gracefully handle missing GitPython


def compute_bus_factor_from_commits(commits: list[str]) -> float:
    """Entropy-based bus factor calculation from a list of commit authors."""
    if not commits:
        return 0.0

    commit_counts = Counter(commits)
    total_commits = sum(commit_counts.values())
    num_contributors = len(commit_counts)

    # Single contributor → bus factor = 0
    if num_contributors <= 1:
        return 0.0

    # Entropy normalized by max possible entropy
    probabilities = [c / total_commits for c in commit_counts.values()]
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
    return entropy / math.log2(num_contributors)


def compute_bus_factor(commits: list[str]) -> tuple[float, int]:
    """
    Backward-compatible function used in tests.
    Returns (score ∈ [0,1], latency_ms).
    """
    start = time.perf_counter()
    score = compute_bus_factor_from_commits(commits)
    latency_ms = int((time.perf_counter() - start) * 1000)
    return score, latency_ms


def metric(resource: dict) -> tuple[float, int]:
    """
    Bus Factor metric:
    - Extract authors from GitHub API.
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
                from src.utils.github_api import GitHubAPI
                api = GitHubAPI()
                
                # Use contributors endpoint which gives commit counts directly
                contributors = api.get_contributors(owner, repo)
                if contributors:
                    commit_counts = [c["contributions"] for c in contributors]
                    total_commits = sum(commit_counts)
                    num_contributors = len(commit_counts)
                    
                    if num_contributors <= 1:
                        score = 0.0
                    else:
                        probabilities = [c / total_commits for c in commit_counts]
                        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
                        score = entropy / math.log2(num_contributors)
                else:
                    # Fallback to commits
                    commits_data = api.get_commits(owner, repo)
                    authors = []
                    for c in commits_data:
                        if c.get("commit") and c["commit"].get("author"):
                            authors.append(c["commit"]["author"].get("email", "unknown"))
                    score = compute_bus_factor_from_commits(authors)
        except Exception:
            score = 0.0

    latency_ms = int((time.perf_counter() - start) * 1000)
    return float(score), latency_ms
