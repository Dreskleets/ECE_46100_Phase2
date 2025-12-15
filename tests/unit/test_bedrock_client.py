# tests/unit/test_bedrock_client.py
"""Tests for bedrock_client module."""
import os


def test_bedrock_client_init_no_credentials(mocker):
    """Test BedrockClient initialization without credentials."""
    # Clear any existing credentials
    mocker.patch.dict(os.environ, {"AWS_ACCESS_KEY_ID": "", "AWS_SECRET_ACCESS_KEY": ""}, clear=False)
    
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    
    assert hasattr(client, 'enabled')
    assert client.enabled is False or client.client is None


def test_get_bedrock_client_singleton():
    """Test that get_bedrock_client returns a singleton."""
    from src.utils.bedrock_client import get_bedrock_client
    
    client1 = get_bedrock_client()
    client2 = get_bedrock_client()
    
    assert client1 is client2


def test_bedrock_cache_key():
    """Test cache key generation."""
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    
    key1 = client._get_cache_key("test prompt 1")
    key2 = client._get_cache_key("test prompt 2")
    key3 = client._get_cache_key("test prompt 1")
    
    assert key1 != key2
    assert key1 == key3


def test_analyze_readme_fallback():
    """Test analyze_readme_for_benchmarks fallback when not enabled."""
    from src.utils.bedrock_client import BedrockClient
    
    client = BedrockClient()
    client.enabled = False
    
    result = client.analyze_readme_for_benchmarks("Some README content")
    
    assert isinstance(result, dict)
    assert "score" in result
    assert "reason" in result
    assert result["score"] == 0.6  # Fallback score
