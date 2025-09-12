"""Logging configuration for the orchestrator."""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import time


class SizeAndTimeRotatingHandler(TimedRotatingFileHandler):
    """Log handler that rotates logs by both size and time."""

    def __init__(self, filename, max_bytes, backup_count=0, **kwargs):
        """Initialize handler with size and time-based rotation."""
        self.max_bytes = max_bytes
        super().__init__(filename, backupCount=backup_count, **kwargs)

    def shouldRollover(self, record):
        """Determine if rollover should occur (by time or file size)."""
        # Time-based rollover
        t = int(time.time())
        if t >= self.rolloverAt:
            return 1

        # Size-based rollover
        if self.stream and self.max_bytes > 0:
            self.stream.seek(0, os.SEEK_END)
            if self.stream.tell() >= self.max_bytes:
                return 1

        return 0

    def doRollover(self):
        """Perform the log file rollover."""
        super().doRollover()
        self.rolloverAt = self.computeRollover(int(time.time()))


def configure_logging():
    """Configure root logger with console and rotating file handlers."""
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = SizeAndTimeRotatingHandler(
        filename="logs/orchestrator.log",
        when="midnight",
        interval=1,
        max_bytes=5 * 1024 * 1024,  # 5 MB
        backup_count=7,
        encoding='utf-8')

    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)