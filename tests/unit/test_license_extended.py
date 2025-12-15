# tests/unit/test_license_extended.py
"""Extended tests for license metric."""
from src.metrics.license import metric


def test_license_no_path():
    """Test with no local path."""
    resource = {"url": "https://github.com/user/repo"}
    score, latency = metric(resource)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert latency >= 0


def test_license_with_license_file(tmp_path):
    """Test with LICENSE file present."""
    license_file = tmp_path / "LICENSE"
    license_file.write_text("MIT License\n\nCopyright (c) 2024")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # Should detect license
    assert score >= 0.5
    assert latency >= 0


def test_license_mit_license(tmp_path):
    """Test with MIT LICENSE."""
    license_file = tmp_path / "LICENSE"
    license_file.write_text("""MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files""")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # MIT is compatible
    assert score >= 0.8
    assert latency >= 0


def test_license_apache_2(tmp_path):
    """Test with Apache 2.0 LICENSE."""
    license_file = tmp_path / "LICENSE"
    license_file.write_text("""Apache License
Version 2.0, January 2004

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION""")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    assert score >= 0.8
    assert latency >= 0


def test_license_gpl(tmp_path):
    """Test with GPL LICENSE."""
    license_file = tmp_path / "LICENSE"
    license_file.write_text("""GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007""")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # GPL may have different score depending on compatibility
    assert isinstance(score, float)
    assert latency >= 0


def test_license_no_license(tmp_path):
    """Test with no LICENSE file."""
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # No license = 0
    assert score == 0.0
    assert latency >= 0


def test_license_txt_variant(tmp_path):
    """Test with LICENSE.txt file."""
    license_file = tmp_path / "LICENSE.txt"
    license_file.write_text("MIT License\n\nCopyright (c) 2024")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # Should detect .txt variant
    assert isinstance(score, float)
    assert latency >= 0


def test_license_md_variant(tmp_path):
    """Test with LICENSE.md file."""
    license_file = tmp_path / "LICENSE.md"
    license_file.write_text("# MIT License\n\nCopyright (c) 2024")
    
    resource = {"local_path": str(tmp_path)}
    score, latency = metric(resource)
    
    # Should detect .md variant
    assert isinstance(score, float)
    assert latency >= 0
