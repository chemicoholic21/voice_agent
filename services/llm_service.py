"""
Large Language Model Service for Voice Agent
Handles conversational AI with Google Gemini and fallback mechanisms
"""

import os
import requests
import random
from typing import List, Dict, Optional
import logging

from schemas.api_models import LLMResult, ServiceStatus, ChatMessage

logger = logging.getLogger(__name__)


class LLMService:
    """Service for handling LLM interactions"""
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize LLM service
        
        Args:
            api_key: Google Gemini API key. If None, will use environment variable
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.is_available = self._check_availability()
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        logger.info(f"LLM Service initialized - Available: {self.is_available}")
    
    def _check_availability(self) -> bool:
        """Check if the LLM service is available"""
        return bool(
            self.api_key and 
            self.api_key.strip() != "" and 
            self.api_key != "DISABLED_FOR_TESTING"
        )
    
    async def generate_response(
        self, 
        text: str, 
        chat_history: Optional[List[ChatMessage]] = None, 
        session_id: str = "default"
    ) -> LLMResult:
        """
        Generate response using LLM with comprehensive error handling
        
        Args:
            text: User input text
            chat_history: Previous conversation messages for context
            session_id: Session identifier for logging
            
        Returns:
            LLMResult with response, status, and metadata
        """
        try:
            # Check if service is available
            if not self.is_available:
                logger.warning("Gemini API service unavailable - API key missing or disabled")
                fallback_response = self._get_contextual_fallback_response(text, chat_history)
                return LLMResult(
                    response=fallback_response,
                    status=ServiceStatus.FALLBACK,
                    service_used="fallback",
                    error_message="API key missing or disabled"
                )
            
            # Build conversation context
            conversation_messages = []
            if chat_history and len(chat_history) > 0:
                # Include last 5 messages for context
                recent_history = chat_history[-5:]
                for msg in recent_history:
                    if msg.role == "user":
                        conversation_messages.append(f"User: {msg.content}")
                    else:
                        conversation_messages.append(f"Assistant: {msg.content}")
            
            # Create conversation context
            if conversation_messages:
                conversation_context = "\\n".join(conversation_messages)
                full_prompt = f"""You are a helpful AI assistant having a conversation. Here is our conversation history:

{conversation_context}

User: {text}

Please respond naturally and conversationally. Keep your response under 200 words."""
            else:
                full_prompt = f"""You are a helpful AI assistant. Please respond to this user message naturally and conversationally. Keep your response under 200 words.

User: {text}"""
            
            logger.info(f"Sending request to Gemini API for session {session_id}")
            
            # Prepare Gemini API request
            url = f"{self.base_url}?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 300,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            # Make API request with timeout
            response = requests.post(
                url, 
                json=payload, 
                headers={"Content-Type": "application/json"},
                timeout=15  # 15 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        llm_text = candidate['content']['parts'][0]['text'].strip()
                        if llm_text:
                            logger.info(f"LLM Response successful: '{llm_text[:50]}...'")
                            return LLMResult(
                                response=llm_text,
                                status=ServiceStatus.SUCCESS,
                                service_used="gemini",
                                tokens_used=result.get('usageMetadata', {}).get('totalTokenCount')
                            )
                        else:
                            logger.warning("Empty LLM response")
                            fallback_response = self._get_contextual_fallback_response(text, chat_history)
                            return LLMResult(
                                response=fallback_response,
                                status=ServiceStatus.FALLBACK,
                                service_used="fallback",
                                error_message="Empty response from API"
                            )
                    else:
                        logger.warning("Invalid LLM response structure")
                        fallback_response = self._get_contextual_fallback_response(text, chat_history)
                        return LLMResult(
                            response=fallback_response,
                            status=ServiceStatus.FALLBACK,
                            service_used="fallback",
                            error_message="Invalid response structure"
                        )
                else:
                    logger.warning("No candidates in LLM response")
                    fallback_response = self._get_contextual_fallback_response(text, chat_history)
                    return LLMResult(
                        response=fallback_response,
                        status=ServiceStatus.FALLBACK,
                        service_used="fallback",
                        error_message="No candidates in response"
                    )
            else:
                logger.error(f"Gemini API Error: {response.status_code} - {response.text}")
                fallback_response = self._get_contextual_fallback_response(text, chat_history)
                return LLMResult(
                    response=fallback_response,
                    status=ServiceStatus.FALLBACK,
                    service_used="fallback",
                    error_message=f"API error: {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            logger.warning("LLM API timeout")
            return LLMResult(
                response="I'm taking a bit longer to think than usual. Could you please try asking your question again?",
                status=ServiceStatus.ERROR,
                service_used="gemini",
                error_message="Request timeout"
            )
        except requests.exceptions.ConnectionError:
            logger.warning("LLM API connection error")
            return LLMResult(
                response="I'm having trouble connecting to my AI brain right now. Please check your internet connection and try again.",
                status=ServiceStatus.ERROR,
                service_used="gemini",
                error_message="Connection error"
            )
        except Exception as e:
            logger.error(f"LLM Error: {str(e)}")
            fallback_response = self._get_contextual_fallback_response(text, chat_history)
            return LLMResult(
                response=fallback_response,
                status=ServiceStatus.ERROR,
                service_used="fallback",
                error_message=str(e)
            )
    
    def _get_contextual_fallback_response(self, text: str, chat_history: Optional[List[ChatMessage]] = None) -> str:
        """Generate contextual fallback responses based on user input and conversation history"""
        text_lower = text.lower()
        
        # Analyze conversation history to provide better context
        user_name = None
        if chat_history:
            for msg in chat_history:
                if msg.role == "user" and ("my name is" in msg.content.lower() or "i'm" in msg.content.lower()):
                    # Try to extract name
                    content = msg.content.lower()
                    if "my name is" in content:
                        name_part = content.split("my name is")[1].strip().split()[0]
                        user_name = name_part.capitalize()
                    elif "i'm" in content:
                        name_part = content.split("i'm")[1].strip().split()[0]
                        user_name = name_part.capitalize()
                    break
        
        # Contextual responses based on input
        if any(greeting in text_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            if user_name:
                return f"Hello {user_name}! I'm experiencing some technical difficulties with my AI systems right now, but I'm still here to help as best I can."
            else:
                return "Hello! I'm having some technical difficulties with my AI brain right now, but I'm still here to chat when my systems are back online."
        
        elif any(name_q in text_lower for name_q in ["what's your name", "your name", "who are you"]):
            return "I'm an AI assistant, though I'm having trouble accessing my full capabilities right now. My AI systems are temporarily experiencing issues."
        
        elif any(name_q in text_lower for name_q in ["my name", "what's my name", "who am i"]):
            if user_name:
                return f"You told me your name is {user_name}, and I remember that even though my AI systems are having issues right now."
            else:
                return "I'm having trouble with my memory systems right now. Could you remind me of your name?"
        
        elif any(thanks in text_lower for thanks in ["thank", "thanks", "appreciate"]):
            return "You're welcome! I'm sorry I can't provide my full AI capabilities right now due to technical difficulties."
        
        elif any(question in text_lower for question in ["what", "how", "why", "when", "where", "?"]):
            return "I'd love to help answer your question, but I'm experiencing connectivity issues with my AI knowledge systems right now. Please try again in a moment."
        
        else:
            # Generic fallback responses
            fallback_responses = [
                "I'm having trouble connecting to my AI brain right now. Please try again in a moment.",
                "Sorry, I'm experiencing some technical difficulties. Could you repeat that?",
                "I'm having connectivity issues at the moment. Please bear with me and try again.",
                "My AI systems are temporarily unavailable. Please try your question again shortly."
            ]
            
            return random.choice(fallback_responses)
    
    def set_api_key(self, api_key: str):
        """
        Update the API key for the service
        
        Args:
            api_key: New Google Gemini API key
        """
        self.api_key = api_key
        self.is_available = self._check_availability()
        logger.info(f"LLM Service API key updated - Available: {self.is_available}")
    
    def get_status(self) -> dict:
        """
        Get current service status
        
        Returns:
            Dictionary with service status information
        """
        return {
            "service": "llm",
            "provider": "gemini",
            "available": self.is_available,
            "api_key_set": bool(self.api_key and self.api_key != "DISABLED_FOR_TESTING"),
            "disabled": self.api_key == "DISABLED_FOR_TESTING"
        }
