# Chapter 4: Implementation

This chapter describes the technical implementation of AetherLog 2.0, including the technology stack, agent implementations, knowledge graph population, and the validation framework used for evaluation.

## 4.1 Technology Stack

### 4.1.1 Programming Language and Environment

- **Language**: Python 3.10
- **Environment Management**: Conda (multimodel-rca environment)
- **Package Management**: pip with requirements.txt

### 4.1.2 Large Language Models

The system uses local LLMs via Ollama, avoiding API costs and enabling full control:

| Model | Size | Purpose | Agents |
|-------|------|---------|--------|
| qwen2:7b | 4.4GB | Structured extraction, hybrid reasoning | LogParser, KGRetrieval, HybridReasoner |
| mistral:7b | 4.1GB | Log analysis, evaluation | LogReasoner, JudgeAgent |
| llama2:7b | 3.8GB | KG-based reasoning | KGReasoner |

**Hardware**: NVIDIA RTX 3050 (6GB VRAM), achieving 85% GPU utilization during inference.

**Configuration** (`config/config.yaml`):
```yaml
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
```

### 4.1.3 Knowledge Graph Database

- **Database**: Neo4j 5.12.0 (Community Edition)
- **Connection**: Bolt protocol at `bolt://localhost:7687`
- **Driver**: neo4j Python driver

**Schema Constraints**:
```cypher
CREATE CONSTRAINT incident_id FOR (i:Incident) REQUIRE i.incident_id IS UNIQUE
CREATE CONSTRAINT entity_name FOR (e:Entity) REQUIRE e.name IS UNIQUE
CREATE INDEX incident_dataset FOR (i:Incident) ON (i.dataset)
CREATE INDEX incident_score FOR (i:Incident) ON (i.final_score)
```

### 4.1.4 Project Structure

```
log/
├── config/
│   └── config.yaml           # System configuration
├── src/
│   ├── agents/               # Agent implementations
│   │   ├── base_agent.py     # Base class for all agents
│   │   ├── log_parser.py     # Log Parser Agent
│   │   ├── kg_retrieval.py   # KG Retrieval Agent
│   │   ├── rca_log_reasoner.py
│   │   ├── rca_kg_reasoner.py
│   │   ├── rca_hybrid_reasoner.py
│   │   └── judge_agent.py    # Judge Agent
│   ├── debate/
│   │   └── debate_coordinator.py  # Debate orchestration
│   ├── kg/
│   │   ├── builder.py        # KG population
│   │   └── query.py          # KG query interface
│   └── utils/
│       └── local_llm_client.py  # Ollama client
├── scripts/
│   ├── validate_ground_truth.py  # Main evaluation script
│   ├── populate_kg.py        # KG population script
│   └── query_kg.py           # KG exploration
├── tests/                    # Test suite
├── loghub/                   # Log datasets
│   └── Hadoop1/              # Hadoop1 dataset
└── docs/                     # Documentation
```

## 4.2 Agent Implementation Details

### 4.2.1 Base Agent Class

All agents inherit from `BaseAgent`, which provides common functionality:

```python
class BaseAgent:
    def __init__(self, name: str, model: str = '', 
                 temperature: float = 0.7, max_tokens: int = 1000,
                 config: Dict = None):
        self.name = name
        self.config = config or self._load_config()
        
        # Agent-specific model mapping
        agent_type_map = {
            "LogParserAgent": "log_parser",
            "KGRetrievalAgent": "kg_retrieval",
            "HybridReasoner": "rca_reasoner_hybrid",
            "LogReasoner": "rca_reasoner_log",
            "KGReasoner": "rca_reasoner_kg",
            "JudgeAgent": "judge"
        }
        
        # Read model from config
        agent_config_key = agent_type_map.get(self.__class__.__name__)
        if agent_config_key and "local_models" in self.config:
            agent_config = self.config["local_models"].get(agent_config_key, {})
            self.model = agent_config.get("model", model)
            self.temperature = agent_config.get("temperature", temperature)
        
        # Initialize LLM client
        self.llm_client = LocalLLMClient(config=self.config)
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt."""
        return self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
```

### 4.2.2 Log Parser Implementation

The Log Parser Agent extracts structured information from raw logs:

