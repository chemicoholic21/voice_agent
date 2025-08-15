"""
Voice Agent FastAPI Application - Refactored for Maintainability
A conversational AI agent with speech-to-text, LLM, and text-to-speech capabilities.
"""

import os
import tempfile
import json
import time
import asyncio
from pathlib import Path
from typing import Generator

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

# Import our modular services and utilities
from services import STTService, LLMService, TTSService, ChatService
from schemas import (
    ChatResponse, StreamEvent, StreamEventType, ErrorSimulationResponse, 
    ErrorStatusResponse, ServiceStatus
)
from utils import (
    setup_logging, get_logger, load_config, validate_config,
    ensure_directory, cleanup_temp_files, save_uploaded_file,
    create_error_response, create_stream_event, validate_session_id,
    log_request_info, measure_execution_time
)

# Initialize configuration and logging
config = load_config()
setup_logging(level=config.log_level, log_file=config.log_file)
logger = get_logger(__name__)

# Validate configuration
config_issues = validate_config(config)
if config_issues:
    for issue in config_issues:
        logger.warning(f"Config issue: {issue}")

# Initialize FastAPI app
app = FastAPI(
    title="Voice Agent with Robust Error Handling", 
    version="2.0.0",
    description="Conversational AI agent with modular architecture"
)

# Mount static files
app.mount("/static", StaticFiles(directory=config.static_dir), name="static")

# Create uploads directory
uploads_dir = ensure_directory(config.uploads_dir)

# Initialize services
logger.info("Initializing AI services...")
stt_service = STTService(config.assemblyai_api_key)
llm_service = LLMService(config.gemini_api_key)
tts_service = TTSService(config.murf_api_key)
chat_service = ChatService(stt_service, llm_service, tts_service)

# Log service initialization status
service_status = chat_service.get_service_status()
logger.info(f"Services initialized: {service_status}")

# Store original API keys for error simulation
original_keys = {
    'assemblyai': config.assemblyai_api_key,
    'gemini': config.gemini_api_key,
    'murf': config.murf_api_key
}


@app.get("/")
async def serve_index():
    """Serve the main HTML page"""
    return FileResponse(f"{config.static_dir}/index.html")


