import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name):
    # Ensure logs directory exists in the project root
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger(name)
    
    # Prevent duplicate logs if setup_logger is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # 1. ROTATING FILE HANDLER: Keeps max 5 files of 5MB each
        log_file = f"logs/{name}.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=5
        )
        
        # 2. STREAM HANDLER: Required for the GUI Audit Feed
        stream_handler = logging.StreamHandler()

        # Professional Formatter
        formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger