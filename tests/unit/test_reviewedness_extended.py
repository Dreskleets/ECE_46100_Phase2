# tests/unit/test_reviewedness_extended.py
"""Extended tests for reviewedness metric to increase coverage."""
from pathlib import Path

from src.metrics.reviewedness import (
    ReviewednessResult,
    _is_code_file,
    _is_reviewed_commit,
    compute_reviewedness,
)


def test_is_reviewed_commit_merge_pr():
    """Test _is_reviewed_commit with merge PR message."""
    assert _is_reviewed_commit("Merge pull request #42 from user/branch") is True


def test_is_reviewed_commit_reviewed_by():
    """Test _is_reviewed_commit with Reviewed-by message."""
    assert _is_reviewed_commit("Some commit\nReviewed-by: user") is True


def test_is_reviewed_commit_code_review():
    """Test _is_reviewed_commit with Code-Review."""
    assert _is_reviewed_commit("Fix: something\nCode-Review+1") is True


def test_is_reviewed_commit_pull_request():
    """Test _is_reviewed_commit with pull request number."""
    assert _is_reviewed_commit("Related to pull request #123") is True


def test_is_reviewed_commit_not_reviewed():
    """Test _is_reviewed_commit with regular commit."""
    assert _is_reviewed_commit("Fix bug in parser") is False


def test_is_code_file_python():
    """Test _is_code_file with Python file."""
    assert _is_code_file("src/main.py") is True


def test_is_code_file_javascript():
    """Test _is_code_file with JavaScript file."""
    assert _is_code_file("app.js") is True


def test_is_code_file_weights_bin():
    """Test _is_code_file with model weights."""
    assert _is_code_file("pytorch_model.bin") is False


def test_is_code_file_safetensors():
    """Test _is_code_file with safetensors."""
    assert _is_code_file("model.safetensors") is False


def test_is_code_file_onnx():
    """Test _is_code_file with ONNX file."""
    assert _is_code_file("model.onnx") is False


def test_compute_reviewedness_result_dataclass():
    """Test ReviewednessResult dataclass."""
    result = ReviewednessResult(
        score=0.75,
        total_code_lines=1000,
        reviewed_code_lines=750,
        reason="Test reason"
    )
    assert result.score == 0.75
    assert result.total_code_lines == 1000
    assert result.reviewed_code_lines == 750


def test_compute_reviewedness_none():
    """Test compute_reviewedness with None."""
    result = compute_reviewedness(None)
    assert result.score == -1.0
    assert "No associated" in result.reason


def test_compute_reviewedness_not_git(tmp_path):
    """Test compute_reviewedness with non-git directory."""
    result = compute_reviewedness(tmp_path)
    assert result.score == -1.0
    assert "not a git repository" in result.reason


def test_compute_reviewedness_path_object(tmp_path):
    """Test compute_reviewedness accepts Path object."""
    result = compute_reviewedness(Path(tmp_path))
    assert result.score == -1.0
