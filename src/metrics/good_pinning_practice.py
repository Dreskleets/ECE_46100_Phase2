from __future__ import annotations
import time
import re
from src.utils.github_api import GitHubAPI

def metric(resource: dict) -> tuple[float, int]:
    """
    Good Pinning Practice metric:
    - Check requirements.txt for pinned dependencies (==).
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
                
                # Check requirements.txt
                content = api.get_contents(owner, repo, "requirements.txt")
                if content and "content" in content:
                    import base64
                    try:
                        text = base64.b64decode(content["content"]).decode("utf-8")
                        lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
                        if lines:
                            pinned = [l for l in lines if "==" in l]
                            score = len(pinned) / len(lines)
                        else:
                            score = 1.0 # Empty requirements file treated as compliant
                    except Exception:
                        score = 0.0
                else:
                    # If no requirements.txt, check if it's a library (setup.py/pyproject.toml)
                    # For now, return 0.5 as neutral/unknown
                    score = 0.5
        except Exception:
            score = 0.0

    latency_ms = int((time.perf_counter() - start) * 1000)
    return float(score), latency_ms