```python
class LogParserAgent(BaseAgent):
    def process(self, raw_logs: str) -> Dict[str, Any]:
        prompt = self._build_enhanced_prompt(raw_logs)
        response = self._call_llm(prompt)
        parsed = self._parse_llm_response(response)
        
        # Build timeline from events
        if parsed.get('events'):
            parsed['timeline'] = self.build_timeline(parsed['events'])
        
        return parsed
    
    def _build_enhanced_prompt(self, raw_logs: str) -> str:
        return f"""You are a log analysis expert. Extract structured information from these logs.

LOGS:
{raw_logs[:8000]}

Return a JSON object with:
{{
  "events": [
    {{"timestamp": "...", "component": "...", "action": "...", "severity": "..."}}
  ],
  "entities": ["entity1", "entity2"],
  "error_messages": ["error1", "error2"]
}}

Focus on ERROR and WARN level events. Extract all unique entities (services, hosts, components).
"""
```

**Key Features**:
- Truncates logs to fit context window (8000 chars)
- Uses low temperature (0.2) for consistent structured output
- Includes JSON auto-correction for malformed responses
- Fallback parsing for edge cases

### 4.2.3 KG Retrieval Implementation

The KG Retrieval Agent queries Neo4j through the KGQuery interface:

```python
class KGRetrievalAgent(BaseAgent):
    def __init__(self, config: Dict = None):
        super().__init__(name="KGRetrievalAgent", config=config)
        self.kg_query = KGQuery(config=self.config)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Extract entity names from input
        entity_names = self._extract_entity_names(
            input_data.get('entities', []),
            input_data.get('events', [])
        )
        
        # Query similar incidents
        similar_incidents = self.kg_query.find_similar_incidents(
            entities=entity_names,
            symptoms=[],
            top_k=5
        )
        
        # Get entity context
        entity_contexts = {}
        for entity in entity_names[:5]:  # Limit to top 5
            context = self.kg_query.get_entity_info(entity)
            if context:
                entity_contexts[entity] = context
        
        return {
            'similar_incidents': similar_incidents,
            'entity_contexts': entity_contexts,
            'all_entities': self.kg_query.get_all_entities()
        }
```

### 4.2.4 Reasoner Implementation

Each reasoner generates hypotheses with a specialized focus:

```python
class HybridReasoner(RCAReasonerBase):
    def _build_prompt(self, input_data: Dict) -> str:
        events = input_data.get('events', [])
        entities = input_data.get('entities', [])
        similar_incidents = input_data.get('similar_incidents', [])
        
        return f"""You are a hybrid RCA expert combining log analysis and historical knowledge.

LOG EVENTS:
{self._format_events(events)}

ENTITIES INVOLVED:
{', '.join(e.get('name', str(e)) for e in entities[:10])}

SIMILAR PAST INCIDENTS:
{self._format_incidents(similar_incidents)}

Generate 3-5 root cause hypotheses. For each:
1. State the hypothesis clearly
2. Provide confidence (0-1)
3. Categorize (network, disk, config, memory, etc.)
4. List supporting evidence from logs AND history
5. Suggest resolution

Return as JSON array of hypothesis objects.
"""
    
    def refine_hypotheses(self, feedback: Dict, other_hypotheses: List) -> List[Dict]:
        """Refine hypotheses based on judge feedback."""
        prompt = self._build_refinement_prompt(feedback, other_hypotheses)
        response = self._call_llm(prompt)
        return self._parse_hypotheses(response)
```

### 4.2.5 Judge Implementation

The Judge Agent evaluates and scores hypotheses:

```python
class JudgeAgent(BaseAgent):
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Collect hypotheses from all reasoners
        all_hypotheses = []
        for key in ['hybrid_hypotheses', 'log_focused_hypotheses', 'kg_focused_hypotheses']:
            hypotheses = input_data.get(key, [])
            for h in hypotheses:
                h['source'] = key.replace('_hypotheses', '')
                all_hypotheses.append(h)
        
        # Score each hypothesis
        evaluated = []
        for hypothesis in all_hypotheses:
            score = self._score_hypothesis(hypothesis, input_data)
            hypothesis['judge_score'] = score
            evaluated.append(hypothesis)
        
        # Rank by score
        evaluated.sort(key=lambda x: x.get('judge_score', 0), reverse=True)
        
        return {
            'top_hypothesis': evaluated[0] if evaluated else None,
            'evaluated_hypotheses': evaluated,
            'consensus_analysis': self._analyze_consensus(evaluated),
            'debate_guidance': self._generate_guidance(evaluated)
        }
    
    def _score_hypothesis(self, hypothesis: Dict, context: Dict) -> int:
        """Score hypothesis on 5 criteria (0-100 scale)."""
        prompt = f"""Score this hypothesis on a 0-100 scale based on:
- Evidence support (30%): How well does evidence support the claim?
- Logical consistency (25%): Is the reasoning coherent?
- Completeness (20%): Does it explain all symptoms?
- Novelty (15%): Does it consider alternatives?
- Clarity (10%): Is it clear and actionable?

Hypothesis: {hypothesis.get('hypothesis', '')}
Evidence: {hypothesis.get('evidence', [])}
Category: {hypothesis.get('category', '')}

Context events: {context.get('events', [])[:5]}

Return only a number 0-100.
"""
        response = self._call_llm(prompt)
        try:
            return int(re.search(r'\d+', response).group())
        except:
            return 50  # Default score
```

