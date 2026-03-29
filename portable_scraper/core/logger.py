import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name):
    # 1. Ensure logs directory exists first
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger = logging.getLogger(name)
    
    # Only configure if handlers don't exist to prevent duplicates
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # 🟢 THE FIX: Define the variable BEFORE using it below
        log_file = f"logs/{name}.log"

        # 2. ROTATING FILE HANDLER with UTF-8 for Emojis
        file_handler = RotatingFileHandler(
            log_file,             # Variable is now defined
            maxBytes=5*1024*1024, 
            backupCount=5, 
            encoding='utf-8'      # 🟢 Fixes the emoji-stripping issue
        )
        
        # 3. STREAM HANDLER for GUI interaction
        stream_handler = logging.StreamHandler()

        # Professional Formatter
        formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger