# AetherLog 2.0: Multi-Agent Knowledge-Graph-Guided RCA System

A novel multi-agent framework for reliable log-based root cause analysis (RCA) using Large Language Models and knowledge graphs. This system addresses hallucinations and tunnel vision in single-LLM approaches through collaborative agent debate and structured reasoning.

## 🎯 Project Overview

Single-LLM systems for root cause analysis often suffer from:
- **Hallucinations**: Making unsupported claims not grounded in logs or facts
- **Tunnel vision**: Missing alternative explanations and causal chains
- **Limited reasoning**: Inability to cross-check hypotheses against multiple perspectives

**AetherLog 2.0** solves these problems through:
- **Multi-agent collaboration**: Specialized agents with different analytical perspectives
- **Knowledge graph grounding**: Shared memory of historical incidents and causal relationships
- **Structured debate**: Agents critique, refine, and converge on accurate explanations
- **Judge mechanism**: Evidence-based selection of the best root cause hypothesis

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Log Input (Failure Case)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Log Parser Agent   │
              │  (Extract entities,  │
              │   events, timeline)  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ KG Retrieval Agent   │
              │ (Fetch relevant KG   │
              │  facts & relations)  │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌────────┐     ┌────────┐     ┌────────┐
    │  RCA   │     │  RCA   │     │  RCA   │
    │Reasoner│     │Reasoner│     │Reasoner│
    │  (Log) │     │  (KG)  │     │(Hybrid)│
    └───┬────┘     └───┬────┘     └───┬────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
            ┌──────────────────┐
            │  Debate Protocol │
            │ (Critique, Refine,│
            │   Cross-check)   │
            └─────────┬────────┘
                      │
                      ▼
            ┌──────────────────┐
            │   Judge Agent    │
            │ (Score & Select  │
            │ best explanation)│
            └─────────┬────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │  Final RCA Prediction  │
         │   + Explanation        │
         └────────────────────────┘
```

## 📁 Project Structure

```
log/
├── src/                          # Source code
│   ├── agents/                   # Agent implementations
│   │   ├── log_parser.py        # Log parsing agent
│   │   ├── kg_retrieval.py      # KG retrieval agent
│   │   ├── rca_reasoner.py      # RCA reasoning agents
│   │   └── judge.py             # Judge agent
│   ├── kg/                       # Knowledge graph modules
│   │   ├── builder.py           # KG construction
│   │   ├── query.py             # KG querying
│   │   └── schema.py            # KG schema definitions
│   ├── debate/                   # Debate protocol
│   │   ├── protocol.py          # Debate orchestration
│   │   └── scoring.py           # Hypothesis scoring
│   ├── utils/                    # Utilities
│   │   ├── llm_client.py        # LLM API wrapper
│   │   ├── log_parser.py        # Log parsing utilities
│   │   └── metrics.py           # Evaluation metrics
│   └── evaluation/               # Evaluation framework
│       ├── baselines.py         # Baseline implementations
│       └── evaluator.py         # Evaluation orchestration
├── data/                         # Data directory
│   ├── raw/                     # Raw log datasets
│   ├── processed/               # Processed logs
│   └── kg/                      # Knowledge graph storage
├── experiments/                  # Experiments
│   ├── baselines/               # Baseline experiments
│   └── results/                 # Experiment results
├── docs/                         # Documentation
│   ├── architecture/            # Architecture diagrams
│   └── design/                  # Design documents
├── tests/                        # Tests
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── config/                       # Configuration files
│   └── config.yaml              # Main configuration
├── logs/                         # Application logs
├── requirements.txt              # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Neo4j 5.0+ (for knowledge graph storage)
- OpenAI API key or Anthropic API key

### Installation