## 4.3 Knowledge Graph Population

### 4.3.1 KG Builder

The `KGBuilder` class populates Neo4j from RCA result files:

```python
class KGBuilder:
    def __init__(self, config: Dict):
        kg_config = config.get('knowledge_graph', {})
        self.driver = GraphDatabase.driver(
            kg_config.get('uri', 'bolt://localhost:7687'),
            auth=(kg_config.get('user', 'neo4j'), 
                  kg_config.get('password', 'neo4j'))
        )
        self._create_schema()
    
    def populate_from_results(self, results_dir: str):
        """Load all result JSON files and store in KG."""
        for result_file in Path(results_dir).glob('*.json'):
            with open(result_file) as f:
                result_data = json.load(f)
            self._store_incident(result_data)
    
    def _store_incident(self, result_data: Dict):
        """Store a single incident with entities and root cause."""
        with self.driver.session() as session:
            # Create incident node
            session.run("""
                MERGE (i:Incident {incident_id: $id})
                SET i.dataset = $dataset,
                    i.final_score = $score,
                    i.final_hypothesis = $hypothesis
            """, id=result_data['incident_id'], ...)
            
            # Extract and link entities
            entities = self._extract_entities_from_text(
                result_data.get('final_hypothesis', '')
            )
            for entity in entities:
                session.run("""
                    MERGE (e:Entity {name: $name})
                    SET e.type = $type
                    WITH e
                    MATCH (i:Incident {incident_id: $incident_id})
                    MERGE (i)-[:INVOLVES]->(e)
                """, name=entity['name'], type=entity['type'], ...)
            
            # Create root cause node
            session.run("""
                MERGE (rc:RootCause {description: $desc})
                SET rc.confidence = $conf
                WITH rc
                MATCH (i:Incident {incident_id: $incident_id})
                MERGE (i)-[:HAS_ROOT_CAUSE]->(rc)
            """, desc=result_data.get('root_cause', ''), ...)
```

### 4.3.2 Entity Extraction

Entities are extracted using pattern matching:

```python
def _extract_entities_from_text(self, text: str) -> List[Dict]:
    """Extract entities from hypothesis text."""
    entities = []
    
    # Pattern-based extraction
    patterns = {
        'resource': r'\b(Network|Memory|Disk|CPU|Storage)\b',
        'component': r'\b(DataNode|NameNode|ResourceManager|Spark|HDFS)\b',
        'config': r'\b(Configuration|Settings|Config)\b',
        'issue': r'\b(Issue|Failure|Error|Problem)\b'
    }
    
    for entity_type, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in set(matches):
            entities.append({
                'name': match.title(),
                'type': entity_type
            })
    
    return entities
```

### 4.3.3 Population Statistics

After population, the KG contains:

| Node Type | Count |
|-----------|-------|
| Incidents | 14 |
| Entities | 12 |
| Root Causes | 12 |
| **Total Nodes** | **38** |

| Relationship Type | Count |
|-------------------|-------|
| INVOLVES | ~28 |
| HAS_ROOT_CAUSE | ~14 |
| SIMILAR_TO | ~28 |
| **Total Relationships** | **~70** |

## 4.4 Validation Framework

### 4.4.1 Ground Truth Validator

The `GroundTruthValidator` class in `scripts/validate_ground_truth.py` provides the evaluation framework:

