"""
Sanitized Logging Module
Ensures sensitive tokens, passwords, and connection strings are masked.
"""

import logging
import re
import sys
from typing import Any

SENSITIVE_PATTERNS = [
    (re.compile(r'(password["\':\s=]+)([\'"]?)([^\'"\s,}&]+)\2', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(token["\':\s=]+)([\'"]?)([^\'"\s,}&]+)\2', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(secret["\':\s=]+)([\'"]?)([^\'"\s,}&]+)\2', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(authorization["\':\s=]+)([\'"]?)([^\'"\s,}&]+)\2', re.IGNORECASE), r'\1***REDACTED***'),
    (re.compile(r'(mongodb(\+srv)?://[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***REDACTED***\4'),
]


class SanitizedFormatter(logging.Formatter):
    """Logging formatter that scrubs secrets from log messages."""

    def format(self, record: logging.LogRecord) -> str:
        orig = super().format(record)
        sanitized = orig
        for pattern, replacement in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure root and application loggers."""
    log_level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("qr_feedback")
    logger.setLevel(log_level)

    # Avoid duplicate handlers on reload
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = SanitizedFormatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()

