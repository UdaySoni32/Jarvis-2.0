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
        else:
            # Memory disabled, set to None
            self.memory_manager = None

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
        
        # Initialize learning system
        try:
            from ..core.learning.storage import LearningStorage
            from ..core.learning.tracker import PreferenceTracker
            from ..core.learning.analytics import AnalyticsEngine
            from ..core.learning.detector import BehaviorDetector
            from ..core.learning.engine import PersonalizationEngine
            from ..core.learning.adapter import AdaptiveResponseGenerator
            
            # Initialize storage backend
            storage_path = settings.user_data_dir / "learning.db"
            self.learning_storage = LearningStorage("sqlite", db_path=str(storage_path))
            asyncio.create_task(self.learning_storage.initialize())
            
            # Initialize learning components with storage
            self.preference_tracker = PreferenceTracker(self.learning_storage)
            self.analytics_engine = AnalyticsEngine(self.learning_storage)
            self.behavior_detector = BehaviorDetector(self.learning_storage)
            self.personalization_engine = PersonalizationEngine(self.learning_storage)
            self.adaptive_response_generator = AdaptiveResponseGenerator(self.personalization_engine)
            
            # Start session tracking
            self.current_session = None
            self.user_id = "default_user"  # In production, would be from auth
            
            logger.info("Learning system initialized")
        except Exception as e:
            logger.warning(f"Could not initialize learning system: {e}")
            self.learning_storage = None
            self.preference_tracker = None
            self.analytics_engine = None
            self.behavior_detector = None
            self.personalization_engine = None
            self.adaptive_response_generator = None

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
                "⚠️  [yellow]No LLM configured![/yellow] Set OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, or use Ollama"
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

**Automation System (Phase 2.4):**
- `automations` - List all automation rules
- `automation template <name>` - Add rule from template
- `automation remove <rule>` - Remove automation rule
- `automation pause <rule>` - Pause automation rule
- `automation resume <rule>` - Resume automation rule
- `automation run <rule>` - Run automation rule manually
- `automation history` - Show recent automation runs

