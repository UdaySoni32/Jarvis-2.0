# 🎙️ JARVIS 2.0 Voice Interface Guide

Complete guide to using voice interaction with JARVIS.

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Supported Providers](#supported-providers)
- [Troubleshooting](#troubleshooting)
- [Advanced](#advanced)

---

## 🚀 Quick Start

### 1. Install Voice Dependencies

```bash
# Basic voice support (offline)
pip install openai-whisper pyttsx3 sounddevice soundfile

# Optional: Premium features
pip install elevenlabs pvporcupine webrtcvad gTTS pygame SpeechRecognition
```

### 2. Configure Voice Settings

Add to your `.env` file:

```bash
# Speech-to-Text
VOICE_STT_PROVIDER=whisper        # or 'google'
WHISPER_MODEL=base                # tiny, base, small, medium, large
USE_WHISPER_API=false             # Use OpenAI API instead of local

# Text-to-Speech  
VOICE_TTS_PROVIDER=pyttsx3        # or 'elevenlabs', 'gtts'
TTS_RATE=200                      # Speech rate (words per minute)
TTS_VOLUME=0.9                    # Volume (0.0 to 1.0)

# Wake Word (optional)
ENABLE_WAKE_WORD=false
PORCUPINE_ACCESS_KEY=your_key_here  # Get free at console.picovoice.ai
```

### 3. Start Using Voice

```bash
python main.py

❯ /voice                          # Start voice mode
# Or press F9 to toggle voice mode
```

---

## ✨ Features

### Core Capabilities

- **🎤 Speech Recognition**
  - OpenAI Whisper (local or API)
  - Google Speech Recognition (free)
  - Custom STT providers
  - Multi-language support

- **🔊 Text-to-Speech**
  - pyttsx3 (offline, instant)
  - ElevenLabs (premium, natural voices)
  - gTTS (free, Google voices)
  - Custom TTS providers

- **👂 Wake Word Detection**
  - "Hey JARVIS" activation
  - Custom wake words
  - Low latency (<500ms)

- **🎯 Smart Features**
  - Voice Activity Detection (VAD)
  - Automatic silence detection
  - Noise reduction
  - Audio normalization

### Voice Modes

1. **Conversation Mode**: Continuous voice chat
2. **Wake Word Mode**: Hands-free activation
3. **Push-to-Talk Mode**: Manual activation

---

## 📦 Installation

### Option 1: Full Installation (Recommended)

```bash
# Install all voice features
pip install -r requirements.txt
```

### Option 2: Minimal Installation

```bash
# Only essential components
pip install openai-whisper pyttsx3 sounddevice soundfile numpy
```

### Option 3: Cloud-Only (No local models)

```bash
# Use only cloud APIs (lighter install)
pip install openai SpeechRecognition elevenlabs sounddevice soundfile
```

### System Requirements

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
sudo apt-get install espeak espeak-ng  # For pyttsx3
```

**macOS:**
```bash
brew install portaudio
# pyttsx3 uses built-in speech synthesis
```

**Windows:**
```bash
# Install Visual C++ Build Tools
# pyttsx3 uses SAPI5 (built-in)
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# === Speech-to-Text Configuration ===

# Provider: 'whisper' or 'google'
VOICE_STT_PROVIDER=whisper

# Whisper Settings
WHISPER_MODEL=base          # Model size affects speed/accuracy
USE_WHISPER_API=false       # true = OpenAI API, false = local
OPENAI_API_KEY=sk-...      # Required if USE_WHISPER_API=true

# Google STT Settings  
GOOGLE_STT_LANGUAGE=en-US   # Language code
GOOGLE_STT_USE_CLOUD=false  # true = Cloud API, false = free API
GOOGLE_CREDENTIALS_FILE=credentials.json  # If USE_CLOUD=true

# === Text-to-Speech Configuration ===

# Provider: 'pyttsx3', 'elevenlabs', or 'gtts'
VOICE_TTS_PROVIDER=pyttsx3

# pyttsx3 Settings (Offline)
TTS_RATE=200               # Words per minute (150-250 normal)
TTS_VOLUME=0.9             # 0.0 to 1.0
TTS_VOICE_ID=            # Specific voice (optional)

# ElevenLabs Settings (Premium)
ELEVENLABS_API_KEY=your_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Voice ID
ELEVENLABS_MODEL=eleven_monolingual_v1

# gTTS Settings (Free)
GTTS_LANGUAGE=en           # Language code
GTTS_SLOW=false           # Slow speech

# === Wake Word Detection ===

ENABLE_WAKE_WORD=false
PORCUPINE_ACCESS_KEY=your_key  # Get free at console.picovoice.ai

# === Audio Settings ===

AUDIO_SAMPLE_RATE=16000    # Hz (16000 recommended for speech)
AUDIO_CHANNELS=1           # 1=mono, 2=stereo
AUDIO_DEVICE_INDEX=       # Leave empty for default
```

### Programmatic Configuration

```python
from src.voice import create_voice_assistant

# Create with custom settings
assistant = create_voice_assistant(
    stt_provider='whisper',
    tts_provider='pyttsx3',
    enable_wake_word=True,
    wake_word_access_key='your_key',
    stt_args={
        'model_size': 'base',
        'device': 'cpu',
        'language': 'en'
    },
    tts_args={
        'rate': 200,
        'volume': 0.9
    }
)

# Use it
assistant.speak("Hello, I'm JARVIS!")
text = assistant.listen(duration=5.0)
print(f"You said: {text}")
```

---

## 🎯 Usage

### In CLI (REPL)

```bash
# Start JARVIS
python main.py

# Activate voice mode
❯ /voice

🎙️  Voice mode active! Start speaking...

🎤 Listening...
You: "What's the weather today?"

🤖 JARVIS: "I'll check the weather for you..."

# Exit voice mode
Say: "exit" or "quit" or press Ctrl+C
```

### Wake Word Mode

```bash
❯ /wake_word

👂 Wake word mode active!
Say 'Hey JARVIS' to activate...

# When you say "Hey JARVIS":
🎙️  Wake word detected!
JARVIS: "Yes? How can I help?"

🎤 Listening...
```

### Python API

```python
from src.voice import VoiceAssistant, AudioManager, create_stt_engine, create_tts_engine

# Initialize components
audio_manager = AudioManager()
stt_engine = create_stt_engine('whisper', model_size='base')
tts_engine = create_tts_engine('pyttsx3', rate=200)

# Create assistant
assistant = VoiceAssistant(
    stt_engine=stt_engine,
    tts_engine=tts_engine,
    audio_manager=audio_manager
)

# Speak
assistant.speak("Hello! I'm listening.")

# Listen
text = assistant.listen(duration=5.0, use_vad=True)
print(f"Heard: {text}")

# Cleanup
assistant.cleanup()
```

### Context Manager Pattern

```python
from src.voice import AudioManager

# Automatic cleanup
with AudioManager() as audio:
    # Record 3 seconds
    recorded = audio.record_audio(duration=3.0)
    
    # Play it back
    audio.play_audio(recorded)
    
    # Save to file
    audio.save_audio(recorded, "recording.wav")

# Resources automatically cleaned up
```

---

## 🔌 Supported Providers

### Speech-to-Text (STT)

| Provider | Type | Accuracy | Latency | Cost | Languages |
|----------|------|----------|---------|------|-----------|
| **Whisper (local)** | Offline | ⭐⭐⭐⭐⭐ | Medium | Free | 99+ |
| **Whisper (API)** | Cloud | ⭐⭐⭐⭐⭐ | Low | $0.006/min | 99+ |
| **Google (free)** | Cloud | ⭐⭐⭐⭐ | Low | Free* | 125+ |
| **Google Cloud** | Cloud | ⭐⭐⭐⭐⭐ | Low | $0.006/15s | 125+ |

*Free tier has limits

#### Whisper Model Sizes

| Model | Size | RAM | Speed | Accuracy |
|-------|------|-----|-------|----------|
| tiny | 39M | ~1GB | Fast | Good |
| base | 74M | ~1GB | Fast | Good |
| small | 244M | ~2GB | Medium | Better |
| medium | 769M | ~5GB | Slow | Great |
| large | 1550M | ~10GB | Very Slow | Best |

### Text-to-Speech (TTS)

| Provider | Type | Quality | Latency | Cost | Voices |
|----------|------|---------|---------|------|--------|
| **pyttsx3** | Offline | ⭐⭐⭐ | Instant | Free | System |
| **ElevenLabs** | Cloud | ⭐⭐⭐⭐⭐ | Low | Paid | 100+ |
| **gTTS** | Cloud | ⭐⭐⭐⭐ | Medium | Free | 100+ |

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "No module named 'sounddevice'"

```bash
pip install sounddevice soundfile
```

On Linux, also install:
```bash
sudo apt-get install portaudio19-dev
```

#### 2. "No audio input device found"

```python
from src.voice import AudioManager

# List available devices
devices = AudioManager.list_devices()
for device in devices:
    print(f"{device['index']}: {device['name']}")

# Use specific device
audio = AudioManager(device=0)  # Use device index
```

#### 3. "Whisper model download fails"

```python
# Manual download
import whisper
model = whisper.load_model("base", download_root="/path/to/models")

# Or use API version
USE_WHISPER_API=true
OPENAI_API_KEY=your_key
```

#### 4. "Wake word detection not working"

- Get free API key: https://console.picovoice.ai/
- Check microphone permissions
- Reduce background noise
- Adjust sensitivity (default: 0.5)

```python
from src.voice import WakeWordDetector

detector = WakeWordDetector(
    access_key='your_key',
    sensitivities=[0.7]  # Higher = more sensitive
)
```

#### 5. "TTS voice sounds robotic"

**Solution 1: Use better provider**
```bash
VOICE_TTS_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your_key
```

**Solution 2: Adjust speech rate**
```bash
TTS_RATE=180  # Slower, more natural
```

**Solution 3: List and choose voices**
```python
from src.voice import create_tts_engine

tts = create_tts_engine('pyttsx3')
voices = tts.list_voices()
for voice in voices:
    print(f"{voice['id']}: {voice['name']}")
```

#### 6. "High latency / slow responses"

**For STT:**
- Use smaller Whisper model: `WHISPER_MODEL=tiny`
- Use Google STT: `VOICE_STT_PROVIDER=google`
- Use Whisper API: `USE_WHISPER_API=true`

**For TTS:**
- Use pyttsx3 (offline): `VOICE_TTS_PROVIDER=pyttsx3`
- Reduce speech rate: `TTS_RATE=200`

#### 7. "Poor transcription accuracy"

- Reduce background noise
- Speak clearly and at normal pace
- Use larger Whisper model: `WHISPER_MODEL=small` or `medium`
- Specify language: `language='en'` in config
- Check microphone quality

---

## 🚀 Advanced

### Custom STT Provider

```python
from src.voice.stt_engine import STTEngine
import numpy as np

class MyCustomSTT(STTEngine):
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        # Your custom transcription logic
        response = requests.post(
            self.api_url,
            json={'audio': audio_data.tolist(), 'rate': sample_rate},
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        return response.json()['text']
    
    def transcribe_file(self, audio_file: str) -> str:
        # Load and transcribe file
        import soundfile as sf
        audio_data, sample_rate = sf.read(audio_file)
        return self.transcribe(audio_data, sample_rate)

# Use it
my_stt = MyCustomSTT('https://my-stt-api.com', 'my_key')
text = my_stt.transcribe_file('audio.wav')
```

### Custom TTS Provider

```python
from src.voice.tts_engine import TTSEngine

class MyCustomTTS(TTSEngine):
    def __init__(self, api_url):
        self.api_url = api_url
    
    def speak(self, text: str, wait: bool = True):
        # Generate and play audio
        response = requests.post(
            self.api_url,
            json={'text': text}
        )
        audio_data = np.frombuffer(response.content, dtype=np.int16)
        
        import sounddevice as sd
        sd.play(audio_data, samplerate=22050)
        if wait:
            sd.wait()
    
    def save_speech(self, text: str, filename: str):
        response = requests.post(
            self.api_url,
            json={'text': text}
        )
        with open(filename, 'wb') as f:
            f.write(response.content)
```

### Audio Processing

```python
from src.voice import AudioManager
import numpy as np

manager = AudioManager()

# Record audio
audio = manager.record_audio(duration=5.0)

# Noise reduction
clean_audio = manager.apply_noise_reduction(audio)

# Normalize
normalized = manager.normalize_audio(clean_audio)

# Detect silence
is_silent = manager.detect_silence(normalized, threshold=0.01)

# Save processed audio
manager.save_audio(normalized, "processed.wav")
```

### Voice Activity Detection

```python
from src.voice.wake_word import VoiceActivityDetector
import soundfile as sf

# Load audio
audio_data, sample_rate = sf.read("recording.wav")

# Detect speech segments
vad = VoiceActivityDetector(sample_rate=sample_rate)
segments = vad.detect_speech_segments(audio_data)

# Extract speech only
for start, end in segments:
    speech_segment = audio_data[start:end]
    print(f"Speech from {start/sample_rate:.2f}s to {end/sample_rate:.2f}s")
```

### Continuous Listening

```python
import asyncio
from src.voice import VoiceAssistant

async def my_handler(user_input: str) -> str:
    """Handle user input and return response"""
    # Your AI logic here
    return f"You said: {user_input}"

async def run_continuous():
    assistant = create_voice_assistant(
        stt_provider='whisper',
        tts_provider='pyttsx3',
        conversation_handler=my_handler
    )
    
    # Run conversation loop
    await assistant.conversation_loop()

# Run it
asyncio.run(run_continuous())
```

---

## 📊 Performance Tips

### Optimize for Speed

```bash
# Use smallest Whisper model
WHISPER_MODEL=tiny

# Use offline TTS
VOICE_TTS_PROVIDER=pyttsx3

# Reduce audio quality (if acceptable)
AUDIO_SAMPLE_RATE=8000  # Lower = faster, but worse quality
```

### Optimize for Accuracy

```bash
# Use larger Whisper model
WHISPER_MODEL=medium

# Use premium TTS
VOICE_TTS_PROVIDER=elevenlabs

# Higher audio quality
AUDIO_SAMPLE_RATE=48000
```

### Optimize for Offline Use

```bash
# All offline providers
VOICE_STT_PROVIDER=whisper
USE_WHISPER_API=false
VOICE_TTS_PROVIDER=pyttsx3
ENABLE_WAKE_WORD=true  # Porcupine runs locally
```

---

## 🎯 Best Practices

1. **Microphone Quality**: Use a good quality microphone for best results
2. **Background Noise**: Minimize background noise when possible
3. **Speech Pace**: Speak clearly at a normal pace
4. **Model Selection**: Balance speed vs accuracy based on your use case
5. **Resource Management**: Always use context managers or call `cleanup()`
6. **Error Handling**: Wrap voice calls in try/except for production
7. **Testing**: Test with different accents and noise levels

---

## 📚 API Reference

### AudioManager

```python
AudioManager(
    sample_rate: int = 16000,
    channels: int = 1,
    dtype: str = "int16",
    block_size: int = 1024,
    device: Optional[int] = None
)

# Methods
.record_audio(duration: float) -> np.ndarray
.play_audio(audio_data: np.ndarray, wait: bool = True)
.save_audio(audio_data: np.ndarray, filename: str)
.load_audio(filename: str) -> np.ndarray
.apply_noise_reduction(audio_data: np.ndarray) -> np.ndarray
.normalize_audio(audio_data: np.ndarray) -> np.ndarray
.detect_silence(audio_data: np.ndarray, threshold: float) -> bool
```

### STTEngine

```python
create_stt_engine(
    provider: str = "whisper",
    **kwargs
) -> STTEngine

# Methods
.transcribe(audio_data: np.ndarray, sample_rate: int) -> str
.transcribe_file(audio_file: str) -> str
```

### TTSEngine

```python
create_tts_engine(
    provider: str = "pyttsx3",
    **kwargs
) -> TTSEngine

# Methods
.speak(text: str, wait: bool = True)
.save_speech(text: str, filename: str)
.list_voices() -> List[Dict[str, str]]  # If supported
```

### VoiceAssistant

```python
VoiceAssistant(
    stt_engine: Optional[STTEngine] = None,
    tts_engine: Optional[TTSEngine] = None,
    audio_manager: Optional[AudioManager] = None,
    wake_word_detector: Optional[WakeWordDetector] = None,
    conversation_handler: Optional[Callable] = None
)

# Methods
.speak(text: str, wait: bool = True)
.listen(duration: float = 5.0, use_vad: bool = True) -> str
.start_wake_word_mode(callback: Optional[Callable] = None)
.stop_wake_word_mode()
.cleanup()
```

---

## 🔗 Resources

- **Whisper**: https://github.com/openai/whisper
- **pyttsx3**: https://github.com/nateshmbhat/pyttsx3
- **ElevenLabs**: https://elevenlabs.io/
- **Porcupine**: https://picovoice.ai/platform/porcupine/
- **Google Speech**: https://cloud.google.com/speech-to-text

---

## 📝 License

Part of JARVIS 2.0 project. See main repository for license information.

---

**Version**: 1.0.0  
**Last Updated**: April 7, 2026  
**Status**: Production Ready 🎙️
