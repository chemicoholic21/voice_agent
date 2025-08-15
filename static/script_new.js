// Global variables for the modern UI
let mediaRecorder;
let recordedChunks = [];
let isRecording = false;
let currentSessionId = null;
let autoRecordEnabled = false;
let messageCount = 0;
let conversationStartTime = null;
let conversationTimer = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎙️ AI Voice Agent - Day 12 UI Loaded');
    initializeSession();
    checkApiStatus();
    
    // Start conversation timer
    startConversationTimer();
    
    // Add periodic API status check
    setInterval(checkApiStatus, 5000);
});

// Initialize new session
function initializeSession() {
    // Generate new session ID or use existing one from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentSessionId = urlParams.get('session') || generateSessionId();
    
    // Update session display
    document.getElementById('sessionIdDisplay').textContent = currentSessionId.split('_')[1].slice(-8).toUpperCase();
    document.getElementById('messageCount').textContent = messageCount;
    
    // Load conversation history
    loadChatHistory();
}

// Generate session ID
function generateSessionId() {
    return `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Start conversation timer
function startConversationTimer() {
    if (!conversationStartTime) {
        conversationStartTime = Date.now();
    }
    
    conversationTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - conversationStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        document.getElementById('conversationTime').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

// Toggle auto-record feature
function toggleAutoRecord() {
    autoRecordEnabled = !autoRecordEnabled;
    const toggle = document.getElementById('autoRecordToggle');
    toggle.classList.toggle('active', autoRecordEnabled);
    
    console.log(`Auto-record ${autoRecordEnabled ? 'enabled' : 'disabled'}`);
}

// Main recording toggle function
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
        console.log('🎙️ Starting recording...');
        
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        // Reset recorded chunks
        recordedChunks = [];
        
        // Create MediaRecorder
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm'
        });
        
        // Handle data available
        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        // Handle stop event
        mediaRecorder.onstop = function() {
            console.log('🎙️ Recording stopped, processing...');
            processRecording();
        };
        
        // Start recording
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        updateRecordingUI(true);
        
        console.log('🎙️ Recording started successfully');
        
    } catch (error) {
        console.error('❌ Error starting recording:', error);
        showStatus('Error accessing microphone. Please check permissions.', 'error');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        console.log('🛑 Stopping recording...');
        mediaRecorder.stop();
        
        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        isRecording = false;
        updateRecordingUI(false, 'processing');
    }
}

// Update recording UI state
function updateRecordingUI(recording, state = null) {
    const button = document.getElementById('mainRecordButton');
    const status = document.getElementById('recordStatus');
    const icon = document.getElementById('recordIcon');
    
    // Remove all state classes
    button.classList.remove('recording', 'processing');
    status.classList.remove('recording', 'processing', 'success');
    
    if (recording) {
        // Recording state
        button.classList.add('recording');
        status.classList.add('recording');
        status.textContent = '🔴 Recording... (tap to stop)';
        icon.textContent = '⏹️';
        
        // Add ripple effect
        addRippleEffect(button);
        
    } else if (state === 'processing') {
        // Processing state
        button.classList.add('processing');
        status.classList.add('processing');
        status.textContent = '⚡ Processing your voice...';
        icon.textContent = '⚡';
        
    } else {
        // Default state
        status.textContent = 'Tap to start conversation';
        icon.textContent = '🎙️';
    }
}

// Add ripple effect to button
function addRippleEffect(button) {
    const ripple = document.createElement('span');
    ripple.classList.add('ripple');
    
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (rect.width / 2 - size / 2) + 'px';
    ripple.style.top = (rect.height / 2 - size / 2) + 'px';
    
    button.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
        if (ripple.parentNode) {
            ripple.parentNode.removeChild(ripple);
        }
    }, 600);
}

// Process recorded audio
async function processRecording() {
    try {
        if (recordedChunks.length === 0) {
            throw new Error('No recorded audio data');
        }
        
        console.log('🎵 Processing recorded audio...');
        
        // Create blob from recorded chunks
        const audioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
        console.log(`📊 Audio blob size: ${audioBlob.size} bytes`);
        
        // Send to server
        await sendChatAudio(audioBlob);
        
    } catch (error) {
        console.error('❌ Error processing recording:', error);
        showStatus(`Recording error: ${error.message}`, 'error');
        updateRecordingUI(false);
    }
}

// Send audio to chat endpoint with enhanced error handling
async function sendChatAudio(audioBlob) {
    try {
        console.log('📤 Sending audio to server...');
        
        // Ensure we have a session ID
        if (!currentSessionId) {
            currentSessionId = generateSessionId();
        }
        
        // Create FormData
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        // Show processing status
        showStatus('🎯 Transcribing your voice...', 'info');
        
        // Send request with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout
        
        const response = await fetch(`/agent/chat/${currentSessionId}/stream`, {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(errorData?.detail || `Server error: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✅ Server response received:', result);
        
        // Update UI with success
        showStatus('✅ Response received!', 'success');
        updateRecordingUI(false);
        
        // Display the conversation
        displayChatExchange(result);
        
        // Update message count
        messageCount++;
        document.getElementById('messageCount').textContent = messageCount;
        
        // Load updated history
        loadChatHistory();
        
        // Auto-record if enabled
        if (autoRecordEnabled && result.ai_audio_url) {
            setTimeout(() => {
                if (!isRecording) {
                    console.log('🔄 Auto-starting next recording...');
                    startRecording();
                }
            }, 2000); // Wait 2 seconds after AI response
        }
        
    } catch (error) {
        console.error('❌ Chat error:', error);
        
        let errorMessage = 'Connection error. Please try again.';
        
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. Please try again.';
        } else if (error.message.includes('fetch')) {
            errorMessage = 'Network error. Check your connection.';
        } else if (error.message.includes('500')) {
            errorMessage = 'Server error. Some services may be down.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        showStatus(`❌ ${errorMessage}`, 'error');
        updateRecordingUI(false);
        
        // Check API status after error
        setTimeout(checkApiStatus, 1000);
    }
}

