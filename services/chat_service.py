"""
Chat Service for Voice Agent
Handles conversation management and session storage
"""

import uuid
from typing import Dict, List, Optional
from datetime import datetime
import logging

from schemas.api_models import ChatMessage, ChatSession
from services.stt_service import STTService
from services.llm_service import LLMService
from services.tts_service import TTSService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat sessions and conversations"""
    
    def __init__(self, stt_service: STTService, llm_service: LLMService, tts_service: TTSService):
        """
        Initialize chat service with required AI services
        
        Args:
            stt_service: Speech-to-text service instance
            llm_service: Large language model service instance  
            tts_service: Text-to-speech service instance
        """
        self.stt_service = stt_service
        self.llm_service = llm_service
        self.tts_service = tts_service
        
        # In-memory chat history storage
        # Format: {session_id: ChatSession}
        self.chat_sessions: Dict[str, ChatSession] = {}
        
        logger.info("Chat Service initialized")
    
    def create_session(self, session_id: str | None = None) -> ChatSession:
        """
        Create a new chat session
        
        Args:
            session_id: Optional session ID. If None, will generate UUID
            
        Returns:
            ChatSession object for the new session
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if session_id in self.chat_sessions:
            logger.info(f"Session {session_id} already exists")
            return self.chat_sessions[session_id]
        
        session = ChatSession(
            session_id=session_id,
            messages=[],
            message_count=0,
            created_at=datetime.now().isoformat()
        )
        
        self.chat_sessions[session_id] = session
        logger.info(f"New chat session created: {session_id}")
        
        return session
    
    def get_session(self, session_id: str) -> ChatSession | None:
        """
        Get an existing chat session
        
        Args:
            session_id: Session identifier
            
        Returns:
            ChatSession if exists, None otherwise
        """
        return self.chat_sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, content: str, confidence: Optional[float] = None) -> ChatMessage:
        """
        Add a message to a chat session
        
        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            confidence: Optional confidence score for user messages
            
        Returns:
            ChatMessage object that was added
        """
        # Ensure session exists
        if session_id not in self.chat_sessions:
            self.create_session(session_id)
        
        message = ChatMessage(
            role=role,  # type: ignore
            content=content,
            timestamp=datetime.now().isoformat(),
            confidence=confidence
        )
        
        self.chat_sessions[session_id].messages.append(message)
        self.chat_sessions[session_id].message_count += 1
        
        logger.info(f"Message added to session {session_id}: {role} - {content[:50]}...")
        
        return message
    
    def get_conversation_history(self, session_id: str, max_messages: int = 10) -> List[ChatMessage]:
        """
        Get recent conversation history for a session
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages to return
            
        Returns:
            List of recent ChatMessage objects
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Return the most recent messages
        return session.messages[-max_messages:] if len(session.messages) > max_messages else session.messages
    
    async def process_audio_message(self, session_id: str, audio_path: str) -> Dict:
        """
        Process audio message through the complete pipeline
        
        Args:
            session_id: Session identifier
            audio_path: Path to audio file to process
            
        Returns:
            Dictionary with processing results and response data
        """
        logger.info(f"Processing audio message for session: {session_id}")
        
        # Ensure session exists
        if session_id not in self.chat_sessions:
            self.create_session(session_id)
        
        # Step 1: Transcribe audio
        transcription_result = await self.stt_service.transcribe_audio(audio_path)
        
        # Add user message to history
        user_message = self.add_message(
            session_id, 
            "user", 
            transcription_result.text, 
            transcription_result.confidence
        )
        
        # Step 2: Generate LLM response
        conversation_history = self.get_conversation_history(session_id, max_messages=5)
        llm_result = await self.llm_service.generate_response(
            transcription_result.text, 
            conversation_history, 
            session_id
        )
        
        # Add assistant message to history
        assistant_message = self.add_message(
            session_id, 
            "assistant", 
            llm_result.response
        )
        
        # Step 3: Generate audio response
        audio_result = await self.tts_service.generate_audio(llm_result.response)
        
        # Prepare comprehensive response
        response_data = {
            "session_id": session_id,
            "user_message": transcription_result.text,
            "assistant_response": llm_result.response,
            "audio_url": audio_result.audio_url,
            "use_browser_tts": audio_result.use_browser_tts,
            "audio_source": audio_result.source,
            "voice_used": audio_result.voice_used,
            "total_messages": self.chat_sessions[session_id].message_count,
            "transcription_confidence": transcription_result.confidence,
            "error_handling": {
                "stt_status": transcription_result.status.value,
                "llm_status": llm_result.status.value,
                "tts_status": audio_result.status.value,
                "error_message": None
            }
        }
        
        logger.info(f"Audio message processed successfully for session {session_id}")
        
        return response_data
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear all messages from a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was cleared, False if session not found
        """
        if session_id in self.chat_sessions:
            self.chat_sessions[session_id].messages = []
            self.chat_sessions[session_id].message_count = 0
            logger.info(f"Session {session_id} cleared")
            return True
        
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session completely
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if session not found
        """
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            logger.info(f"Session {session_id} deleted")
            return True
        
        return False
    
    def get_all_sessions(self) -> Dict[str, ChatSession]:
        """
        Get all active chat sessions
        
        Returns:
            Dictionary of all chat sessions
        """
        return self.chat_sessions.copy()
    
    def get_service_status(self) -> Dict:
        """
        Get status of all underlying services
        
        Returns:
            Dictionary with status of STT, LLM, and TTS services
        """
        return {
            "stt": self.stt_service.get_status(),
            "llm": self.llm_service.get_status(),
            "tts": self.tts_service.get_status(),
            "active_sessions": len(self.chat_sessions),
            "total_messages": sum(session.message_count for session in self.chat_sessions.values())
        }
