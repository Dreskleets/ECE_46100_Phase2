from huggingface_service import ModelMetadata
from typing import Any


def score_model_size(metadata: ModelMetadata) -> dict[str, float]:
    """Return size compatibility scores per hardware type (0–1)."""
    size_mb = metadata.modelSize / (1024 * 1024)  # MB
    size_gb = size_mb / 1024

    def normalize(value: float, min_val: float, max_val: float) -> float:
        """Linearly scale size into [0,1], clamped."""
        if value <= min_val:
            return 1.0
        elif value >= max_val:
            return 0.0
        return 1 - ((value - min_val) / (max_val - min_val))

    return {
        "raspberry_pi": normalize(size_gb, 0.0, 1.0),  # best <1GB
        "jetson_nano": normalize(size_gb, 0.0, 2.0),  # best <2GB
        "desktop_pc": normalize(size_gb, 0.0, 6.0),  # best <6GB
        "aws_server": normalize(size_gb, 0.0, 10.0),  # best <10GB
    }

def metric(resource: dict[str, Any]) -> tuple[float, int]:
    """
    Compute size score based on GitHub repo size.
    Returns (score, latency).
    """
    import time
    start = time.perf_counter()
    score = 0.0
    
    url = resource.get("url", "")
    if "github.com" in url:
        try:
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                owner, repo = parts[-2], parts[-1]
                from src.utils.github_api import GitHubAPI
                api = GitHubAPI()
                info = api.get_repo_info(owner, repo)
                if info:
                    size_kb = info.get("size", 0)
                    size_mb = size_kb / 1024
                    size_gb = size_mb / 1024
                    
                    # Use a generous limit: 1GB = 1.0, 10GB = 0.0
                    if size_gb <= 1.0:
                        score = 1.0
                    elif size_gb >= 10.0:
                        score = 0.0
                    else:
                        score = 1.0 - ((size_gb - 1.0) / (10.0 - 1.0))
        except Exception:
            score = 0.0

    latency_ms = int((time.perf_counter() - start) * 1000)
    return float(score), latency_ms
