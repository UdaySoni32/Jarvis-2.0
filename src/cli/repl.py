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
        
        # Initialize automation engine
        try:
            from ..core.automation import automation_engine
            import asyncio
            # Start in background
            asyncio.create_task(automation_engine.start())
            logger.info("Automation engine starting...")
        except Exception as e:
            logger.warning(f"Could not start automation engine: {e}")

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

**Agent System (Phase 2.3):**
- `agents` - List all available agents
- `agent <task>` - Delegate task to appropriate agent

**Automation System (Phase 2.4 - NEW):**
- `automations` - List all automation rules
- `automation template <name>` - Add rule from template
- `automation remove <rule>` - Remove automation rule
- `automation pause <rule>` - Pause automation rule
- `automation resume <rule>` - Resume automation rule
- `automation run <rule>` - Run automation rule manually
- `automation history` - Show recent automation runs

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

        return False
    
    async def handle_async_commands(self, user_input: str) -> bool:
        """
        Handle async commands (agents and automation).
        
        Args:
            user_input: User input string
            
        Returns:
            True if command was handled, False otherwise
        """
        command = user_input.lower().strip()
        
        # Agent commands
        if command.startswith("agent "):
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
        
        # Automation commands
        return await self.handle_automation_commands(user_input)
    
    async def handle_automation_commands(self, user_input: str) -> bool:
        """
        Handle automation commands.
        
        Args:
            user_input: User input string
            
        Returns:
            True if command was handled, False otherwise
        """
        command = user_input.lower().strip()
        
        if command == "automations" or command == "automation list":
            # List automation rules
            from ..core.automation import automation_engine
            
            rules = automation_engine.list_rules()
            if not rules:
                self.console.print("\n[yellow]No automation rules configured[/yellow]\n")
            else:
                lines = ["## ⚡ Automation Rules", ""]
                for rule in rules:
                    status_color = "green" if rule.status.value == "active" else "yellow"
                    lines.append(f"**{rule.name}** [{status_color}]{rule.status.value}[/{status_color}]")
                    lines.append(f"  - {rule.description or 'No description'}")
                    lines.append(f"  - Trigger: {rule.trigger.trigger_type.value}")
                    if rule.trigger.schedule:
                        schedule = rule.trigger.schedule
                        if schedule.type.value == "daily" and schedule.time:
                            lines.append(f"  - Schedule: Daily at {schedule.time}")
                        elif schedule.type.value == "interval":
                            interval = schedule.interval_minutes or schedule.interval_hours or schedule.interval_seconds
                            unit = "minutes" if schedule.interval_minutes else ("hours" if schedule.interval_hours else "seconds")
                            lines.append(f"  - Schedule: Every {interval} {unit}")
                        elif schedule.type.value == "cron" and schedule.cron_expression:
                            lines.append(f"  - Schedule: {schedule.cron_expression}")
                    lines.append(f"  - Actions: {len(rule.actions)}")
                    lines.append(f"  - Runs: {rule.run_count}")
                    if rule.last_run:
                        lines.append(f"  - Last run: {rule.last_run.strftime('%Y-%m-%d %H:%M')}")
                    lines.append("")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title=f"Automation ({len(rules)} rules)",
                    border_style="cyan"
                ))
            return True
        
        elif command.startswith("automation "):
            # Automation management commands
            parts = command.split()
            if len(parts) < 2:
                self.console.print("[yellow]Usage: automation <add|remove|pause|resume|run> [args][/yellow]")
                return True
            
            subcommand = parts[1]
            
            if subcommand == "add":
                self.console.print("[yellow]Use automation templates or rule builder[/yellow]")
                self.console.print("Examples:")
                self.console.print("  automation template daily_backup")
                self.console.print("  automation template morning_briefing")
                return True
            
            elif subcommand == "template" and len(parts) >= 3:
                # Add rule from template
                template_name = parts[2]
                from ..core.automation import create_from_template, automation_engine
                
                try:
                    rule = create_from_template(template_name)
                    if rule:
                        success = await automation_engine.add_rule(rule)
                        if success:
                            self.console.print(f"✅ [green]Added automation rule: {rule.name}[/green]")
                        else:
                            self.console.print(f"[red]Failed to add rule[/red]")
                    else:
                        self.console.print(f"[red]Template not found: {template_name}[/red]")
                        self.console.print("Available templates: daily_backup, morning_briefing, high_cpu_alert, file_watcher")
                except Exception as e:
                    self.console.print(f"[red]Error adding template: {e}[/red]")
                return True
            
            elif subcommand == "remove" and len(parts) >= 3:
                rule_name = " ".join(parts[2:])
                from ..core.automation import automation_engine
                
                # Find rule by name
                rule = None
                for r in automation_engine.list_rules():
                    if r.name.lower() == rule_name.lower():
                        rule = r
                        break
                
                if rule:
                    success = await automation_engine.remove_rule(rule.id)
                    if success:
                        self.console.print(f"✅ [green]Removed rule: {rule.name}[/green]")
                    else:
                        self.console.print(f"[red]Failed to remove rule[/red]")
                else:
                    self.console.print(f"[red]Rule not found: {rule_name}[/red]")
                return True
            
            elif subcommand == "pause" and len(parts) >= 3:
                rule_name = " ".join(parts[2:])
                from ..core.automation import automation_engine
                
                rule = None
                for r in automation_engine.list_rules():
                    if r.name.lower() == rule_name.lower():
                        rule = r
                        break
                
                if rule:
                    success = await automation_engine.pause_rule(rule.id)
                    if success:
                        self.console.print(f"⏸️ [yellow]Paused rule: {rule.name}[/yellow]")
                    else:
                        self.console.print(f"[red]Failed to pause rule[/red]")
                else:
                    self.console.print(f"[red]Rule not found: {rule_name}[/red]")
                return True
            
            elif subcommand == "resume" and len(parts) >= 3:
                rule_name = " ".join(parts[2:])
                from ..core.automation import automation_engine
                
                rule = None
                for r in automation_engine.list_rules():
                    if r.name.lower() == rule_name.lower():
                        rule = r
                        break
                
                if rule:
                    success = await automation_engine.resume_rule(rule.id)
                    if success:
                        self.console.print(f"▶️ [green]Resumed rule: {rule.name}[/green]")
                    else:
                        self.console.print(f"[red]Failed to resume rule[/red]")
                else:
                    self.console.print(f"[red]Rule not found: {rule_name}[/red]")
                return True
            
            elif subcommand == "run" and len(parts) >= 3:
                rule_name = " ".join(parts[2:])
                from ..core.automation import automation_engine
                
                rule = None
                for r in automation_engine.list_rules():
                    if r.name.lower() == rule_name.lower():
                        rule = r
                        break
                
                if rule:
                    self.console.print(f"\n⚡ [cyan]Running automation rule: {rule.name}[/cyan]\n")
                    result = await automation_engine.execute_rule(rule.id)
                    if result["success"]:
                        run_info = result["run"]
                        self.console.print(f"✅ [green]Completed[/green] - {run_info['actions_executed']} actions succeeded")
                        if run_info['actions_failed'] > 0:
                            self.console.print(f"⚠️ [yellow]{run_info['actions_failed']} actions failed[/yellow]")
                    else:
                        self.console.print(f"[red]❌ Execution failed: {result.get('error')}[/red]")
                else:
                    self.console.print(f"[red]Rule not found: {rule_name}[/red]")
                return True
            
            else:
                self.console.print("[yellow]Usage: automation <add|remove|pause|resume|run|template> [args][/yellow]")
            
            return True
        
        elif command == "automation history":
            # Show recent automation runs
            from ..core.automation import automation_engine
            
            runs = automation_engine.get_recent_runs(limit=10)
            if not runs:
                self.console.print("\n[yellow]No automation runs yet[/yellow]\n")
            else:
                lines = ["## 📊 Recent Automation Runs", ""]
                for run in runs:
                    status_icon = "✅" if run.status == "success" else ("⚠️" if run.status == "partial" else "❌")
                    duration = ""
                    if run.completed_at:
                        delta = run.completed_at - run.started_at
                        duration = f" ({delta.total_seconds():.1f}s)"
                    
                    lines.append(f"{status_icon} **{run.rule_name}** - {run.started_at.strftime('%Y-%m-%d %H:%M')}{duration}")
                    lines.append(f"  Actions: {run.actions_executed} succeeded, {run.actions_failed} failed")
                    if run.error:
                        lines.append(f"  Error: {run.error}")
                    lines.append("")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title=f"History ({len(runs)} runs)",
                    border_style="blue"
                ))
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
        
        # Check for async commands (agents and automation)
        if await self.handle_async_commands(user_input):
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
        
        # Cleanup automation engine on exit
        try:
            from ..core.automation import automation_engine
            await automation_engine.stop()
            logger.info("Automation engine stopped")
        except Exception as e:
            logger.warning(f"Error stopping automation engine: {e}")


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
