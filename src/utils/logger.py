import logging

from colorlog import ColoredFormatter


def setup_logging() -> None:
    """Configure the logging system for the application with colored output."""

    # Define the color scheme
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    # Create handlers
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('chat_processor.log')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[stream_handler, file_handler]
    )

    # Suppress INFO and DEBUG logs from specific modules
    # They just spam each request making the log unreadable
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
