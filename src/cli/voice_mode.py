"""
Voice Mode for JARVIS CLI

Enables voice interaction with JARVIS
"""

import logging
import asyncio
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..voice import (
    AudioManager,
    create_stt_engine,
    create_tts_engine,
    VoiceAssistant,
    WakeWordDetector,
)
from ..core.config import settings

logger = logging.getLogger(__name__)
console = Console()


class VoiceMode:
    """Voice interaction mode for JARVIS"""
    
    def __init__(self, conversation_handler):
        """
        Initialize voice mode
        
        Args:
            conversation_handler: Function to handle user input and generate response
        """
        self.conversation_handler = conversation_handler
        self.assistant: Optional[VoiceAssistant] = None
        self.is_active = False
    
    async def initialize(self):
        """Initialize voice components"""
        try:
            console.print("\n[yellow]🎙️  Initializing voice mode...[/yellow]")
            
            # Create STT engine
            stt_provider = getattr(settings, 'voice_stt_provider', 'whisper')
            console.print(f"[dim]Setting up {stt_provider} for speech recognition...[/dim]")
            
            stt_args = {}
            if stt_provider == 'whisper':
                stt_args = {
                    'model_size': getattr(settings, 'whisper_model', 'base'),
                    'device': 'cpu',
                    'use_api': getattr(settings, 'use_whisper_api', False),
                }
                if stt_args['use_api']:
                    stt_args['api_key'] = settings.openai_api_key
            
            stt_engine = create_stt_engine(stt_provider, **stt_args)
            
            # Create TTS engine
            tts_provider = getattr(settings, 'voice_tts_provider', 'pyttsx3')
            console.print(f"[dim]Setting up {tts_provider} for text-to-speech...[/dim]")
            
            tts_args = {}
            if tts_provider == 'pyttsx3':
                tts_args = {
                    'rate': getattr(settings, 'tts_rate', 200),
                    'volume': getattr(settings, 'tts_volume', 0.9),
                }
            elif tts_provider == 'elevenlabs':
                tts_args = {
                    'api_key': getattr(settings, 'elevenlabs_api_key', ''),
                }
            
            tts_engine = create_tts_engine(tts_provider, **tts_args)
            
            # Create audio manager
            audio_manager = AudioManager()
            
            # Create wake word detector if enabled
            wake_word_detector = None
            if getattr(settings, 'enable_wake_word', False):
                porcupine_key = getattr(settings, 'porcupine_access_key', None)
                if porcupine_key:
                    console.print("[dim]Initializing wake word detection...[/dim]")
                    wake_word_detector = WakeWordDetector(access_key=porcupine_key)
            
            # Create voice assistant
            self.assistant = VoiceAssistant(
                stt_engine=stt_engine,
                tts_engine=tts_engine,
                audio_manager=audio_manager,
                wake_word_detector=wake_word_detector,
                conversation_handler=self.conversation_handler,
            )
            
            console.print("[green]✅ Voice mode initialized successfully![/green]\n")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize voice mode: {e}")
            console.print(f"[red]❌ Failed to initialize voice mode: {e}[/red]")
            console.print("[yellow]💡 Tip: Install voice dependencies with:[/yellow]")
            console.print("[dim]pip install openai-whisper pyttsx3 sounddevice soundfile[/dim]\n")
            return False
    
    def show_voice_help(self):
        """Show voice mode help"""
        help_text = Text()
        help_text.append("Voice Mode Commands\n\n", style="bold cyan")
        help_text.append("• Press ", style="dim")
        help_text.append("SPACE", style="bold yellow")
        help_text.append(" to start speaking\n", style="dim")
        help_text.append("• Say your question or command\n", style="dim")
        help_text.append("• JARVIS will respond with voice\n", style="dim")
        help_text.append("• Press ", style="dim")
        help_text.append("Ctrl+C", style="bold red")
        help_text.append(" to exit voice mode\n", style="dim")
        
        console.print(Panel(help_text, border_style="cyan"))
    
    async def run_conversation_mode(self):
        """Run continuous voice conversation"""
        if not self.assistant:
            await self.initialize()
        
        if not self.assistant:
            return
        
        self.is_active = True
        self.show_voice_help()
        
        console.print("\n[green]🎙️  Voice mode active! Start speaking...[/green]\n")
        
        try:
            while self.is_active:
                # Listen for user input
                console.print("[yellow]🎤 Listening...[/yellow]")
                user_input = self.assistant.listen(duration=5.0, use_vad=True)
                
                if not user_input or len(user_input.strip()) == 0:
                    console.print("[dim]No speech detected[/dim]")
                    continue
                
                # Display user input
                console.print(Panel(
                    user_input,
                    title="[cyan]You said[/cyan]",
                    border_style="cyan"
                ))
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'stop', 'goodbye']:
                    self.assistant.speak("Goodbye!")
                    break
                
                # Get response from conversation handler
                console.print("[yellow]🤖 Thinking...[/yellow]")
                response = await self.conversation_handler(user_input)
                
                if response:
                    # Display response
                    console.print(Panel(
                        response,
                        title="[green]JARVIS[/green]",
                        border_style="green"
                    ))
                    
                    # Speak response
                    self.assistant.speak(response)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Voice mode interrupted[/yellow]")
        
        except Exception as e:
            logger.error(f"Error in voice conversation: {e}")
            console.print(f"[red]❌ Error: {e}[/red]")
        
        finally:
            self.is_active = False
            console.print("\n[dim]Voice mode ended[/dim]\n")
    
    async def run_wake_word_mode(self):
        """Run wake word detection mode"""
        if not self.assistant:
            await self.initialize()
        
        if not self.assistant or not self.assistant.wake_word_detector:
            console.print("[red]❌ Wake word detection not available[/red]")
            return
        
        console.print("\n[green]👂 Wake word mode active![/green]")
        console.print("[dim]Say 'Hey JARVIS' to activate...[/dim]\n")
        
        async def on_wake_word():
            """Handle wake word detection"""
            console.print("\n[green]🎙️  Wake word detected![/green]")
            self.assistant.speak("Yes? How can I help?")
            
            # Listen for command
            user_input = self.assistant.listen(duration=5.0)
            
            if user_input:
                console.print(Panel(
                    user_input,
                    title="[cyan]You said[/cyan]",
                    border_style="cyan"
                ))
                
                # Get and speak response
                response = await self.conversation_handler(user_input)
                if response:
                    console.print(Panel(
                        response,
                        title="[green]JARVIS[/green]",
                        border_style="green"
                    ))
                    self.assistant.speak(response)
        
        try:
            self.assistant.start_wake_word_mode(callback=lambda idx: asyncio.run(on_wake_word()))
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(0.1)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Wake word mode interrupted[/yellow]")
        
        finally:
            self.assistant.stop_wake_word_mode()
            console.print("\n[dim]Wake word mode ended[/dim]\n")
    
    def cleanup(self):
        """Clean up voice mode resources"""
        self.is_active = False
        if self.assistant:
            self.assistant.cleanup()


# Quick test function
async def test_voice_mode():
    """Test voice mode functionality"""
    async def test_handler(user_input: str) -> str:
        """Test conversation handler"""
        return f"You said: {user_input}"
    
    voice_mode = VoiceMode(test_handler)
    
    if await voice_mode.initialize():
        # Test speak
        voice_mode.assistant.speak("Voice mode test successful!")
        
        # Test listen
        console.print("\n[yellow]Say something...[/yellow]")
        text = voice_mode.assistant.listen(duration=3.0)
        console.print(f"[green]Heard: {text}[/green]")
    
    voice_mode.cleanup()


if __name__ == "__main__":
    asyncio.run(test_voice_mode())
