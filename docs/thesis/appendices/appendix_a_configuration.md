# Appendix A: Configuration Files

## A.1 Main Configuration (config/config.yaml)

```yaml
# Multi-Agent RCA System Configuration

# Knowledge Graph Settings
knowledge_graph:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "your_password_here"
  database: "neo4j"

# Local LLM Models (via Ollama)
local_models:
  log_parser:
    model: "qwen2:7b"
    temperature: 0.2
    max_tokens: 1500
  
  kg_retrieval:
    model: "qwen2:7b"
    temperature: 0.5
    max_tokens: 1000
  
  rca_reasoner_log:
    model: "mistral:7b"
    temperature: 0.7
    max_tokens: 2000
  
  rca_reasoner_kg:
    model: "llama2:7b"
    temperature: 0.7
    max_tokens: 2000
  
  rca_reasoner_hybrid:
    model: "qwen2:7b"
    temperature: 0.7
    max_tokens: 2000
  
  judge:
    model: "mistral:7b"
    temperature: 0.2
    max_tokens: 2000

# Debate Protocol Settings
debate:
  max_rounds: 3
  convergence_threshold: 5  # Stop if improvement < 5 points
  min_hypotheses_per_reasoner: 3
  max_hypotheses_per_reasoner: 5

# Log Processing Settings
log_processing:
  max_files_per_app: 6
  max_lines_per_app: 2500
  error_keywords:
    - "ERROR"
    - "WARN"
    - "Exception"
    - "failed"
    - "timeout"
    - "refused"
    - "unreachable"
    - "no space"

# Validation Settings
validation:
  hadoop1_labels_path: "loghub/Hadoop1/abnormal_label.txt"
  output_dir: "docs"
  
# Ollama Settings
ollama:
  base_url: "http://localhost:11434"
  timeout: 120
```

## A.2 Environment Setup (environment.yml)

```yaml
name: multimodel-rca
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip
  - numpy
  - pandas
  - scikit-learn
  - matplotlib
  - seaborn
  - jupyter
  - pyyaml
  - requests
  - tqdm
  - pip:
    - neo4j
    - ollama
    - pytest
    - black
    - flake8
```

## A.3 Requirements (requirements.txt)

```
# Core dependencies
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
pyyaml>=6.0

# LLM and API
requests>=2.31.0
ollama>=0.1.0

# Knowledge Graph
neo4j>=5.0.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0

# Development
pytest>=7.4.0
black>=23.0.0
flake8>=6.0.0
tqdm>=4.65.0

# Jupyter
jupyter>=1.0.0
ipykernel>=6.25.0
```
