# Advanced AI Model Setup Guide

Complete guide to configuring and using all AI models in JARVIS 2.0.

## Table of Contents

1. [Supported Models](#supported-models)
2. [Quick Setup](#quick-setup)
3. [Custom Models](#custom-models)
4. [Local Models](#local-models)
5. [Advanced Configuration](#advanced-configuration)
6. [Examples](#examples)

## Supported Models

### Built-in Providers

| Provider | Model | Type | Cost | Setup |
|----------|-------|------|------|-------|
| OpenAI | GPT-4, GPT-3.5 | Cloud | Paid | API Key |
| Claude | 3.5 Sonnet | Cloud | Paid | API Key |
| Gemini | 1.5 Pro | Cloud | Paid | API Key |
| Ollama | Llama3, Mistral | Local | Free | Install app |
| Custom | Any HTTP API | Variable | Variable | URL + Config |
| Local | llama.cpp, vLLM | Local | Free | Server |

## Quick Setup

### 1. OpenAI

```bash
# Set API key
export OPENAI_API_KEY=sk-...

# Start with GPT-4
DEFAULT_LLM=openai python main.py

# Or in .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
DEFAULT_LLM=openai
```

### 2. Claude (Anthropic)

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Start with Claude
DEFAULT_LLM=claude python main.py

# Or in .env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022
DEFAULT_LLM=claude
```

### 3. Gemini (Google)

```bash
# Get API key from https://ai.google.dev
export GEMINI_API_KEY=AIzaSy...

# Start with Gemini
DEFAULT_LLM=gemini python main.py

# Or in .env
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-1.5-pro
DEFAULT_LLM=gemini
```

### 4. Ollama (Local & Free)

```bash
# Install from https://ollama.ai
# Download a model
ollama pull llama3

# Start JARVIS
DEFAULT_LLM=ollama python main.py

# Or in .env
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM=ollama
```

## Custom Models

### HTTP API Models

Register any HTTP-based API as a model:

```python
from src.core.llm.multi_model import get_multi_model_manager
from src.core.llm.base import Message

async def setup_custom():
    manager = get_multi_model_manager()
    await manager.initialize()
    
    # Register custom model
    manager.register_custom_model(
        name='my-api',
        api_url='https://api.example.com/v1/chat/completions',
        api_key='your-api-key',
    )
    
    # Now use it
    messages = [Message("user", "Hello")]
    response = await manager.chat(messages, model='my-api')
    print(response)
```

### Custom with Formatters

Handle non-standard APIs:

```python
def format_request(messages, temperature, **kwargs):
    """Format request for custom API."""
    return {
        "input": messages[-1].content,  # Just send last message
        "temperature": temperature,
        "max_length": 500,
    }

def parse_response(data):
    """Parse custom API response."""
    return data.get("output", {}).get("text", "")

manager.register_custom_model(
    name='custom-api',
    api_url='https://custom.api.com/generate',
    api_key='key',
    request_formatter=format_request,
    response_parser=parse_response,
)
```

### LiteLLM Models

Use any model via LiteLLM:

```python
def format_litellm(messages, temperature, **kwargs):
    return {
        "model": "claude-3-sonnet-20240229",  # Any supported model
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
    }

manager.register_custom_model(
    name='litellm-claude',
    api_url='http://localhost:8000/chat/completions',
    request_formatter=format_litellm,
)
```

## Local Models

### llama.cpp

```bash
# Install and start server
./server -m model.gguf -ngl 33

# Register with JARVIS
manager.register_local_model(
    base_url='http://localhost:8000',
    model_name='local-llama'
)
```

### vLLM

```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-hf

# Register with JARVIS
manager.register_local_model(
    base_url='http://localhost:8000',
    model_name='llama-2'
)
```

### Text Generation WebUI

```bash
# Start oobabooga's WebUI (with OpenAI extension)
# Then register
manager.register_local_model(
    base_url='http://localhost:5000/v1',
    model_name='webui-model'
)
```

## Advanced Configuration

### Multi-Model Setup

```python
import asyncio
from src.core.llm.multi_model import get_multi_model_manager
from src.core.llm.base import Message

async def setup_all_models():
    manager = get_multi_model_manager()
    await manager.initialize()
    
    # Register additional models
    manager.register_local_model(
        base_url='http://localhost:8000',
        model_name='local-llama'
    )
    
    manager.register_custom_model(
        name='huggingface-api',
        api_url='https://api-inference.huggingface.co/models/...',
        api_key='hf_...',
    )
    
    # List all available
    for model_info in manager.get_available_models():
        print(f"{model_info.name}: {model_info.description}")
    
    # Switch between models
    messages = [Message("user", "Hello")]
    
    # Use Ollama
    r1 = await manager.chat(messages, model='ollama')
    print("Ollama:", r1)
    
    # Use OpenAI
    r2 = await manager.chat(messages, model='openai')
    print("OpenAI:", r2)
    
    # Use Claude
    r3 = await manager.chat(messages, model='claude')
    print("Claude:", r3)
    
    # Use local
    r4 = await manager.chat(messages, model='local-llama')
    print("Local:", r4)

asyncio.run(setup_all_models())
```

### Temperature Control

Different models work better with different temperatures:

```bash
# Creative responses
TEMPERATURE=0.9 DEFAULT_LLM=gemini python main.py

# Balanced
TEMPERATURE=0.7 DEFAULT_LLM=openai python main.py

# Deterministic/factual
TEMPERATURE=0.1 DEFAULT_LLM=claude python main.py
```

### Token Limits

```bash
# Adjust max tokens
MAX_TOKENS=4000 DEFAULT_LLM=openai python main.py

# Or in code
response = await manager.chat(messages, max_tokens=8000)
```

## Examples

### Example 1: Auto-select Best Model

```python
async def smart_chat(question):
    manager = get_multi_model_manager()
    await manager.initialize()
    
    messages = [Message("user", question)]
    
    # Use local model for speed
    if "quick" in question:
        return await manager.chat(messages, model='ollama')
    
    # Use Claude for analysis
    if "analyze" in question:
        return await manager.chat(messages, model='claude')
    
    # Use Gemini for research
    if "research" in question:
        return await manager.chat(messages, model='gemini')
    
    # Default to OpenAI
    return await manager.chat(messages, model='openai')
```

### Example 2: Compare Models

```python
async def compare_models(question):
    manager = get_multi_model_manager()
    await manager.initialize()
    
    messages = [Message("user", question)]
    models = ['openai', 'claude', 'gemini', 'ollama']
    
    print(f"Question: {question}\n")
    
    for model in models:
        try:
            response = await manager.chat(messages, model=model)
            print(f"{model.upper()}:")
            print(f"  {response[:100]}...\n")
        except:
            print(f"{model.upper()}: Unavailable\n")
```

### Example 3: Streaming

```python
async def stream_response(question):
    manager = get_multi_model_manager()
    await manager.initialize()
    
    messages = [Message("user", question)]
    
    print("Streaming response from Gemini:")
    async for chunk in manager.stream_chat(messages, model='gemini'):
        print(chunk, end='', flush=True)
    print()
```

### Example 4: Custom LLM API

```python
# HuggingFace Inference API
def format_hf_request(messages, temperature, **kwargs):
    return {
        "inputs": messages[-1].content,
        "parameters": {
            "temperature": temperature,
            "max_length": 500,
        }
    }

def parse_hf_response(data):
    if isinstance(data, list) and len(data) > 0:
        return data[0].get("generated_text", "")
    return str(data)

manager.register_custom_model(
    name='huggingface',
    api_url='https://api-inference.huggingface.co/models/gpt2',
    api_key='hf_YOUR_TOKEN',
    request_formatter=format_hf_request,
    response_parser=parse_hf_response,
)
```

## Performance Tips

### 1. Use Local Models for Speed
```bash
# Fastest for real-time
DEFAULT_LLM=ollama python main.py
```

### 2. Use Claude for Quality
```bash
# Best reasoning and analysis
DEFAULT_LLM=claude python main.py
```

### 3. Use OpenAI for Balance
```bash
# Best balance of speed/quality
DEFAULT_LLM=openai python main.py
```

### 4. Use Gemini for Cost
```bash
# Good quality, reasonable cost
DEFAULT_LLM=gemini python main.py
```

## Troubleshooting

### Model Not Found
```bash
# Check available models
❯ /available_models

# Check logs
tail -f logs/jarvis.log
```

### API Key Error
```bash
# Verify key is set
echo $OPENAI_API_KEY

# Check .env file
cat .env | grep API_KEY
```

### Connection Timeout
```bash
# For local models, check server is running
curl http://localhost:8000/api/tags

# For cloud APIs, check internet connection
curl https://api.openai.com
```

### Model Performance

```bash
# If model is slow, try another
/switch_model ollama  # Faster local
/switch_model openai  # Higher quality
/switch_model gemini  # Good balance
```

## Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Claude/Anthropic**: https://console.anthropic.com
- **Gemini/Google**: https://ai.google.dev
- **HuggingFace**: https://huggingface.co/settings/tokens

## Next Steps

1. ✅ Choose your primary model (recommendation: Ollama for free testing)
2. ✅ Configure API keys in `.env`
3. ✅ Set `DEFAULT_LLM` to your choice
4. ✅ Start JARVIS: `python main.py`
5. ✅ Try `/available_models` to see all available
6. ✅ Use `/switch_model MODEL_NAME` to switch

## Support

- GitHub: https://github.com/UdaySoni32/Jarvis-2.0/issues
- Docs: Check MULTI_MODEL_SUPPORT.md for more details
- Models: Visit https://ollama.ai, https://huggingface.co, etc.
