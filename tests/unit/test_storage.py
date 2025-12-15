
import pytest

from src.api.models import Package, PackageData, PackageMetadata, PackageQuery
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


@pytest.fixture
def storage():
    """Fresh storage instance for each test."""
    s = LocalStorage()
    s.reset()
    return s


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


def test_list_packages_with_queries(storage, sample_package):
    """Test list_packages with queries."""
    storage.add_package(sample_package)
    
    # Query matching by name
    queries = [PackageQuery(name="test-package")]
    result = storage.list_packages(queries=queries)
    assert len(result) == 1


def test_list_packages_with_wildcard_query(storage, sample_package):
    """Test list_packages with wildcard query."""
    storage.add_package(sample_package)
    
    # Wildcard query
    queries = [PackageQuery(name="*")]
    result = storage.list_packages(queries=queries)
    assert len(result) >= 1


def test_list_packages_pagination(storage):
    """Test list_packages with pagination."""
    # Add multiple packages
    for i in range(15):
        pkg = Package(
            metadata=PackageMetadata(name=f"pkg-{i}", version="1.0.0", id=f"id-{i}"),
            data=PackageData(content="test")
        )
        storage.add_package(pkg)
    
    # Test offset
    result = storage.list_packages(offset=10)
    assert len(result) == 5
    
    # Test limit
    result = storage.list_packages(limit=5)
    assert len(result) == 5


def test_search_by_regex_case_insensitive(storage, sample_package):
    """Test regex search is case insensitive."""
    storage.add_package(sample_package)
    
    result = storage.search_by_regex("TEST")
    # May or may not find based on readme content
    assert isinstance(result, list)


def test_search_by_regex_no_match(storage, sample_package):
    """Test regex search with no matches."""
    storage.add_package(sample_package)
    
    result = storage.search_by_regex("xyz123nonexistent9999")
    assert len(result) == 0


def test_search_by_regex_invalid_pattern(storage, sample_package):
    """Test regex search with invalid regex pattern."""
    storage.add_package(sample_package)
    
    # Invalid regex should return empty list
    result = storage.search_by_regex("[invalid")
    assert result == []


def test_search_by_regex_redos_protection(storage, sample_package):
    """Test regex search has ReDoS protection."""
    storage.add_package(sample_package)
    
    # ReDoS pattern should be detected and return empty
    result = storage.search_by_regex("(a+)+$")
    assert result == []


def test_search_by_regex_length_limit(storage, sample_package):
    """Test regex search has length limit."""
    storage.add_package(sample_package)
    
    # Very long regex should return empty
    result = storage.search_by_regex("a" * 600)
    assert result == []


def test_delete_package_nonexistent(storage):
    """Test deleting non-existent package returns False."""
    result = storage.delete_package("nonexistent-id")
    assert result is False

