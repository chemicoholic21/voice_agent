"""
API utilities for Voice Agent
"""

import json
from typing import Dict, Any, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse
import logging

from schemas.api_models import ErrorHandlingStatus, ServiceStatus

logger = logging.getLogger(__name__)


def handle_api_error(
    error: Exception,
    service_name: str,
    session_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Handle API errors and return standardized error response
    
    Args:
        error: Exception that occurred
        service_name: Name of the service where error occurred
        session_id: Session identifier for logging
        
    Returns:
        Standardized error response dictionary
    """
    error_msg = str(error)
    logger.error(f"API error in {service_name} for session {session_id}: {error_msg}")
    
    # Determine user-friendly error message based on error type
    if "timeout" in error_msg.lower():
        user_message = "The service is taking longer than usual. Please try again."
    elif "network" in error_msg.lower() or "connection" in error_msg.lower():
        user_message = "Network connection issue. Please check your internet and try again."
    elif "unauthorized" in error_msg.lower() or "403" in error_msg or "401" in error_msg:
        user_message = "Service authentication issue. Please contact support."
    elif "rate limit" in error_msg.lower() or "429" in error_msg:
        user_message = "Service is busy. Please wait a moment and try again."
    else:
        user_message = "A technical issue occurred. Please try again."
    
    return {
        "error": True,
        "service": service_name,
        "user_message": user_message,
        "technical_error": error_msg,
        "session_id": session_id
    }


def create_error_response(
    message: str,
    session_id: str,
    error_details: Optional[Dict] = None
) -> JSONResponse:
    """
    Create a standardized error response for chat endpoints
    
    Args:
        message: User-friendly error message
        session_id: Session identifier
        error_details: Optional additional error details
        
    Returns:
        JSONResponse with error information
    """
    response_data = {
        "session_id": session_id,
        "user_message": "Error processing request",
        "assistant_response": message,
        "audio_url": None,
        "use_browser_tts": True,
        "audio_source": "browser_tts",
        "voice_used": "browser_fallback",
        "total_messages": 0,
        "transcription_confidence": 0.0,
        "error_handling": ErrorHandlingStatus(
            stt_status=ServiceStatus.ERROR,
            llm_status=ServiceStatus.ERROR,
            tts_status=ServiceStatus.FALLBACK,
            error_message=message
        ).dict()
    }
    
    if error_details:
        response_data.update(error_details)
    
    return JSONResponse(response_data, status_code=500)


def create_stream_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    Create a Server-Sent Event formatted string
    
    Args:
        event_type: Type of the event
        data: Event data dictionary
        
    Returns:
        Formatted SSE string
    """
    event_data = {"type": event_type, **data}
    return f"data: {json.dumps(event_data)}\\n\\n"


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format and content
    
    Args:
        session_id: Session identifier to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not session_id or not isinstance(session_id, str):
        return False
    
    # Basic validation - alphanumeric and common separators
    if not session_id.replace("-", "").replace("_", "").isalnum():
        return False
    
    # Length check
    if len(session_id) < 3 or len(session_id) > 100:
        return False
    
    return True


def sanitize_text_for_tts(text: str, max_length: int = 3000) -> str:
    """
    Sanitize text for TTS services
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove or replace problematic characters
    sanitized = text.strip()
    
    # Replace multiple whitespace with single space
    import re
    sanitized = re.sub(r'\\s+', ' ', sanitized)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length - 3] + "..."
    
    return sanitized


def create_success_response(
    session_id: str,
    user_message: str,
    assistant_response: str,
    audio_url: Optional[str],
    audio_source: str,
    voice_used: str,
    use_browser_tts: bool,
    total_messages: int,
    confidence: float,
    error_handling: Dict[str, str]
) -> Dict[str, Any]:
    """
    Create a standardized success response for chat endpoints
    
    Args:
        session_id: Session identifier
        user_message: User's message
        assistant_response: AI assistant's response
        audio_url: URL to generated audio (if any)
        audio_source: Source of audio generation
        voice_used: Voice model used
        use_browser_tts: Whether to use browser TTS
        total_messages: Total messages in session
        confidence: Transcription confidence
        error_handling: Error handling status
        
    Returns:
        Standardized response dictionary
    """
    return {
        "session_id": session_id,
        "user_message": user_message,
        "assistant_response": assistant_response,
        "audio_url": audio_url,
        "use_browser_tts": use_browser_tts,
        "audio_source": audio_source,
        "voice_used": voice_used,
        "total_messages": total_messages,
        "transcription_confidence": confidence,
        "error_handling": error_handling
    }


def log_request_info(
    endpoint: str,
    session_id: str,
    method: str = "POST",
    additional_info: Optional[Dict] = None
) -> None:
    """
    Log request information in a structured format
    
    Args:
        endpoint: API endpoint being called
        session_id: Session identifier
        method: HTTP method
        additional_info: Optional additional information
    """
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "session_id": session_id
    }
    
    if additional_info:
        log_data.update(additional_info)
    
    logger.info(f"API Request: {log_data}")


def measure_execution_time(func):
    """
    Decorator to measure and log execution time of functions
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function with timing
    """
    import time
    import functools
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    # Return appropriate wrapper based on function type
    if hasattr(func, '__code__') and 'async' in str(func.__code__.co_flags):
        return async_wrapper
    else:
        return sync_wrapper
