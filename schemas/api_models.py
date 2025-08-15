"""
Pydantic models for Voice Agent API
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Literal
from datetime import datetime
from enum import Enum


class ServiceStatus(str, Enum):
    """Status enum for service responses"""
    SUCCESS = "success"
    FALLBACK = "fallback"
    ERROR = "error"


class ChatMessage(BaseModel):
    """Model for chat messages in conversation history"""
    role: Literal["user", "assistant"]
    content: str
    timestamp: str
    confidence: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2024-01-15T10:30:00",
                "confidence": 0.95
            }
        }


class ChatSession(BaseModel):
    """Model for chat session data"""
    session_id: str
    messages: List[ChatMessage]
    message_count: int
    created_at: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "user123_20240115",
                "messages": [],
                "message_count": 0,
                "created_at": "2024-01-15T10:30:00"
            }
        }


class AudioResponse(BaseModel):
    """Model for audio generation responses"""
    audio_url: Optional[str] = None
    source: str = Field(description="Source of audio generation (murf_api, browser_tts, etc.)")
    voice_used: str = Field(description="Voice model used for generation")
    use_browser_tts: bool = Field(default=True, description="Whether to use browser TTS fallback")
    text: str = Field(description="Text that was converted to audio")
    status: ServiceStatus = Field(description="Status of audio generation")
    note: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_url": "https://example.com/audio.mp3",
                "source": "murf_api",
                "voice_used": "ken-conversational",
                "use_browser_tts": False,
                "text": "Hello, how can I help you?",
                "status": "success"
            }
        }


class ErrorHandlingStatus(BaseModel):
    """Model for error handling status information"""
    stt_status: ServiceStatus
    llm_status: ServiceStatus
    tts_status: ServiceStatus
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "stt_status": "success",
                "llm_status": "success", 
                "tts_status": "fallback",
                "error_message": None
            }
        }


class ChatResponse(BaseModel):
    """Model for chat endpoint responses"""
    session_id: str
    user_message: str
    assistant_response: str
    audio_url: Optional[str] = None
    use_browser_tts: bool = True
    audio_source: str = "browser_tts"
    voice_used: str = "browser_fallback"
    total_messages: int
    transcription_confidence: float
    error_handling: ErrorHandlingStatus
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "user123_20240115",
                "user_message": "Hello there",
                "assistant_response": "Hello! How can I help you today?",
                "audio_url": None,
                "use_browser_tts": True,
                "audio_source": "browser_tts",
                "voice_used": "browser_fallback",
                "total_messages": 2,
                "transcription_confidence": 0.95,
                "error_handling": {
                    "stt_status": "success",
                    "llm_status": "success",
                    "tts_status": "fallback"
                }
            }
        }


class StreamEventType(str, Enum):
    """Types of streaming events"""
    STATUS = "status"
    SESSION = "session"
    TRANSCRIPTION = "transcription"
    LLM_RESPONSE = "llm_response"
    AUDIO = "audio"
    ERROR = "error"
    COMPLETE = "complete"


class StreamEvent(BaseModel):
    """Model for Server-Sent Events in streaming responses"""
    type: StreamEventType
    message: Optional[str] = None
    text: Optional[str] = None
    confidence: Optional[float] = None
    is_complete: Optional[bool] = None
    is_fallback: Optional[bool] = None
    url: Optional[str] = None
    use_browser_tts: Optional[bool] = None
    source: Optional[str] = None
    session_id: Optional[str] = None
    message_count: Optional[int] = None
    status: Optional[str] = None
    details: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "transcription",
                "text": "Hello there",
                "confidence": 0.95
            }
        }


class ErrorSimulationRequest(BaseModel):
    """Model for error simulation requests"""
    error_type: Literal["stt", "llm", "tts", "all"]
    action: Literal["disable", "enable"] = "disable"
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_type": "stt",
                "action": "disable"
            }
        }


class ErrorSimulationResponse(BaseModel):
    """Model for error simulation responses"""
    status: str = "success"
    message: str
    error_type: str
    apis_disabled: Optional[List[str]] = None
    apis_restored: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Simulated stt error - API keys disabled",
                "error_type": "stt",
                "apis_disabled": ["stt"]
            }
        }


class ErrorStatusResponse(BaseModel):
    """Model for error status responses"""
    stt_disabled: bool
    llm_disabled: bool
    tts_disabled: bool
    assemblyai_key_set: bool
    gemini_key_set: bool
    murf_key_set: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "stt_disabled": False,
                "llm_disabled": False,
                "tts_disabled": False,
                "assemblyai_key_set": True,
                "gemini_key_set": True,
                "murf_key_set": True
            }
        }


class TranscriptionResult(BaseModel):
    """Model for transcription service results"""
    text: str
    confidence: float
    status: ServiceStatus
    service_used: str = "assemblyai"
    error_message: Optional[str] = None


class LLMResult(BaseModel):
    """Model for LLM service results"""
    response: str
    status: ServiceStatus
    service_used: str = "gemini"
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None
