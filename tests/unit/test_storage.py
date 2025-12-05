
import pytest

from src.api.models import Package, PackageData, PackageMetadata
from src.services.storage import LocalStorage


@pytest.fixture
def sample_package():
    return Package(
        metadata=PackageMetadata(
            name="test-package",
            version="1.0.0",
            id="test-id"
        ),
        data=PackageData(
            content="base64content",
            url="https://github.com/test/repo",
            jsprogram="console.log('test')"
        )
    )

def test_local_storage(sample_package):
    storage = LocalStorage()
    
    # Test Add
    storage.add_package(sample_package)
    assert "test-id" in storage.packages
    
    # Test Get
    pkg = storage.get_package("test-id")
    assert pkg == sample_package
    assert storage.get_package("non-existent") is None
    
    # Test List
    pkgs = storage.list_packages()
    assert len(pkgs) == 1
    assert pkgs[0].name == "test-package"
    
    # Test Delete
    storage.delete_package("test-id")
    assert "test-id" not in storage.packages
    
    # Test Reset
    storage.add_package(sample_package)
    storage.reset()
    assert len(storage.packages) == 0


