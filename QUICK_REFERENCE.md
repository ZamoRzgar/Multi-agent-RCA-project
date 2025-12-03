# Quick Reference Card

## 🚀 Installation (One-Time Setup)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download models (~12GB total)
ollama pull qwen2:7b
ollama pull mistral:7b
ollama pull llama2:7b

# 3. Install Python dependencies
cd /home/zamo/projects/log
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ⚡ Daily Workflow

```bash
# Start your work session
cd /home/zamo/projects/log
source venv/bin/activate

# Ollama runs automatically, but verify:
curl http://localhost:11434/api/tags

# Test setup
python examples/test_local_llm.py
```

## 📊 Working with Loghub Data

### Load Dataset
```python
from src.utils.data_loader import LoghubDataLoader

loader = LoghubDataLoader(loghub_path="loghub")
df = loader.load_dataset("HDFS", use_structured=True)
```

### Get Statistics
```python
from src.utils.data_loader import DatasetStatistics

stats = DatasetStatistics.analyze_dataset(df)
DatasetStatistics.print_statistics(stats)
```

### Extract Cases
```python
# Get single case
case = loader.extract_log_case(df, index=0)

# Get failure cases (BGL has labels)
failures = loader.get_failure_cases("BGL", max_cases=50)
```

### Split for Training
```python
train_df, val_df, test_df = loader.split_dataset(
    df, 
    train_ratio=0.7, 
    val_ratio=0.15, 
    test_ratio=0.15
)
```

## 🤖 Using Local LLMs

### Single Model
```python
from src.utils.local_llm_client import LocalLLMClient

client = LocalLLMClient(backend="ollama", model="qwen2:7b")
response = client.generate(prompt, temperature=0.3, max_tokens=500)
```

### Multi-Model (Different roles)
```python
from src.utils.local_llm_client import MultiModelManager
import yaml

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

manager = MultiModelManager(config)
log_parser_client = manager.get_client("log_parser")
judge_client = manager.get_client("judge")
```

### With Agents
```python
from src.agents import LogParserAgent, RCAReasonerAgent, JudgeAgent

# Agents automatically use models from config
log_parser = LogParserAgent(model="qwen2:7b")
reasoner = RCAReasonerAgent(focus="log", model="mistral:7b")
judge = JudgeAgent(model="mistral:7b")
```

## 🔧 Common Commands

### Ollama Management
```bash
# List models
ollama list

# Remove model
ollama rm qwen2:7b

# Update model
ollama pull qwen2:7b

# Check running models
ollama ps

# Stop Ollama
pkill ollama

# Start Ollama
ollama serve
```

### Test Individual Models
```bash
# Interactive mode
ollama run qwen2:7b
ollama run mistral:7b
ollama run llama2:7b

# Single query
ollama run qwen2:7b "Analyze this error log"
```

### Python Testing
```bash
# Full test suite
python examples/test_local_llm.py

# Test specific agent
python -c "from src.agents import LogParserAgent; agent = LogParserAgent(); print('OK')"

# Test data loading
python -c "from src.utils.data_loader import LoghubDataLoader; loader = LoghubDataLoader(); df = loader.load_dataset('HDFS'); print(f'Loaded {len(df)} logs')"
```

## 📁 Available Datasets

| Dataset | Size | Labeled | Best For |
|---------|------|---------|----------|
| **HDFS** | 2,000 | ✓ | Distributed systems, block failures |
| **BGL** | 2,000 | ✓ | Hardware alerts, supercomputer |
| **Hadoop** | 2,000 | ✓ | MapReduce jobs |
| **OpenStack** | 2,000 | ✓ | Cloud infrastructure |
| **Spark** | 2,000 | ✗ | Big data processing |
| **Linux** | 2,000 | ✗ | OS-level logs |
| **Apache** | 2,000 | ✗ | Web server errors |

## 🎯 Model Selection Guide

**For structured extraction (parsing, entity extraction):**
- Use: `qwen2:7b` with temperature 0.2-0.3

**For reasoning and hypothesis generation:**
- Use: `mistral:7b` with temperature 0.6-0.8

**For evaluation and judging:**
- Use: `mistral:7b` with temperature 0.1-0.3

**For general/balanced tasks:**
- Use: `llama2:7b` with temperature 0.5-0.7

## 🐛 Quick Fixes

**"Connection refused" error:**
```bash
ollama serve
```

**"Model not found" error:**
```bash
ollama pull qwen2:7b
```

**"Out of memory" error:**
```bash
# Use one model at a time, or use quantized versions:
ollama pull mistral:7b-instruct-q4_0
```

**Import errors:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📈 Performance Tips

1. **Use GPU if available** - 10-20x faster
2. **Quantized models** - Use q4_0 or q5_0 versions for less memory
3. **Batch processing** - Process multiple logs together
4. **Cache responses** - Save LLM outputs to avoid re-processing
5. **Adjust max_tokens** - Use smaller values (256-512) for faster responses

## 🔗 File Locations

- **Config**: `config/config.yaml`
- **Agents**: `src/agents/`
- **Data loader**: `src/utils/data_loader.py`
- **LLM client**: `src/utils/local_llm_client.py`
- **Test script**: `examples/test_local_llm.py`
- **Loghub data**: `loghub/`
- **Setup guide**: `SETUP_INSTRUCTIONS.md`

---

**Quick Start**: `ollama pull qwen2:7b && python examples/test_local_llm.py`
