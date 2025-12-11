from __future__ import annotations

import time
from typing import Any

from huggingface_hub import model_info
from huggingface_hub.utils import HfHubHTTPError


def normalize(value: float, min_val: float, max_val: float) -> float:
    """Linearly scale size into [0,1], clamped."""
    if value <= min_val:
        return 1.0
    elif value >= max_val:
        return 0.0
    return 1 - ((value - min_val) / (max_val - min_val))


# Fallback scores for models where we can't determine size
# Assumes a mid-sized model (~500MB-1GB) - reasonable default
FALLBACK_SCORES = {
    "raspberry_pi": 0.5,
    "jetson_nano": 0.7,
    "desktop_pc": 0.9,
    "aws_server": 0.95,
}


def metric(resource: dict[str, Any]) -> tuple[dict[str, float], int]:
    """
    Model size metric - returns scores for different hardware types.
    Uses HuggingFace API to get actual model size.
    Falls back to reasonable defaults when size can't be determined.
    Returns (dict with 4 hardware scores, latency_ms)
    """
    start = time.perf_counter()
    
    default_scores = {
        "raspberry_pi": 0.0,
        "jetson_nano": 0.0,
        "desktop_pc": 0.0,
        "aws_server": 0.0
    }
    
    category = resource.get("category", "").upper()
    if category != "MODEL":
        latency_ms = int((time.perf_counter() - start) * 1000)
        return default_scores, latency_ms
    
    url = resource.get("url", "")
    name = resource.get("name", "")
    
    # Try to extract model_id from URL
    model_id = None
    if "huggingface.co" in url:
        try:
            # Extract from URL like https://huggingface.co/org/model
            model_id = url.split("huggingface.co/")[-1].strip("/")
        except:
            pass
    
    # If no model_id from URL, use name directly
    if not model_id and name:
        model_id = name
    
    if not model_id:
        # Can't determine model, use fallback
        latency_ms = int((time.perf_counter() - start) * 1000)
        return FALLBACK_SCORES, latency_ms
    
    try:
        info = model_info(model_id)
        
        size_bytes = 0
        if hasattr(info, 'safetensors') and info.safetensors:
            if hasattr(info.safetensors, 'total'):
                size_bytes = info.safetensors.total
        elif hasattr(info, 'siblings') and info.siblings:
            for sibling in info.siblings:
                if hasattr(sibling, 'size') and sibling.size:
                    size_bytes += sibling.size
        
        if size_bytes == 0:
            # Model found but no size info - use fallback
            latency_ms = int((time.perf_counter() - start) * 1000)
            return FALLBACK_SCORES, latency_ms
        
        size_gb = size_bytes / (1024 ** 3)
        
        scores = {
            "raspberry_pi": normalize(size_gb, 0.0, 1.0),
            "jetson_nano": normalize(size_gb, 0.0, 2.0),
            "desktop_pc": normalize(size_gb, 0.0, 6.0),
            "aws_server": normalize(size_gb, 0.0, 10.0),
        }
        
        latency_ms = int((time.perf_counter() - start) * 1000)
        return scores, latency_ms
        
    except (HfHubHTTPError, Exception):
        # Model not found on HuggingFace, use fallback scores
        latency_ms = int((time.perf_counter() - start) * 1000)
        return FALLBACK_SCORES, latency_ms
