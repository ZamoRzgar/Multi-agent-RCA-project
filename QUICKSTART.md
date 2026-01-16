# Quick Start Guide

Get the multi-agent RCA system running in ~15 minutes.

## Prerequisites

- Python 3.9+
- 8GB+ RAM (16GB recommended)
- 15GB disk space for models

## Step 1: Install Ollama (2 min)

```bash
# Install Ollama for local LLM inference
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

## Step 2: Download Models (10 min)

```bash
# Download required models
ollama pull qwen2:7b      # ~4.4GB - Structured tasks
ollama pull mistral:7b    # ~4.1GB - Reasoning
ollama pull llama2:7b     # ~3.8GB - General purpose

# Verify models
ollama list
```

## Step 3: Python Environment (2 min)

```bash
cd /home/zamo/projects/log

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Neo4j Setup (3 min)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install neo4j

# Start Neo4j
sudo systemctl start neo4j

# Verify running
curl http://localhost:7474
```

Configure Neo4j credentials:
```bash
cp .env.example .env
# Edit .env with:
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password
```

## Step 5: Verify Setup

```bash
# Test Ollama is running
curl http://localhost:11434/api/tags

# Test a model
ollama run qwen2:7b "What is root cause analysis?" --verbose
# Press Ctrl+D to exit

# Test Python imports
python -c "from src.agents import LogParserAgent; print('OK')"
```

## Running Experiments

### Multi-Agent Pipeline
```bash
python -m experiments.run_evaluation --dataset hadoop1 --pipeline multi-agent
```

### Baselines
```bash
# Single-agent (no KG, no debate)
python -m experiments.run_evaluation --dataset hadoop1 --pipeline single-agent

# RAG (KG retrieval, no debate)
python -m experiments.run_evaluation --dataset hadoop1 --pipeline rag
```

### Available Datasets
- `hadoop1` - 55 Hadoop failure cases
- `cmcc` - 93 OpenStack failure cases
- `hdfs` - 200 HDFS block traces

## Configuration

Edit `config/config.yaml` to customize:
- Model assignments per agent
- Temperature settings
- Debate rounds (default: 3)
- Neo4j connection

## Troubleshooting

**Ollama not responding:**
```bash
# Check if running
ps aux | grep ollama

# Restart
pkill ollama && ollama serve
```

**Out of memory:**
```bash
# Use quantized models
ollama pull mistral:7b-instruct-q4_0
```

**Neo4j connection failed:**
```bash
sudo systemctl status neo4j
sudo systemctl restart neo4j
```

**Import errors:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Project Structure

```
src/
├── agents/           # 6 agent implementations
│   ├── log_parser.py
│   ├── kg_retrieval.py
│   ├── rca_log_reasoner.py
│   ├── rca_kg_reasoner.py
│   ├── rca_hybrid_reasoner.py
│   └── judge_agent.py
├── debate/           # Debate protocol
├── kg/               # Knowledge graph
└── utils/            # LLM client, helpers

data/                 # Datasets (Hadoop1, CMCC, HDFS)
experiments/          # Evaluation scripts
docs/thesis/          # Thesis documentation
```

## Resources

- **Ollama**: https://ollama.com/
- **Neo4j**: https://neo4j.com/docs/
- **LogHub**: https://github.com/logpai/loghub
- **Setup Details**: See `SETUP_INSTRUCTIONS.md`
