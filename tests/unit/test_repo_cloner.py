# tests/unit/test_repo_cloner.py

from unittest.mock import MagicMock

import pytest

from src.utils.repo_cloner import clone_repo_to_temp


def test_clone_repo_failure(mocker):
    """
    Tests that clone_repo_to_temp raises Exception when both git clone and zip download fail.
    """
    # Mock git.Repo.clone_from to raise an exception
    mocker.patch("git.Repo.clone_from", side_effect=Exception("clone failed"))
    
    # Mock requests.get to simulate zip download failure
    mock_response = MagicMock()
    mock_response.status_code = 404
    mocker.patch("requests.get", return_value=mock_response)
    
    # Mock shutil.rmtree to prevent cleanup issues
    mocker.patch("shutil.rmtree")
    
    # The function should raise an Exception when both methods fail
    with pytest.raises(Exception):  # noqa: B017
        clone_repo_to_temp("https://invalid/repo.git")


def test_clone_repo_success_git(mocker):
    """
    Tests successful git clone path.
    """
    # Mock successful git clone
    mock_repo = MagicMock()
    mock_repo.working_dir = "/tmp/test_repo"
    mocker.patch("git.Repo.clone_from", return_value=mock_repo)
    mocker.patch("os.path.exists", return_value=True)
    
    result = clone_repo_to_temp("https://github.com/user/repo")
    assert result is not None


def test_clone_huggingface_model(mocker):
    """
    Tests HuggingFace model cloning.
    """
    # Mock successful git clone for HF
    mock_repo = MagicMock()
    mock_repo.working_dir = "/tmp/hf_model"
    mocker.patch("git.Repo.clone_from", return_value=mock_repo)
    mocker.patch("os.path.exists", return_value=True)
    
    result = clone_repo_to_temp("https://huggingface.co/bert-base-uncased")
    assert result is not None
