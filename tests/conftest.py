"""
Test configuration and fixtures for Voice Agent
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from services import STTService, LLMService, TTSService, ChatService
from schemas.api_models import TranscriptionResult, LLMResult, AudioResponse, ServiceStatus
from utils.config import Config


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return Config(
        assemblyai_api_key="test_assemblyai_key",
        gemini_api_key="test_gemini_key", 
        murf_api_key="test_murf_key",
        host="localhost",
        port=8000,
        uploads_dir="test_uploads",
        static_dir="static",
        log_level="DEBUG"
    )


@pytest.fixture
def mock_stt_service():
    """Mock STT service for testing"""
    service = Mock(spec=STTService)
    service.transcribe_audio = AsyncMock(return_value=TranscriptionResult(
        text="Hello, this is a test",
        confidence=0.95,
        status=ServiceStatus.SUCCESS,
        service_used="assemblyai"
    ))
    service.get_status.return_value = {
        "service": "stt",
        "provider": "assemblyai",
        "available": True,
        "api_key_set": True,
        "disabled": False
    }
    return service


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    service = Mock(spec=LLMService)
    service.generate_response = AsyncMock(return_value=LLMResult(
        response="Hello! How can I help you today?",
        status=ServiceStatus.SUCCESS,
        service_used="gemini",
        tokens_used=50
    ))
    service.get_status.return_value = {
        "service": "llm",
        "provider": "gemini",
        "available": True,
        "api_key_set": True,
        "disabled": False
    }
    return service


@pytest.fixture
def mock_tts_service():
    """Mock TTS service for testing"""
    service = Mock(spec=TTSService)
    service.generate_audio = AsyncMock(return_value=AudioResponse(
        audio_url="https://example.com/audio.mp3",
        source="murf_api",
        voice_used="ken-conversational",
        use_browser_tts=False,
        text="Hello! How can I help you today?",
        status=ServiceStatus.SUCCESS
    ))
    service.get_status.return_value = {
        "service": "tts",
        "provider": "murf",
        "available": True,
        "api_key_set": True,
        "disabled": False
    }
    return service


@pytest.fixture
def mock_chat_service(mock_stt_service, mock_llm_service, mock_tts_service):
    """Mock chat service for testing"""
    service = Mock(spec=ChatService)
    service.stt_service = mock_stt_service
    service.llm_service = mock_llm_service
    service.tts_service = mock_tts_service
    
    service.process_audio_message = AsyncMock(return_value={
        "session_id": "test_session",
        "user_message": "Hello, this is a test",
        "assistant_response": "Hello! How can I help you today?",
        "audio_url": "https://example.com/audio.mp3",
        "use_browser_tts": False,
        "audio_source": "murf_api",
        "voice_used": "ken-conversational",
        "total_messages": 2,
        "transcription_confidence": 0.95,
        "error_handling": {
            "stt_status": "success",
            "llm_status": "success",
            "tts_status": "success"
        }
    })
    
    service.get_service_status.return_value = {
        "stt": mock_stt_service.get_status(),
        "llm": mock_llm_service.get_status(),
        "tts": mock_tts_service.get_status(),
        "active_sessions": 0,
        "total_messages": 0
    }
    
    return service


@pytest.fixture
def temp_audio_file():
    """Create a temporary audio file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        # Write some dummy audio data
        f.write(b"RIFF....WAVE")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def test_uploads_dir():
    """Create a temporary uploads directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test data
SAMPLE_AUDIO_DATA = b"RIFF....WAVE"  # Minimal WAV file structure

SAMPLE_TRANSCRIPTION = "Hello, how are you today?"

SAMPLE_LLM_RESPONSE = "I'm doing well, thank you for asking! How can I help you?"

SAMPLE_ERROR_RESPONSES = {
    "stt_error": "I'm having trouble understanding your audio. Please try speaking more clearly.",
    "llm_error": "I'm having trouble generating a response. Please try again.",
    "tts_error": "I'm having trouble generating audio. The text response is still available."
}
