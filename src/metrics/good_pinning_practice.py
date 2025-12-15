"""
Good Pinning Practice Metric Module.

Checks if the package dependencies are pinned to specific versions to ensure reproducibility.
"""
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

def metric(resource: dict) -> tuple[float, int]:
    """
    Good Pinning Practice:
    - For HF models: Check if framework versions are specified
    - For repos: Check if dependencies are pinned (e.g., ==1.2.3)
    """
    start = time.perf_counter()
    score = 0.0
    
    url = resource.get("url", "")
    
    # HuggingFace Model
    if "huggingface.co" in url and resource.get("category") == "MODEL":
        try:
            from src.metrics.huggingface_service import HuggingFaceService
            repo_id = url.split("huggingface.co/")[-1].rstrip("/")
            service = HuggingFaceService()
            config = service.get_model_config(repo_id)
            
            # Check for pinned framework versions in tags/config
            checks = 0
            total = 0
            
            if config:
                # Check for transformers version
                if "transformers_version" in config:
                    checks += 1
                total += 1
                
                # Check for specific architecture (indicates version)
                if "model_type" in config:
                    checks += 1
                total += 1
            
            if total > 0:
                score = checks / total
            else:
                # Default reasonable score for models
                score = 0.7
                
        except Exception:
            score = 0.7  # Default for HF models
    
    # GitHub or local repo
    else:
        local_path = resource.get("local_path")
        if local_path:
            repo_path = Path(local_path)
            
            # Check requirements.txt
            req_file = repo_path / "requirements.txt"
            total_deps = 0
            pinned_deps = 0
            
            if req_file.exists():
                try:
                    content = req_file.read_text(errors="replace")
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        # Check for == or ~=
                        if "==" in line or "~=" in line:
                            pinned_deps += 1
                        total_deps += 1
                except Exception:
                    pass
                    
            # Check package.json
            pkg_json = repo_path / "package.json"
            if pkg_json.exists():
                try:
                    import json
                    data = json.loads(pkg_json.read_text(errors="replace"))
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    all_deps = {**deps, **dev_deps}
                    
                    for ver in all_deps.values():
                        # npm pinning: exact version (no ^ or ~)
                        if not ver.startswith("^") and not ver.startswith("~") and not ver.startswith(">") and not ver.startswith("<"):
                            pinned_deps += 1
                        total_deps += 1
                except Exception:
                    pass
            
            if total_deps > 0:
                score = pinned_deps / total_deps
            else:
                # No dependencies found, but repo exists
                score = 0.6
        else:
            # No local path
            score = 0.6
            
    latency_ms = int((time.perf_counter() - start) * 1000)
    return float(score), latency_ms
