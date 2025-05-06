"""Logging setup for lmi CLI: file and rich console logging, config/CLI control."""

import logging
from pathlib import Path

from rich.logging import RichHandler

LOG_FILE_DEFAULT = str(Path("~/.local/share/lmi/lmi.log").expanduser())
LOG_LEVELS = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}

def setup_logging(
    verbosity: int = 0,
    log_file: str | None = None,
    disable_file: bool = False,
) -> None:
    """Set up logging for both file and console with rich formatting.

    Args:
        verbosity: 0=WARNING, 1=INFO, 2=DEBUG
        log_file: Optional path to log file (default: ~/.local/share/lmi/lmi.log)
        disable_file: If True, do not log to file

    """
    log_level = LOG_LEVELS.get(verbosity, logging.DEBUG)
    handlers = []

    # Console handler (rich)
    handlers.append(
        RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_level=True,
            show_path=True,
            markup=True,
            log_time_format="%Y-%m-%d %H:%M:%S",
        ),
    )

    # File handler
    if not disable_file:
        log_path = Path(log_file) if log_file else Path(LOG_FILE_DEFAULT)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ),
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        format="%(message)s",  # RichHandler handles formatting
        force=True,
    )
