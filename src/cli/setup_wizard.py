"""First-time setup wizard for JARVIS 2.0."""

import os
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog, yes_no_dialog, message_dialog
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class SetupWizard:
    """Interactive setup wizard for first-time configuration."""

    def __init__(self):
        """Initialize setup wizard."""
        self.env_file = Path(".env")
        self.config = {}

    def welcome_screen(self):
        """Display welcome message."""
        welcome_text = """[bold cyan]🤖 Welcome to JARVIS 2.0 Setup![/bold cyan]

This wizard will help you configure JARVIS for first use.

[yellow]What we'll set up:[/yellow]
  • Choose your AI provider (OpenAI, Claude, or local Ollama)
  • Configure API keys (if needed)
  • Set up preferences
  • Test your configuration

[dim]This will only take a few minutes![/dim]
"""
        console.print(Panel(welcome_text, border_style="cyan"))
        console.print()

    async def choose_llm_provider(self) -> str:
        """Let user choose LLM provider."""
        console.print("[bold]Step 1: Choose Your AI Provider[/bold]\n")

        result = await radiolist_dialog(
            title="LLM Provider",
            text="Select which AI provider you want to use:",
            values=[
                ("openai", "OpenAI GPT-4 (Best quality, requires API key, ~$0.03/1K tokens)"),
                ("ollama", "Ollama (Free, runs locally, requires installation)"),
                ("claude", "Anthropic Claude (High quality, requires API key)"),
            ],
        ).run_async()

        return result or "ollama"

    async def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for the selected provider."""
        if provider == "ollama":
            return None

        provider_info = {
            "openai": {
                "name": "OpenAI",
                "url": "https://platform.openai.com/api-keys",
                "env_var": "OPENAI_API_KEY",
            },
            "claude": {
                "name": "Anthropic Claude",
                "url": "https://console.anthropic.com/",
                "env_var": "ANTHROPIC_API_KEY",
            },
        }

        info = provider_info.get(provider, {})
        
        console.print(f"\n[bold]Step 2: {info['name']} API Key[/bold]\n")
        console.print(f"Get your API key from: [link]{info['url']}[/link]")
        console.print()

        api_key = await input_dialog(
            title=f"{info['name']} API Key",
            text=f"Enter your {info['name']} API key:",
            password=True,
        ).run_async()

        return api_key

    async def configure_ollama(self) -> dict:
        """Configure Ollama settings."""
        console.print("\n[bold]Step 2: Ollama Configuration[/bold]\n")
        console.print("[yellow]Note:[/yellow] Make sure Ollama is installed and running.")
        console.print("Install from: https://ollama.ai/\n")

        url = await input_dialog(
            title="Ollama URL",
            text="Ollama API URL:",
            default="http://localhost:11434",
        ).run_async()

        model = await input_dialog(
            title="Ollama Model",
            text="Which model to use?",
            default="llama3",
        ).run_async()

        return {
            "OLLAMA_BASE_URL": url or "http://localhost:11434",
            "OLLAMA_MODEL": model or "llama3",
        }

    async def configure_features(self) -> dict:
        """Configure optional features."""
        console.print("\n[bold]Step 3: Optional Features[/bold]\n")

        enable_memory = await yes_no_dialog(
            title="Enable Memory",
            text="Enable conversation memory? (Remembers context across sessions)",
        ).run_async()

        enable_plugins = await yes_no_dialog(
            title="Enable Plugins",
            text="Enable plugins/tools? (Allows JARVIS to use tools like web search, calculator, etc.)",
        ).run_async()

        return {
            "ENABLE_MEMORY": str(enable_memory if enable_memory is not None else True).lower(),
            "ENABLE_PLUGINS": str(enable_plugins if enable_plugins is not None else True).lower(),
        }

    async def test_connection(self, provider: str) -> bool:
        """Test the LLM connection."""
        console.print("\n[bold]Step 4: Testing Configuration[/bold]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Testing {provider} connection...", total=None)

            try:
                if provider == "openai":
                    # Test OpenAI connection
                    from openai import AsyncOpenAI
                    client = AsyncOpenAI(api_key=self.config.get("OPENAI_API_KEY"))
                    await client.models.retrieve("gpt-4-turbo-preview")
                    progress.update(task, description="✅ OpenAI connection successful!")
                    return True

                elif provider == "claude":
                    # Test Claude connection
                    console.print("[yellow]Claude connection test not implemented yet[/yellow]")
                    return True

                elif provider == "ollama":
                    # Test Ollama connection
                    import httpx
                    url = self.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{url}/api/tags")
                        if response.status_code == 200:
                            progress.update(task, description="✅ Ollama connection successful!")
                            return True
                        else:
                            progress.update(task, description="❌ Ollama connection failed!")
                            return False

            except Exception as e:
                progress.update(task, description=f"❌ Connection failed: {e}")
                return False

        return False

    def save_configuration(self):
        """Save configuration to .env file."""
        console.print("\n[bold]Step 5: Saving Configuration[/bold]\n")

        # Read existing .env.example as template
        template_file = Path(".env.example")
        if template_file.exists():
            with open(template_file, "r") as f:
                template = f.read()
        else:
            template = ""

        # Update with user configuration
        env_lines = []
        for line in template.split("\n"):
            if "=" in line and not line.strip().startswith("#"):
                key = line.split("=")[0].strip()
                if key in self.config:
                    env_lines.append(f"{key}={self.config[key]}")
                else:
                    env_lines.append(line)
            else:
                env_lines.append(line)

        # Write to .env
        with open(self.env_file, "w") as f:
            f.write("\n".join(env_lines))

        console.print(f"✅ Configuration saved to [cyan]{self.env_file}[/cyan]")

    def completion_screen(self):
        """Show completion message."""
        completion_text = """[bold green]🎉 Setup Complete![/bold green]

