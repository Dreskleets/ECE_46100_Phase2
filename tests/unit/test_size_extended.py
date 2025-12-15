# tests/unit/test_size_extended.py
"""Extended tests for size metric."""
from unittest.mock import MagicMock

from src.metrics.size import get_model_size_via_http, metric, normalize


def test_normalize_small():
    """Test normalize with small values."""
    assert normalize(0.0, 0.0, 10.0) == 1.0
    assert normalize(-1.0, 0.0, 10.0) == 1.0


def test_normalize_large():
    """Test normalize with values at or beyond max."""
    assert normalize(10.0, 0.0, 10.0) == 0.0
    assert normalize(15.0, 0.0, 10.0) == 0.0


def test_normalize_mid():
    """Test normalize with mid-range values."""
    result = normalize(5.0, 0.0, 10.0)
    assert 0.4 <= result <= 0.6  # Should be around 0.5


def test_metric_non_model():
    """Test metric with non-MODEL category returns zeros."""
    resource = {"category": "CODE", "url": "https://github.com/test/repo"}
    
    scores, latency = metric(resource)
    
    assert isinstance(scores, dict)
    assert all(v == 0.0 for v in scores.values())
    assert latency >= 0


def test_metric_no_url():
    """Test metric with no URL returns zeros."""
    resource = {"category": "MODEL", "url": ""}
    
    scores, latency = metric(resource)
    
    assert isinstance(scores, dict)
    assert all(v == 0.0 for v in scores.values())


def test_metric_non_hf_url():
    """Test metric with non-HuggingFace URL returns zeros."""
    resource = {"category": "MODEL", "url": "https://github.com/test/model"}
    
    scores, latency = metric(resource)
    
    assert isinstance(scores, dict)
    assert all(v == 0.0 for v in scores.values())


def test_metric_hf_url(mocker):
    """Test metric with HuggingFace URL."""
    mock_info = MagicMock()
    mock_info.safetensors = MagicMock(total=1_000_000_000)  # 1GB
    mock_info.siblings = []
    
    mocker.patch("src.metrics.size.model_info", return_value=mock_info)
    
    resource = {"category": "MODEL", "url": "https://huggingface.co/test/model"}
    
    scores, latency = metric(resource)
    
    assert isinstance(scores, dict)
    assert "raspberry_pi" in scores
    assert "jetson_nano" in scores
    assert "desktop_pc" in scores
    assert "aws_server" in scores


def test_get_model_size_via_http_no_files():
    """Test HTTP fallback with no model files."""
    result = get_model_size_via_http("test/model", [])
    
    assert isinstance(result, int)
