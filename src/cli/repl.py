"""Command-line interface for JARVIS 2.0."""

import sys
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..core.config import settings
from ..core.logger import logger

console = Console()


class REPL:
    """Read-Eval-Print Loop for JARVIS CLI."""

    def __init__(self):
        """Initialize REPL with prompt session and history."""
        self.console = console
        self.running = False

        # Set up prompt session with history
        history_file = settings.user_data_dir / ".jarvis_history"
        self.session = PromptSession(history=FileHistory(str(history_file)))

        # Custom style for prompt
        self.prompt_style = Style.from_dict(
            {
                "prompt": "#00ff00 bold",
            }
        )

        # Start memory session if enabled
        if settings.enable_memory:
            from ..core.memory import memory_manager
            memory_manager.start_session(title="CLI Session")
            logger.info(f"Started memory session")

        logger.info("REPL initialized")

    def print_welcome(self):
        """Print welcome message."""
        welcome_text = """
# 🤖 JARVIS 2.0 - AI Personal Assistant

Welcome! I'm JARVIS, your AI-powered personal assistant.

**Available Commands:**
- Type your question or request naturally
- `help` - Show available commands
- `clear` - Clear screen
- `exit` or `quit` - Exit JARVIS

**Tips:**
- Use natural language - no commands needed!
- I can help with code, tasks, information, and more
- Type `status` to see system status
        """
        self.console.print(Panel(Markdown(welcome_text), border_style="cyan"))

        # Show configuration status
        if settings.has_openai_key:
            self.console.print(
                "✅ [green]OpenAI API configured[/green] (using GPT-4)"
            )
        elif settings.default_llm == "ollama":
            self.console.print(
                "✅ [green]Using local LLM[/green] (Ollama - " + settings.ollama_model + ")"
            )
        else:
            self.console.print(
                "⚠️  [yellow]No LLM configured![/yellow] Set OPENAI_API_KEY or use Ollama"
            )

        self.console.print()

    def print_help(self):
        """Print help message."""
        help_text = """
## Available Commands

**Built-in Commands:**
- `help` - Show this help message
- `status` - Show system status
- `clear` - Clear screen
- `history` - Show command history
- `exit` / `quit` - Exit JARVIS

**Natural Language:**
Just type what you want naturally! Examples:
- "What's the weather in Tokyo?"
- "Create a Python script to parse JSON"
- "What's my CPU usage?"
- "Search the web for best Python frameworks"

**Settings:**
- Configuration: `~/.jarvis-2.0/.env`
- History: `{history_file}`
- Logs: `{log_file}`
        """.format(
            history_file=settings.user_data_dir / ".jarvis_history",
            log_file=settings.log_file,
        )
        self.console.print(Panel(Markdown(help_text), border_style="blue"))

    def print_status(self):
        """Print system status."""
        status_lines = [
            "## 🔧 System Status",
            "",
            f"**LLM Provider:** {settings.default_llm}",
        ]

        if settings.default_llm == "openai":
            status_lines.append(f"**Model:** {settings.openai_model}")
            status_lines.append(f"**API Key:** {'✅ Configured' if settings.has_openai_key else '❌ Missing'}")
        elif settings.default_llm == "ollama":
            status_lines.append(f"**Model:** {settings.ollama_model}")
            status_lines.append(f"**URL:** {settings.ollama_base_url}")

        status_lines.extend([
            "",
            f"**Memory:** {'✅ Enabled' if settings.enable_memory else '❌ Disabled'}",
            f"**Plugins:** {'✅ Enabled' if settings.enable_plugins else '❌ Disabled'}",
            f"**Voice:** {'✅ Enabled' if settings.enable_voice else '❌ Disabled'}",
            f"**Debug Mode:** {'✅ On' if settings.debug else '❌ Off'}",
            "",
            f"**Data Directory:** {settings.user_data_dir}",
            f"**Log Level:** {settings.log_level}",
        ])

        self.console.print(Panel(Markdown("\n".join(status_lines)), border_style="yellow"))

    def handle_builtin_command(self, user_input: str) -> bool:
        """
        Handle built-in commands.

        Args:
            user_input: User input string

        Returns:
            True if command was handled, False otherwise
        """
        command = user_input.lower().strip()

        if command in ["exit", "quit", "q"]:
            self.console.print("\n👋 [cyan]Goodbye![/cyan]\n")
            return True

        elif command == "help":
            self.print_help()
            return True

        elif command == "clear":
            self.console.clear()
            self.print_welcome()
            return True

        elif command == "status":
            self.print_status()
            return True

        elif command == "tools":
            from ..core.tools import tool_registry
            
            if len(tool_registry) == 0:
                self.console.print("\n[yellow]⚠️  No tools registered yet.[/yellow]\n")
            else:
                tools_list = ["## 🔧 Available Tools", ""]
                for tool_name in tool_registry.list_tools():
                    tool = tool_registry.get(tool_name)
                    tools_list.append(f"**{tool_name}** - {tool.description}")
                
                self.console.print(Panel(
                    Markdown("\n".join(tools_list)),
                    title=f"Tools ({len(tool_registry)} registered)",
                    border_style="cyan"
                ))
            return True

        elif command == "memory":
            from ..core.memory import memory_manager
            
            summary = memory_manager.get_session_summary()
            if summary["active"]:
                info = [
                    "## 🧠 Memory Status",
                    "",
                    f"**Session ID:** {summary['session_id'][:16]}...",
                    f"**Title:** {summary['title']}",
                    f"**Messages:** {summary['message_count']}",
                    f"**Started:** {summary['created_at'].split('T')[0]}",
                ]
                self.console.print(Panel(
                    Markdown("\n".join(info)),
                    title="Conversation Memory",
                    border_style="magenta"
                ))
            else:
                self.console.print("\n[yellow]No active session[/yellow]\n")
            return True

        elif command.startswith("sessions"):
            from ..core.memory import memory_manager
            
            sessions = memory_manager.list_sessions(limit=10)
            if not sessions:
                self.console.print("\n[yellow]No saved sessions[/yellow]\n")
            else:
                lines = ["## 💾 Recent Sessions", ""]
                for i, sess in enumerate(sessions, 1):
                    lines.append(f"{i}. **{sess.title}** - {sess.session_id[:8]}... ({sess.created_at.strftime('%Y-%m-%d')})")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title=f"Sessions ({len(sessions)})",
                    border_style="blue"
                ))
            return True

        elif command == "history":
            # TODO: Implement history viewing
            self.console.print("[yellow]Command history feature coming soon![/yellow]")
            return True

        return False

    async def process_input(self, user_input: str):
        """
        Process user input and generate response.

        Args:
            user_input: User's input text
        """
        # Check for built-in commands
        if self.handle_builtin_command(user_input):
            if user_input.lower().strip() in ["exit", "quit", "q"]:
                self.running = False
            return

        # Import LLM manager and tools
        from ..core.llm import llm_manager, Message
        from ..core.tools import tool_registry, tool_executor
        from ..core.config import settings

        try:
            # Show processing indicator
            self.console.print("\n[cyan]🤖 Thinking...[/cyan]", end="")

            # Add user message to memory
            if settings.enable_memory:
                memory_manager.add_message("user", user_input)

            # Get context messages from memory
            if settings.enable_memory:
                context_messages = memory_manager.get_context_messages()
                messages = [
                    Message("system", "You are JARVIS, a helpful AI assistant. Be concise but friendly. You have access to tools to help users.")
                ] + [Message(msg["role"], msg["content"]) for msg in context_messages]
            else:
                # No memory, just current message
                messages = [
                    Message("system", "You are JARVIS, a helpful AI assistant. Be concise but friendly. You have access to tools to help users."),
                    Message("user", user_input),
                ]

            # Get LLM provider
            provider = await llm_manager.get_provider()

            # Check if tools are enabled and available
            tools_available = settings.enable_plugins and len(tool_registry) > 0

            if tools_available:
                # Get function schemas
                functions = tool_registry.get_openai_functions()

                # Generate with function calling
                self.console.print("\r" + " " * 50 + "\r", end="")  # Clear "Thinking..."

                response = await provider.generate_with_functions(
                    messages,
                    functions,
                    temperature=0.7,
                )

                # Check if LLM wants to call a tool
                if response.get("tool_calls"):
                    for tool_call in response["tool_calls"]:
                        tool_name = tool_call["name"]
                        self.console.print(f"[dim]🔧 Using tool: {tool_name}...[/dim]")

                        # Execute tool
                        tool_result = await tool_executor.execute_from_llm(tool_call)

                        # Add tool interaction to memory
                        if settings.enable_memory:
                            memory_manager.add_message("assistant", f"[Using tool: {tool_name}]")
                            memory_manager.add_message("function", tool_executor.format_result_for_llm(tool_result))

                        # Add tool result to messages
                        messages.append(Message("assistant", f"[Calling {tool_name}]"))
                        messages.append(
                            Message("function", tool_executor.format_result_for_llm(tool_result))
                        )

                    # Get final response with tool results
                    self.console.print("[bold cyan]JARVIS:[/bold cyan] ", end="")
                    response_text = []
                    async for chunk in llm_manager.stream_chat(messages, temperature=0.7):
                        self.console.print(chunk, end="", flush=True)
                        response_text.append(chunk)
                    self.console.print("\n")
                    
                    # Save assistant response to memory
                    if settings.enable_memory:
                        memory_manager.add_message("assistant", "".join(response_text))

                elif response.get("content"):
                    # Direct response without tools
                    self.console.print("[bold cyan]JARVIS:[/bold cyan] " + response["content"] + "\n")
                    
                    # Save to memory
                    if settings.enable_memory:
                        memory_manager.add_message("assistant", response["content"])

            else:
                # No tools, just regular chat
                self.console.print("\r" + " " * 50 + "\r", end="")  # Clear "Thinking..."
                self.console.print("[bold cyan]JARVIS:[/bold cyan] ", end="")

                response_text = []
                async for chunk in llm_manager.stream_chat(messages, temperature=0.7):
                    self.console.print(chunk, end="", flush=True)
                    response_text.append(chunk)

                self.console.print("\n")
                
                # Save assistant response to memory
                if settings.enable_memory:
                    memory_manager.add_message("assistant", "".join(response_text))

        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            self.console.print(f"\n[red]❌ Error:[/red] {e}\n")
            self.console.print(
                "[dim]Tip: Check your API key or try 'status' to see configuration[/dim]\n"
            )

    async def run(self):
        """Run the REPL loop."""
        self.running = True
        self.print_welcome()

        while self.running:
            try:
                # Get user input
                user_input = await self.session.prompt_async(
                    "❯ ",
                    style=self.prompt_style,
                )

                # Skip empty input
                if not user_input.strip():
                    continue

                # Process input
                await self.process_input(user_input)

            except KeyboardInterrupt:
                # Ctrl+C pressed
                continue

            except EOFError:
                # Ctrl+D pressed
                self.console.print("\n👋 [cyan]Goodbye![/cyan]\n")
                break

            except Exception as e:
                logger.error(f"Error in REPL: {e}", exc_info=True)
                self.console.print(f"\n[red]❌ Error:[/red] {e}\n")


async def main():
    """Main entry point for CLI."""
    try:
        repl = REPL()
        await repl.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        console.print(f"[red]❌ Fatal error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
