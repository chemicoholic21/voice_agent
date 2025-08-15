"""
File utilities for Voice Agent
"""

import os
import tempfile
import shutil
import time
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def ensure_directory(directory_path: str | Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path object for the directory
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Directory ensured: {path}")
    return path


def cleanup_temp_files(file_paths: List[str | Path], ignore_errors: bool = True) -> None:
    """
    Clean up temporary files safely
    
    Args:
        file_paths: List of file paths to delete
        ignore_errors: Whether to ignore deletion errors
    """
    for file_path in file_paths:
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.debug(f"Cleaned up file: {path}")
        except Exception as e:
            if not ignore_errors:
                raise
            logger.warning(f"Could not clean up file {file_path}: {e}")


def save_uploaded_file(
    file_content: bytes, 
    filename: str,
    upload_dir: str | Path = "uploads"
) -> Path:
    """
    Save uploaded file content to disk
    
    Args:
        file_content: Binary content of the file
        filename: Name for the saved file
        upload_dir: Directory to save the file in
        
    Returns:
        Path to the saved file
    """
    upload_path = ensure_directory(upload_dir)
    file_path = upload_path / filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    logger.info(f"File saved: {file_path} ({len(file_content)} bytes)")
    return file_path


def create_temp_file(suffix: str = ".wav", prefix: str = "voice_agent_") -> str:
    """
    Create a temporary file and return its path
    
    Args:
        suffix: File extension/suffix
        prefix: File prefix
        
    Returns:
        Path to the temporary file
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)  # Close the file descriptor, but keep the file
    logger.debug(f"Temporary file created: {path}")
    return path


def get_file_size(file_path: str | Path) -> int:
    """
    Get the size of a file in bytes
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
    """
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return 0


def is_valid_audio_file(file_path: str | Path, max_size_mb: int = 25) -> tuple[bool, Optional[str]]:
    """
    Validate if a file is a valid audio file
    
    Args:
        file_path: Path to the file to validate
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False, "File does not exist"
    
    # Check file size
    file_size = get_file_size(path)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Check file extension (basic validation)
    valid_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm'}
    if path.suffix.lower() not in valid_extensions:
        return False, f"Invalid file type. Supported: {', '.join(valid_extensions)}"
    
    return True, None


def generate_unique_filename(base_name: str, session_id: str, counter: int = 0) -> str:
    """
    Generate a unique filename for uploaded audio
    
    Args:
        base_name: Base name for the file
        session_id: Session identifier
        counter: Optional counter for uniqueness
        
    Returns:
        Unique filename
    """
    timestamp = int(time.time())
    return f"{base_name}_{session_id}_{counter}_{timestamp}.wav"


def copy_static_files(source_dir: str | Path, dest_dir: str | Path) -> None:
    """
    Copy static files from source to destination directory
    
    Args:
        source_dir: Source directory path
        dest_dir: Destination directory path
    """
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    if not source_path.exists():
        logger.warning(f"Source directory does not exist: {source_path}")
        return
    
    ensure_directory(dest_path)
    
    try:
        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        logger.info(f"Static files copied from {source_path} to {dest_path}")
    except Exception as e:
        logger.error(f"Failed to copy static files: {e}")


def get_directory_size(directory_path: str | Path) -> int:
    """
    Calculate total size of a directory and its contents
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    continue
    except Exception:
        pass
    
    return total_size