**Learning System (Phase 2.5 - NEW):**
- `preferences` - Show user preferences and settings
- `set preference <category>.<key> <value>` - Update preference
- `analytics` - Show usage analytics and metrics
- `insights` - Show command usage insights
- `patterns` - Show detected behavior patterns
- `suggestions` - Show personalized suggestions
- `learning status` - Show learning system status
- `learning enable/disable/reset` - Control learning system

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
        if await self.handle_automation_commands(user_input):
            return True
        
        # Learning system commands
        if await self.handle_learning_commands(user_input):
            return True
        
        return False
    
    async def handle_learning_commands(self, user_input: str) -> bool:
        """
        Handle learning system commands.
        
        Args:
            user_input: User input string
            
        Returns:
            True if command was handled, False otherwise
        """
        command = user_input.lower().strip()
        
        if not self.learning_storage:
            if any(cmd in command for cmd in ["preferences", "learning", "analytics", "patterns"]):
                self.console.print("[yellow]Learning system not available[/yellow]")
                return True
            return False
        
        # Preferences commands
        if command == "preferences" or command == "prefs":
            # Show user preferences
            try:
                profile = await self.personalization_engine.get_user_profile(self.user_id)
                prefs_summary = self.preference_tracker.get_preference_summary(self.user_id)
                
                lines = ["## 👤 User Preferences", ""]
                
                # Response style
                lines.append("### Response Style")
                style = prefs_summary["response_style"]
                lines.append(f"• **Tone**: {style['tone']}")
                lines.append(f"• **Verbosity**: {style['verbosity']}")
                lines.append(f"• **Technical Level**: {style['technical_level']}/5")
                lines.append(f"• **Include Explanations**: {style['include_explanations']}")
                lines.append(f"• **Use Emojis**: {style['use_emojis']}")
                lines.append("")
                
                # Tool preferences
                lines.append("### Tool Preferences")
                tools = prefs_summary["tool_preferences"]
                lines.append(f"• **Preferred LLM**: {tools['preferred_llm_model']}")
                lines.append(f"• **Automation Enabled**: {tools['automation_enabled']}")
                lines.append(f"• **Suggestion Frequency**: {tools['suggestion_frequency']}/5")
                lines.append("")
                
                # Time preferences
                lines.append("### Time Preferences")
                time_prefs = prefs_summary["time_preferences"]
                lines.append(f"• **Timezone**: {time_prefs['timezone']}")
                lines.append(f"• **Active Hours**: {time_prefs['active_hours']}")
                lines.append(f"• **Weekend Mode**: {time_prefs['weekend_mode']}")
                lines.append("")
                
                # Privacy settings
                lines.append("### Privacy Settings")
                privacy = prefs_summary["privacy_settings"]
                lines.append(f"• **Collect Usage Data**: {privacy['collect_usage_data']}")
                lines.append(f"• **Data Retention**: {privacy['data_retention_days']} days")
                lines.append("")
                
                lines.append(f"**Last Updated**: {prefs_summary['last_updated']}")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title="User Preferences",
                    border_style="blue"
                ))
            except Exception as e:
                self.console.print(f"[red]Error loading preferences: {e}[/red]")
            
            return True
        
        elif command.startswith("set preference ") or command.startswith("set pref "):
            # Set a preference
            # Format: set preference <category>.<key> <value>
            parts = user_input.split(maxsplit=3)
            if len(parts) < 4:
                self.console.print("[yellow]Usage: set preference <category>.<key> <value>[/yellow]")
                self.console.print("[dim]Example: set preference response_style.tone casual[/dim]")
                return True
            
            try:
                pref_path = parts[2]
                value = parts[3]
                
                if "." not in pref_path:
                    self.console.print("[red]Invalid preference path. Use format: category.key[/red]")
                    return True
                
                category, key = pref_path.split(".", 1)
                
                # Convert value to appropriate type
                if value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                
                self.preference_tracker.set_explicit_preference(
                    self.user_id, category, key, value
                )
                
                self.console.print(f"✅ [green]Set {category}.{key} = {value}[/green]")
            except Exception as e:
                self.console.print(f"[red]Error setting preference: {e}[/red]")
            
            return True
        
        # Analytics commands
        elif command == "analytics" or command == "stats":
            # Show usage analytics
            try:
                metrics = await self.analytics_engine.get_user_metrics(self.user_id, days=30)
                
                lines = ["## 📊 Usage Analytics (Last 30 Days)", ""]
                lines.append(f"• **Total Commands**: {metrics.total_commands}")
                lines.append(f"• **Total Sessions**: {metrics.total_sessions}")
                lines.append(f"• **Average Session Duration**: {metrics.avg_session_duration:.1f} minutes")
                lines.append(f"• **Success Rate**: {metrics.success_rate:.1%}")
                lines.append(f"• **Average Response Time**: {metrics.avg_response_time:.0f}ms")
                lines.append(f"• **Peak Usage Hour**: {metrics.peak_usage_hour:02d}:00")
                lines.append(f"• **Most Used Command**: {metrics.most_used_command}")
                lines.append(f"• **Most Used Category**: {metrics.most_used_category.value}")
                lines.append(f"• **Command Diversity**: {metrics.command_diversity:.1%}")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title="Usage Analytics",
                    border_style="cyan"
                ))
            except Exception as e:
                self.console.print(f"[red]Error loading analytics: {e}[/red]")
            
            return True
        
        elif command == "insights" or command == "command insights":
            # Show command insights
            try:
                insights = await self.analytics_engine.get_command_insights(self.user_id, days=30)
                
                if not insights:
                    self.console.print("[yellow]No command insights available yet[/yellow]")
                    return True
                
                lines = ["## 💡 Command Insights", ""]
                
                for insight in insights[:5]:  # Top 5 commands
                    lines.append(f"### {insight.command}")
                    lines.append(f"• **Usage Count**: {insight.usage_count}")
                    lines.append(f"• **Success Rate**: {insight.success_rate:.1%}")
                    lines.append(f"• **Avg Execution Time**: {insight.avg_execution_time:.0f}ms")
                    
                    if insight.usage_contexts:
                        contexts = ", ".join([ctx.value for ctx in insight.usage_contexts])
                        lines.append(f"• **Primary Contexts**: {contexts}")
                    
                    if insight.recommendation:
                        lines.append(f"• **Recommendation**: {insight.recommendation}")
                    
                    lines.append("")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title="Command Insights",
                    border_style="purple"
                ))
            except Exception as e:
                self.console.print(f"[red]Error loading insights: {e}[/red]")
            
            return True
        
        # Behavior patterns commands
        elif command == "patterns" or command == "behavior patterns":
            # Show detected behavior patterns
            try:
                patterns = await self.behavior_detector.detect_user_patterns(self.user_id)
                
                if not patterns:
                    self.console.print("[yellow]No behavior patterns detected yet[/yellow]")
                    return True
                
                lines = ["## 🧠 Behavior Patterns", ""]
                
                for pattern in patterns[:8]:  # Top 8 patterns
                    lines.append(f"### {pattern.pattern_name}")
                    lines.append(f"• **Type**: {pattern.pattern_type.value}")
                    lines.append(f"• **Description**: {pattern.description}")
                    lines.append(f"• **Confidence**: {pattern.confidence_score:.1%}")
                    lines.append(f"• **Strength**: {pattern.strength:.1%}")
                    lines.append(f"• **Observations**: {pattern.observation_count}")
                    
                    if pattern.examples:
                        lines.append(f"• **Examples**: {', '.join(pattern.examples[:2])}")
                    
                    lines.append("")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title="Behavior Patterns",
                    border_style="magenta"
                ))
            except Exception as e:
                self.console.print(f"[red]Error loading patterns: {e}[/red]")
            
            return True
        
        elif command == "suggestions":
            # Show personalized suggestions
            try:
                profile = await self.personalization_engine.get_user_profile(self.user_id)
                suggestions = await self.personalization_engine.get_personalized_suggestions(self.user_id)
                
                if not suggestions:
                    self.console.print("[yellow]No suggestions available at the moment[/yellow]")
                    return True
                
                lines = ["## 💡 Personalized Suggestions", ""]
                
                for i, suggestion in enumerate(suggestions, 1):
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion["priority"], "⚪")
                    lines.append(f"### {i}. {suggestion['title']} {priority_emoji}")
                    lines.append(f"**Type**: {suggestion['type']}")
                    lines.append(f"**Description**: {suggestion['description']}")
                    
                    if suggestion.get("benefits"):
                        benefits = ", ".join(suggestion["benefits"])
                        lines.append(f"**Benefits**: {benefits}")
                    
                    lines.append("")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title="Personalized Suggestions",
                    border_style="yellow"
                ))
            except Exception as e:
                self.console.print(f"[red]Error loading suggestions: {e}[/red]")
            
            return True
        
        elif command == "learning status":
            # Show learning system status
            try:
                if self.personalization_engine:
                    personalization_stats = self.personalization_engine.get_personalization_stats()
                else:
                    personalization_stats = {}
                
                if self.behavior_detector:
                    detection_stats = self.behavior_detector.get_detection_stats()
                else:
                    detection_stats = {}
                
                if self.learning_storage:
                    storage_stats = await self.learning_storage.get_storage_stats()
                else:
                    storage_stats = {}
                
                lines = ["## 🧠 Learning System Status", ""]
                
                # Personalization status
                lines.append("### Personalization Engine")
                lines.append(f"• **Enabled**: {personalization_stats.get('personalization_enabled', False)}")
                lines.append(f"• **Learning Enabled**: {personalization_stats.get('learning_enabled', False)}")
                lines.append(f"• **Cached Profiles**: {personalization_stats.get('cached_profiles', 0)}")
                lines.append("")
                
                # Behavior detection
                lines.append("### Behavior Detection")
                lines.append(f"• **Total Users**: {detection_stats.get('total_users', 0)}")
                lines.append(f"• **Total Patterns**: {detection_stats.get('total_patterns', 0)}")
                lines.append(f"• **Avg Patterns/User**: {detection_stats.get('avg_patterns_per_user', 0):.1f}")
                lines.append("")
                
                # Storage statistics
                lines.append("### Storage")
                lines.append(f"• **Storage Type**: {storage_stats.get('storage_type', 'unknown')}")
                lines.append(f"• **Auto Cleanup**: {storage_stats.get('auto_cleanup_enabled', False)}")
                lines.append(f"• **Database Size**: {storage_stats.get('database_size_mb', 0):.2f} MB")
                lines.append(f"• **User Profiles**: {storage_stats.get('user_profiles_count', 0)}")
                lines.append(f"• **Command Usage Records**: {storage_stats.get('command_usage_count', 0)}")
                lines.append(f"• **Behavior Patterns**: {storage_stats.get('behavior_patterns_count', 0)}")
                
                self.console.print(Panel(
                    Markdown("\n".join(lines)),
                    title="Learning System Status",
                    border_style="green"
                ))
            except Exception as e:
                self.console.print(f"[red]Error loading learning status: {e}[/red]")
            
            return True
        
        elif command.startswith("learning "):
            # Learning system control commands
            subcommand = command[9:].strip()
            
            if subcommand == "enable":
                if self.personalization_engine:
                    self.personalization_engine.enable_personalization()
                    self.personalization_engine.enable_learning()
                self.console.print("✅ [green]Learning system enabled[/green]")
            
            elif subcommand == "disable":
                if self.personalization_engine:
                    self.personalization_engine.disable_personalization()
                    self.personalization_engine.disable_learning()
                self.console.print("⚠️ [yellow]Learning system disabled[/yellow]")
            
            elif subcommand == "reset":
                # Reset user data (with confirmation)
                self.console.print("[yellow]⚠️ This will delete all learning data for your user.[/yellow]")
                confirm = input("Type 'RESET' to confirm: ")
                if confirm == "RESET":
                    try:
                        if self.personalization_engine:
                            self.personalization_engine.clear_user_cache(self.user_id)
                        if self.learning_storage:
                            await self.learning_storage.cleanup_expired_data(self.user_id)
                        self.console.print("✅ [green]Learning data reset[/green]")
                    except Exception as e:
                        self.console.print(f"[red]Error resetting data: {e}[/red]")
                else:
                    self.console.print("Reset cancelled")
            
            else:
                self.console.print(f"[yellow]Unknown learning command: {subcommand}[/yellow]")
                self.console.print("[dim]Available: enable, disable, reset[/dim]")
            
            return True
        
        return False
    
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
        # Import LLM manager and tools
        from ..core.llm import llm_manager, Message
        from ..core.tools import tool_registry, tool_executor
        from ..core.config import settings
        
        # Track command start time for analytics
        import time
        start_time = time.time()
        command_success = True
        error_message = None
        
        try:
            # Check for built-in commands
            if self.handle_builtin_command(user_input):
                if user_input.lower().strip() in ["exit", "quit", "q"]:
                    self.running = False
                return
            
            # Check for async commands (agents and automation)
            if await self.handle_async_commands(user_input):
                return

            # Show processing indicator
            self.console.print("\n[cyan]🤖 Thinking...[/cyan]", end="")

            # Add user message to memory
            if settings.enable_memory:
                self.memory_manager.add_message("user", user_input)

            # Get context messages from memory
            if settings.enable_memory:
                context_messages = self.memory_manager.get_context_messages()
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
                            self.memory_manager.add_message("assistant", f"[Using tool: {tool_name}]")
                            self.memory_manager.add_message("function", tool_executor.format_result_for_llm(tool_result))

                        # Add tool result to messages
                        messages.append(Message("assistant", f"[Calling {tool_name}]"))
                        messages.append(
                            Message("function", tool_executor.format_result_for_llm(tool_result))
                        )

                    # Get final response with tool results
                    self.console.print("[bold cyan]JARVIS:[/bold cyan] ", end="")
                    response_text = []
                    async for chunk in llm_manager.stream_chat(messages, temperature=0.7):
                        self.console.print(chunk, end="")
                        response_text.append(chunk)
                    self.console.print("\n")
                    
                    # Save assistant response to memory
                    if settings.enable_memory:
                        self.memory_manager.add_message("assistant", "".join(response_text))

                elif response.get("content"):
                    # Direct response without tools
                    self.console.print("[bold cyan]JARVIS:[/bold cyan] " + response["content"] + "\n")
                    
                    # Save to memory
                    if settings.enable_memory:
                        self.memory_manager.add_message("assistant", response["content"])

            else:
                # No tools, just regular chat
                self.console.print("\r" + " " * 50 + "\r", end="")  # Clear "Thinking..."
                self.console.print("[bold cyan]JARVIS:[/bold cyan] ", end="")

                response_text = []
                async for chunk in llm_manager.stream_chat(messages, temperature=0.7):
                    self.console.print(chunk, end="")
                    response_text.append(chunk)

                self.console.print("\n")
                
                # Save assistant response to memory
                if settings.enable_memory:
                    self.memory_manager.add_message("assistant", "".join(response_text))

        except Exception as e:
            command_success = False
            error_message = str(e)
            logger.error(f"Error processing input: {e}", exc_info=True)
            self.console.print(f"\n[red]❌ Error:[/red] {e}\n")
            self.console.print(
                "[dim]Tip: Check your API key or try 'status' to see configuration[/dim]\n"
            )
        
        finally:
            # Track command usage for learning
            if self.analytics_engine and self.preference_tracker:
                try:
                    execution_time_ms = (time.time() - start_time) * 1000
                    
                    # Create command usage record
                    from ..core.learning.schemas import CommandUsage, CommandCategory, UsageContext
                    import uuid
                    
                    # Determine command category
                    command_lower = user_input.lower().strip()
                    if any(cmd in command_lower for cmd in ["agent", "delegate"]):
                        category = CommandCategory.AGENT
                    elif any(cmd in command_lower for cmd in ["automation", "schedule"]):
                        category = CommandCategory.AUTOMATION
                    elif any(cmd in command_lower for cmd in ["tool", "use"]):
                        category = CommandCategory.TOOL
                    elif any(cmd in command_lower for cmd in ["help", "status", "info"]):
                        category = CommandCategory.HELP
                    elif any(cmd in command_lower for cmd in ["search", "find", "query"]):
                        category = CommandCategory.SEARCH
                    elif any(cmd in command_lower for cmd in ["create", "file", "write", "save"]):
                        category = CommandCategory.FILE
                    else:
                        category = CommandCategory.SYSTEM
                    
                    # Create usage record
                    command_usage = CommandUsage(
                        user_id=self.user_id,
                        session_id=getattr(self, 'current_session_id', 'default_session'),
                        command=user_input[:100],  # Truncate long commands
                        category=category,
                        arguments={"length": len(user_input)},
                        success=command_success,
                        execution_time_ms=execution_time_ms,
                        error_message=error_message,
                        context=UsageContext.PERSONAL  # Default context
                    )
                    
                    # Track command usage (run in background to avoid blocking)
                    import asyncio
                    asyncio.create_task(self.preference_tracker.track_command_usage(self.user_id, command_usage))
                    asyncio.create_task(self.analytics_engine.record_command_usage(command_usage))
                    
                    # Record interaction for personalization
                    asyncio.create_task(self.personalization_engine.record_user_interaction(
                        self.user_id, user_input[:50], command_success, user_input
                    ))
                    
                except Exception as e:
                    logger.debug(f"Could not track command usage: {e}")
    

    async def run(self):
        """Run the REPL loop."""
        self.running = True
        
        # Start learning session tracking
        if self.analytics_engine and self.learning_storage:
            try:
                from ..core.learning.schemas import UsageSession
                import uuid
                
                self.current_session_id = str(uuid.uuid4())
                session = UsageSession(
                    session_id=self.current_session_id,
                    user_id=self.user_id
                )
                await self.analytics_engine.start_session(session)
                logger.debug(f"Started learning session: {self.current_session_id}")
            except Exception as e:
                logger.debug(f"Could not start learning session: {e}")
                self.current_session_id = "default_session"
        
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
        
        # Cleanup learning session on exit
        if self.analytics_engine and hasattr(self, 'current_session_id'):
            try:
                await self.analytics_engine.end_session(self.current_session_id)
                logger.debug("Learning session ended")
            except Exception as e:
                logger.debug(f"Error ending learning session: {e}")
        
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
