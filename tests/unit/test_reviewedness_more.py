# tests/unit/test_reviewedness_more.py
"""More tests for reviewedness metric to increase coverage."""

import pytest

from src.metrics.reviewedness import ReviewednessResult, compute_reviewedness, metric


def test_metric_no_local_path():
    """Test metric with no local path."""
    resource = {"url": "https://huggingface.co/user/model"}
    score, latency = metric(resource)
    assert score == 0.0
    assert latency >= 0


def test_metric_success(mocker):
    """Test metric success path."""
    mock_compute = mocker.patch("src.metrics.reviewedness.compute_reviewedness")
    mock_compute.return_value = ReviewednessResult(
        score=0.8,
        total_code_lines=100,
        reviewed_code_lines=80
    )
    
    resource = {"local_path": "/tmp/repo"}
    score, latency = metric(resource)
    
    assert score == 0.8
    assert latency >= 0


def test_metric_negative_score(mocker):
    """Test metric with negative score (error/no repo)."""
    mock_compute = mocker.patch("src.metrics.reviewedness.compute_reviewedness")
    mock_compute.return_value = ReviewednessResult(
        score=-1.0,
        total_code_lines=0,
        reviewed_code_lines=0
    )
    
    resource = {"local_path": "/tmp/repo"}
    score, latency = metric(resource)
    
    assert score == 0.0
    assert latency >= 0


def test_compute_reviewedness_no_git(tmp_path):
    """Test compute_reviewedness on non-git dir."""
    res = compute_reviewedness(tmp_path)
    assert res.score == -1.0
    assert "not a git repository" in res.reason


def test_compute_reviewedness_none():
    """Test compute_reviewedness with None."""
    res = compute_reviewedness(None)
    assert res.score == -1.0


def test_compute_reviewedness_full_flow(tmp_path, mocker):
    """Test full flow mock."""
    # Mock .git check
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    # Mock helpers
    mocker.patch("src.metrics.reviewedness._get_main_branch", return_value="main")
    
    # Mock iter commits
    mocker.patch("src.metrics.reviewedness._iter_commits_with_messages", return_value=[
        ("hash1", "Merge pull request #1"),
        ("hash2", "Direct commit")
    ])
    
    # Mock count loc
    # hash1: 100 lines, reviewed
    # hash2: 50 lines, not reviewed
    mocker.patch("src.metrics.reviewedness._count_loc_for_commit", side_effect=[
        (100, 100),
        (50, 50)
    ])
    
    res = compute_reviewedness(tmp_path)
    
    # Total: 150
    # Reviewed: 100 (because hash1 msg matches keyword)
    # Score: 100/150 = 0.666
    
    assert res.score == pytest.approx(0.666, 0.01)
    assert res.total_code_lines == 150
    assert res.reviewed_code_lines == 100
