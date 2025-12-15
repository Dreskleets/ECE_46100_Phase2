# tests/unit/test_responsive_maintainer.py
"""Tests for responsive_maintainer metric."""
from unittest.mock import MagicMock

from src.metrics.responsive_maintainer import metric


def test_responsive_maintainer_no_path():
    """Test metric when no local path is available."""
    resource = {"url": "https://github.com/test/repo"}
    
    score, latency = metric(resource)
    
    assert isinstance(score, int | float)
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_responsive_maintainer_empty_resource():
    """Test metric with empty resource."""
    resource = {}
    
    score, latency = metric(resource)
    
    assert isinstance(score, int | float)
    assert latency >= 0


def test_github_repo_success(mocker):
    """Test with valid GitHub repo."""
    mock_requests = mocker.patch("requests.get")
    mock_requests.return_value.status_code = 200
    mock_requests.return_value.json.return_value = [
        {"created_at": "2023-01-01T00:00:00Z", "closed_at": "2023-01-02T00:00:00Z"},
        {"created_at": "2023-01-03T00:00:00Z", "closed_at": "2023-01-05T00:00:00Z"},
    ]
    
    resource = {"url": "https://github.com/test/repo"}
    score, latency = metric(resource)
    
    assert isinstance(score, int | float)
    assert latency >= 0


def test_huggingface_model_success(mocker):
    """Test with valid HuggingFace model."""
    mock_metadata = MagicMock()
    mock_metadata.lastModified = "2023-01-01T00:00:00Z"
    mock_metadata.modelLikes = 100
    
    mocker.patch("src.metrics.huggingface_service.HuggingFaceService.fetch_model_metadata", return_value=mock_metadata)
    
    resource = {"url": "https://huggingface.co/test/model", "category": "MODEL"}
    score, latency = metric(resource)
    
    assert isinstance(score, int | float)
    assert latency >= 0


def test_responsive_maintainer_with_local_path(tmp_path, mocker):
    """Test metric with a local git repo path."""
    # Create a fake .git directory
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    
    resource = {"local_path": str(tmp_path)}
    
    # Mock git commands
    mocker.patch("subprocess.run", side_effect=Exception("Git not available"))
    
    score, latency = metric(resource)
    
    assert isinstance(score, int | float)
    assert latency >= 0


def test_responsive_maintainer_huggingface():
    """Test metric with HuggingFace URL."""
    resource = {"url": "https://huggingface.co/bert-base-uncased"}
    
    score, latency = metric(resource)
    
    assert isinstance(score, int | float)
    assert latency >= 0
