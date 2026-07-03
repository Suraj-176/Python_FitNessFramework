import os
import logging
from logging.handlers import TimedRotatingFileHandler

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ensure logs folder exists
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "framework.log")

# Configure logger
logger = logging.getLogger("FitNessePythonFramework")
logger.setLevel(logging.DEBUG)

# Clear existing handlers to avoid duplicates
if logger.hasHandlers():
    logger.handlers.clear()

# Create formatters
formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Console Handler (Prints clear info to the terminal)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File Handler (Timed Log Rotation)
# when="D" rotates the logs daily at midnight.
# interval=1 means rotation happens every 1 day.
# backupCount=7 keeps exactly the last 7 daily log files and automatically deletes older ones!
file_handler = TimedRotatingFileHandler(
    LOG_FILE, when="D", interval=1, backupCount=7, encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log_request(method: str, url: str, headers: dict = None, payload: dict = None) -> None:
    """Logs the HTTP request details in a structured format."""
    logger.info(f"---> HTTP REQUEST: {method} {url}")
    if headers:
        logger.debug(f"Request Headers: {headers}")
    if payload:
        logger.debug(f"Request Payload: {payload}")


def log_response(status_code: int, response_text: str, response_headers: dict = None) -> None:
    """Logs the HTTP response details in a structured format."""
    logger.info(f"<--- HTTP RESPONSE: Status Code {status_code}")
    if response_headers:
        logger.debug(f"Response Headers: {response_headers}")
    if response_text:
        # Limit logging size of responses to keep logs clean
        truncated_text = response_text[:1000] + "..." if len(response_text) > 1000 else response_text
        logger.debug(f"Response Body: {truncated_text}")
