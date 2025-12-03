# Quick Start Guide

## Initial Setup (5 minutes)

### 1. Create Virtual Environment
```bash
cd /home/zamo/projects/log
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY or ANTHROPIC_API_KEY
# - NEO4J_PASSWORD (if using Neo4j)
```

### 4. Install Neo4j (Optional - for KG features)
```bash
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j

# Start Neo4j
sudo systemctl start neo4j
```

## Testing the Setup

### Run Tests (when implemented)
```bash
pytest tests/
```

### Test Individual Components
```python
# Test LLM client
python -c "from src.utils.llm_client import LLMClient; client = LLMClient(); print('LLM client OK')"

# Test agent initialization
python -c "from src.agents import LogParserAgent; agent = LogParserAgent(); print('Agents OK')"
```

## Next Steps

1. **Phase 2: System Design**
   - Create architectural diagrams in `docs/architecture/`
   - Design debate protocol details
   - Define data schemas

2. **Phase 3: Knowledge Graph**
   - Prepare historical log data in `data/raw/`
   - Implement KG construction pipeline
   - Build initial KG

3. **Phase 4: Agent Implementation**
   - Complete LLM integration in agents
   - Implement log parsing logic
   - Build debate mechanism

## Development Workflow

```bash
# Activate environment
source venv/bin/activate

# Run main system (once implemented)
python src/main.py --log-file data/raw/sample.log

# Run experiments
python experiments/run_evaluation.py

# Build knowledge graph
python src/kg/builder.py --input data/raw/historical_logs/
```

## Project Structure Overview

```
src/
├── agents/          # All agent implementations ✓
├── kg/             # Knowledge graph modules ✓
├── debate/         # Debate protocol ✓
└── utils/          # Utilities (LLM client, etc.) ✓

config/             # Configuration files ✓
data/              # Data storage ✓
experiments/       # Experiment scripts (TODO)
docs/             # Documentation (TODO)
tests/            # Test suite (TODO)
```

## Troubleshooting

**Import errors**: Make sure virtual environment is activated
```bash
source venv/bin/activate
```

**API key errors**: Check `.env` file has correct keys
```bash
cat .env | grep API_KEY
```

**Neo4j connection errors**: Ensure Neo4j is running
```bash
sudo systemctl status neo4j
```

## Resources

- **OpenAI API**: https://platform.openai.com/docs/api-reference
- **Anthropic API**: https://docs.anthropic.com/claude/reference
- **Neo4j Docs**: https://neo4j.com/docs/
- **Drain3 Parser**: https://github.com/logpai/Drain3
