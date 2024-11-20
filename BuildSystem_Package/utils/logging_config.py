"""Logging configuration."""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Simple format for all logs
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'

def setup_logging(logger_name, log_file):
    """Setup logging with appropriate configuration."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")  # Changed to use relative path
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Configure logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        logger.handlers.clear()

        # Console handler - errors only
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)

        # File handler
        file_handler = RotatingFileHandler(
            logs_dir / log_file,
            maxBytes=50*1024,  # 50KB
            backupCount=2,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(file_handler)

        return logger

    except (OSError, IOError, PermissionError) as e:  # Catch specific file/IO related errors
        # Fallback to basic console-only logging
        logging.basicConfig(
            level=logging.ERROR,
            format=LOG_FORMAT
        )
        logging.error(f"Failed to setup logging: {str(e)}")
        return logging.getLogger(logger_name)

# Initialize loggers
server_logger = setup_logging("server", "server.log")
model_logger = setup_logging("model", "model.log")
