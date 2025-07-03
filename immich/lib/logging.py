import logging
import logging.config
import os

LOGGER_NAME = 'immich-python'

LOGGER = logging.getLogger(LOGGER_NAME)

def configure_logging():
    """Configure logging with basic string formatting and output to STDERR."""
    # Get log level from environment variable, default to INFO
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Map string to logging level
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,  # Common alias
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # Get the log level, default to INFO if invalid
    log_level = log_level_map.get(log_level_str, logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=None,  # Default stream is STDERR
        force=True  # Override any existing configuration
    )

def get_logger():
    return LOGGER
