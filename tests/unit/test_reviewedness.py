# tests/unit/test_reviewedness.py
"""Tests for reviewedness metric."""
from src.metrics.reviewedness import ReviewednessResult, compute_reviewedness


def test_reviewedness_result_attributes():
    """Test ReviewednessResult has expected attributes."""
    result = ReviewednessResult(
        score=0.5, 
        total_code_lines=100,
        reviewed_code_lines=50,
        reason="Test reason"
    )
    
    assert result.score == 0.5
    assert result.total_code_lines == 100
    assert result.reviewed_code_lines == 50
    assert result.reason == "Test reason"


def test_compute_reviewedness_none_path():
    """Test compute_reviewedness with None path."""
    result = compute_reviewedness(None)
    
    assert isinstance(result, ReviewednessResult)
    assert result.score == -1.0
    assert "No associated" in result.reason


def test_compute_reviewedness_not_git_repo(tmp_path):
    """Test compute_reviewedness with path that is not a git repo."""
    result = compute_reviewedness(tmp_path)
    
    assert isinstance(result, ReviewednessResult)
    assert result.score == -1.0
    assert "not a git repository" in result.reason


def test_compute_reviewedness_string_path(tmp_path):
    """Test compute_reviewedness accepts string path."""
    result = compute_reviewedness(str(tmp_path))
    
    assert isinstance(result, ReviewednessResult)
    assert result.score == -1.0  # No .git directory
