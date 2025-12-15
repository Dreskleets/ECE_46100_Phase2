# tests/unit/test_huggingface_service.py
"""Tests for huggingface_service module."""
from datetime import datetime

from src.metrics.huggingface_service import HuggingFaceService, ModelMetadata


class TestModelMetadata:
    """Test the ModelMetadata class."""
    
    def test_init_and_attributes(self):
        """Test ModelMetadata initialization."""
        meta = ModelMetadata(
            name="test/model",
            category="text-classification",
            size=1_000_000_000,
            license="MIT",
            downloads=50000,
            likes=100,
            last_modified=datetime.now(),
            files=["model.safetensors", "config.json"]
        )
        
        assert meta.modelName == "test/model"
        assert meta.modelCategory == "text-classification"
        assert meta.modelSize == 1_000_000_000
        assert meta.license == "MIT"
        assert meta.timesDownloaded == 50000
        assert meta.modelLikes == 100
        assert len(meta.files) == 2
    
    def test_pretty_size_units(self):
        """Test pretty_size method."""
        # Create instance with 1GB
        meta = ModelMetadata(
            name="test/model",
            category="model",
            size=1_000_000_000,  # ~1GB
            license="MIT",
            downloads=0,
            likes=0,
            last_modified=datetime.now(),
            files=[]
        )
        
        pretty = meta.pretty_size()
        assert "MB" in pretty or "GB" in pretty
    
    def test_repr(self):
        """Test __repr__ method."""
        meta = ModelMetadata(
            name="test/model",
            category="text",
            size=1_000_000,
            license="MIT",
            downloads=100,
            likes=10,
            last_modified=datetime.now(),
            files=[]
        )
        
        repr_str = repr(meta)
        assert "test/model" in repr_str
        assert "ModelMetadata" in repr_str


class TestHuggingFaceService:
    """Tests for HuggingFaceService class."""
    
    def test_init_no_token(self):
        """Test HuggingFaceService initialization without token."""
        service = HuggingFaceService()
        assert hasattr(service, 'api')
    
    def test_fetch_model_metadata_invalid(self):
        """Test fetch_model_metadata with invalid model."""
        service = HuggingFaceService()
        result = service.fetch_model_metadata("this-model-definitely-does-not-exist-12345")
        
        # Should return None for invalid model
        assert result is None
    
    def test_get_raw_model_info_invalid(self):
        """Test get_raw_model_info with invalid model."""
        service = HuggingFaceService()
        result = service.get_raw_model_info("this-also-does-not-exist-12345")
        
        # Should return None for invalid model
        assert result is None
