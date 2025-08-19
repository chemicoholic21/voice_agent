"""
🎙️ WebSocket Audio Streaming Handler - Voice Agent Day 15
Real-time audio data transmission from client to server using WebSockets
"""

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio streaming
    
    Features:
    - Real-time binary audio data streaming
    - Audio session management with file saving
    - Control commands (start_recording, stop_recording)
    - Live feedback and chunk acknowledgments
    """
    await manager.connect(websocket)
    session_id = manager._get_session_id_for_websocket(websocket)
    
    try:
        # Welcome message to client
        await manager.send_personal_message(
            "🎙️ Connected to Voice Agent Audio Streaming! Send 'start_recording' to begin.", 
            websocket
        )
        
        audio_session_active = False
        
        while True:
            try:
                # Handle text commands (start/stop recording)
                data = await websocket.receive_text()
                logger.info(f"WebSocket received text: {data}")
                
                if data == "start_recording":
                    if not audio_session_active:
                        filepath = manager.create_audio_session(session_id)
                        audio_session_active = True
                        await manager.send_personal_message(
                            f"🔴 Recording started! Audio will be saved to: {Path(filepath).name}", 
                            websocket
                        )
                
                elif data == "stop_recording":
                    if audio_session_active:
                        manager._close_audio_session(session_id)
                        audio_session_active = False
                        await manager.send_personal_message(
                            "⏹️ Recording stopped and saved successfully!", 
                            websocket
                        )
                        
            except WebSocketDisconnect:
                break
            except Exception:
                # Handle binary audio data streaming
                try:
                    audio_data = await websocket.receive_bytes()
                    logger.info(f"WebSocket received audio chunk: {len(audio_data)} bytes")
                    
                    if audio_session_active:
                        # Save audio chunk to file
                        await manager.save_audio_chunk(session_id, audio_data)
                        
                        # Send progress updates (every 10th chunk)
                        session_info = manager.audio_sessions.get(session_id, {})
                        chunk_count = session_info.get('chunks_received', 0)
                        
                        if chunk_count % 10 == 0:
                            await manager.send_personal_message(
                                f"📡 Received {chunk_count} audio chunks ({session_info.get('total_bytes', 0)} bytes)", 
                                websocket
                            )
                    else:
                        await manager.send_personal_message(
                            "⚠️ Audio received but no recording session active. Send 'start_recording' first.", 
                            websocket
                        )
                        
                except Exception as inner_e:
                    logger.error(f"WebSocket error processing data: {str(inner_e)}")
                    break
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)


# ConnectionManager class for audio session management
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.audio_sessions: dict = {}  # Track audio streaming sessions
    
    def create_audio_session(self, session_id: str) -> str:
        """Create new audio streaming session with file handling"""
        timestamp = int(time.time())
        filename = f"stream_audio_{session_id}_{timestamp}.wav"
        filepath = Path(config.uploads_dir) / filename
        
        self.audio_sessions[session_id] = {
            'filepath': filepath,
            'file_handle': None,
            'chunks_received': 0,
            'total_bytes': 0,
            'start_time': timestamp
        }
        
        logger.info(f"Created audio session: {session_id} -> {filename}")
        return str(filepath)
    
    async def save_audio_chunk(self, session_id: str, audio_data: bytes):
        """Save real-time audio chunk to file"""
        if session_id not in self.audio_sessions:
            raise ValueError(f"Audio session {session_id} not found")
        
        session = self.audio_sessions[session_id]
        
        # Open file if not already open
        if session['file_handle'] is None:
            session['file_handle'] = open(session['filepath'], 'wb')
        
        # Write audio data in real-time
        session['file_handle'].write(audio_data)
        session['chunks_received'] += 1
        session['total_bytes'] += len(audio_data)
        
        logger.info(f"Session {session_id}: Saved chunk {session['chunks_received']} ({len(audio_data)} bytes)")
