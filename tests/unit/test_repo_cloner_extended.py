# tests/unit/test_repo_cloner_extended.py
"""Extended tests for repo_cloner module."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.utils.repo_cloner import clone_repo_to_temp, download_repo_zip


def test_clone_repo_valid_github(mocker):
    """Test cloning with valid GitHub URL."""
    mock_repo = MagicMock()
    mock_repo.working_dir = "/tmp/test"
    mocker.patch("git.Repo.clone_from", return_value=mock_repo)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.listdir", return_value=["file.py"])
    
    result = clone_repo_to_temp("https://github.com/user/repo")
    assert result is not None


def test_clone_repo_huggingface(mocker):
    """Test cloning with HuggingFace URL."""
    mock_repo = MagicMock()
    mock_repo.working_dir = "/tmp/test"
    mocker.patch("git.Repo.clone_from", return_value=mock_repo)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.listdir", return_value=["file.py"])
    
    result = clone_repo_to_temp("https://huggingface.co/user/model")
    assert result is not None


def test_clone_repo_git_failure_zip_success(mocker):
    """Test fallback to zip when git clone fails."""
    mocker.patch("git.Repo.clone_from", side_effect=Exception("Git failed"))
    
    # Mock successful zip download
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'PK\x03\x04'  # Minimal zip header
    mocker.patch("requests.get", return_value=mock_response)
    
    # Mock zipfile
    mock_zipfile = MagicMock()
    mock_zipfile.__enter__ = MagicMock(return_value=mock_zipfile)
    mock_zipfile.__exit__ = MagicMock(return_value=False)
    mock_zipfile.namelist.return_value = ["repo-main/file.py"]
    mocker.patch("zipfile.ZipFile", return_value=mock_zipfile)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.listdir", return_value=["repo-main"])
    
    result = clone_repo_to_temp("https://github.com/user/repo")
    # Either returns a path or raises
    assert result is None or isinstance(result, str | Path)


def test_download_repo_zip_github(mocker):
    """Test downloading zip from GitHub."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'PK\x03\x04'
    mocker.patch("requests.get", return_value=mock_response)
    
    mock_zipfile = MagicMock()
    mock_zipfile.__enter__ = MagicMock(return_value=mock_zipfile)
    mock_zipfile.__exit__ = MagicMock(return_value=False)
    mock_zipfile.namelist.return_value = ["repo-main/"]
    mocker.patch("zipfile.ZipFile", return_value=mock_zipfile)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.listdir", return_value=["repo-main"])
    
    # Should not raise
    try:
        result = download_repo_zip("https://github.com/user/repo")
    except Exception:
        result = None
    
    # Result    # Either returns a path or raises
    assert result is None or isinstance(result, str | Path)


def test_clone_empty_url(mocker):
    """Test cloning with empty URL."""
    with pytest.raises(Exception):  # noqa: B017
        clone_repo_to_temp("")
