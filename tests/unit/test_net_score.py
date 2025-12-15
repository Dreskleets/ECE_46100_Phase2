# tests/unit/test_net_score.py
"""Tests for net_score metric."""
from src.metrics.net_score import compute_net_score


def test_net_score_formula():
    """Test that compute_net_score returns a valid score."""
    metric_scores = {
        "ramp_up_time": 0.8,
        "bus_factor": 0.6,
        "license": 1.0,
        "dataset_and_code_score": 0.7,
        "dataset_quality": 0.5,
        "code_quality": 0.9,
        "performance_claims": 0.8,
    }
    
    score = compute_net_score(metric_scores)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_net_score_with_all_metrics():
    """Test net_score with all metrics including trust metrics."""
    metric_scores = {
        "ramp_up_time": 0.8,
        "bus_factor": 0.6,
        "license": 1.0,
        "dataset_and_code_score": 0.7,
        "dataset_quality": 0.5,
        "code_quality": 0.9,
        "performance_claims": 0.8,
        "reproducibility": 0.7,
        "reviewedness": 0.6,
        "treescore": 0.5,
    }
    
    score = compute_net_score(metric_scores)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_net_score_empty_scores():
    """Test net_score with empty scores dict."""
    score = compute_net_score({})
    assert score == 0.0


def test_net_score_partial_metrics():
    """Test net_score with only some metrics."""
    metric_scores = {
        "license": 1.0,
        "bus_factor": 0.5,
    }
    
    score = compute_net_score(metric_scores)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_net_score_clamps_values():
    """Test that values outside [0,1] are clamped."""
    metric_scores = {
        "license": 2.0,  # Should be clamped to 1.0
        "bus_factor": -0.5,  # Should be clamped to 0.0
    }
    
    score = compute_net_score(metric_scores)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
