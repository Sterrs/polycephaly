import os
import logging
import json
from datetime import datetime
from typing import Any, Dict

def setup_logger(name: str, log_file: str, level=logging.DEBUG) -> logging.Logger:
    """Set up a logger with file and console handlers"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create formatter with code location
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler with mode='w' to overwrite
    file_handler = logging.FileHandler(f'logs/{log_file}', mode='w')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)  # File gets all logs
    
    # Create console handler for warnings and errors only
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)  # Console only gets warnings and errors
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove any existing handlers
    logger.handlers.clear()
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def format_data(data: Any) -> str:
    """Format data for logging"""
    try:
        if isinstance(data, (dict, list)):
            return json.dumps(data, indent=2)
        return str(data)
    except Exception as e:
        return f"<Error formatting data: {e}>"

def log_socket_event(logger: logging.Logger, direction: str, event: str, data: Any = None) -> None:
    """Log a socket.io event"""
    message = f"{direction} Socket Event: {event}"
    if data is not None:
        message += f"\nData: {format_data(data)}"
    logger.info(message)

def log_api_call(logger: logging.Logger, method: str, url: str, request_data: Any = None, response_data: Any = None, error: Exception = None) -> None:
    """Log an API call"""
    message = f"API {method} {url}"
    if request_data is not None:
        message += f"\nRequest: {format_data(request_data)}"
    if response_data is not None:
        message += f"\nResponse: {format_data(response_data)}"
    if error is not None:
        message += f"\nError: {str(error)}"
    logger.info(message) 