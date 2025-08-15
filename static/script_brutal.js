// BRUTALISM VOICE AI - SIMPLIFIED & CLEAN CODE
console.log('🔥 BRUTALISM VOICE AI LOADED');

// Global state
let isRecording = false;
let mediaRecorder = null;
let recordedChunks = [];
let currentSessionId = null;
let messageCount = 0;
let startTime = Date.now();
let autoRecordEnabled = false;

// DOM Elements
const recordBtn = document.getElementById('recordBtn');
const recordIcon = document.getElementById('recordIcon');
const statusText = document.getElementById('statusText');
const sessionIdDisplay = document.getElementById('sessionId');
const messageCountDisplay = document.getElementById('messageCount');
const uptimeDisplay = document.getElementById('uptime');
const chatBox = document.getElementById('chatBox');
const chatContent = document.getElementById('chatContent');
const errorBox = document.getElementById('errorBox');
const errorText = document.getElementById('errorText');
const autoSwitch = document.getElementById('autoSwitch');
const audioPlayer = document.getElementById('audioPlayer');

// Initialize
document.addEventListener('DOMContentLoaded', init);

function init() {
    console.log('🚀 INITIALIZING BRUTALISM AI');
    
    // Generate session ID
    currentSessionId = generateSessionId();
    sessionIdDisplay.textContent = currentSessionId.slice(-6).toUpperCase();
    
    // Start uptime counter
    setInterval(updateUptime, 1000);
    
    // Update message count
    updateMessageCount();
    
    console.log('✅ INITIALIZATION COMPLETE');
}

function generateSessionId() {
    return `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function updateUptime() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    uptimeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function updateMessageCount() {
    messageCountDisplay.textContent = messageCount;
}

function showStatus(message, type = 'info') {
    statusText.textContent = message.toUpperCase();
    statusText.className = `status-text ${type}`;
}

function showError(message) {
    errorText.textContent = message.toUpperCase();
    errorBox.classList.add('visible');
    setTimeout(() => {
        errorBox.classList.remove('visible');
    }, 5000);
}

async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        console.log('🎙️ STARTING RECORDING');
        
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = processRecording;
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        recordBtn.classList.add('recording');
        recordIcon.textContent = '⏹';
        showStatus('RECORDING...', 'recording');
        
        console.log('✅ RECORDING STARTED');
        
    } catch (error) {
        console.error('❌ RECORDING ERROR:', error);
        showError('MICROPHONE ACCESS DENIED');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        console.log('⏹️ STOPPING RECORDING');
        
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        isRecording = false;
        
        // Update UI
        recordBtn.classList.remove('recording');
        recordBtn.classList.add('processing');
        recordIcon.textContent = '⚡';
        showStatus('PROCESSING...', 'processing');
    }
}

async function processRecording() {
    try {
        console.log('⚡ PROCESSING RECORDING');
        
        if (recordedChunks.length === 0) {
            throw new Error('NO AUDIO DATA');
        }

        const audioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
        console.log(`📊 AUDIO SIZE: ${audioBlob.size} BYTES`);

        await sendToAPI(audioBlob);
        
    } catch (error) {
        console.error('❌ PROCESSING ERROR:', error);
        showError(`ERROR: ${error.message}`);
        resetUI();
    }
}

async function sendToAPI(audioBlob) {
    try {
        console.log('📤 SENDING TO API');
        
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        
        showStatus('SENDING...', 'processing');
        
        const response = await fetch(`/agent/chat/${currentSessionId}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || `SERVER ERROR: ${response.status}`);
        }

        const result = await response.json();
        console.log('✅ API RESPONSE:', result);
        
        displayConversation(result);
        messageCount++;
        updateMessageCount();
        
        resetUI();
        
        // Auto-record if enabled
        if (autoRecordEnabled && result.audio_url) {
            setTimeout(() => {
                if (!isRecording) {
                    console.log('🔄 AUTO-RECORDING NEXT');
                    startRecording();
                }
            }, 2000);
        }
        
    } catch (error) {
        console.error('❌ API ERROR:', error);
        showError(`API ERROR: ${error.message}`);
        resetUI();
    }
}

function displayConversation(result) {
    console.log('💬 DISPLAYING CONVERSATION');
    
    // Show chat box
    chatBox.classList.add('visible');
    
    // Create user message
    const userMsg = createMessage('user', result.user_message || 'VOICE MESSAGE');
    chatContent.appendChild(userMsg);
    
    // Create AI message
    const aiMsg = createMessage('ai', result.assistant_response || 'NO RESPONSE');
    chatContent.appendChild(aiMsg);
    
    // Add audio player if available
    if (result.audio_url) {
        const audioContainer = document.createElement('div');
        audioContainer.style.marginTop = '15px';
        audioContainer.innerHTML = `
            <button class="control-btn" onclick="playAudio('${result.audio_url}')">
                ▶ PLAY AI RESPONSE
            </button>
        `;
        aiMsg.appendChild(audioContainer);
    }
    
    // Scroll to bottom
    chatContent.scrollTop = chatContent.scrollHeight;
    
    console.log('✅ CONVERSATION DISPLAYED');
}

function createMessage(type, text) {
    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    
    msg.innerHTML = `
        <div class="message-label">${type === 'user' ? 'YOU' : 'AI'}</div>
        <div class="message-text">${text}</div>
    `;
    
    return msg;
}

function playAudio(url) {
    console.log('🔊 PLAYING AUDIO');
    audioPlayer.src = url;
    audioPlayer.play().catch(error => {
        console.error('❌ AUDIO PLAY ERROR:', error);
        showError('AUDIO PLAYBACK FAILED');
    });
}

function resetUI() {
    recordBtn.classList.remove('recording', 'processing');
    recordIcon.textContent = '●';
    showStatus('PRESS TO SPEAK', 'info');
}

function toggleAuto() {
    autoRecordEnabled = !autoRecordEnabled;
    autoSwitch.classList.toggle('active', autoRecordEnabled);
    console.log(`🔄 AUTO-RECORD: ${autoRecordEnabled ? 'ON' : 'OFF'}`);
}

function newSession() {
    console.log('🆕 NEW SESSION');
    currentSessionId = generateSessionId();
    sessionIdDisplay.textContent = currentSessionId.slice(-6).toUpperCase();
    messageCount = 0;
    updateMessageCount();
    startTime = Date.now();
    clearChat();
}

function clearChat() {
    console.log('🗑️ CLEARING CHAT');
    chatContent.innerHTML = '';
    chatBox.classList.remove('visible');
}

// Error handling
window.addEventListener('error', (event) => {
    console.error('💥 GLOBAL ERROR:', event.error);
    showError('SYSTEM ERROR OCCURRED');
});

// API status check (simplified)
async function checkStatus() {
    try {
        const response = await fetch('/admin/error-status');
        if (response.ok) {
            const status = await response.json();
            console.log('📊 API STATUS:', status);
        }
    } catch (error) {
        console.warn('⚠️ STATUS CHECK FAILED');
    }
}

// Check status every 30 seconds
setInterval(checkStatus, 30000);

console.log('🎯 BRUTALISM VOICE AI READY');
