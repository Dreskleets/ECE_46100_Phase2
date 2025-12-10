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


def metric(resource: dict[str, Any]) -> tuple[dict[str, float], int]:
    """
    Model size metric - returns scores for different hardware types.
    Returns (dict with 4 hardware scores, latency_ms)
    """
    start = time.perf_counter()
    
    # Default scores if we can't get size
    default_scores = {
        "raspberry_pi": 0.0,
        "jetson_nano": 0.0,
        "desktop_pc": 0.0,
        "aws_server": 0.0
    }
    
    category = resource.get("category", "")
    if category != "MODEL":
        # Only models have size scores
        latency_ms = int((time.perf_counter() - start) * 1000)
        return default_scores, latency_ms
    
    # Try to get model info from HuggingFace
    url = resource.get("url", "")
    if "huggingface.co" not in url:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return default_scores, latency_ms
    
    # Extract model ID from URL
    model_id = resource.get("name", "")
    if not model_id:
        try:
            model_id = url.split("huggingface.co/")[-1].strip("/")
        except:
            pass
    
    if not model_id:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return default_scores, latency_ms
    
    try:
        info = model_info(model_id)
        
        # Get model size in bytes
        size_bytes = 0
        if hasattr(info, 'safetensors') and info.safetensors:
            # Prefer safetensors total size
            if hasattr(info.safetensors, 'total'):
                size_bytes = info.safetensors.total
        elif hasattr(info, 'siblings') and info.siblings:
            # Sum up all file sizes
            for sibling in info.siblings:
                if hasattr(sibling, 'size') and sibling.size:
                    size_bytes += sibling.size
        
        if size_bytes == 0:
            # Fallback: can't determine size
            latency_ms = int((time.perf_counter() - start) * 1000)
            return default_scores, latency_ms
        
        # Convert to GB
        size_gb = size_bytes / (1024 ** 3)
        
        # Calculate scores for each hardware type
        scores = {
            "raspberry_pi": normalize(size_gb, 0.0, 1.0),    # best <1GB
            "jetson_nano": normalize(size_gb, 0.0, 2.0),     # best <2GB
            "desktop_pc": normalize(size_gb, 0.0, 6.0),      # best <6GB
            "aws_server": normalize(size_gb, 0.0, 10.0),     # best <10GB
        }
        
        latency_ms = int((time.perf_counter() - start) * 1000)
        return scores, latency_ms
        
    except (HfHubHTTPError, Exception) as e:
        print(f"DEBUG: size metric error for {model_id}: {e}")
        latency_ms = int((time.perf_counter() - start) * 1000)
        return default_scores, latency_ms