@app.post("/agent/chat/{session_id}", response_model=ChatResponse)
@measure_execution_time
async def conversational_chat(session_id: str, file: UploadFile = File(...)):
    """
    Conversational agent with chat history memory and comprehensive error handling
    """
    log_request_info("conversational_chat", session_id)
    
    try:
        # Validate session ID
        if not validate_session_id(session_id):
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        
        logger.info(f"Processing conversational chat for session: {session_id}")
        
        # Save uploaded audio file
        try:
            audio_content = await file.read()
            audio_filename = f"chat_{session_id}_{int(time.time())}.wav"
            audio_path = save_uploaded_file(audio_content, audio_filename, uploads_dir)
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save audio file. Please try again.")
        
        # Process the audio message through the complete pipeline
        try:
            response_data = await chat_service.process_audio_message(session_id, str(audio_path))
        finally:
            # Clean up uploaded file
            cleanup_temp_files([audio_path], ignore_errors=True)
        
        logger.info(f"Conversational chat completed for session {session_id}")
        return JSONResponse(response_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in conversational chat: {str(e)}")
        return create_error_response(
            "I'm sorry, I'm experiencing technical difficulties right now. Please try again in a moment.",
            session_id,
            {"unexpected_error": str(e)}
        )


@app.post("/agent/chat/{session_id}/stream")
@measure_execution_time
async def stream_conversational_chat(session_id: str, file: UploadFile = File(...)):
    """
    Real-time streaming conversational agent with comprehensive error handling
    Returns Server-Sent Events for real-time UI updates
    """
    log_request_info("stream_conversational_chat", session_id)
    
    def generate_stream() -> Generator[str, None, None]:
        try:
            yield create_stream_event("status", {"message": "Processing audio...", "status": "info"})
            
            # Validate session ID
            if not validate_session_id(session_id):
                yield create_stream_event("error", {"message": "Invalid session ID format"})
                return
            
            # Create session if it doesn't exist
            session = chat_service.get_session(session_id)
            if not session:
                chat_service.create_session(session_id)
                yield create_stream_event("session", {"message": f"New session created: {session_id}"})
            
            # Save uploaded audio file
            try:
                audio_content = file.file.read()
                audio_filename = f"stream_{session_id}_{int(time.time())}.wav"
                audio_path = save_uploaded_file(audio_content, audio_filename, uploads_dir)
                
                yield create_stream_event("status", {"message": "🎙️ Transcribing your voice...", "status": "info"})
            except Exception as e:
                yield create_stream_event("error", {"message": "Failed to process audio file. Please try again."})
                return
            
            # Step 1: Real-time transcription
            try:
                # Run async transcription in event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                transcription_result = loop.run_until_complete(stt_service.transcribe_audio(str(audio_path)))
                
                if transcription_result.status == ServiceStatus.ERROR:
                    yield create_stream_event("error", {"message": transcription_result.text})
                    return
                
                # Send transcription result
                yield create_stream_event("transcription", {
                    "text": transcription_result.text, 
                    "confidence": transcription_result.confidence
                })
                
            except Exception as e:
                yield create_stream_event("error", {"message": "Speech recognition is temporarily unavailable. Please try again."})
                return
            
            # Add user message to chat history
            chat_service.add_message(session_id, "user", transcription_result.text, transcription_result.confidence)
            
            yield create_stream_event("status", {"message": "🤖 AI is thinking...", "status": "info"})
            
            # Step 2: Get LLM response with streaming
            try:
                conversation_history = chat_service.get_conversation_history(session_id)
                llm_result = loop.run_until_complete(llm_service.generate_response(
                    transcription_result.text, conversation_history, session_id
                ))
                
                # Stream the response word by word for real-time effect
                words = llm_result.response.split()
                full_response = ""
                
                for i, word in enumerate(words):
                    full_response += word + " "
                    # Send incremental response every few words
                    if i % 3 == 0 or i == len(words) - 1:
                        yield create_stream_event("llm_response", {
                            "text": full_response.strip(), 
                            "is_complete": i == len(words) - 1,
                            "is_fallback": llm_result.status != ServiceStatus.SUCCESS
                        })
                        time.sleep(0.1)  # Small delay for streaming effect
                
                # Add assistant message to chat history
                chat_service.add_message(session_id, "assistant", full_response.strip())
                
            except Exception as e:
                fallback_response = "I'm experiencing some technical difficulties. Could you please try again?"
                yield create_stream_event("llm_response", {
                    "text": fallback_response, 
                    "is_complete": True, 
                    "is_fallback": True
                })
                full_response = fallback_response
            
            yield create_stream_event("status", {"message": "🔊 Generating audio...", "status": "info"})
            
            # Step 3: Generate audio with fallback handling
            try:
                audio_result = loop.run_until_complete(tts_service.generate_audio(full_response.strip()))
                
                if audio_result.audio_url:
                    yield create_stream_event("audio", {
                        "url": audio_result.audio_url, 
                        "source": audio_result.source
                    })
                else:
                    yield create_stream_event("audio", {
                        "use_browser_tts": True, 
                        "text": full_response.strip(), 
                        "source": "browser"
                    })
                
            except Exception as e:
                yield create_stream_event("audio", {
                    "use_browser_tts": True, 
                    "text": full_response.strip(), 
                    "source": "browser"
                })
            
            # Clean up audio file
            cleanup_temp_files([audio_path], ignore_errors=True)
            
            # Final completion
            session = chat_service.get_session(session_id)
            yield create_stream_event("complete", {
                "session_id": session_id, 
                "message_count": session.message_count if session else 0, 
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield create_stream_event("error", {
                "message": "Unexpected error: Please try again.", 
                "details": str(e)
            })
    
    return StreamingResponse(generate_stream(), media_type="text/plain")


@app.get("/agent/chat/{session_id}/history")
async def get_chat_history(session_id: str):
    """Get the chat history for a session"""
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    session = chat_service.get_session(session_id)
    if not session:
        return JSONResponse({
            "session_id": session_id, 
            "messages": [], 
            "message_count": 0
        })
    
    return JSONResponse({
        "session_id": session_id,
        "messages": [msg.dict() for msg in session.messages],
        "message_count": session.message_count
    })


# Admin endpoints for error simulation and testing
@app.post("/admin/simulate-error/{error_type}", response_model=ErrorSimulationResponse)
async def simulate_error(error_type: str, action: str = "disable"):
    """
    Simulate API errors by temporarily disabling API keys for testing
    error_type: 'stt', 'llm', 'tts', or 'all'
    action: 'disable' or 'enable'
    """
    logger.info(f"Error simulation request: {error_type} - {action}")
    
    if action == "disable":
        if error_type == "stt" or error_type == "all":
            stt_service.set_api_key("DISABLED_FOR_TESTING")
        if error_type == "llm" or error_type == "all":
            llm_service.set_api_key("DISABLED_FOR_TESTING")
        if error_type == "tts" or error_type == "all":
            tts_service.set_api_key("DISABLED_FOR_TESTING")
        
        return ErrorSimulationResponse(
            message=f"Simulated {error_type} error - API keys disabled",
            error_type=error_type,
            apis_disabled=[error_type] if error_type != "all" else ["stt", "llm", "tts"]
        )
    
    elif action == "enable":
        if error_type == "stt" or error_type == "all":
            stt_service.set_api_key(original_keys['assemblyai'])
        if error_type == "llm" or error_type == "all":
            llm_service.set_api_key(original_keys['gemini'])
        if error_type == "tts" or error_type == "all":
            tts_service.set_api_key(original_keys['murf'])
        
        return ErrorSimulationResponse(
            message=f"Restored {error_type} API functionality",
            error_type=error_type,
            apis_restored=[error_type] if error_type != "all" else ["stt", "llm", "tts"]
        )
    
    else:
        raise HTTPException(status_code=400, detail="Action must be 'disable' or 'enable'")


@app.get("/admin/error-status", response_model=ErrorStatusResponse)
async def get_error_status():
    """Get current error simulation status"""
    stt_status = stt_service.get_status()
    llm_status = llm_service.get_status()
    tts_status = tts_service.get_status()
    
    return ErrorStatusResponse(
        stt_disabled=stt_status["disabled"],
        llm_disabled=llm_status["disabled"],
        tts_disabled=tts_status["disabled"],
        assemblyai_key_set=stt_status["api_key_set"],
        gemini_key_set=llm_status["api_key_set"],
        murf_key_set=tts_status["api_key_set"]
    )


@app.get("/admin/service-status")
async def get_service_status():
    """Get comprehensive service status"""
    return chat_service.get_service_status()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": chat_service.get_service_status()
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting Voice Agent server on {config.host}:{config.port}")
    uvicorn.run(app, host=config.host, port=config.port)
