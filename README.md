# Multi-Agent Knowledge-Graph-Guided RCA System

A multi-agent framework for reliable log-based root cause analysis (RCA) using Large Language Models and knowledge graphs. The system addresses hallucinations and tunnel vision in single-LLM approaches through collaborative agent debate and structured reasoning.

## Overview

This system implements a **multi-agent debate protocol** where specialized LLM agents with different analytical perspectives generate competing hypotheses for root cause analysis. A judge agent evaluates and selects the best hypothesis based on evidence quality and reasoning.

**Key Features:**
- **Multi-agent collaboration**: Log Reasoner, KG Reasoner, and Hybrid Reasoner generate diverse hypotheses
- **Knowledge graph grounding**: Neo4j-based incident memory for historical context retrieval
- **Structured debate**: Up to 3 rounds of hypothesis generation, judging, and refinement
- **Local LLM inference**: Runs entirely on local hardware via Ollama (Qwen2, Mistral, LLaMA2)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Presentation Layer                          │
│            (Evaluation Scripts, Result Collection)           │
├─────────────────────────────────────────────────────────────┤
│                  Orchestration Layer                         │
│            (Debate Protocol, Workflow Control)               │
├─────────────────────────────────────────────────────────────┤
│                     Agent Layer                              │
│   Log Parser → KG Retrieval → 3 Reasoners → Judge           │
├─────────────────────────────────────────────────────────────┤
│                   Knowledge Layer                            │
│            (Incident KG, Similarity Retrieval)               │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                         │
│              (Ollama LLM, Neo4j Graph DB)                    │
└─────────────────────────────────────────────────────────────┘
```

**Pipeline Flow:**
1. **Log Parser Agent** → Extracts structured events, entities, and timeline
2. **KG Retrieval Agent** → Fetches similar historical incidents from Neo4j
3. **Three Reasoners** → Generate competing hypotheses (Log-focused, KG-focused, Hybrid)
4. **Judge Agent** → Scores hypotheses and provides feedback
5. **Refinement** → Reasoners refine based on feedback (up to 3 rounds)
6. **Final Output** → Best hypothesis with root cause category and resolution

## Project Structure

```
log/
├── src/
│   ├── agents/
│   │   ├── log_parser.py          # Log parsing and entity extraction
│   │   ├── kg_retrieval.py        # KG similarity retrieval
│   │   ├── rca_log_reasoner.py    # Log-focused hypothesis generation
│   │   ├── rca_kg_reasoner.py     # KG-focused hypothesis generation
│   │   ├── rca_hybrid_reasoner.py # Hybrid hypothesis generation
│   │   └── judge_agent.py         # Hypothesis evaluation and scoring
│   ├── debate/
│   │   └── protocol.py            # Multi-agent debate orchestration
│   ├── kg/
│   │   ├── builder.py             # Knowledge graph construction
│   │   └── query.py               # KG querying utilities
│   └── utils/
│       └── local_llm_client.py    # Ollama LLM client
├── config/
│   └── config.yaml                # Model and agent configuration
├── data/
│   ├── Hadoop1/                   # Hadoop dataset (55 cases)
│   ├── CMCC/                      # CMCC OpenStack dataset (93 cases)
│   └── HDFS_v1/                   # HDFS dataset (200 sampled blocks)
├── experiments/
│   └── results/                   # Evaluation results
├── docs/
│   └── thesis/                    # Thesis documentation
└── loghub/                        # LogHub datasets
```

## Quick Start

### Prerequisites
- Python 3.9+
- Ollama (for local LLM inference)
- Neo4j 5.0+ (for knowledge graph)

### Installation

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download models
ollama pull qwen2:7b
ollama pull mistral:7b
ollama pull llama2:7b

# 3. Set up Python environment

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Start Neo4j
sudo systemctl start neo4j

# 5. Configure environment
cp .env.example .env
# Edit .env with Neo4j credentials
```

### Running Evaluation

```bash
# Run multi-agent evaluation on Hadoop1
python -m experiments.run_evaluation --dataset hadoop1 --pipeline multi-agent

# Run single-agent baseline
python -m experiments.run_evaluation --dataset hadoop1 --pipeline single-agent

# Run RAG baseline
python -m experiments.run_evaluation --dataset hadoop1 --pipeline rag
```

## Evaluation Results

Evaluated on three datasets with macro-F1 scores:

| Dataset | Multi-Agent | RAG | Single-Agent |
|---------|-------------|-----|--------------|
| Hadoop1 (Coarse) | **39.1%** | 37.9% | 25.8% |
| CMCC | **52.4%** | 7.8% | 3.9% |
| HDFS_v1 | **69.4%** | 63.0% | 56.8% |

The multi-agent system shows consistent improvements, with the largest gains on CMCC (+48.5 pp over single-agent).

## Model Configuration

| Agent | Model | Temperature | Purpose |
|-------|-------|-------------|---------|
| Log Parser | Qwen2-7B | 0.2 | Structured extraction |
| KG Retrieval | Qwen2-7B | 0.3 | Query generation |
| Log Reasoner | Mistral-7B | 0.7 | Log-based hypotheses |
| KG Reasoner | LLaMA2-7B | 0.7 | KG-based hypotheses |
| Hybrid Reasoner | Qwen2-7B | 0.7 | Combined hypotheses |
| Judge | Mistral-7B | 0.2 | Evaluation and scoring |

## Datasets

- **Hadoop1** (LogHub): 55 labeled applications with 4 fault types
- **CMCC** (LogKG): 93 OpenStack failure cases with 7 failure types  
- **HDFS_v1** (LogHub): 575,061 block traces, evaluated on 200 balanced samples

## Documentation

- **Thesis**: `docs/thesis/latex/thesis/` - Full LaTeX thesis with methodology and results
- **Setup Guide**: `SETUP_INSTRUCTIONS.md` - Detailed local LLM setup

## Hardware Requirements

**Minimum**: 8GB RAM, 4 CPU cores, 15GB disk (runs 1 model at a time)  
**Recommended**: 16GB+ RAM, NVIDIA GPU with 8GB+ VRAM, 30GB disk

## Acknowledgments

- Inspired by multi-agent debate approaches for improving LLM factuality
- Built with Ollama for local inference and Neo4j for knowledge graph storage
- Datasets from LogHub and LogKG benchmarks
