# tests/unit/test_dataset_quality_extended.py
"""Extended tests for dataset_quality metric."""
from unittest.mock import MagicMock

from src.metrics.dataset_quality import metric


def test_dataset_quality_no_name():
    """Test with no name in resource."""
    resource = {}
    score, latency = metric(resource)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_dataset_quality_github_url():
    """Test with GitHub URL (not HuggingFace)."""
    resource = {"name": "test", "url": "https://github.com/user/repo"}
    score, latency = metric(resource)
    
    # Returns fallback for non-HF
    assert isinstance(score, float)
    assert latency >= 0


def test_dataset_quality_huggingface_url(mocker):
    """Test with HuggingFace URL."""
    mock_info = MagicMock()
    mock_info.cardData = {"datasets": ["dataset1", "dataset2"]}
    mock_info.downloads = 5000
    mock_info.likes = 20
    
    mocker.patch("src.metrics.dataset_quality.model_info", return_value=mock_info)
    
    resource = {"name": "test/model", "url": "https://huggingface.co/test/model"}
    score, latency = metric(resource)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_dataset_quality_high_downloads(mocker):
    """Test with high downloads."""
    mock_info = MagicMock()
    mock_info.cardData = None
    mock_info.downloads = 100000
    mock_info.likes = 500
    
    mocker.patch("src.metrics.dataset_quality.model_info", return_value=mock_info)
    
    resource = {"name": "popular/model", "url": "https://huggingface.co/popular/model"}
    score, latency = metric(resource)
    
    # High downloads should give some score
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_dataset_quality_api_error(mocker):
    """Test when HF API fails."""
    mocker.patch("src.metrics.dataset_quality.model_info", side_effect=Exception("API Error"))
    
    resource = {"name": "test/model", "url": "https://huggingface.co/test/model"}
    score, latency = metric(resource)
    
    # Should return fallback score
    assert isinstance(score, float)
    assert latency >= 0


def test_dataset_quality_no_model_card(mocker):
    """Test when model has no card data."""
    mock_info = MagicMock()
    mock_info.cardData = None
    mock_info.downloads = 100
    mock_info.likes = 5
    
    mocker.patch("src.metrics.dataset_quality.model_info", return_value=mock_info)
    
    resource = {"name": "no-card/model", "url": "https://huggingface.co/no-card/model"}
    score, latency = metric(resource)
    
    assert isinstance(score, float)
    assert latency >= 0
