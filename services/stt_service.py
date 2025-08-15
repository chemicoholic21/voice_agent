"""
Speech-to-Text Service for Voice Agent
Handles audio transcription with AssemblyAI and fallback mechanisms
"""

import os
import assemblyai as aai
from typing import Tuple
import logging

from schemas.api_models import TranscriptionResult, ServiceStatus

logger = logging.getLogger(__name__)


class STTService:
    """Service for handling speech-to-text transcription"""
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize STT service
        
        Args:
            api_key: AssemblyAI API key. If None, will use environment variable
        """
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        self.is_available = self._check_availability()
        
        if self.is_available:
            aai.settings.api_key = self.api_key
            logger.info("STT Service initialized with AssemblyAI")
        else:
            logger.warning("STT Service initialized without API key - fallback mode only")
    
    def _check_availability(self) -> bool:
        """Check if the STT service is available"""
        return bool(
            self.api_key and 
            self.api_key.strip() != "" and 
            self.api_key != "DISABLED_FOR_TESTING"
        )
    
    async def transcribe_audio(self, file_path: str) -> TranscriptionResult:
        """
        Transcribe audio file to text with comprehensive error handling
        
        Args:
            file_path: Path to the audio file to transcribe
            
        Returns:
            TranscriptionResult with text, confidence, and status
        """
        try:
            # Check if service is available
            if not self.is_available:
                logger.warning("AssemblyAI service unavailable - API key missing or disabled")
                return TranscriptionResult(
                    text="I'm having trouble with my speech recognition right now. Could you please try again?",
                    confidence=0.0,
                    status=ServiceStatus.ERROR,
                    service_used="assemblyai",
                    error_message="API key missing or disabled"
                )
            
            logger.info(f"Transcribing audio file: {file_path}")
            transcriber = aai.Transcriber()
            
            # Transcribe with timeout
            transcript = transcriber.transcribe(file_path)
            
            if transcript.error:
                logger.error(f"AssemblyAI transcription error: {transcript.error}")
                return TranscriptionResult(
                    text="I couldn't understand what you said. Please try speaking more clearly.",
                    confidence=0.0,
                    status=ServiceStatus.ERROR,
                    service_used="assemblyai",
                    error_message=transcript.error
                )
            
            if not transcript.text or transcript.text.strip() == "":
                logger.warning("Empty transcription result")
                return TranscriptionResult(
                    text="I didn't hear anything. Could you please speak louder or closer to your microphone?",
                    confidence=0.0,
                    status=ServiceStatus.ERROR,
                    service_used="assemblyai",
                    error_message="Empty transcription"
                )
            
            confidence = getattr(transcript, 'confidence', 0.8)
            logger.info(f"Transcription successful: '{transcript.text}' (confidence: {confidence})")
            
            return TranscriptionResult(
                text=transcript.text.strip(),
                confidence=confidence,
                status=ServiceStatus.SUCCESS,
                service_used="assemblyai"
            )
            
        except Exception as e:
            logger.error(f"STT Error: {str(e)}")
            
            # Return user-friendly error message based on error type
            if "network" in str(e).lower() or "timeout" in str(e).lower():
                error_text = "I'm having network connectivity issues. Please check your internet connection and try again."
            elif "api" in str(e).lower():
                error_text = "My speech recognition service is temporarily unavailable. Please try again in a moment."
            else:
                error_text = "I'm having trouble understanding your audio. Please try speaking more clearly."
            
            return TranscriptionResult(
                text=error_text,
                confidence=0.0,
                status=ServiceStatus.ERROR,
                service_used="assemblyai",
                error_message=str(e)
            )
    
    def set_api_key(self, api_key: str):
        """
        Update the API key for the service
        
        Args:
            api_key: New AssemblyAI API key
        """
        self.api_key = api_key
        self.is_available = self._check_availability()
        
        if self.is_available:
            aai.settings.api_key = self.api_key
            logger.info("STT Service API key updated")
        else:
            logger.warning("STT Service API key invalid or disabled")
    
    def get_status(self) -> dict:
        """
        Get current service status
        
        Returns:
            Dictionary with service status information
        """
        return {
            "service": "stt",
            "provider": "assemblyai",
            "available": self.is_available,
            "api_key_set": bool(self.api_key and self.api_key != "DISABLED_FOR_TESTING"),
            "disabled": self.api_key == "DISABLED_FOR_TESTING"
        }
