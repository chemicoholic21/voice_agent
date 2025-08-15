"""
Configuration management for Voice Agent
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration class for Voice Agent application"""
    
    # API Keys
    assemblyai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    murf_api_key: Optional[str] = None
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8001
    
    # File Paths
    uploads_dir: str = "uploads"
    static_dir: str = "static"
    log_file: Optional[str] = None
    
    # Service Configuration
    max_text_length: int = 3000  # Murf API limit
    max_retries: int = 2
    api_timeout: int = 15
    
    # Logging
    log_level: str = "INFO"
    
    # Chat Configuration
    max_conversation_history: int = 5
    session_timeout_hours: int = 24


def load_config() -> Config:
    """
    Load configuration from environment variables
    
    Returns:
        Config object with loaded values
    """
    # Load environment variables from .env file
    load_dotenv()
    
    config = Config(
        # API Keys
        assemblyai_api_key=os.getenv("ASSEMBLYAI_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        murf_api_key=os.getenv("MURF_API_KEY"),
        
        # Server Configuration
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8001)),
        
        # File Paths
        uploads_dir=os.getenv("UPLOADS_DIR", "uploads"),
        static_dir=os.getenv("STATIC_DIR", "static"),
        log_file=os.getenv("LOG_FILE"),  # Optional
        
        # Service Configuration
        max_text_length=int(os.getenv("MAX_TEXT_LENGTH", 3000)),
        max_retries=int(os.getenv("MAX_RETRIES", 2)),
        api_timeout=int(os.getenv("API_TIMEOUT", 15)),
        
        # Logging
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        
        # Chat Configuration
        max_conversation_history=int(os.getenv("MAX_CONVERSATION_HISTORY", 5)),
        session_timeout_hours=int(os.getenv("SESSION_TIMEOUT_HOURS", 24))
    )
    
    return config


def validate_config(config: Config) -> list[str]:
    """
    Validate configuration and return list of warnings/errors
    
    Args:
        config: Configuration object to validate
        
    Returns:
        List of validation messages (empty if all valid)
    """
    issues = []
    
    # Check API keys
    if not config.assemblyai_api_key or config.assemblyai_api_key.strip() == "":
        issues.append("AssemblyAI API key not set - STT service will use fallback mode")
    
    if not config.gemini_api_key or config.gemini_api_key.strip() == "":
        issues.append("Gemini API key not set - LLM service will use fallback mode")
    
    if not config.murf_api_key or config.murf_api_key.strip() == "":
        issues.append("Murf API key not set - TTS service will use browser fallback")
    
    # Check port range
    if not (1 <= config.port <= 65535):
        issues.append(f"Invalid port number: {config.port}")
    
    # Check timeout values
    if config.api_timeout <= 0:
        issues.append(f"Invalid API timeout: {config.api_timeout}")
    
    if config.max_retries < 0:
        issues.append(f"Invalid max retries: {config.max_retries}")
    
    # Check log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.log_level.upper() not in valid_log_levels:
        issues.append(f"Invalid log level: {config.log_level}. Must be one of {valid_log_levels}")
    
    return issues
