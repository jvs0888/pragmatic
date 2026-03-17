import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


def init_logger(file_log: bool = True, stream_log: bool = True, rotate: bool = True) -> logging.Logger:
    log_directory: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    if not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory)
        except Exception as e:
            exit(f"failed to create log directory on a path :: {log_directory} :: {e}")

    log_filename: str = f"logger_{datetime.now().isoformat(timespec='minutes')}.log"
    log_filepath: str = os.path.join(log_directory, log_filename)

    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter: logging.Formatter = logging.Formatter(
        fmt=u"%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s")

    if file_log:
        if rotate:
            file_handler: logging.FileHandler = RotatingFileHandler(log_filepath, maxBytes=10_000_000, backupCount=5)
        else:
            file_handler: logging.FileHandler = logging.FileHandler(log_filepath)

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if stream_log:
        stream_handler: logging.StreamHandler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger


logger: logging.Logger = init_logger()
