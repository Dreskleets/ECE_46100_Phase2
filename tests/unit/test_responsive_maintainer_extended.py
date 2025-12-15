# tests/unit/test_responsive_maintainer_extended.py
"""Extended tests for responsive_maintainer metric."""
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from src.metrics.responsive_maintainer import metric


def test_responsive_maintainer_github_success(mocker):
    """Test responsive_maintainer with successful GitHub API call."""
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{
        "created_at": week_ago.isoformat(),
        "closed_at": now.isoformat()
    }]
    
    mocker.patch("requests.get", return_value=mock_response)
    
    resource = {
        "url": "https://github.com/test/repo",
        "category": "CODE"
    }
    
    score, latency = metric(resource)
    
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_responsive_maintainer_github_no_issues(mocker):
    """Test responsive_maintainer when repo has no closed issues."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    
    mocker.patch("requests.get", return_value=mock_response)
    
    resource = {
        "url": "https://github.com/owner/repo",
        "category": "CODE"
    }
    
    score, latency = metric(resource)
    
    # Default for no issues
    assert score == 0.5
    assert latency >= 0


def test_responsive_maintainer_github_api_error(mocker):
    """Test responsive_maintainer when GitHub API fails."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    
    mocker.patch("requests.get", return_value=mock_response)
    
    resource = {
        "url": "https://github.com/owner/repo",
        "category": "CODE"
    }
    
    score, latency = metric(resource)
    
    assert score == 0.5
    assert latency >= 0


def test_responsive_maintainer_huggingface(mocker):
    """Test responsive_maintainer for HuggingFace model."""
    mock_metadata = MagicMock()
    mock_metadata.lastModified = datetime.now(UTC)
    mock_metadata.modelLikes = 150
    
    # Mock at correct location - HuggingFaceService import
    mocker.patch("src.metrics.huggingface_service.HuggingFaceService.fetch_model_metadata", return_value=mock_metadata)
    
    resource = {
        "url": "https://huggingface.co/test/model",
        "category": "MODEL"
    }
    
    score, latency = metric(resource)
    
    # May not get exact value but should be valid
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_responsive_maintainer_huggingface_old_model(mocker):
    """Test responsive_maintainer for old HuggingFace model."""
    old_date = datetime.now(UTC) - timedelta(days=400)
    
    mock_metadata = MagicMock()
    mock_metadata.lastModified = old_date
    mock_metadata.modelLikes = 5
    
    mocker.patch("src.metrics.huggingface_service.HuggingFaceService.fetch_model_metadata", return_value=mock_metadata)
    
    resource = {
        "url": "https://huggingface.co/test/old-model",
        "category": "MODEL"
    }
    
    score, latency = metric(resource)
    
    # Should return some score
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_responsive_maintainer_unknown_url():
    """Test responsive_maintainer with unknown URL source."""
    resource = {
        "url": "https://gitlab.com/test/repo",
        "category": "CODE"
    }
    
    score, latency = metric(resource)
    
    # Default for unknown
    assert score == 0.5
    assert latency >= 0
