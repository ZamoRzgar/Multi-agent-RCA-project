# Complete Setup Instructions for Local LLMs

## 🚀 Quick Start (30 minutes)

### Step 1: Install Ollama (5 minutes)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### Step 2: Download Models (15 minutes)

```bash
# Download the models (this will take time depending on internet speed)
ollama pull qwen2:7b          # ~4.4GB - Best for structured tasks
ollama pull mistral:7b        # ~4.1GB - Best for reasoning
ollama pull llama2:7b         # ~3.8GB - General purpose

# Verify models are installed
ollama list
```

### Step 3: Test Models (5 minutes)

```bash
# Test Qwen2
ollama run qwen2:7b "Analyze this log: ERROR database connection failed"

# Test Mistral
ollama run mistral:7b "What causes network timeouts?"

# Test LLaMA2
ollama run llama2:7b "Explain root cause analysis"

# Press Ctrl+D or type /bye to exit each model
```

### Step 4: Start Ollama Server (1 minute)

```bash
# Ollama runs as a service automatically after installation
# Check if it's running:
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve
```

### Step 5: Install Python Dependencies (5 minutes)

```bash
cd /home/zamo/projects/log
source venv/bin/activate  # or create: python -m venv venv

# Install requirements
pip install -r requirements.txt

# Install additional dependencies for local LLM
pip install requests
```

### Step 6: Test Your Setup (5 minutes)

```bash
# Run the test script
python examples/test_local_llm.py
```

## 📊 Model Role Assignments

Your configuration uses different models for different tasks:

| Agent Role | Model | Why? | Temperature |
|------------|-------|------|-------------|
| **Log Parser** | Qwen2-7B | Excellent at structured extraction | 0.3 (precise) |
| **KG Retrieval** | Qwen2-7B | Good query understanding | 0.5 (balanced) |
| **RCA Reasoner (Log)** | Mistral-7B | Strong reasoning abilities | 0.7 (creative) |
| **RCA Reasoner (KG)** | LLaMA2-7B | Good knowledge integration | 0.7 (creative) |
| **RCA Reasoner (Hybrid)** | Qwen2-7B | Balanced approach | 0.7 (creative) |
| **Judge** | Mistral-7B | Good at evaluation | 0.2 (very precise) |

## 🔧 Configuration

Your `config/config.yaml` is already set up for local models:

```yaml
llm:
  provider: "local"
  backend: "ollama"
  model: "qwen2:7b"

local_models:
  log_parser:
    model: "qwen2:7b"
  rca_reasoner_log:
    model: "mistral:7b"
  rca_reasoner_kg:
    model: "llama2:7b"
  # ... etc
```

## 📁 Using with Loghub Data

### Load HDFS Dataset

```python
from src.utils.data_loader import LoghubDataLoader

# Initialize loader
loader = LoghubDataLoader(loghub_path="loghub")

# Load HDFS data (pre-parsed)
df = loader.load_dataset("HDFS", use_structured=True)
print(f"Loaded {len(df)} HDFS logs")

# Get a sample case
case = loader.extract_log_case(df, 0)
print(case)
```

### Run RCA on Sample Log

```python
from src.agents import LogParserAgent
from src.utils.local_llm_client import LocalLLMClient

# Initialize agent with local model
agent = LogParserAgent(model="qwen2:7b")

# Load sample logs
loader = LoghubDataLoader(loghub_path="loghub")
df = loader.load_dataset("HDFS")
sample_logs = "\n".join(df["Content"].head(10).tolist())

# Parse logs
result = agent.process({"raw_logs": sample_logs})
print(result)
```

### Build Knowledge Graph from Multiple Datasets

```python
# Prepare data for KG construction
datasets = ["HDFS", "BGL", "Hadoop"]
combined_df = loader.prepare_for_kg(datasets)

# Use for KG building
from src.kg import KGBuilder
builder = KGBuilder(config={})
builder.build_from_logs(combined_df)
```

## 🎯 Example Workflow

### 1. Test Single Model

```python
from src.utils.local_llm_client import LocalLLMClient

client = LocalLLMClient(backend="ollama", model="qwen2:7b")

prompt = """Analyze this HDFS log:
081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating

Extract: component, action, entities"""

response = client.generate(prompt, temperature=0.3)
print(response)
```

### 2. Test Multi-Agent System

```python
from src.agents import LogParserAgent, RCAReasonerAgent, JudgeAgent
from src.debate import DebateProtocol

# Initialize agents with different models
log_parser = LogParserAgent(model="qwen2:7b")
reasoners = [
    RCAReasonerAgent(focus="log", model="mistral:7b"),
    RCAReasonerAgent(focus="kg", model="llama2:7b"),
    RCAReasonerAgent(focus="hybrid", model="qwen2:7b")
]
judge = JudgeAgent(model="mistral:7b")

# Create debate protocol
debate = DebateProtocol(reasoners, judge)

# Load real log case
loader = LoghubDataLoader(loghub_path="loghub")
df = loader.load_dataset("HDFS")
case = loader.extract_log_case(df, 0)

# Run RCA (when implemented)
# result = debate.run(parsed_logs, kg_facts)
```

## 💾 Hardware Requirements

### Minimum (Run 1 model at a time)
- **RAM**: 8GB
- **Disk**: 15GB free
- **CPU**: 4 cores
- **Speed**: ~5-10 tokens/sec on CPU

### Recommended (Run multiple models)
- **RAM**: 16GB+
- **GPU**: NVIDIA with 8GB+ VRAM
- **Disk**: 30GB free
- **Speed**: ~50-100 tokens/sec on GPU

### Optimal (Best performance)
- **RAM**: 32GB+
- **GPU**: NVIDIA RTX 3090/4090 (24GB VRAM)
- **Disk**: 50GB free SSD
- **Speed**: ~100-200 tokens/sec

## 🐛 Troubleshooting

### Ollama not found
```bash
# Check if installed
which ollama

# If not, reinstall
curl -fsSL https://ollama.com/install.sh | sh
```

### Model download fails
```bash
# Check internet connection
ping ollama.com

# Try downloading again
ollama pull qwen2:7b
```

### Server not responding
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
pkill ollama
ollama serve
```

### Out of memory
```bash
# Run one model at a time
# Or use smaller models:
ollama pull qwen2:1.5b
ollama pull mistral:7b-instruct-q4_0  # Quantized version
```

### Python import errors
```bash
# Make sure you're in virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## 🔄 Alternative: Using vLLM (Advanced)

If you need better performance or batch processing:

```bash
# Install vLLM
pip install vllm

# Serve model
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2-7B-Instruct \
    --port 8000 \
    --gpu-memory-utilization 0.8
```

Then update config:
```yaml
local_models:
  log_parser:
    backend: "vllm"
    base_url: "http://localhost:8000"
    model: "Qwen/Qwen2-7B-Instruct"
```

## 📚 Next Steps

1. ✅ Install Ollama and download models
2. ✅ Test with `examples/test_local_llm.py`
3. ✅ Load loghub data with `data_loader.py`
4. 🔨 Implement agent logic (complete TODOs)
5. 🔨 Build knowledge graph from loghub data
6. 🔨 Run full multi-agent RCA pipeline
7. 📊 Evaluate on labeled datasets (HDFS, BGL)

## 📖 Resources

- **Ollama**: https://ollama.com/
- **Qwen2**: https://huggingface.co/Qwen/Qwen2-7B-Instruct
- **Mistral**: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2
- **LLaMA2**: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
- **Loghub**: https://github.com/logpai/loghub

---

**Ready to start!** Run `python examples/test_local_llm.py` to verify everything works.