1. **Clone the repository** (if using git):
```bash
cd /home/zamo/projects/log
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. **Install Neo4j** (for knowledge graph):
```bash
# Follow Neo4j installation guide for your OS
# https://neo4j.com/docs/operations-manual/current/installation/
```

6. **Download spaCy model** (for NLP):
```bash
python -m spacy download en_core_web_sm
```

### Configuration

Edit `config/config.yaml` to customize:
- LLM provider and model selection
- Agent parameters (temperature, max tokens)
- Debate protocol settings
- Knowledge graph configuration
- Evaluation metrics

## 📊 Research Questions

**RQ1 – Accuracy**: Does multi-agent KG-guided RCA achieve higher accuracy than single-LLM + KG baseline?

**RQ2 – Reliability**: Does agent debate + KG grounding reduce hallucinations compared to single-LLM and self-consistency?

**RQ3 – Explanation Quality**: Do multi-agent explanations score higher in correctness, clarity, and evidence-use?

**RQ4 – Agent Dynamics**: How does agent agreement/disagreement relate to correctness?

**RQ5 – Cost vs Benefit**: What is the computational overhead and is it acceptable for practical RCA workflows?

## 🧪 Usage

### Basic Usage

```python
from src.agents import LogParserAgent, KGRetrievalAgent, RCAReasonerAgent, JudgeAgent
from src.debate import DebateProtocol
from src.kg import KnowledgeGraph

# Initialize components
log_parser = LogParserAgent()
kg_retrieval = KGRetrievalAgent()
reasoners = [
    RCAReasonerAgent(focus="log"),
    RCAReasonerAgent(focus="kg"),
    RCAReasonerAgent(focus="hybrid")
]
judge = JudgeAgent()
debate = DebateProtocol(reasoners, judge)

# Process log case
log_case = load_log_case("data/raw/case_001.log")
parsed_logs = log_parser.parse(log_case)
kg_facts = kg_retrieval.retrieve(parsed_logs)

# Run debate and get final prediction
result = debate.run(parsed_logs, kg_facts)
print(f"Root Cause: {result.root_cause}")
print(f"Explanation: {result.explanation}")
```

### Running Experiments

```bash
# Run full evaluation
python experiments/run_evaluation.py --config config/config.yaml

# Run specific baseline
python experiments/run_baseline.py --method single_llm_with_kg

# Run ablation study
python experiments/run_ablation.py --ablation no_debate
```

### Building Knowledge Graph

```bash
# Build KG from historical logs
python src/kg/builder.py --input data/raw/historical_logs/ --output data/kg/

# Validate KG
python src/kg/validate.py --kg data/kg/
```

## 📈 Evaluation Metrics

- **Accuracy / F1 Score**: Root cause identification correctness
- **Hallucination Rate**: Percentage of unsupported claims in explanations
- **Explanation Quality**: Human-rated correctness, clarity, and evidence-use
- **Agent Agreement**: Consensus level among reasoning agents
- **Latency & Cost**: Computational overhead vs single-agent methods

## 🗓️ Development Timeline

- **Phase 1** (Weeks 1-3): Literature review & problem formulation ✓
- **Phase 2** (Weeks 4-6): System design & architecture
- **Phase 3** (Weeks 5-8): Knowledge graph construction
- **Phase 4** (Weeks 8-12): Multi-agent implementation
- **Phase 5** (Weeks 12-15): Baselines & evaluation setup
- **Phase 6** (Weeks 15-19): Experiments & analysis

## 🔬 Datasets

This project uses:
- **Alibaba System Logs**: Production system failure logs
- **Telecom Logs**: Telecommunications infrastructure logs
- Custom synthetic logs for controlled experiments

## 🤝 Contributing

This is a research project. For collaboration inquiries, please contact the project maintainer.

## 📝 Citation

If you use this work, please cite:

```bibtex
@article{aetherlog2024,
  title={Multi-Agent Knowledge-Graph-Guided Reasoning for Reliable Log-Based Root Cause Analysis},
  author={Your Name},
  journal={arXiv preprint},
  year={2024}
}
```

## 📄 License

[Specify your license here]

## 🙏 Acknowledgments

- Based on AetherLog framework
- Inspired by "Society of Minds" multi-agent debate approaches
- Built with OpenAI GPT-4, Anthropic Claude, and Neo4j

## 📧 Contact

[Your contact information]

---

**Status**: 🚧 Under Development - Phase 2 (System Design)