// Display chat exchange
function displayChatExchange(result) {
    const chatResult = document.getElementById('chatResult');
    chatResult.style.display = 'block';
    
    // Create exchange container
    const exchange = document.createElement('div');
    exchange.className = 'chat-exchange';
    
    // User message
    const userMessage = createMessageElement({
        text: result.transcription || 'Voice message',
        confidence: result.confidence,
        sender: 'user'
    });
    
    // AI message
    const aiMessage = createMessageElement({
        text: result.ai_response || 'No response available',
        sender: 'assistant'
    });
    
    exchange.appendChild(userMessage);
    exchange.appendChild(aiMessage);
    
    // Add action buttons
    const actions = document.createElement('div');
    actions.className = 'action-buttons';
    
    if (result.ai_audio_url) {
        const playButton = document.createElement('button');
        playButton.className = 'action-button';
        playButton.innerHTML = '🔊 Play AI Response';
        playButton.onclick = () => playAudioResponse(result.ai_audio_url);
        actions.appendChild(playButton);
    }
    
    const newConversationButton = document.createElement('button');
    newConversationButton.className = 'action-button';
    newConversationButton.innerHTML = '🆕 New Conversation';
    newConversationButton.onclick = startNewConversation;
    actions.appendChild(newConversationButton);
    
    exchange.appendChild(actions);
    
    // Add to chat result (replace previous)
    chatResult.innerHTML = '';
    chatResult.appendChild(exchange);
    
    // Scroll to result
    exchange.scrollIntoView({ behavior: 'smooth' });
}

// Create message element
function createMessageElement(data) {
    const message = document.createElement('div');
    message.className = 'chat-message';
    
    // Avatar
    const avatar = document.createElement('div');
    avatar.className = `message-avatar ${data.sender}`;
    avatar.textContent = data.sender === 'user' ? '👤' : '🤖';
    
    // Content
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const text = document.createElement('div');
    text.className = 'message-text';
    text.textContent = data.text;
    
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.innerHTML = `
        <span>${new Date().toLocaleTimeString()}</span>
        ${data.confidence ? `<span class="confidence-badge">${Math.round(data.confidence * 100)}% confidence</span>` : ''}
    `;
    
    content.appendChild(text);
    content.appendChild(meta);
    
    message.appendChild(avatar);
    message.appendChild(content);
    
    return message;
}

