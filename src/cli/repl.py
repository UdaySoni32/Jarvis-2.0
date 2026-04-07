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
            try:
                # Try to use semantic memory if available
                from ..core.memory.semantic import semantic_memory
                semantic_memory.start_session(title="CLI Session")
                self.memory_manager = semantic_memory
                logger.info(f"Started semantic memory session")
            except:
                # Fall back to regular memory
                from ..core.memory import memory_manager
                memory_manager.start_session(title="CLI Session")
                self.memory_manager = memory_manager
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
- `tools` - List available tools
- `memory` - Show current session info
- `sessions` - List recent sessions
- `exit` / `quit` - Exit JARVIS

**Semantic Search (Phase 2.1):**
- `search <query>` - Search similar conversations
- `knowledge` - List all stored knowledge
- `knowledge search <query>` - Search knowledge base

**Agent System (Phase 2.3 - NEW):**
- `agents` - List all available agents
- `agent <task>` - Delegate task to appropriate agent

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
        
        elif command.startswith("search "):
            # Semantic search command
            query = user_input[7:].strip()  # Remove "search "
            if not query:
                self.console.print("[yellow]Usage: search <query>[/yellow]")
                return True
            
            try:
                from ..core.memory.semantic import semantic_memory
                
                if not semantic_memory.semantic_enabled:
                    self.console.print("[yellow]⚠️  Semantic search not available[/yellow]")
                    return True
                
                results = semantic_memory.search_similar(query, n_results=5)
                
                if not results:
                    self.console.print(f"\n[yellow]No results found for: {query}[/yellow]\n")
                else:
                    lines = [f"## 🔍 Search Results for: {query}", ""]
                    for i, result in enumerate(results, 1):
                        role = result['metadata']['role']
                        content = result['content']
                        # Truncate long messages
                        if len(content) > 100:
                            content = content[:97] + "..."
                        
                        lines.append(f"**{i}.** [{role}] {content}")
                    
                    self.console.print(Panel(
                        Markdown("\n".join(lines)),
                        title=f"Found {len(results)} similar messages",
                        border_style="green"
                    ))
            except Exception as e:
                self.console.print(f"[red]Search error: {e}[/red]")
            
            return True
        
        elif command.startswith("knowledge"):
            # Knowledge base commands
            parts = command.split(maxsplit=1)
            
            if len(parts) == 1 or parts[1] == "list":
                # List all knowledge
                try:
                    from ..core.memory.semantic import semantic_memory
                    
                    if not semantic_memory.semantic_enabled:
                        self.console.print("[yellow]⚠️  Knowledge base not available[/yellow]")
                        return True
                    
                    # Search for all knowledge
                    knowledge = semantic_memory.search_knowledge("", n_results=20)
                    
                    if not knowledge:
                        self.console.print("\n[yellow]No knowledge stored yet[/yellow]\n")
                    else:
                        lines = ["## 🧠 Knowledge Base", ""]
                        for i, item in enumerate(knowledge, 1):
                            content = item['content']
                            category = item['metadata'].get('category', 'general')
                            importance = item['metadata'].get('importance', 0.5)
                            
                            if len(content) > 80:
                                content = content[:77] + "..."
                            
                            lines.append(f"**{i}.** [{category}] {content} (importance: {importance:.1f})")
                        
                        self.console.print(Panel(
                            Markdown("\n".join(lines)),
                            title=f"Knowledge ({len(knowledge)} items)",
                            border_style="purple"
                        ))
                except Exception as e:
                    self.console.print(f"[red]Knowledge error: {e}[/red]")
            
            elif parts[1].startswith("search "):
                # Search knowledge
                query = parts[1][7:].strip()
                if not query:
                    self.console.print("[yellow]Usage: knowledge search <query>[/yellow]")
                    return True
                
                try:
                    from ..core.memory.semantic import semantic_memory
                    
                    if not semantic_memory.semantic_enabled:
                        self.console.print("[yellow]⚠️  Knowledge base not available[/yellow]")
                        return True
                    
                    results = semantic_memory.search_knowledge(query, n_results=5)
                    
                    if not results:
                        self.console.print(f"\n[yellow]No knowledge found for: {query}[/yellow]\n")
                    else:
                        lines = [f"## 🔎 Knowledge Search: {query}", ""]
                        for i, item in enumerate(results, 1):
                            content = item['content']
                            category = item['metadata'].get('category', 'general')
                            
                            lines.append(f"**{i}.** [{category}] {content}")
                        
                        self.console.print(Panel(
                            Markdown("\n".join(lines)),
                            title=f"Found {len(results)} knowledge items",
                            border_style="purple"
                        ))
                except Exception as e:
                    self.console.print(f"[red]Knowledge search error: {e}[/red]")
            else:
                self.console.print("[yellow]Usage: knowledge [list|search <query>][/yellow]")
            
            return True
        
        elif command == "agents":
            # List available agents
            from ..core.agents import agent_coordinator
            
            agents = agent_coordinator.list_agents()
            if not agents:
                self.console.print("\n[yellow]No agents available[/yellow]\n")
            else:
                lines = ["## 🤖 Available Agents", ""]
                for agent_info in agents:
                    lines.append(f"**{agent_info['name']}**")
                    lines.append(f"  - {agent_info['description']}")
                    lines.append(f"  - Status: {agent_info['status']}")
                    lines.append(f"  - Capabilities:")
                    for cap in agent_info['capabilities'][:4]:
                        lines.append(f"    • {cap}")
                    if len(agent_info['capabilities']) > 4:
                        lines.append(f"    • ...and {len(agent_info['capabilities']) - 4} more")
                    lines.append("")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title=f"Agents ({len(agents)} available)",
                    border_style="green"
                ))
            return True
        
        elif command.startswith("agent "):
            # Execute agent command
            task = user_input[6:].strip()  # Remove "agent "
            if not task:
                self.console.print("[yellow]Usage: agent <task description>[/yellow]")
                return True
            
            import asyncio
            from ..core.agents import agent_coordinator
            
            self.console.print(f"\n🤖 [cyan]Delegating to agent:[/cyan] {task}\n")
            
            try:
                result = await agent_coordinator.delegate_task(task)
                
                if result.get("success"):
                    agent_name = result.get("agent", "Unknown")
                    self.console.print(f"✅ [green]Completed by {agent_name}[/green]\n")
                    
                    # Display result based on type
                    if "plan" in result:
                        plan = result["plan"]
                        lines = ["## 📋 Plan", ""]
                        for step in plan.get("steps", []):
                            lines.append(f"{step['number']}. {step['description']}")
                        self.console.print(Panel(Markdown("\n".join(lines)), border_style="blue"))
                    
                    elif "findings" in result:
                        findings = result["findings"]
                        lines = ["## 🔍 Research Findings", ""]
                        if "overview" in findings:
                            lines.append(findings["overview"])
                        self.console.print(Panel(Markdown("\n".join(lines)), border_style="purple"))
                    
                    elif "result" in result:
                        res = result["result"]
                        if "code" in res:
                            lines = ["## 💻 Generated Code", "", f"```{res.get('language', 'python')}", res["code"], "```"]
                            self.console.print(Panel(Markdown("\n".join(lines)), border_style="green"))
                        else:
                            self.console.print(Panel(str(res), border_style="cyan"))
                else:
                    error = result.get("error", "Unknown error")
                    self.console.print(f"[red]❌ Agent error: {error}[/red]")
            
            except Exception as e:
                self.console.print(f"[red]Agent execution error: {e}[/red]")
            
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
        from ..core.memory import memory_manager

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
