# tests/unit/test_code_quality.py
"""Tests for code_quality metric."""
from unittest.mock import MagicMock

from src.metrics.code_quality import metric


def test_code_quality_huggingface_model(mocker):
    """Test code_quality for HuggingFace model."""
    # Mock HfApi
    mock_api = MagicMock()
    mock_api.list_repo_files.return_value = [
        "config.json", 
        "README.md", 
        "model_card.md",
        "pytorch_model.bin"
    ]
    mocker.patch("huggingface_hub.HfApi", return_value=mock_api)
    
    resource = {
        "url": "https://huggingface.co/test/model",
        "category": "MODEL"
    }
    
    score, latency = metric(resource)
    
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_code_quality_huggingface_api_error(mocker):
    """Test code_quality when HF API fails."""
    mocker.patch("huggingface_hub.HfApi", side_effect=Exception("API Error"))
    
    resource = {
        "url": "https://huggingface.co/test/model",
        "category": "MODEL"
    }
    
    score, latency = metric(resource)
    
    # Should fallback to 0.6
    assert score == 0.6
    assert latency >= 0


def test_code_quality_github_with_local_path(tmp_path):
    """Test code_quality for GitHub repo with local path."""
    # Create some quality indicators
    (tmp_path / "requirements.txt").write_text("fastapi==0.100.0")
    (tmp_path / "tests").mkdir()
    (tmp_path / ".github").mkdir()
    (tmp_path / "Dockerfile").write_text("FROM python:3.10")
    
    resource = {
        "url": "https://github.com/test/repo",
        "local_path": str(tmp_path),
        "category": "CODE"
    }
    
    score, latency = metric(resource)
    
    # All 4 checks pass = 1.0
    assert score == 1.0
    assert latency >= 0


def test_code_quality_github_partial(tmp_path):
    """Test code_quality with partial indicators."""
    # Only create requirements.txt
    (tmp_path / "requirements.txt").write_text("fastapi==0.100.0")
    
    resource = {
        "url": "https://github.com/test/repo",
        "local_path": str(tmp_path),
        "category": "CODE"
    }
    
    score, latency = metric(resource)
    
    # Only 1 of 4 checks pass = 0.25
    assert score == 0.25
    assert latency >= 0


def test_code_quality_no_local_path():
    """Test code_quality without local path."""
    resource = {
        "url": "https://github.com/test/repo",
        "category": "CODE"
    }
    
    score, latency = metric(resource)
    
    # Default score when no local path
    assert score == 0.5
    assert latency >= 0


def test_code_quality_empty_resource():
    """Test code_quality with empty resource."""
    score, latency = metric({})
    
    assert score == 0.5
    assert latency >= 0
