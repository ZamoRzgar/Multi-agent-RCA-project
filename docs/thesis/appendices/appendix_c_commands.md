# Appendix C: Reproducibility Commands

## C.1 Environment Setup

### C.1.1 Create Conda Environment

```bash
# Create environment from file
conda env create -f environment.yml

# Or create manually
conda create -n multimodel-rca python=3.10
conda activate multimodel-rca
pip install -r requirements.txt
```

### C.1.2 Install Ollama and Models

```bash
# Install Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Download required models
ollama pull qwen2:7b
ollama pull mistral:7b
ollama pull llama2:7b

# Verify models
ollama list
```

### C.1.3 Setup Neo4j

```bash
# Install Neo4j Desktop from https://neo4j.com/download/
# Or use Docker:
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:5.12.0

# Verify connection
python scripts/debug_config.py
```

## C.2 Knowledge Graph Population

### C.2.1 Create Schema

```bash
python scripts/create_kg_schema.py
```

### C.2.2 Populate from Results

```bash
python scripts/populate_kg.py
```

### C.2.3 Verify Population

```bash
python scripts/query_kg.py
```

## C.3 Running Experiments

### C.3.1 Multi-Agent Pipeline (Full Hadoop1)

```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline multi_agent \
  --all \
  --max-lines 2500 \
  --max-files 6
```

**Output Files**:
- `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`
- `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

### C.3.2 Single-Agent Baseline (Full Hadoop1)

```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline single_agent \
  --all \
  --single-agent-model qwen2:7b
```

**Output Files**:
- `docs/HADOOP1_SINGLE_AGENT_RESULTS.json`
- `docs/HADOOP1_SINGLE_AGENT_METRICS.json`

### C.3.3 Balanced Sampling (5 per class)

```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline multi_agent \
  --balanced-per-class 5 \
  --seed 42
```

### C.3.4 Specific Applications

```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline multi_agent \
  --apps "application_1445062781478_0011,application_1445062781478_0012"
```

### C.3.5 Quick Smoke Test

```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline single_agent \
  --max-apps 2 \
  --single-agent-model qwen2:7b
```

## C.4 Running Tests

### C.4.1 End-to-End Test with KG

```bash
python tests/test_end_to_end_with_kg.py
```

### C.4.2 Dataset-Specific Tests

```bash
# Hadoop
python tests/test_hadoop_real_data.py

# HDFS
python tests/test_hdfs_real_data.py

# Spark
python tests/test_spark_real_data.py
```

### C.4.3 Unit Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_kg_query.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## C.5 Visualization

### C.5.1 Generate Result Visualizations

```bash
python scripts/visualize_results.py
```

**Output**: `docs/figures/*.png`

## C.6 CLI Reference

### C.6.1 validate_ground_truth.py Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | Validation mode | `hadoop1` |
| `--pipeline` | Pipeline type | `multi_agent` |
| `--all` | Run on all labeled apps | False |
| `--max-apps` | Maximum apps to process | 3 |
| `--balanced-per-class` | Sample N per class | 0 |
| `--seed` | Random seed | 42 |
| `--apps` | Comma-separated app IDs | "" |
| `--max-lines` | Max log lines per app | 2500 |
| `--max-files` | Max log files per app | 6 |
| `--single-agent-model` | Model for baseline | "" |
| `--output-results` | Results output path | auto |
| `--output-metrics` | Metrics output path | auto |

### C.6.2 Example Commands

```bash
# Full multi-agent run
python scripts/validate_ground_truth.py --mode hadoop1 --pipeline multi_agent --all

# Full single-agent run
python scripts/validate_ground_truth.py --mode hadoop1 --pipeline single_agent --all --single-agent-model qwen2:7b

# Balanced sample with seed
python scripts/validate_ground_truth.py --mode hadoop1 --balanced-per-class 5 --seed 42

# Custom output paths
python scripts/validate_ground_truth.py --mode hadoop1 --all \
  --output-results docs/custom_results.json \
  --output-metrics docs/custom_metrics.json
```

## C.7 Troubleshooting

### C.7.1 Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
systemctl restart ollama
# or
ollama serve
```

### C.7.2 Neo4j Connection Issues

```bash
# Check Neo4j status
curl http://localhost:7474

# Verify credentials in config.yaml
python scripts/debug_config.py
```

### C.7.3 Memory Issues

```bash
# Reduce max_tokens in config.yaml
# Or use smaller models:
ollama pull qwen2:1.5b
ollama pull mistral:7b-instruct-q4_0
```

### C.7.4 GPU Issues

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
nvidia-smi
```
