"""
Enhanced middleware and utilities for Voice Agent
"""

import time
import uuid
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from utils import get_logger

logger = get_logger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track requests with unique IDs and performance metrics"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        logger.info(f"[{request_id}] {request.method} {request.url.path} - Started")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log successful response
            duration = time.time() - start_time
            logger.info(f"[{request_id}] {response.status_code} - {duration:.3f}s")
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error response
            duration = time.time() - start_time
            logger.error(f"[{request_id}] ERROR - {duration:.3f}s - {str(e)}")
            raise


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests: Dict[str, list] = {}
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip] 
                if current_time - req_time < 60
            ]
        
        # Check rate limit
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        if len(self.requests[client_ip]) >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute."
            )
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


def validate_audio_file(file) -> Optional[str]:
    """
    Validate uploaded audio file
    
    Returns:
        Error message if validation fails, None if valid
    """
    # Check file size (25MB limit)
    if hasattr(file, 'size') and file.size > 25 * 1024 * 1024:
        return "File too large. Maximum size is 25MB."
    
    # Check content type
    allowed_types = [
        'audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac', 
        'audio/ogg', 'audio/webm', 'application/octet-stream'
    ]
    
    if hasattr(file, 'content_type') and file.content_type not in allowed_types:
        return f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
    
    # Check filename extension
    if hasattr(file, 'filename') and file.filename:
        allowed_extensions = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm']
        file_extension = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
    
    return None


async def handle_service_error(error: Exception, service_name: str, session_id: str) -> Dict[str, Any]:
    """
    Centralized service error handling
    
    Args:
        error: The exception that occurred
        service_name: Name of the service (stt, llm, tts)
        session_id: Session identifier
        
    Returns:
        Error response dictionary
    """
    error_msg = str(error)
    
    # Log the error with context
    logger.error(f"Service error in {service_name} for session {session_id}: {error_msg}")
    
    # Map service-specific errors to user-friendly messages
    service_messages = {
        'stt': "I'm having trouble understanding your audio. Please try speaking more clearly.",
        'llm': "I'm having trouble generating a response. Please try again.",
        'tts': "I'm having trouble generating audio. The text response is still available."
    }
    
    # Determine error type and user message
    if "timeout" in error_msg.lower():
        user_message = f"The {service_name} service is taking longer than usual. Please try again."
    elif "network" in error_msg.lower() or "connection" in error_msg.lower():
        user_message = f"Network issues with {service_name} service. Please check your connection."
    elif "unauthorized" in error_msg.lower() or "api" in error_msg.lower():
        user_message = f"Authentication issue with {service_name} service. Please try again later."
    else:
        user_message = service_messages.get(service_name, "A technical issue occurred. Please try again.")
    
    return {
        "error": True,
        "service": service_name,
        "user_message": user_message,
        "technical_error": error_msg,
        "session_id": session_id,
        "timestamp": time.time()
    }


class ServiceHealthChecker:
    """Utility class for checking service health"""
    
    def __init__(self, chat_service):
        self.chat_service = chat_service
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services"""
        health_status = {
            "overall": "healthy",
            "services": {},
            "timestamp": time.time()
        }
        
        # Check STT service
        stt_status = self.chat_service.stt_service.get_status()
        health_status["services"]["stt"] = {
            "available": stt_status["available"],
            "provider": stt_status["provider"],
            "status": "healthy" if stt_status["available"] else "degraded"
        }
        
        # Check LLM service
        llm_status = self.chat_service.llm_service.get_status()
        health_status["services"]["llm"] = {
            "available": llm_status["available"],
            "provider": llm_status["provider"],
            "status": "healthy" if llm_status["available"] else "degraded"
        }
        
        # Check TTS service
        tts_status = self.chat_service.tts_service.get_status()
        health_status["services"]["tts"] = {
            "available": tts_status["available"],
            "provider": tts_status["provider"],
            "status": "healthy" if tts_status["available"] else "degraded"
        }
        
        # Determine overall health
        service_statuses = [svc["status"] for svc in health_status["services"].values()]
        if all(status == "healthy" for status in service_statuses):
            health_status["overall"] = "healthy"
        elif any(status == "healthy" for status in service_statuses):
            health_status["overall"] = "degraded"
        else:
            health_status["overall"] = "unhealthy"
        
        return health_status
    
    async def check_service(self, service_name: str) -> Dict[str, Any]:
        """Check health of a specific service"""
        service_map = {
            "stt": self.chat_service.stt_service,
            "llm": self.chat_service.llm_service,
            "tts": self.chat_service.tts_service
        }
        
        if service_name not in service_map:
            return {"error": f"Unknown service: {service_name}"}
        
        service = service_map[service_name]
        status = service.get_status()
        
        return {
            "service": service_name,
            "available": status["available"],
            "provider": status["provider"],
            "status": "healthy" if status["available"] else "degraded",
            "timestamp": time.time()
        }


def format_error_response(
    message: str, 
    session_id: str, 
    error_code: str = "GENERAL_ERROR",
    details: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Format standardized error response
    
    Args:
        message: User-friendly error message
        session_id: Session identifier
        error_code: Error code for client handling
        details: Additional error details
        
    Returns:
        Formatted error response
    """
    response = {
        "error": True,
        "error_code": error_code,
        "message": message,
        "session_id": session_id,
        "timestamp": time.time()
    }
    
    if details:
        response["details"] = details
    
    return response
