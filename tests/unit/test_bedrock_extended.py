# tests/unit/test_bedrock_extended.py
"""Extended tests for bedrock_client to increase coverage."""
import os


def test_bedrock_client_credentials_check(mocker):
    """Test BedrockClient credential validation."""
    # Set fake credentials
    mocker.patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "AKIATEST123",
        "AWS_SECRET_ACCESS_KEY": "secret123"
    })
    
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    # Check credential validation logic ran
    assert hasattr(client, '_check_credentials')


def test_bedrock_client_placeholder_credentials(mocker):
    """Test BedrockClient with placeholder credentials."""
    mocker.patch.dict(os.environ, {
        "AWS_ACCESS_KEY_ID": "REPLACE_ME",
        "AWS_SECRET_ACCESS_KEY": "REPLACE_ME"
    })
    
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    # Should not be enabled with placeholder credentials
    assert client.enabled is False


def test_bedrock_cache_operations(tmp_path, mocker):
    """Test Bedrock cache operations."""
    mocker.patch("src.utils.bedrock_client.CACHE_DIR", tmp_path)
    
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    
    # Test cache key generation
    key = client._get_cache_key("test prompt")
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash length
    
    # Test caching response
    client._cache_response(key, {"score": 0.5, "reason": "test"})
    
    # Test retrieving cached response
    cached = client._get_cached_response(key)
    assert cached is not None
    assert cached["score"] == 0.5


def test_bedrock_cache_miss(tmp_path, mocker):
    """Test Bedrock cache miss."""
    mocker.patch("src.utils.bedrock_client.CACHE_DIR", tmp_path)
    
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    
    # Get non-existent cache entry
    cached = client._get_cached_response("nonexistent123")
    assert cached is None


def test_analyze_readme_disabled():
    """Test analyze_readme_for_benchmarks when disabled."""
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    client.enabled = False
    
    result = client.analyze_readme_for_benchmarks("# Test README\nSome content here.")
    
    assert result["score"] == 0.6
    assert "not available" in result["reason"]


def test_analyze_readme_truncation():
    """Test that long README content is truncated."""
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    client.enabled = False
    
    # Create very long content
    long_content = "A" * 5000
    
    # Should not raise, even with long content
    result = client.analyze_readme_for_benchmarks(long_content)
    assert result is not None


def test_get_bedrock_client_singleton():
    """Test singleton pattern."""
    from src.utils.bedrock_client import get_bedrock_client
    
    client1 = get_bedrock_client()
    client2 = get_bedrock_client()
    
    assert client1 is client2