JARVIS 2.0 is now configured and ready to use!

[bold]To start JARVIS:[/bold]
  [cyan]python -m src.cli[/cyan]

[bold]Quick tips:[/bold]
  • Type [cyan]help[/cyan] to see available commands
  • Type [cyan]status[/cyan] to check system status
  • Just chat naturally - no commands needed!
  • Type [cyan]exit[/cyan] or [cyan]quit[/cyan] to exit

[bold]Configuration file:[/bold]
  Location: [cyan].env[/cyan]
  You can edit this file anytime to change settings

[dim]Enjoy using JARVIS! 🚀[/dim]
"""
        console.print()
        console.print(Panel(completion_text, border_style="green"))

    async def run(self) -> bool:
        """Run the setup wizard."""
        try:
            # Welcome
            self.welcome_screen()

            # Step 1: Choose LLM provider
            provider = await self.choose_llm_provider()
            self.config["DEFAULT_LLM"] = provider

            # Step 2: Get API key or configure Ollama
            if provider == "ollama":
                ollama_config = await self.configure_ollama()
                self.config.update(ollama_config)
            else:
                api_key = await self.get_api_key(provider)
                if not api_key:
                    console.print("[red]Setup cancelled - API key required[/red]")
                    return False

                if provider == "openai":
                    self.config["OPENAI_API_KEY"] = api_key
                    self.config["OPENAI_MODEL"] = "gpt-4-turbo-preview"
                elif provider == "claude":
                    self.config["ANTHROPIC_API_KEY"] = api_key
                    self.config["CLAUDE_MODEL"] = "claude-3-opus-20240229"

            # Step 3: Configure features
            features = await self.configure_features()
            self.config.update(features)

            # Step 4: Test connection
            test_passed = await self.test_connection(provider)
            if not test_passed:
                retry = await yes_no_dialog(
                    title="Connection Test Failed",
                    text="Connection test failed. Continue anyway?",
                ).run_async()
                if not retry:
                    console.print("[yellow]Setup cancelled[/yellow]")
                    return False

            # Step 5: Save configuration
            self.save_configuration()

            # Completion
            self.completion_screen()

            return True

        except KeyboardInterrupt:
            console.print("\n[yellow]Setup cancelled by user[/yellow]")
            return False
        except Exception as e:
            console.print(f"\n[red]Setup error: {e}[/red]")
            return False


async def run_setup_wizard() -> bool:
    """Run the setup wizard and return success status."""
    wizard = SetupWizard()
    return await wizard.run()


def needs_setup() -> bool:
    """Check if setup is needed."""
    env_file = Path(".env")
    
    # Check if .env exists
    if not env_file.exists():
        return True
    
    # Check if it has required configuration
    required_vars = ["DEFAULT_LLM"]
    env_content = env_file.read_text()
    
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=" in env_content and "your_" in env_content:
            return True
    
    # Check if API keys are configured (if not using ollama)
    if "DEFAULT_LLM=openai" in env_content and "OPENAI_API_KEY=" not in env_content:
        return True
    
    if "DEFAULT_LLM=claude" in env_content and "ANTHROPIC_API_KEY=" not in env_content:
        return True
    
    return False
