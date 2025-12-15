# tests/unit/test_logging.py
"""Tests for logging utility module."""


def test_logger_import():
    """Test logger can be imported."""
    from src.utils.logging import logger
    assert logger is not None


def test_logger_has_handlers():
    """Test logger configuration."""
    from src.utils.logging import logger
    
    # Logger should be set up
    assert hasattr(logger, 'debug')
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'warning')
    assert hasattr(logger, 'error')


def test_logger_debug_call():
    """Test logger debug method works."""
    from src.utils.logging import logger
    
    # Should not raise
    logger.debug("Test debug message")


def test_logger_info_call():
    """Test logger info method works."""
    from src.utils.logging import logger
    
    logger.info("Test info message")


def test_logger_warning_call():
    """Test logger warning method works."""
    from src.utils.logging import logger
    
    logger.warning("Test warning message")


def test_logger_error_call():
    """Test logger error method works."""  
    from src.utils.logging import logger
    
    logger.error("Test error message")
