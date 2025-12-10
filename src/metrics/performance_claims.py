from __future__ import annotations

import logging
import time
from typing import Any

from huggingface_hub import model_info, hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

# Import Bedrock client
from src.utils.bedrock_client import get_bedrock_client

logger = logging.getLogger("phase1_cli")


def metric(resource: dict[str, Any]) -> tuple[float, int]:
    """
    Performance Claims metric using AWS Bedrock for README analysis.
    
    Analyzes model README for:
    - Benchmark results and tables
    - Performance metrics (accuracy, F1, BLEU, etc.)
    - Model comparisons
    - Links to evaluation papers/datasets
    
    Falls back to download-based scoring if Bedrock unavailable.
    """
    start_time = time.perf_counter()
    score = 0.0

    try:
        repo_id = resource.get("name")
        if not repo_id:
            logger.debug("No repo_id in resource")
            return 0.0, int((time.perf_counter() - start_time) * 1000)

        url = resource.get("url", "")
        if "huggingface.co" not in url:
            logger.debug(f"Skipping non-HF resource: {repo_id}")
            return 0.0, int((time.perf_counter() - start_time) * 1000)

        # Get model info for downloads (fallback scoring)
        info = model_info(repo_id)
        downloads = info.downloads or 0
        
        # Try Bedrock README analysis first
        bedrock_client = get_bedrock_client()
        if bedrock_client.enabled:
            try:
                # Download README
                readme_path = hf_hub_download(
                    repo_id=repo_id,
                    filename="README.md",
                    repo_type="model"
                )
                with open(readme_path, 'r', encoding='utf-8', errors='replace') as f:
                    readme_content = f.read()
                
                # Analyze with Bedrock
                result = bedrock_client.analyze_readme_for_benchmarks(readme_content)
                score = result['score']
                logger.debug(f"Bedrock analysis for {repo_id}: {result['reason']}")
                
                # Boost score slightly based on downloads (popular = likely good claims)
                if downloads > 100_000:
                    score = min(1.0, score * 1.1)
                elif downloads > 10_000:
                    score = min(1.0, score * 1.05)
                
            except Exception as e:
                logger.debug(f"Bedrock analysis failed, using download fallback: {e}")
                # Fall through to download-based scoring
                score = _score_by_downloads(downloads)
        else:
            # Bedrock not available, use download-based scoring
            logger.debug("Bedrock not enabled, using download-based scoring")
            score = _score_by_downloads(downloads)

    except HfHubHTTPError:
        logger.error(f"Could not find model on Hub")
        score = 0.0
    except Exception as e:
        logger.exception(f"Unexpected error in performance_claims: {e}")
        score = 0.0

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    return score, latency_ms


def _score_by_downloads(downloads: int) -> float:
    """Fallback scoring based on download popularity."""
    if downloads > 1_000_000:
        return 1.0
    elif downloads > 100_000:
        return 0.8
    elif downloads > 10_000:
        return 0.6
    elif downloads > 1_000:
        return 0.4
    elif downloads > 100:
        return 0.2
    else:
        return 0.1
