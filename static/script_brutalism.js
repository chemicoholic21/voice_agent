// Brutalism Bento UI - Simplified Voice Agent
let mediaRecorder;
let recordedChunks = [];
let isRecording = false;
let currentSessionId = null;
let autoRecordEnabled = false;
let messageCount = 0;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎙️ BRUTALISM VOICE AGENT LOADED');
    initializeSession();
    checkApiStatus();
    setInterval(checkApiStatus, 5000);
});

// Initialize session
function initializeSession() {
    const urlParams = new URLSearchParams(window.location.search);
    currentSessionId = urlParams.get('session') || generateSessionId();
    
    document.getElementById('sessionIdDisplay').textContent = currentSessionId.split('_')[1].slice(-6).toUpperCase();
    document.getElementById('messageCount').textContent = messageCount;
}

// Generate session ID
function generateSessionId() {
    return `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Toggle auto-record
function toggleAutoRecord() {
    autoRecordEnabled = !autoRecordEnabled;
    const toggle = document.getElementById('autoRecordToggle');
    toggle.classList.toggle('active', autoRecordEnabled);
    
    showStatus(autoRecordEnabled ? 'AUTO-RECORD ENABLED' : 'AUTO-RECORD DISABLED', 'info');
}

// Main recording function
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

// Start recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        
        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = function() {
            processRecording();
        };
        
        mediaRecorder.start();
        isRecording = true;
        updateRecordingUI(true);
        
    } catch (error) {
        console.error('❌ MIC ERROR:', error);
        showStatus('MIC ACCESS DENIED', 'error');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        updateRecordingUI(false, 'processing');
    }
}

// Update UI
function updateRecordingUI(recording, state = null) {
    const button = document.getElementById('mainRecordButton');
    const status = document.getElementById('recordStatus');
    const icon = document.getElementById('recordIcon');
    
    button.classList.remove('recording', 'processing');
    
    if (recording) {
        button.classList.add('recording');
        status.textContent = 'RECORDING...';
        status.className = 'record-status recording';
        icon.textContent = '⏹️';
    } else if (state === 'processing') {
        button.classList.add('processing');
        status.textContent = 'PROCESSING...';
        status.className = 'record-status processing';
        icon.textContent = '⚡';
    } else {
        status.textContent = 'TAP TO START';
        status.className = 'record-status';
        icon.textContent = '🎙️';
    }
}

// Process recorded audio
async function processRecording() {
    try {
        if (recordedChunks.length === 0) {
            throw new Error('NO AUDIO DATA');
        }
        
        const audioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
        await sendChatAudio(audioBlob);
        
    } catch (error) {
        console.error('❌ PROCESSING ERROR:', error);
        showStatus(`ERROR: ${error.message}`, 'error');
        updateRecordingUI(false);
    }
}

// Send audio to server
async function sendChatAudio(audioBlob) {
    try {
        showStatus('TRANSCRIBING...', 'info');
        
        if (!currentSessionId) {
            currentSessionId = generateSessionId();
        }
        
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        const response = await fetch(`/agent/chat/${currentSessionId}`, {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || `SERVER ERROR: ${response.status}`);
        }
        
        const result = await response.json();
        
        showStatus('RESPONSE RECEIVED', 'success');
        updateRecordingUI(false);
        displayChatExchange(result);
        
        messageCount++;
        document.getElementById('messageCount').textContent = messageCount;
        
        if (autoRecordEnabled && result.audio_url) {
            setTimeout(() => {
                if (!isRecording) {
                    startRecording();
                }
            }, 2000);
        }
        
    } catch (error) {
        console.error('❌ CHAT ERROR:', error);
        
        let errorMessage = 'CONNECTION ERROR';
        
        if (error.name === 'AbortError') {
            errorMessage = 'REQUEST TIMEOUT';
        } else if (error.message.includes('500')) {
            errorMessage = 'SERVER ERROR';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        showStatus(errorMessage, 'error');
        updateRecordingUI(false);
        setTimeout(checkApiStatus, 1000);
    }
}

// Display chat
function displayChatExchange(result) {
    const chatCard = document.getElementById('chatCard');
    const chatContent = document.getElementById('chatContent');
    const actionButtons = document.getElementById('actionButtons');
    const playButton = document.getElementById('playButton');
    
    chatCard.classList.add('active');
    
    const userMessage = createMessage({
        text: result.user_message || 'VOICE MESSAGE',
        confidence: result.transcription_confidence,
        sender: 'USER'
    });
    
    const aiMessage = createMessage({
        text: result.assistant_response || 'NO RESPONSE',
        sender: 'AI'
    });
    
    chatContent.innerHTML = '';
    chatContent.appendChild(userMessage);
    chatContent.appendChild(aiMessage);
    
    if (result.audio_url) {
        actionButtons.style.display = 'block';
        playButton.onclick = () => playAudioResponse(result.audio_url);
    } else {
        actionButtons.style.display = 'none';
    }
}

// Create message element
function createMessage(data) {
    const message = document.createElement('div');
    message.className = 'chat-message';
    
    message.innerHTML = `
        <div class="message-header">
            <span class="message-sender">${data.sender === 'USER' ? '👤 USER' : '🤖 AI'}</span>
            <span class="message-time">${new Date().toLocaleTimeString()}</span>
        </div>
        <div class="message-text">${data.text}</div>
        ${data.confidence ? `<span class="confidence-badge">${Math.round(data.confidence * 100)}% CONF</span>` : ''}
    `;
    
    return message;
}

// Play audio
function playAudioResponse(audioUrl) {
    const audio = document.getElementById('chatResponseAudio');
    audio.src = audioUrl;
    
    audio.play().catch(error => {
        console.error('❌ AUDIO ERROR:', error);
        showStatus('AUDIO PLAYBACK FAILED', 'error');
    });
    
    showStatus('PLAYING AI RESPONSE', 'info');
}

// Start new conversation
function startNewConversation() {
    currentSessionId = generateSessionId();
    messageCount = 0;
    
    document.getElementById('sessionIdDisplay').textContent = currentSessionId.split('_')[1].slice(-6).toUpperCase();
    document.getElementById('messageCount').textContent = messageCount;
    document.getElementById('chatCard').classList.remove('active');
    document.getElementById('statusCard').classList.remove('active');
    
    const newUrl = new URL(window.location);
    newUrl.searchParams.set('session', currentSessionId);
    window.history.pushState({}, '', newUrl);
    
    showStatus('NEW SESSION STARTED', 'success');
}

// Show status
function showStatus(message, type = 'info') {
    const statusCard = document.getElementById('statusCard');
    const statusMessage = document.getElementById('statusMessage');
    
    statusCard.className = `bento-card status-card active ${type}`;
    statusMessage.textContent = message;
    
    if (type === 'success') {
        setTimeout(() => {
            statusCard.classList.remove('active');
        }, 3000);
    }
}

// Check API status
async function checkApiStatus() {
    try {
        const response = await fetch('/admin/error-status');
        if (!response.ok) return;
        
        const status = await response.json();
        const errorBadges = document.getElementById('errorBadges');
        
        errorBadges.innerHTML = '';
        
        const downServices = [];
        if (!status.stt_available) downServices.push('STT DOWN');
        if (!status.llm_available) downServices.push('LLM DOWN');
        if (!status.tts_available) downServices.push('TTS DOWN');
        
        if (downServices.length > 0) {
            downServices.forEach(service => {
                const badge = document.createElement('span');
                badge.className = 'error-badge';
                badge.textContent = service;
                errorBadges.appendChild(badge);
            });
            
            const statusCard = document.getElementById('statusCard');
            statusCard.classList.add('active');
        }
        
    } catch (error) {
        console.warn('STATUS CHECK FAILED:', error);
    }
}

// Export functions
window.toggleRecording = toggleRecording;
window.toggleAutoRecord = toggleAutoRecord;
window.startNewConversation = startNewConversation;
