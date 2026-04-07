# Multi-Model AI Support in JARVIS 2.0

JARVIS 2.0 now supports multiple AI model providers, allowing you to use the best model for your needs.

## Supported Models

### 1. OpenAI (Cloud)
- **Models**: GPT-4, GPT-4-Turbo, GPT-3.5-Turbo
- **Setup**: Set `OPENAI_API_KEY` in `.env`
- **Speed**: Fast, requires internet
- **Cost**: Pay-per-token
- **Best for**: Complex reasoning, code generation

### 2. Ollama (Local)
- **Models**: Llama3, Mistral, Neural Chat, Code Llama, etc.
- **Setup**: Install Ollama from https://ollama.ai, run `ollama run llama3`
- **Speed**: Depends on hardware, can be very fast
- **Cost**: Free (runs locally)
- **Best for**: Privacy, offline use, fast responses

### 3. Claude (Cloud)
- **Models**: Claude 3.5 Sonnet
- **Setup**: Set `ANTHROPIC_API_KEY` in `.env`
- **Speed**: Fast, requires internet
- **Cost**: Pay-per-token
- **Best for**: Long-form content, analysis, creative writing

## Configuration

### Environment Setup

Create a `.env` file with your API keys:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic/Claude
ANTHROPIC_API_KEY=sk-ant-your-key-here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Ollama (local)
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434

# Default LLM to use
DEFAULT_LLM=openai  # or ollama, claude
```

### Setting Default Model

```bash
# Start JARVIS with Ollama
DEFAULT_LLM=ollama python main.py

# Start JARVIS with Claude
DEFAULT_LLM=claude python main.py

# Start JARVIS with OpenAI (default)
DEFAULT_LLM=openai python main.py
```

## Usage

### Check Available Models

```
❯ status

System Status:
- LLM Provider: openai
- Available Models: openai, ollama, claude
- Current Model: openai (GPT-4)
```

### Switch Models in CLI

```
❯ /model openai
✅ Switched to OpenAI (GPT-4)

❯ /model ollama
✅ Switched to Ollama (llama3)

❯ /model claude
✅ Switched to Claude (Claude 3.5 Sonnet)

❯ /available_models
Available Models:
- openai: OpenAI (GPT-4)
- ollama: Ollama (llama3)
- claude: Claude (Claude 3.5 Sonnet)
```

### Programmatic Usage

```python
from src.core.llm.multi_model import get_multi_model_manager
from src.core.llm.base import Message

async def chat_with_models():
    manager = get_multi_model_manager()
    await manager.initialize()
    
    messages = [
        Message("system", "You are a helpful assistant"),
        Message("user", "What is Python?")
    ]
    
    # Use default model
    response = await manager.chat(messages)
    print("OpenAI:", response)
    
    # Use specific model
    response = await manager.chat(messages, model="ollama")
    print("Ollama:", response)
    
    # Use Claude
    response = await manager.chat(messages, model="claude")
    print("Claude:", response)
```

## Installation

### OpenAI
```bash
pip install openai tiktoken
```

### Claude/Anthropic
```bash
pip install anthropic
```

### Ollama
1. Download from https://ollama.ai
2. Run: `ollama run llama3` (or your preferred model)
3. Ollama runs at `http://localhost:11434`

## Model Comparison

| Feature | OpenAI | Ollama | Claude |
|---------|--------|--------|--------|
| **Cost** | Paid | Free | Paid |
| **Privacy** | Cloud | Local | Cloud |
| **Speed** | Very Fast | Variable | Very Fast |
| **Quality** | Excellent | Good | Excellent |
| **Offline** | ❌ | ✅ | ❌ |
| **Setup** | Easy | Medium | Easy |
| **Customization** | Limited | High | Limited |

## Best Practices

### 1. Use Ollama for Testing
```bash
DEFAULT_LLM=ollama python main.py
```
- No API costs
- Instant responses
- Good for development

### 2. Use OpenAI for Production
```bash
DEFAULT_LLM=openai python main.py
```
- Highest quality responses
- Reliable and fast
- Best for critical tasks

### 3. Use Claude for Analysis
```bash
DEFAULT_LLM=claude python main.py
```
- Excellent for complex analysis
- Great for long-form content
- Best reasoning capabilities

### 4. Combine Models for Different Tasks

```python
async def analyze_text(text):
    manager = get_multi_model_manager()
    
    # Quick summary with Ollama
    summary = await manager.chat(
        [Message("user", f"Summarize: {text}")],
        model="ollama"
    )
    
    # Deep analysis with Claude
    analysis = await manager.chat(
        [Message("user", f"Analyze: {text}")],
        model="claude"
    )
    
    return {"summary": summary, "analysis": analysis}
```

## Switching Models Dynamically

```bash
❯ /switch_model openai
✅ Switched to OpenAI

❯ What is machine learning?
[Response from OpenAI]

❯ /switch_model ollama
✅ Switched to Ollama

❯ Explain quantum computing
[Response from Ollama - much faster!]
```

## Troubleshooting

### OpenAI not working
```bash
# Check API key
echo $OPENAI_API_KEY

# Update key in .env
OPENAI_API_KEY=sk-your-new-key
```

### Ollama not connecting
```bash
# Make sure Ollama is running
ollama run llama3

# Check connection
curl http://localhost:11434/api/tags
```

### Claude not working
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Update key in .env
ANTHROPIC_API_KEY=sk-ant-your-new-key
```

## Advanced Configuration

### Custom Model Settings

```python
from src.core.config import settings

# Use specific OpenAI model
settings.openai_model = "gpt-4-turbo-preview"

# Use specific Ollama model
settings.ollama_model = "mistral"

# Use specific Claude model
settings.claude_model = "claude-3-5-sonnet-20241022"
```

### Temperature Control

```bash
# Set temperature for more creative responses
TEMPERATURE=0.9 python main.py

# Set temperature for deterministic responses
TEMPERATURE=0.1 python main.py
```

## Next Steps

1. ✅ Set up at least one model (Ollama is easiest)
2. ✅ Test JARVIS with `python main.py`
3. ✅ Try switching between models
4. ✅ Use the best model for your use case

## Support

For issues or questions:
- Check GitHub Issues: https://github.com/UdaySoni32/Jarvis-2.0/issues
- Review logs: `tail -f logs/jarvis.log`
- Test models independently:
  - OpenAI: https://platform.openai.com
  - Claude: https://console.anthropic.com
  - Ollama: https://ollama.ai
