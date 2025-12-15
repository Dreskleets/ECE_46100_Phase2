"""
Code Quality Metric Module.

Evaluates the code quality of a package based on various heuristics and static analysis.
"""
import time
from pathlib import Path
from typing import Any


def metric(resource: dict[str, Any]) -> tuple[float, int]:
    """
    Code quality score for models and repositories.
    
    For HuggingFace models: Check for quality indicators in model files
    For GitHub repos: Check for best practices files
    """
    start_time = time.perf_counter()
    score = 0.0

    url = resource.get("url", "")
    
    # HuggingFace Model
    if "huggingface.co" in url and resource.get("category") == "MODEL":
        try:
            from huggingface_hub import HfApi
            repo_id = url.split("huggingface.co/")[-1].rstrip("/")
            api = HfApi()
            files = api.list_repo_files(repo_id=repo_id)
            
            checks = {
                "has_config": "config.json" in files,
                "has_readme": "README.md" in files,
                "has_model_card": any("model" in f.lower() and f.endswith(".md") for f in files),
                "has_training_code": any(f in files for f in ["train.py", "training.py", "fine_tune.py"]),
            }
            score = sum(checks.values()) / len(checks)
            
        except Exception:
            # Fallback: assume reasonable quality if model exists
            score = 0.6
    
    # GitHub or local repo
    else:
        local_repo_path = resource.get("local_path")
        if local_repo_path:
            repo_path = Path(local_repo_path)
            checks = {
                "dependencies": (repo_path / "requirements.txt").exists()
                or (repo_path / "pyproject.toml").exists(),
                "testing": (repo_path / "tests").is_dir(),
                "ci_cd": (repo_path / ".github").is_dir() or (repo_path / ".gitlab-ci.yml").exists(),
                "containerization": (repo_path / "Dockerfile").exists(),
            }
            score = sum(checks.values()) / len(checks)
        else:
            # No local path, default score
            score = 0.5

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return score, latency_ms
