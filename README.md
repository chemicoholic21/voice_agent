# 🎤 AI Voice Agent - 30 Days Challenge

[![Built with FastAPI](https://img.shields.io/badge/Built%20with-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Powered by Murf AI](https://img.shields.io/badge/Powered%20by-Murf%20AI-ff6b35.svg)](https://murf.ai/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A production-ready conversational AI voice agent built during the #30DaysofVoiceAgents challenge. Features bulletproof error handling, real-time streaming, and a brutalist bento UI design.**

## 🌟 Overview

This project is a sophisticated voice-powered conversational AI that combines cutting-edge speech technologies into a seamless user experience. Built over 12 days, it evolved from a simple text-to-speech tool into a robust, production-ready voice agent with memory, error resilience, and modern UI design.

### ✨ Key Achievements
- **🎯 End-to-End Voice Pipeline**: Speech → AI → Voice response
- **🧠 Conversational Memory**: Session-based chat history
- **🛡️ Production-Grade Error Handling**: Graceful degradation for all failure scenarios
- **🎨 Modern Brutalist UI**: Clean, focused, accessible design
- **⚡ Real-Time Processing**: Streaming responses and live updates

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Voice    │───▶│   Web Audio API  │───▶│  FastAPI Server │
│     Input       │    │   (Recording)    │    │   (Backend)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 │                                 │
                       ▼                                 ▼                                 ▼
              ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
              │  AssemblyAI STT │              │ Google Gemini   │              │    Murf AI      │
              │ (Speech-to-Text)│              │     (LLM)       │              │ (Text-to-Speech)│
              └─────────────────┘              └─────────────────┘              └─────────────────┘
                       │                                 │                                 │
                       ▼                                 ▼                                 ▼
              ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
              │  Transcription  │              │  AI Response    │              │  Audio Stream   │
              │   + Confidence  │              │   + Context     │              │   + Fallback    │
              └─────────────────┘              └─────────────────┘              └─────────────────┘
                       │                                 │                                 │
                       └─────────────────┐               │               ┌─────────────────┘
                                         │               │               │
                                         ▼               ▼               ▼
                                  ┌─────────────────────────────────────────────────────────┐
                                  │           Chat History Storage                          │
                                  │        (Session-based Memory)                          │
                                  └─────────────────────────────────────────────────────────┘
                                                         │
                                                         ▼
                                  ┌─────────────────────────────────────────────────────────┐
                                  │              Error Handling Layer                      │
                                  │         (Fallbacks + Health Monitoring)               │
                                  └─────────────────────────────────────────────────────────┘
```

### 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python 3.8+ | RESTful API server with async support |
| **Speech-to-Text** | AssemblyAI API | High-accuracy voice transcription |
| **AI Brain** | Google Gemini 1.5 Flash | Intelligent conversation generation |
| **Text-to-Speech** | Murf AI + Browser TTS | Professional voice synthesis |
| **Frontend** | Vanilla JS + CSS Grid | Responsive brutalist UI |
| **Storage** | In-memory Python dict | Session-based chat history |
| **Error Handling** | Custom middleware | Comprehensive fallback system |

---

## 🚀 Features

### 🎙️ **Core Voice Capabilities**
- **One-Click Recording**: Smart button that adapts to current state
- **Real-Time Transcription**: Live speech-to-text conversion
- **Intelligent Responses**: Context-aware AI conversations
- **Professional Voice Output**: High-quality TTS with fallbacks

### 🧠 **Advanced AI Features**
- **Conversational Memory**: Remembers entire chat history
- **Context Awareness**: AI responds based on previous messages
- **Auto-Record Mode**: Seamless conversation flow
- **Confidence Scoring**: Speech recognition accuracy metrics

### 🛡️ **Production-Ready Robustness**
- **Comprehensive Error Handling**: Graceful degradation for all APIs
- **Multiple Fallback Layers**: Service redundancy at every level
- **Health Monitoring**: Real-time API status indicators
- **Timeout Protection**: Prevents hanging requests
- **User-Friendly Errors**: Technical issues translated to natural language

### 🎨 **Modern UI/UX**
- **Brutalist Bento Design**: Bold, geometric, accessible
- **Responsive Layout**: Works on mobile and desktop
- **State-Aware Interface**: Visual feedback for all actions
- **Real-Time Updates**: Live session tracking and statistics
- **Accessibility Focus**: High contrast, keyboard navigation

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Modern web browser with microphone support

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd voice-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:

```env
# Required API Keys
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here
MURF_API_KEY=your_murf_api_key_here

# Optional Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 4. Get API Keys

#### 🎤 AssemblyAI (Speech-to-Text)
1. Visit [AssemblyAI](https://www.assemblyai.com/)
2. Sign up for a free account
3. Copy your API key from the dashboard

#### 🤖 Google Gemini (LLM)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new project
3. Generate an API key for Gemini

#### 🗣️ Murf AI (Text-to-Speech)
1. Visit [Murf AI](https://murf.ai/)
2. Sign up and get your API credentials
3. Add your API key to the environment

### 5. Run the Server
```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --port 8001

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 6. Access the Application
Open your browser and navigate to:
```
http://localhost:8001
```

---

## 🎯 Usage Guide

### 🗣️ **Starting a Conversation**
1. **Click the record button** - The orange button will turn red and start pulsing
2. **Speak your message** - Talk naturally, the system will capture your voice
3. **Click to stop recording** - Button turns yellow while processing
4. **Listen to AI response** - The agent responds with voice and text

### ⚡ **Auto-Record Mode**
- **Toggle the "Auto-Record" switch** for seamless conversations
- **AI automatically starts listening** after each response
- **Perfect for natural back-and-forth dialogue**

### 📊 **Session Management**
- **Session ID**: Unique identifier for your conversation
- **Message Counter**: Tracks conversation length
- **Timer**: Shows conversation duration
- **New Conversation**: Reset and start fresh

### 🛠️ **Error Testing** (Admin Features)
Access error simulation endpoints for testing resilience:
- **STT Testing**: Simulate speech recognition failures
- **LLM Testing**: Simulate AI brain outages
- **TTS Testing**: Simulate voice synthesis issues
- **Network Testing**: Simulate connectivity problems

---

## 📁 Project Structure

```
voice-agent/
├── main.py                 # FastAPI server & API endpoints
├── static/
│   ├── index.html         # Brutalist UI interface
│   └── script.js          # Frontend JavaScript logic
├── uploads/               # Temporary audio file storage
├── .env                   # Environment variables (create this)
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── README.md            # This documentation
└── .gitignore          # Git ignore rules
```

---

## 🔌 API Endpoints

### 🎙️ **Voice Conversation**
```http
POST /agent/chat/{session_id}
Content-Type: multipart/form-data

Parameters:
- file: Audio file (WAV, MP3, WebM)

Response:
{
    "session_id": "chat_1234567890_abc123",
    "user_message": "Hello, how are you?",
    "assistant_response": "I'm doing great! How can I help you today?",
    "audio_url": "https://murf-audio-url.com/response.mp3",
    "use_browser_tts": false,
    "audio_source": "murf",
    "voice_used": "en-US-neural",
    "total_messages": 1,
    "transcription_confidence": 0.95,
    "error_handling": {
        "stt_status": "success",
        "llm_status": "success",
        "tts_status": "success"
    }
}
```

### 📊 **Session Management**
```http
GET /agent/chat/{session_id}/history
# Get conversation history for a session

Response:
{
    "session_id": "chat_1234567890_abc123",
    "messages": [
        {
            "role": "user",
            "content": "Hello, how are you?",
            "timestamp": "2025-08-14T10:30:00Z"
        },
        {
            "role": "assistant", 
            "content": "I'm doing great! How can I help you today?",
            "timestamp": "2025-08-14T10:30:02Z"
        }
    ],
    "message_count": 2
}
```

### 🔧 **Health & Admin**
```http
GET /                      # Serve main application
GET /admin/error-status    # Check API health status
POST /admin/simulate-error/{service}?action={enable|disable}
# Simulate service failures for testing
```

---

## 🛡️ Error Handling System

This voice agent implements **bulletproof error handling** across all components:

### 🎯 **Smart Fallbacks**

| Failure Type | User Experience | Technical Fallback |
|--------------|-----------------|-------------------|
| **STT Failure** | "I couldn't understand what you said. Please try speaking more clearly." | Retry mechanism + user guidance |
| **LLM Outage** | "I'm having trouble connecting to my AI brain right now. Please try again in a moment." | Cached responses + service restoration |
| **TTS Issues** | Seamless switch to browser speech synthesis | Murf AI → Browser TTS → Text-only |
| **Network Problems** | "Having connection issues. Checking your internet connection might help." | Timeout handling + retry logic |
| **Complete Failure** | "All systems are temporarily down. Please try again later." | Graceful degradation + admin alerts |

### 📊 **Monitoring & Recovery**
- **Real-time API status** indicators in UI
- **Comprehensive error logging** for debugging
- **Health check endpoints** for monitoring
- **Automatic service restoration** testing
- **Admin simulation tools** for failure testing

---

## 🎨 UI Design Philosophy

### 🖤 **Brutalist Bento Aesthetic**
- **High Contrast**: Black background with orange accents for maximum readability
- **Geometric Layout**: Clean grid system with sharp, defined boundaries  
- **Monospace Typography**: Technical, authentic feel that matches the AI theme
- **Functional First**: Every element serves a purpose, no decorative bloat

### 🎯 **Interaction Design**
- **Single Action Button**: Record/Stop/Processing states all in one interface
- **Visual State Feedback**: Colors and animations indicate system status
- **Responsive Behavior**: Adapts seamlessly to different screen sizes
- **Accessibility**: High contrast, keyboard navigation, screen reader support

---

## 🧪 Testing & Quality Assurance

### 🔍 **Error Resilience Testing**
```bash
# Test STT failure simulation
curl -X POST "http://localhost:8001/admin/simulate-error/stt?action=disable"

# Test LLM failure simulation  
curl -X POST "http://localhost:8001/admin/simulate-error/llm?action=disable"

# Test TTS failure simulation
curl -X POST "http://localhost:8001/admin/simulate-error/tts?action=disable"

# Restore all services
curl -X POST "http://localhost:8001/admin/simulate-error/all?action=enable"
```

### ✅ **Quality Checklist**
- [x] **Cross-browser compatibility** (Chrome, Firefox, Safari, Edge)
- [x] **Mobile responsiveness** (iOS Safari, Chrome Mobile)
- [x] **Microphone permissions** handling
- [x] **Network timeout** protection
- [x] **API rate limiting** respect
- [x] **Memory leak** prevention
- [x] **Security best practices** (API key protection)

---

## 🚀 Deployment

### 🐳 **Docker Deployment** (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 🌐 **Production Considerations**
- **Environment Variables**: Never commit API keys to version control
- **HTTPS**: Use SSL certificates for production deployment
- **Rate Limiting**: Implement API rate limiting for cost control
- **Monitoring**: Set up logging and health check endpoints
- **Scaling**: Consider async processing for high-traffic scenarios

---

## 📈 Development Journey

### 🗓️ **30 Days Progress**
- **Days 1-3**: Basic TTS implementation with Murf AI
- **Days 4-5**: Voice recording and echo bot functionality
- **Days 6-10**: Full conversational AI with memory and context
- **Day 11**: Comprehensive error handling and resilience testing
- **Day 12**: Complete UI/UX overhaul with brutalist bento design

### 🎯 **Key Learnings**
- **User Experience**: Simple interfaces hide complex functionality
- **Error Handling**: Graceful degradation is essential for production apps
- **API Integration**: Multiple fallbacks prevent single points of failure
- **Design Philosophy**: Brutalism + functionality creates memorable experiences

---

## 🤝 Contributing

### 🛠️ **Development Setup**
```bash
# Clone and setup
git clone <repo-url>
cd voice-agent
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Add your API keys to .env

# Run in development mode
python main.py
```

### 📝 **Code Style**
- **Python**: Follow PEP 8 standards
- **JavaScript**: Use modern ES6+ features
- **CSS**: BEM methodology for class naming
- **Comments**: Explain complex logic and API integrations

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Murf AI](https://murf.ai/)** for providing excellent TTS capabilities
- **[AssemblyAI](https://www.assemblyai.com/)** for reliable speech recognition
- **[Google](https://ai.google.com/)** for powerful Gemini AI models
- **#30DaysofVoiceAgents** community for inspiration and feedback

---

## 📞 Contact & Support

- **GitHub Issues**: [Create an issue](../../issues) for bugs or feature requests
- **LinkedIn**: [Your LinkedIn Profile] for project updates
- **Twitter**: [@YourTwitter] for quick questions

---

**Built with ❤️ during the #30DaysofVoiceAgents challenge**

*"Sometimes the best UI is the one that gets out of the way and lets the technology shine."* ✨
