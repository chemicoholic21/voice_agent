"""
Logging configuration for Voice Agent
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up comprehensive logging for the Voice Agent application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging. If None, logs to console only
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Set specific loggers to appropriate levels
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("assemblyai").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    logger.info(f"Logging initialized - Level: {level}, File: {log_file or 'Console only'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_api_call(
    logger: logging.Logger,
    service: str,
    endpoint: str,
    status_code: Optional[int] = None,
    error: Optional[str] = None,
    duration: Optional[float] = None
) -> None:
    """
    Log API call details in a structured format
    
    Args:
        logger: Logger instance to use
        service: Service name (e.g., 'assemblyai', 'gemini', 'murf')
        endpoint: API endpoint called
        status_code: HTTP status code (if applicable)
        error: Error message (if any)
        duration: Request duration in seconds
    """
    log_data = {
        "service": service,
        "endpoint": endpoint,
        "status_code": status_code,
        "duration": f"{duration:.3f}s" if duration else None,
        "error": error
    }
    
    # Filter out None values
    log_data = {k: v for k, v in log_data.items() if v is not None}
    
    if error:
        logger.error(f"API call failed: {log_data}")
    elif status_code and status_code >= 400:
        logger.warning(f"API call returned error: {log_data}")
    else:
        logger.info(f"API call successful: {log_data}")


def log_service_status(logger: logging.Logger, service_name: str, status: dict) -> None:
    """
    Log service status information
    
    Args:
        logger: Logger instance to use
        service_name: Name of the service
        status: Status dictionary from service.get_status()
    """
    logger.info(f"{service_name} status: {status}")


def log_session_activity(
    logger: logging.Logger,
    session_id: str,
    action: str,
    details: Optional[dict] = None
) -> None:
    """
    Log session-related activities
    
    Args:
        logger: Logger instance to use
        session_id: Session identifier
        action: Action performed (created, message_added, cleared, etc.)
        details: Optional additional details
    """
    log_msg = f"Session {session_id}: {action}"
    if details:
        log_msg += f" - {details}"
    
    logger.info(log_msg)
