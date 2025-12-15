# tests/unit/test_routes_security.py
"""Security-focused route tests."""
from fastapi.testclient import TestClient

from src.api.routes import ALLOWED_URL_DOMAINS, validate_auth_token, validate_url_domain
from src.main import app

client = TestClient(app)


def test_validate_url_domain_github():
    """Test GitHub URL validation."""
    assert validate_url_domain("https://github.com/user/repo") is True


def test_validate_url_domain_huggingface():
    """Test HuggingFace URL validation."""
    assert validate_url_domain("https://huggingface.co/user/model") is True


def test_validate_url_domain_hf_short():
    """Test hf.co URL validation."""
    assert validate_url_domain("https://hf.co/user/model") is True


def test_validate_url_domain_blocked():
    """Test blocked domain."""
    assert validate_url_domain("https://evil.com/malware") is False


def test_validate_url_domain_empty():
    """Test empty URL."""
    assert validate_url_domain("") is True  # Empty is OK (content upload)


def test_validate_url_domain_none():
    """Test None URL would be empty string."""
    assert validate_url_domain("") is True


def test_validate_auth_token_none():
    """Test None auth token."""
    assert validate_auth_token(None) is False


def test_validate_auth_token_empty():
    """Test empty auth token."""
    assert validate_auth_token("") is False


def test_validate_auth_token_valid_admin():
    """Test valid admin token."""
    assert validate_auth_token("bearer admin") is True


def test_allowed_domains_list():
    """Test allowed domains list exists."""
    assert "github.com" in ALLOWED_URL_DOMAINS
    assert "huggingface.co" in ALLOWED_URL_DOMAINS
    assert "hf.co" in ALLOWED_URL_DOMAINS


def test_url_validation_blocks_evil_domain():
    """Integration test - evil domain blocked."""
    client.delete("/reset")
    
    response = client.post("/package", json={
        "url": "https://malicious-site.com/package"
    })
    assert response.status_code == 400
    assert "domain not allowed" in response.json()["detail"]


def test_regex_search_timeout_protection():
    """Test regex search has timeout protection."""
    client.delete("/reset")
    client.post("/package", json={"content": "test", "name": "test-pkg"})
    
    # ReDoS pattern
    response = client.post("/package/byRegEx", json={"RegEx": "(a+)+$"})
    assert response.status_code == 200
    # Should return empty, not timeout
    assert isinstance(response.json(), list)


def test_regex_search_length_limit():
    """Test regex search has length limit."""
    client.delete("/reset")
    client.post("/package", json={"content": "test", "name": "test-pkg"})
    
    # Very long regex
    response = client.post("/package/byRegEx", json={"RegEx": "a" * 600})
    assert response.status_code == 200
    assert response.json() == []
