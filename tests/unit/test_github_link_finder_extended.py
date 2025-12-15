# tests/unit/test_github_link_finder_extended.py
"""Extended tests for github_link_finder module."""

from src.utils.github_link_finder import find_github_url_from_hf


def test_find_github_url_direct_readme(mocker):
    """Test finding GitHub URL from model README."""
    # Mock hf_hub_download to return a dummy path
    mocker.patch("src.utils.github_link_finder.hf_hub_download", return_value="dummy_path")
    
    # Mock open
    mock_open = mocker.mock_open(read_data="Check check [Our Repo](https://github.com/user/repo)")
    mocker.patch("builtins.open", mock_open)
    
    result = find_github_url_from_hf("test/model")
    assert "github.com/user/repo" in result


def test_find_github_url_in_content(mocker):
    """Test finding GitHub URL (raw) in README content."""
    mocker.patch("src.utils.github_link_finder.hf_hub_download", return_value="dummy_path")
    
    content = "Check our repo at https://github.com/user/model-repo"
    mock_open = mocker.mock_open(read_data=content)
    mocker.patch("builtins.open", mock_open)
    
    result = find_github_url_from_hf("test/model")
    assert "github.com/user/model-repo" in result


def test_find_github_url_no_readme(mocker):
    """Test when README download fails."""
    mocker.patch("src.utils.github_link_finder.hf_hub_download", side_effect=Exception("Not found"))
    
    # Needs to proceed to fallback logic
    # No well known repo match
    result = find_github_url_from_hf("some-unknown-org/model")
    assert result is None


def test_find_github_url_api_error(mocker):
    """Test when everything fails."""
    # Mock download failure
    mocker.patch("src.utils.github_link_finder.hf_hub_download", side_effect=Exception("API Error"))
    
    result = find_github_url_from_hf("org/model")
    # Might return None
    assert result is None


def test_find_github_url_empty_input():
    """Test with empty model ID."""
    result = find_github_url_from_hf("")
    assert result is None or result == ""
