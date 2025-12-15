# tests/unit/test_treescore.py
"""Tests for treescore metric."""
from src.metrics.treescore import TreescoreResult, compute_treescore


def test_treescore_result_attributes():
    """Test TreescoreResult has expected attributes."""
    result = TreescoreResult(
        score=0.75, 
        num_parents=3,
        num_scored_parents=2,
        missing_parents=["modelC"]
    )
    
    assert result.score == 0.75
    assert result.num_parents == 3
    assert result.num_scored_parents == 2
    assert result.missing_parents == ["modelC"]


def test_compute_treescore_no_parents():
    """Test compute_treescore with no parents."""
    result = compute_treescore("childModel", [], {})
    
    assert isinstance(result, TreescoreResult)
    assert result.score == -1.0
    assert result.num_parents == 0


def test_compute_treescore_all_parents_scored():
    """Test compute_treescore when all parents have scores."""
    parents = ["modelA", "modelB"]
    scores = {"modelA": 0.8, "modelB": 0.6}
    
    result = compute_treescore("childModel", parents, scores)
    
    assert isinstance(result, TreescoreResult)
    assert result.score == 0.7  # Average of 0.8 and 0.6
    assert result.num_parents == 2
    assert result.num_scored_parents == 2
    assert result.missing_parents == []


def test_compute_treescore_some_parents_missing():
    """Test compute_treescore when some parents don't have scores."""
    parents = ["modelA", "modelB", "modelC"]
    scores = {"modelA": 0.8, "modelB": 0.6}  # modelC missing
    
    result = compute_treescore("childModel", parents, scores)
    
    assert isinstance(result, TreescoreResult)
    assert result.score == 0.7  # Average of 0.8 and 0.6
    assert result.num_parents == 3
    assert result.num_scored_parents == 2
    assert "modelC" in result.missing_parents


def test_compute_treescore_no_scored_parents():
    """Test compute_treescore when no parents have scores."""
    parents = ["modelA", "modelB"]
    scores = {}  # No scores
    
    result = compute_treescore("childModel", parents, scores)
    
    assert isinstance(result, TreescoreResult)
    assert result.score == -1.0
    assert result.num_parents == 2
    assert result.num_scored_parents == 0