// Play audio response
function playAudioResponse(audioUrl) {
    const audio = document.getElementById('chatResponseAudio');
    audio.src = audioUrl;
    audio.style.display = 'block';
    
    audio.play().catch(error => {
        console.error('❌ Error playing audio:', error);
        showStatus('Could not play audio response', 'warning');
    });
    
    console.log('🔊 Playing AI audio response');
}

// Start new conversation
function startNewConversation() {
    currentSessionId = generateSessionId();
    messageCount = 0;
    conversationStartTime = Date.now();
    
    // Update UI
    document.getElementById('sessionIdDisplay').textContent = currentSessionId.split('_')[1].slice(-8).toUpperCase();
    document.getElementById('messageCount').textContent = messageCount;
    document.getElementById('chatResult').style.display = 'none';
    document.getElementById('chatHistoryContainer').classList.add('hidden');
    
    // Update URL
    const newUrl = new URL(window.location);
    newUrl.searchParams.set('session', currentSessionId);
    window.history.pushState({}, '', newUrl);
    
    showStatus('Started new conversation', 'success');
    console.log('🆕 Started new conversation:', currentSessionId);
}

// Load chat history
async function loadChatHistory() {
    try {
        const response = await fetch(`/agent/chat/${currentSessionId}/history`);
        if (!response.ok) return;
        
        const history = await response.json();
        
        if (history.messages && history.messages.length > 0) {
            displayChatHistory(history);
        }
        
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}

// Display chat history
function displayChatHistory(history) {
    const container = document.getElementById('chatHistoryContainer');
    const content = document.getElementById('chatHistory');
    
    content.innerHTML = '';
    
    history.messages.forEach(msg => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-message';
        historyItem.innerHTML = `
            <strong>${msg.role === 'user' ? '👤 You' : '🤖 AI'}:</strong>
            <span>${msg.content}</span>
            <small style="color: #6b7280; margin-left: 10px;">
                ${new Date(msg.timestamp).toLocaleTimeString()}
            </small>
        `;
        content.appendChild(historyItem);
    });
    
    container.classList.remove('hidden');
}

// Show status message
function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('chatStatus');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    statusDiv.classList.remove('hidden');
    
    // Auto-hide after 3 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 3000);
    }
}

// Check API status
async function checkApiStatus() {
    try {
        const response = await fetch('/admin/error-status');
        if (!response.ok) return;
        
        const status = await response.json();
        
        // Show error indicators if any APIs are down
        const errorContainer = document.querySelector('.error-indicators');
        if (errorContainer) {
            errorContainer.remove();
        }
        
        const downServices = [];
        if (!status.stt_available) downServices.push('Speech Recognition');
        if (!status.llm_available) downServices.push('AI Brain');
        if (!status.tts_available) downServices.push('Voice Synthesis');
        
        if (downServices.length > 0) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-indicators';
            
            downServices.forEach(service => {
                const badge = document.createElement('span');
                badge.className = 'error-badge';
                badge.textContent = `${service} Offline`;
                errorDiv.appendChild(badge);
            });
            
            const recordSection = document.querySelector('.record-section');
            recordSection.insertBefore(errorDiv, recordSection.firstChild);
        }
        
    } catch (error) {
        console.warn('Could not check API status:', error);
    }
}

// Utility function for error simulation (for testing)
async function simulateError(service, action) {
    try {
        const response = await fetch(`/admin/simulate-error/${service}?action=${action}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            console.log(`${service} ${action}d for testing`);
            checkApiStatus();
        }
    } catch (error) {
        console.error('Error simulating failure:', error);
    }
}

// Export functions for global access
window.toggleRecording = toggleRecording;
window.toggleAutoRecord = toggleAutoRecord;
window.startNewConversation = startNewConversation;
window.simulateError = simulateError;
