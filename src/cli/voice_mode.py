"""
Voice Mode for JARVIS CLI

Enables voice interaction with JARVIS
"""

import logging
import asyncio
import inspect
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..voice import (
    AudioManager,
    create_stt_engine,
    create_tts_engine,
    VoiceAssistant,
    WakeWordDetector,
    AssistantMode,
    IntentRouter,
    MacroEngine,
    FollowupResolver,
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
        self.intent_router = IntentRouter()
        self.active_mode: Optional[AssistantMode] = None  # None => auto-routing
        self.macro_engine = MacroEngine()
        self.followup_resolver = FollowupResolver()
        self.last_user_input: Optional[str] = None
        self.last_response: Optional[str] = None

        self._handler_accepts_mode = False
        self._handler_accepts_original_input = False
        try:
            signature = inspect.signature(self.conversation_handler)
            parameters = signature.parameters
            accepts_kwargs = any(
                param.kind == inspect.Parameter.VAR_KEYWORD
                for param in parameters.values()
            )
            self._handler_accepts_mode = accepts_kwargs or "mode" in parameters
            self._handler_accepts_original_input = (
                accepts_kwargs or "original_input" in parameters
            )
        except Exception:
            # Keep backward-compatible default behavior if introspection fails.
            pass
    
    async def initialize(self):
        """Initialize voice components"""
        try:
            console.print("\n[yellow]🎙️  Initializing voice mode...[/yellow]")

            profile = getattr(settings, "voice_profile", "local").strip().lower()
            if profile not in {"local", "cloud"}:
                raise ValueError("VOICE_PROFILE must be 'local' or 'cloud'")

            devices = AudioManager.list_devices()
            if not devices:
                raise RuntimeError(
                    "No microphone devices found. Check mic connection and system audio permissions."
                )

            stt_provider = getattr(settings, "voice_stt_provider", "whisper")
            tts_provider = getattr(settings, "voice_tts_provider", "pyttsx3")

            if profile == "cloud":
                stt_provider = getattr(settings, "voice_cloud_stt_provider", stt_provider)
                tts_provider = getattr(settings, "voice_cloud_tts_provider", tts_provider)

            console.print(
                f"[dim]Voice profile: {profile} | STT: {stt_provider} | TTS: {tts_provider}[/dim]"
            )

            try:
                stt_engine = self._create_stt_engine(stt_provider, profile)
                tts_engine = self._create_tts_engine(tts_provider, profile)
            except Exception as primary_error:
                if profile == "cloud" and getattr(settings, "voice_fallback_to_local", True):
                    console.print(
                        f"[yellow]⚠️ Cloud voice init failed ({primary_error}). "
                        "Falling back to local voice stack.[/yellow]"
                    )
                    stt_engine = self._create_stt_engine("whisper", "local")
                    tts_engine = self._create_tts_engine("pyttsx3", "local")
                else:
                    raise

            audio_manager = AudioManager()

            wake_word_detector = self._create_wake_word_detector()
            
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

    def _create_stt_engine(self, provider: str, profile: str):
        provider = provider.strip().lower()
        console.print(f"[dim]Setting up {provider} for speech recognition...[/dim]")

        stt_args = {}
        if provider == "whisper":
            use_api = bool(getattr(settings, "use_whisper_api", False)) or profile == "cloud"
            stt_args = {
                "model_size": getattr(settings, "whisper_model", "base"),
                "device": "cpu",
                "use_api": use_api,
            }
            if use_api:
                if not settings.openai_api_key:
                    raise ValueError("OPENAI_API_KEY is required for cloud Whisper API mode")
                stt_args["api_key"] = settings.openai_api_key

        elif provider == "google":
            use_cloud = bool(getattr(settings, "google_stt_use_cloud", False)) or profile == "cloud"
            credentials_file = getattr(settings, "google_application_credentials", None)
            if use_cloud and not credentials_file:
                console.print(
                    "[yellow]⚠️ GOOGLE_APPLICATION_CREDENTIALS not set; "
                    "using Google free STT mode instead of Google Cloud STT.[/yellow]"
                )
                use_cloud = False
            stt_args = {
                "language": getattr(settings, "voice_language", "en-US"),
                "use_cloud": use_cloud,
                "credentials_file": credentials_file,
            }
        return create_stt_engine(provider, **stt_args)

    def _create_tts_engine(self, provider: str, profile: str):
        provider = provider.strip().lower()
        console.print(f"[dim]Setting up {provider} for text-to-speech...[/dim]")

        tts_args = {}
        if provider == "pyttsx3":
            tts_args = {
                "rate": getattr(settings, "tts_rate", 200),
                "volume": getattr(settings, "tts_volume", 0.9),
            }
        elif provider == "elevenlabs":
            api_key = getattr(settings, "elevenlabs_api_key", None)
            if not api_key:
                raise ValueError("ELEVENLABS_API_KEY is required for ElevenLabs TTS")
            tts_args = {
                "api_key": api_key,
                "voice_id": getattr(settings, "elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM"),
            }
        elif provider == "gtts":
            tts_args = {
                "language": getattr(settings, "voice_language", "en"),
                "slow": False,
            }

        return create_tts_engine(provider, **tts_args)

    def _create_wake_word_detector(self):
        if not getattr(settings, "enable_wake_word", False):
            return None

        porcupine_key = getattr(settings, "porcupine_access_key", None)
        if not porcupine_key:
            raise ValueError("PORCUPINE_ACCESS_KEY is required when ENABLE_WAKE_WORD=true")

        keyword_paths = None
        keyword_path = getattr(settings, "wake_word_keyword_path", None)
        if keyword_path:
            resolved = Path(keyword_path).expanduser().resolve()
            if not resolved.exists():
                raise FileNotFoundError(f"Wake-word keyword file not found: {resolved}")
            keyword_paths = [str(resolved)]

        console.print("[dim]Initializing wake word detection...[/dim]")
        return WakeWordDetector(
            access_key=porcupine_key,
            keyword_paths=keyword_paths,
            sensitivities=[float(getattr(settings, "wake_word_sensitivity", 0.5))],
        )
    
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
        help_text.append("\nMode routing:\n", style="bold cyan")
        help_text.append("• ", style="dim")
        help_text.append("mode coding|ops|productivity|research|general", style="bold yellow")
        help_text.append(" to lock a mode\n", style="dim")
        help_text.append("• ", style="dim")
        help_text.append("mode auto", style="bold yellow")
        help_text.append(" to return to automatic intent routing\n", style="dim")
        help_text.append("• ", style="dim")
        help_text.append("current mode", style="bold yellow")
        help_text.append(" to inspect active routing mode\n", style="dim")
        help_text.append("\nVoice macros:\n", style="bold cyan")
        help_text.append("• ", style="dim")
        help_text.append("macros", style="bold yellow")
        help_text.append(" to list available macros\n", style="dim")
        help_text.append("• ", style="dim")
        help_text.append("run macro <name>", style="bold yellow")
        help_text.append(" to execute a multi-step workflow\n", style="dim")
        help_text.append("\nNatural followups:\n", style="bold cyan")
        help_text.append("• ", style="dim")
        help_text.append("do the same for <target>", style="bold yellow")
        help_text.append(", ", style="dim")
        help_text.append("make it shorter", style="bold yellow")
        help_text.append(", ", style="dim")
        help_text.append("expand on that", style="bold yellow")
        help_text.append("\n", style="dim")
        
        console.print(Panel(help_text, border_style="cyan"))

    @staticmethod
    def _mode_from_text(mode_text: str) -> Optional[AssistantMode]:
        value = mode_text.strip().lower()
        mapping = {
            "general": AssistantMode.GENERAL,
            "coding": AssistantMode.CODING,
            "ops": AssistantMode.OPS,
            "productivity": AssistantMode.PRODUCTIVITY,
            "research": AssistantMode.RESEARCH,
        }
        return mapping.get(value)

    def _handle_mode_command(self, user_input: str) -> bool:
        """Handle voice mode switching commands."""
        normalized = user_input.strip().lower()

        if normalized in {"current mode", "what mode", "what mode are you", "mode"}:
            active = self.active_mode.value if self.active_mode else "auto"
            console.print(f"[dim]Current voice mode: [bold]{active}[/bold][/dim]")
            return True

        command_prefixes = ("mode ", "set mode ", "switch to ")
        requested: Optional[str] = None
        for prefix in command_prefixes:
            if normalized.startswith(prefix):
                requested = normalized[len(prefix):].strip()
                break

        if requested is None:
            return False

        if requested.endswith(" mode"):
            requested = requested[:-5].strip()

        if requested in {"auto", "automatic"}:
            self.active_mode = None
            console.print("[green]✅ Voice mode routing set to auto[/green]")
            return True

        selected = self._mode_from_text(requested)
        if selected is None:
            console.print(
                "[yellow]Unknown mode. Use: general, coding, ops, productivity, research, auto[/yellow]"
            )
            return True

        self.active_mode = selected
        console.print(f"[green]✅ Voice mode locked to {selected.value}[/green]")
        return True

    async def _invoke_conversation_handler(
        self,
        routed_input: str,
        original_input: str,
        mode: AssistantMode,
    ) -> str:
        """Invoke conversation handler while preserving backward compatibility."""
        kwargs = {}
        if self._handler_accepts_mode:
            kwargs["mode"] = mode.value
        if self._handler_accepts_original_input:
            kwargs["original_input"] = original_input

        if kwargs:
            return await self.conversation_handler(routed_input, **kwargs)
        return await self.conversation_handler(routed_input)

    async def _handle_macro_command(self, user_input: str) -> bool:
        """Handle macro listing and execution commands."""
        normalized = user_input.strip().lower()

        if normalized in {"macros", "list macros", "macro list"}:
            macro_lines = ["[bold cyan]Available Voice Macros[/bold cyan]\n"]
            for macro in self.macro_engine.list_macros():
                macro_lines.append(
                    f"• [bold]{macro.name}[/bold] "
                    f"({macro.mode.value}) - {macro.description}"
                )
            console.print(Panel("\n".join(macro_lines), border_style="cyan"))
            return True

        macro_name: Optional[str] = None
        if normalized.startswith("run macro "):
            macro_name = user_input.strip()[len("run macro "):].strip()
        elif normalized.startswith("macro "):
            macro_name = user_input.strip()[len("macro "):].strip()

        if not macro_name:
            return False

        macro = self.macro_engine.get_macro(macro_name)
        if not macro:
            console.print(
                f"[yellow]Unknown macro: {macro_name}[/yellow]\n"
                "[dim]Say 'macros' to list available workflows.[/dim]"
            )
            return True

        console.print(
            Panel(
                f"[bold]{macro.name}[/bold]\n{macro.description}",
                title="[cyan]Running macro[/cyan]",
                border_style="cyan",
            )
        )
        if self.assistant:
            self.assistant.speak(f"Running macro {macro.name.replace('-', ' ')}")

        for index, step in enumerate(macro.steps, start=1):
            console.print(f"[yellow]⚙️ Macro step {index}/{len(macro.steps)}[/yellow]: {step}")
            routed_input, _ = self.intent_router.route_input(
                step,
                explicit_mode=macro.mode,
            )
            response = await self._invoke_conversation_handler(
                routed_input=routed_input,
                original_input=step,
                mode=macro.mode,
            )
            if response:
                console.print(
                    Panel(
                        response,
                        title=f"[green]{macro.name} · Step {index}[/green]",
                        border_style="green",
                    )
                )

        if self.assistant:
            self.assistant.speak("Macro completed")
        console.print("[green]✅ Macro completed[/green]")
        return True
    
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

                # Handle mode routing commands
                if self._handle_mode_command(user_input):
                    continue

                # Handle workflow macros
                if await self._handle_macro_command(user_input):
                    continue

                # Resolve natural follow-up phrases into explicit requests
                followup = self.followup_resolver.resolve(
                    user_input=user_input,
                    last_user_input=self.last_user_input,
                    last_response=self.last_response,
                )
                if followup.is_followup:
                    console.print(
                        f"[dim]↪ Follow-up resolved ({followup.reason}): "
                        f"{followup.resolved_input}[/dim]"
                    )

                # Route request into a specialized assistant mode
                routed_input, route = self.intent_router.route_input(
                    followup.resolved_input,
                    explicit_mode=self.active_mode,
                )
                console.print(
                    f"[dim]🎯 Intent route: {route.mode.value} "
                    f"(source={route.source}, confidence={route.confidence:.2f})[/dim]"
                )
                
                # Get response from conversation handler
                console.print("[yellow]🤖 Thinking...[/yellow]")
                response = await self._invoke_conversation_handler(
                    routed_input=routed_input,
                    original_input=user_input,
                    mode=route.mode,
                )
                
                if response:
                    self.last_user_input = followup.resolved_input
                    self.last_response = response
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
        console.print(
            f"[dim]Say '{getattr(settings, 'wake_word_phrase', 'Jarvis')}' to activate...[/dim]\n"
        )
        
        async def on_wake_word():
            """Handle wake word detection"""
            console.print("\n[green]🎙️  Wake word detected![/green]")
            self.assistant.speak("Yes? How can I help?")
            
            # Listen for command
            user_input = self.assistant.listen(duration=5.0)
            
            if user_input:
                normalized = user_input.strip().lower()
                if normalized in {"sleep", "stop listening"}:
                    self.assistant.speak("Going to sleep mode.")
                    return

                console.print(Panel(
                    user_input,
                    title="[cyan]You said[/cyan]",
                    border_style="cyan"
                ))
                
                # Get and speak response
                routed_input, route = self.intent_router.route_input(
                    user_input,
                    explicit_mode=self.active_mode,
                )
                response = await self._invoke_conversation_handler(
                    routed_input=routed_input,
                    original_input=user_input,
                    mode=route.mode,
                )
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
