# tests/unit/test_dataset_quality.py
from unittest.mock import MagicMock

from src.metrics.dataset_quality import metric


class FakeDatasetInfo:
    def __init__(self, cardData=None, downloads=0, likes=0):
        self.cardData = cardData
        self.downloads = downloads
        self.likes = likes


def test_dataset_quality_high_score(mocker):
    """Test a dataset with all quality indicators."""
    mocker.patch(
        "src.metrics.dataset_quality.find_datasets_from_resource",
        return_value=(["https://huggingface.co/datasets/squad"], 5),
    )
    mocker.patch(
        "src.metrics.dataset_quality._get_datasets_from_model_card",
        return_value=[],
    )
    mocker.patch(
        "src.metrics.dataset_quality.dataset_info",
        return_value=FakeDatasetInfo(
            cardData={"dataset_card": "some content"}, downloads=15000, likes=50
        ),
    )

    score, latency = metric({"name": "some/model"})
    # Actual scoring: 0.5 (base) + 0.2 (card) + 0.25 (downloads>10000) + 0.1 (likes>5) = 1.0 (capped)
    assert score >= 0.9  # Allow some flexibility
    assert latency >= 0


def test_dataset_quality_no_link_found(mocker):
    """Test when no dataset link is found."""
    mocker.patch(
        "src.metrics.dataset_quality.find_datasets_from_resource",
        return_value=([], 5),
    )
    mocker.patch(
        "src.metrics.dataset_quality._get_datasets_from_model_card",
        return_value=[],
    )

    score, latency = metric({"name": "some/model", "category": "CODE"})
    assert score == 0.0
    assert latency >= 0


def test_dataset_quality_model_fallback(mocker):
    """Test HuggingFace fallback for models without datasets."""
    mocker.patch(
        "src.metrics.dataset_quality.find_datasets_from_resource",
        return_value=([], 5),
    )
    mocker.patch(
        "src.metrics.dataset_quality._get_datasets_from_model_card",
        return_value=[],
    )
    
    # Mock model_info for fallback
    mock_info = MagicMock()
    mock_info.downloads = 50000
    mocker.patch(
        "src.metrics.dataset_quality.model_info",
        return_value=mock_info,
    )
    
    score, latency = metric({"name": "test/model", "category": "MODEL", "url": "https://huggingface.co/test/model"})
    assert score >= 0.4  # Should get fallback score based on downloads
    assert latency >= 0


def test_dataset_quality_code_category():
    """Test that CODE category returns 0.0."""
    score, latency = metric({"name": "some/code", "category": "CODE"})
    assert score == 0.0
    assert latency >= 0
