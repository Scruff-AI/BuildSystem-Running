"""Logging configuration."""

import logging
import sys

# Configure server logger
server_logger = logging.getLogger("server")
server_logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(console_formatter)
server_logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler("server.log")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)
server_logger.addHandler(file_handler)
