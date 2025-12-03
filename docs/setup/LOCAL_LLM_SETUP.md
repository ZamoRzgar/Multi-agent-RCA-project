# Local LLM Setup Guide

## Using Ollama (Recommended)

### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### 2. Pull Models

```bash
# Pull the models you want to use
ollama pull qwen2:7b          # Qwen 7B
ollama pull llama2:7b         # LLaMA 2 7B
ollama pull mistral:7b        # Mistral 7B
ollama pull deepseek-coder:6.7b  # DeepSeek alternative

# List installed models
ollama list
```

### 3. Test Models

```bash
# Test each model
ollama run qwen2:7b "Analyze this log: ERROR: Connection timeout"
ollama run llama2:7b "What causes database connection failures?"
ollama run mistral:7b "Explain root cause analysis"
```

### 4. Start Ollama Server

```bash
# Ollama runs as a service by default on port 11434
# Check if running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

## Alternative: Using vLLM (For Production/Batch Processing)

### 1. Install vLLM

```bash
pip install vllm
```

### 2. Download Models from HuggingFace

```bash
# Install HuggingFace CLI
pip install huggingface-hub

# Login (optional, for gated models)
huggingface-cli login

# Models will be auto-downloaded when first used
```

### 3. Serve Models

```bash
# Serve Mistral
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.2 \
    --port 8000

# Serve Qwen (in another terminal)
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-7B-Instruct \
    --port 8001

# Serve LLaMA (in another terminal)
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --port 8002
```

## Hardware Requirements

- **RAM**: 16GB minimum (32GB recommended for multiple models)
- **GPU**: 
  - NVIDIA GPU with 8GB+ VRAM (recommended)
  - CPU-only works but slower
- **Disk**: ~20GB per model

## Model Comparison for RCA Tasks

| Model | Best For | Strengths |
|-------|----------|-----------|
| **Qwen2-7B** | Log parsing, structured analysis | Strong reasoning, Chinese+English |
| **Mistral-7B** | Hypothesis generation | Balanced, good instruction following |
| **LLaMA2-7B** | General reasoning | Stable, well-tested |
| **DeepSeek-Coder** | Code/system analysis | Technical understanding |

## Recommended Role Assignment

1. **Log Parser Agent**: Qwen2-7B (structured extraction)
2. **RCA Reasoner (Log-focused)**: Mistral-7B (reasoning)
3. **RCA Reasoner (KG-focused)**: LLaMA2-7B (knowledge integration)
4. **RCA Reasoner (Hybrid)**: Qwen2-7B (balanced)
5. **Judge Agent**: Mistral-7B (evaluation)
