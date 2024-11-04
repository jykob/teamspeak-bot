import atexit
import logging
import logging.handlers
import queue
import sys


def calculate_verbosity(level: int) -> int:
    if level >= 2:
        return logging.DEBUG
    if level >= 1:
        return logging.INFO
    return logging.WARNING


def create_console_handler(verbosity: int, console_format: str) -> logging.Handler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(calculate_verbosity(verbosity))
    handler.setFormatter(logging.Formatter(console_format))
    return handler


def create_file_handler(
    log_filepath: str, file_format: str
) -> logging.handlers.RotatingFileHandler:
    handler = logging.handlers.RotatingFileHandler(
        log_filepath, maxBytes=1024 * 1024, backupCount=1
    )
    handler.setLevel(logging.WARNING)
    handler.setFormatter(logging.Formatter(file_format))
    return handler


def create_queue_handler(queue: queue.Queue[logging.LogRecord]) -> logging.handlers.QueueHandler:
    handler = logging.handlers.QueueHandler(queue)
    return handler


def create_queue_listener(
    queue: queue.Queue[logging.LogRecord], *handlers: logging.Handler
) -> logging.handlers.QueueListener:
    handler = logging.handlers.QueueListener(queue, *handlers, respect_handler_level=True)
    handler.start()
    atexit.register(handler.stop)
    return handler


def setup_logger(verbosity: int, log_filepath: str, console_format: str, file_format: str) -> None:
    console_handler = create_console_handler(verbosity, console_format)
    file_handler = create_file_handler(log_filepath, file_format)

    log_queue: queue.Queue[logging.LogRecord] = queue.Queue()
    queue_handler = create_queue_handler(log_queue)

    create_queue_listener(log_queue, console_handler, file_handler)

    root = logging.getLogger()
    root.setLevel(logging.NOTSET)
    root.addHandler(queue_handler)
