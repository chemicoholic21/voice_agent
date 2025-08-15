"""
Text-to-Speech Service for Voice Agent
Handles audio generation with Murf AI and fallback mechanisms
"""

import os
import requests
import asyncio
from typing import Dict, Any
import logging

from schemas.api_models import AudioResponse, ServiceStatus

logger = logging.getLogger(__name__)


class TTSService:
    """Service for handling text-to-speech generation"""
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize TTS service
        
        Args:
            api_key: Murf AI API key. If None, will use environment variable
        """
        self.api_key = api_key or os.getenv("MURF_API_KEY")
        self.is_available = self._check_availability()
        self.base_url = "https://api.murf.ai/v1/speech/generate"
        self.max_text_length = 3000  # Murf API limit
        
        logger.info(f"TTS Service initialized - Available: {self.is_available}")
    
    def _check_availability(self) -> bool:
        """Check if the TTS service is available"""
        return bool(
            self.api_key and 
            self.api_key.strip() != "" and 
            self.api_key != "DISABLED_FOR_TESTING"
        )
    
    async def generate_audio(self, text: str, max_retries: int = 2) -> AudioResponse:
        """
        Generate audio from text with multiple fallback options
        
        Args:
            text: Text to convert to speech
            max_retries: Number of retry attempts for Murf API
            
        Returns:
            AudioResponse with audio URL and generation details
        """
        # Limit text length for Murf API
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length - 3] + "..."
            logger.info(f"Text truncated to fit Murf API limits: {len(text)} characters")
        
        # Try Murf API with retries
        if self.is_available:
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting Murf TTS (attempt {attempt + 1}/{max_retries})")
                    
                    result = await self._call_murf_api(text)
                    if result:
                        return result
                    
                except requests.exceptions.Timeout:
                    logger.warning(f"Murf API timeout on attempt {attempt + 1}")
                except requests.exceptions.ConnectionError:
                    logger.warning(f"Murf API connection error on attempt {attempt + 1}")
                except Exception as e:
                    logger.error(f"Murf API error on attempt {attempt + 1}: {str(e)}")
                
                # Wait before retry (except on last attempt)
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        else:
            logger.info("Murf API service unavailable - API key missing or disabled")
        
        # Fallback to browser TTS
        logger.info("Using browser TTS fallback")
        return AudioResponse(
            audio_url=None,
            source="browser_tts",
            voice_used="browser_fallback",
            use_browser_tts=True,
            text=text,
            status=ServiceStatus.FALLBACK,
            note="Using browser TTS - Murf API unavailable"
        )
    
    async def _call_murf_api(self, text: str) -> AudioResponse | None:
        """
        Make API call to Murf TTS service
        
        Args:
            text: Text to convert to speech
            
        Returns:
            AudioResponse if successful, None if failed
        """
        # Prepare Murf API request
        payload = {
            "voiceId": "en-US-ken",
            "style": "Conversational",
            "text": text,
            "rate": 0,
            "pitch": 0,
            "sampleRate": 48000,
            "format": "MP3",
            "channelType": "MONO",
            "pronunciationDictionary": {},
            "encodeAsBase64": False,
            "variation": 1,
            "audioDuration": 0
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json", 
            "api-key": self.api_key
        }
        
        # Make request with timeout
        response = requests.post(
            self.base_url, 
            json=payload, 
            headers=headers,
            timeout=20  # 20 second timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'audioFile' in result and result['audioFile']:
                logger.info("Murf TTS successful")
                return AudioResponse(
                    audio_url=result['audioFile'],
                    source="murf_api",
                    voice_used="ken-conversational",
                    use_browser_tts=False,
                    text=text,
                    status=ServiceStatus.SUCCESS
                )
            else:
                logger.warning("Murf API returned empty audio file")
        else:
            logger.error(f"Murf API failed: {response.status_code} - {response.text}")
        
        return None
    
    def set_api_key(self, api_key: str):
        """
        Update the API key for the service
        
        Args:
            api_key: New Murf AI API key
        """
        self.api_key = api_key
        self.is_available = self._check_availability()
        logger.info(f"TTS Service API key updated - Available: {self.is_available}")
    
    def get_status(self) -> dict:
        """
        Get current service status
        
        Returns:
            Dictionary with service status information
        """
        return {
            "service": "tts",
            "provider": "murf",
            "available": self.is_available,
            "api_key_set": bool(self.api_key and self.api_key != "DISABLED_FOR_TESTING"),
            "disabled": self.api_key == "DISABLED_FOR_TESTING",
            "max_text_length": self.max_text_length
        }
