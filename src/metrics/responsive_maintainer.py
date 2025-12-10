import logging
import os
import time
from datetime import datetime, timezone, timedelta
import requests

logger = logging.getLogger(__name__)

def metric(resource: dict) -> tuple[float, int]:
    """
    Responsive Maintainer:
    - For GitHub repos: Check average time to close issues
    - For HuggingFace models: Use recent activity (last modified, likes)
    """
    start = time.perf_counter()
    score = 0.0
    
    url = resource.get("url", "")
    
    # HuggingFace Model
    if "huggingface.co" in url and resource.get("category") == "MODEL":
        try:
            from src.metrics.huggingface_service import get_model_metadata
            repo_id = url.split("huggingface.co/")[-1].rstrip("/")
            metadata = get_model_metadata(repo_id)
            
            if metadata:
                # Use last modified date as proxy for active maintenance
                if metadata.lastModified:
                    try:
                        last_mod = datetime.fromisoformat(metadata.lastModified.replace("Z", "+00:00"))
                        days_since_update = (datetime.now(timezone.utc) - last_mod).days
                        
                        # Recent updates = responsive
                        if days_since_update < 30:  # < 1 month
                            score = 0.9
                        elif days_since_update < 90:  # < 3 months
                            score = 0.7
                        elif days_since_update < 180:  # < 6 months
                            score = 0.5
                        elif days_since_update < 365:  # < 1 year
                            score = 0.3
                        else:
                            score = 0.1
                        
                        # Boost for popular models (community engagement)
                        likes = metadata.modelLikes or 0
                        if likes > 100:
                            score = min(1.0, score + 0.1)
                        elif likes > 50:
                            score = min(1.0, score + 0.05)
                            
                    except Exception:
                        score = 0.5  # Default if date parsing fails
                else:
                    score = 0.5
            else:
                score = 0.5
                
        except Exception as e:
            logger.debug(f"HF responsive check failed: {e}")
            score = 0.5
    
    # GitHub Repository
    elif "github.com" in url:
        try:
            # Extract owner/repo
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[-2], parts[-1]
                
                api_url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=closed&per_page=100"
                headers = {}
                token = os.environ.get("GITHUB_TOKEN")
                if token and not token.startswith("ghp_REPLACE"):
                    headers["Authorization"] = f"token {token}"
                
                response = requests.get(api_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    issues = response.json()
                    close_times = []
                    for issue in issues:
                        if "pull_request" in issue:
                            continue # Skip PRs, focus on issues
                        
                        created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                        closed_at = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
                        close_times.append((closed_at - created_at).total_seconds())
                    
                    if close_times:
                        avg_close_time = sum(close_times) / len(close_times)
                        # 1 week = 604800 seconds
                        # 1 month = 2592000 seconds
                        if avg_close_time < 604800:
                            score = 1.0
                        elif avg_close_time > 2592000:
                            score = 0.0
                        else:
                            score = 1.0 - (avg_close_time - 604800) / (2592000 - 604800)
                    else:
                        # No closed issues? Default to 0.5
                        score = 0.5
                else:
                    logger.debug(f"GitHub API returned {response.status_code}")
                    score = 0.5
        except Exception as e:
            logger.debug(f"GitHub responsive check failed: {e}")
            score = 0.5
    else:
        # Unknown source, default
        score = 0.5
            
    latency_ms = int((time.perf_counter() - start) * 1000)
    return float(score), latency_ms