```python
class GroundTruthValidator:
    def __init__(self, config: Dict):
        self.config = config
        self.labels = self._load_hadoop1_labels()
    
    def validate_hadoop1_applications(self, apps: List[str], 
                                       pipeline: str = 'multi_agent') -> List[Dict]:
        """Validate RCA on labeled Hadoop1 applications."""
        results = []
        
        for app_id in apps:
            # Load logs
            raw_logs = self._load_application_logs(app_id)
            
            # Run RCA pipeline
            if pipeline == 'single_agent':
                result = self._run_single_agent(raw_logs)
            else:
                result = self._run_multi_agent_pipeline(raw_logs)
            
            # Get ground truth
            ground_truth = self.labels.get(app_id, {})
            
            # Normalize prediction
            predicted = self._normalize_predicted_category(
                result.get('category', ''),
                result.get('hypothesis', '')
            )
            
            results.append({
                'application_id': app_id,
                'ground_truth': ground_truth.get('label'),
                'predicted_failure_type': predicted,
                'hypothesis': result.get('hypothesis'),
                'confidence': result.get('confidence'),
                'match': predicted == ground_truth.get('label')
            })
        
        return results
    
    def compute_metrics(self, results: List[Dict]) -> Dict:
        """Compute accuracy, precision, recall, F1 metrics."""
        # ... metric computation logic
```

### 4.4.2 Prediction Normalization

Predictions are normalized to match ground truth labels:

```python
def _normalize_predicted_category(self, category: str, hypothesis: str) -> str:
    """Map predicted category/hypothesis to ground truth label space."""
    text = f"{category} {hypothesis}".lower()
    
    # Disk full detection
    if any(kw in text for kw in ['disk', 'space', 'storage full', 'no space']):
        return 'disk_full'
    
    # Network/connectivity detection
    if any(kw in text for kw in ['network', 'connection', 'timeout', 'refused',
                                  'unreachable', 'disconnect']):
        return 'network_disconnection'
    
    # Machine down detection
    if any(kw in text for kw in ['machine down', 'node down', 'host down',
                                  'server down', 'node failure']):
        return 'machine_down'
    
    # Normal detection
    if any(kw in text for kw in ['normal', 'healthy', 'no issue', 'no error']):
        return 'normal'
    
    return 'unknown'
```

### 4.4.3 Coarse Label Mapping

For coarse evaluation, labels are grouped:

```python
def _to_coarse_label(self, strict_label: str) -> str:
    """Map strict label to coarse label."""
    if strict_label in ['machine_down', 'network_disconnection']:
        return 'connectivity'
    return strict_label  # 'normal', 'disk_full', 'unknown'
```

## 4.5 Single-Agent Baseline

### 4.5.1 Implementation

The single-agent baseline provides a comparison point:

```python
class SingleAgentBaselineAgent(BaseAgent):
    def __init__(self, model: str = '', temperature: float = 0.3, 
                 max_tokens: int = 1400, **kwargs):
        super().__init__(name='SingleAgentBaseline', model=model, 
                        temperature=temperature, max_tokens=max_tokens, **kwargs)
        if model:
            self.model = model  # Override with explicit model
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(input_data)
        response = self._call_llm(prompt)
        parsed = self._parse_response(response)
        
        # Fallback: use raw response as hypothesis if parsing fails
        hypothesis = parsed.get('hypothesis', '') or ''
        if not hypothesis and response:
            hypothesis = response.strip()
        
        return {
            'hypothesis': hypothesis,
            'category': parsed.get('category', 'unknown'),
            'confidence': parsed.get('confidence'),
            'source': 'single_agent',
            'raw_response': response
        }
    
    def _build_prompt(self, input_data: Dict) -> str:
        raw_logs = input_data.get('raw_logs', '')
        errors = input_data.get('error_messages', [])
        entities = input_data.get('entities', [])
        
        return f"""Analyze these system logs and identify the root cause of any failure.

LOGS (sample):
{raw_logs[:6000]}

ERROR MESSAGES:
{chr(10).join(errors[:10])}

ENTITIES:
{', '.join(str(e) for e in entities[:15])}

Provide your analysis as JSON:
{{
  "hypothesis": "The root cause is...",
  "category": "network|disk|config|memory|normal",
  "confidence": 0.0-1.0,
  "evidence": ["evidence1", "evidence2"],
  "suggested_resolution": "..."
}}
"""
```

### 4.5.2 CLI Support

The baseline is accessible via command-line:

```bash
# Run single-agent baseline on all Hadoop1 apps
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline single_agent \
  --all \
  --single-agent-model qwen2:7b

# Run multi-agent pipeline
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline multi_agent \
  --all
```

### 4.5.3 Key Differences from Multi-Agent

| Aspect | Single-Agent | Multi-Agent |
|--------|--------------|-------------|
| LLM Calls | 1 per app | 8-15 per app |
| Perspectives | 1 | 3 (Log, KG, Hybrid) |
| KG Integration | No | Yes |
| Debate/Refinement | No | Yes (2-3 rounds) |
| Cross-Validation | No | Yes (Judge) |
| Runtime | ~30 sec/app | ~3-5 min/app |
