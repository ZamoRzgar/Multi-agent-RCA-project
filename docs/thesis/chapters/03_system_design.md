# Chapter 3: System Design and Architecture

This chapter presents the design and architecture of AetherLog 2.0, a multi-agent knowledge-graph-guided root cause analysis system. We describe the overall system structure, individual agent designs, knowledge graph schema, and the debate protocol that orchestrates multi-agent collaboration.

## 3.1 System Overview

AetherLog 2.0 is designed as a layered architecture with five distinct layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  - CLI Interface                                                 │
│  - Validation Scripts                                            │
│  - Result Visualization                                          │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
│  - DebateCoordinator (Multi-round debate management)            │
│  - GroundTruthValidator (Evaluation framework)                  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Log Parser  │  │KG Retrieval │  │Log Reasoner │             │
│  │   Agent     │  │   Agent     │  │   Agent     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │KG Reasoner  │  │   Hybrid    │  │    Judge    │             │
│  │   Agent     │  │  Reasoner   │  │    Agent    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYER                               │
│  - Knowledge Graph (Neo4j)                                       │
│  - Historical Incidents Database                                 │
│  - Entity and Root Cause Catalog                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                             │
│  - LLM Backend (Ollama with local models)                       │
│  - Graph Database (Neo4j)                                        │
│  - File Storage (Log datasets, results)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1.1 Design Principles

The system is designed according to the following principles:

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Modularity**: Agents can be replaced or upgraded independently
3. **Configuration-Driven**: Model selection and parameters are externalized to configuration files
4. **Graceful Degradation**: The system continues to function even if the knowledge graph is unavailable
5. **Reproducibility**: All experiments can be reproduced with documented commands

### 3.1.2 End-to-End Pipeline

For each incident, the system executes the following pipeline:

```
Raw Logs → Log Parser → KG Retrieval → 3 Reasoners → Debate → Judge → Final RCA
```

1. **Log Parsing**: Extract structured events, entities, and error messages from raw logs
2. **KG Retrieval**: Query the knowledge graph for similar historical incidents
3. **Hypothesis Generation**: Three reasoners generate competing hypotheses
4. **Debate Protocol**: Multi-round refinement with judge feedback
5. **Final Selection**: Judge selects the best hypothesis with confidence score

## 3.2 Agent Architecture

All agents inherit from a common `BaseAgent` class that provides:
- LLM client initialization and management
- Configuration loading from `config.yaml`
- Common prompt construction utilities
- Response parsing and error handling

### 3.2.1 Log Parser Agent

**Purpose**: Extract structured information from raw log text.

**Model**: qwen2:7b (temperature: 0.2 for structured extraction)

**Input**: Raw log text (string)

**Output**:
```json
{
  "events": [
    {
      "timestamp": "2025-12-05 10:00:00",
      "component": "DataNode",
      "action": "Block replication failed",
      "severity": "ERROR"
    }
  ],
  "entities": ["DataNode", "NameNode", "Block"],
  "error_messages": ["IOException: Connection refused"],
  "timeline": [...]
}
```

**Key Methods**:
- `process(raw_logs)`: Main entry point
- `_build_enhanced_prompt()`: Constructs detailed prompt with JSON schema
- `_parse_llm_response()`: Extracts JSON from LLM output
- `_clean_json_string()`: Auto-corrects malformed JSON
- `build_timeline()`: Orders events temporally

### 3.2.2 KG Retrieval Agent

**Purpose**: Query the knowledge graph for relevant historical context.

**Model**: qwen2:7b (temperature: 0.5)

**Input**: Parsed events and entities from Log Parser

**Output**:
```json
{
  "similar_incidents": [
    {
      "incident_id": "hadoop_scenario_1",
      "dataset": "Hadoop",
      "root_cause": "Network connectivity issue",
      "confidence": 0.95,
      "entity_matches": 2
    }
  ],
  "entity_contexts": {
    "Network": {
      "type": "resource",
      "incident_count": 5,
      "datasets": ["HDFS", "Hadoop"]
    }
  }
}
```

**Key Methods**:
- `process(input_data)`: Main entry point
- `_extract_entity_names()`: Extracts entities from input
- `query_similar_incidents()`: Wrapper for KGQuery
- `get_entity_context()`: Retrieves entity statistics

**Architecture**: The agent uses a clean separation between the agent layer and data access layer:
```
KGRetrievalAgent → KGQuery → Neo4j
```

### 3.2.3 RCA Reasoner Agents

Three specialized reasoner agents generate hypotheses from different perspectives:

#### Log-Focused Reasoner
**Model**: mistral:7b (temperature: 0.7)
**Focus**: Temporal patterns, error propagation, log-based evidence
**Strengths**: Detailed log analysis, sequence detection
**Weaknesses**: May miss historical context

#### KG-Focused Reasoner
**Model**: llama2:7b (temperature: 0.7)
**Focus**: Historical patterns, known failure modes, KG-based evidence
**Strengths**: Leverages past incidents, pattern matching
**Weaknesses**: May miss novel failures

#### Hybrid Reasoner
**Model**: qwen2:7b (temperature: 0.7)
**Focus**: Combined log and KG analysis
**Strengths**: Balanced perspective, comprehensive
**Weaknesses**: More complex reasoning

**Common Output Format**:
```json
{
  "hypothesis": "Root cause is network connectivity failure",
  "confidence": 0.85,
  "category": "network",
  "evidence": [
    "Log shows connection timeout at 10:05:00",
    "KG shows 5 similar incidents with network issues"
  ],
  "reasoning_chain": [...],
  "suggested_resolution": "Check network connectivity between nodes"
}
```

**Key Methods**:
- `process(input_data)`: Generate initial hypotheses
- `refine_hypotheses(feedback, other_hypotheses)`: Refine based on judge feedback
- `_build_prompt()`: Construct reasoning prompt
- `_parse_hypotheses()`: Extract structured hypotheses from LLM output

### 3.2.4 Judge Agent

**Purpose**: Evaluate, score, and rank competing hypotheses.

**Model**: mistral:7b (temperature: 0.2 for consistent evaluation)

**Input**: Hypotheses from all three reasoners, plus context

**Output**:
```json
{
  "top_hypothesis": {
    "hypothesis": "Network connectivity failure due to node timeout",
    "judge_score": 87,
    "confidence": 0.95,
    "category": "network",
    "source": "hybrid",
    "reasoning": "...",
    "evidence": [...]
  },
  "evaluated_hypotheses": [...],
  "consensus_analysis": "All reasoners agree on network-related issues",
  "debate_guidance": "Consider investigating timeout thresholds"
}
```

**Scoring Criteria**:
```python
score = (
    0.30 * evidence_support +      # How well evidence supports claim
    0.25 * logical_consistency +   # Internal logic coherence
    0.20 * completeness +          # Covers all observed symptoms
    0.15 * novelty +               # Considers alternative explanations
    0.10 * clarity                 # Clear and understandable
)
```

**Key Methods**:
- `process(input_data)`: Evaluate all hypotheses
- `_score_hypothesis()`: Calculate score for single hypothesis
- `_rank_hypotheses()`: Order by score
- `_generate_feedback()`: Provide improvement suggestions

## 3.3 Knowledge Graph Design

### 3.3.1 Schema Design

The knowledge graph uses a simple, practical schema focused on incident-level analysis:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Incident     │     │     Entity      │     │   RootCause     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ incident_id     │     │ name            │     │ description     │
│ dataset         │     │ type            │     │ confidence      │
│ scenario_id     │     │                 │     │ source          │
│ final_score     │     │                 │     │                 │
│ final_hypothesis│     │                 │     │                 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │    INVOLVES           │                       │
         ├───────────────────────┤                       │
         │                                               │
         │              HAS_ROOT_CAUSE                   │
         ├───────────────────────────────────────────────┤
         │
         │    SIMILAR_TO
         ├─────────────────────────────────────────────────┐
         │                                                 │
         ▼                                                 ▼
┌─────────────────┐                               ┌─────────────────┐
│    Incident     │                               │    Incident     │
└─────────────────┘                               └─────────────────┘
```

### 3.3.2 Node Types

**Incident Node**:
- `incident_id`: Unique identifier (e.g., "hadoop_scenario_1")
- `dataset`: Source dataset (HDFS, Hadoop, Spark)
- `scenario_id`: Scenario number within dataset
- `final_score`: Judge's final score (0-100)
- `final_hypothesis`: Text of the winning hypothesis

**Entity Node**:
- `name`: Entity name (e.g., "Network", "Configuration")
- `type`: Entity type (resource, config, component, issue)

**RootCause Node**:
- `description`: Text description of the root cause
- `confidence`: Confidence score (0-1)
- `source`: Which reasoner identified this cause

### 3.3.3 Relationship Types

**INVOLVES**: Links incidents to the entities they involve
- Direction: `(Incident)-[:INVOLVES]->(Entity)`
- Enables entity-based similarity search

**HAS_ROOT_CAUSE**: Links incidents to their identified root causes
- Direction: `(Incident)-[:HAS_ROOT_CAUSE]->(RootCause)`
- Enables root cause pattern analysis

**SIMILAR_TO**: Links incidents with similar characteristics
- Direction: `(Incident)-[:SIMILAR_TO]-(Incident)` (bidirectional)
- Created when incidents have similar scores (< 10 point difference) in the same dataset

### 3.3.4 Query Methods

The `KGQuery` class provides the following query methods:

**find_similar_incidents(entities, symptoms, top_k)**:
```cypher
MATCH (i:Incident)-[:INVOLVES]->(e:Entity)
WHERE e.name IN $entities
WITH i, count(DISTINCT e) as entity_matches
MATCH (i)-[:HAS_ROOT_CAUSE]->(rc:RootCause)
RETURN i.incident_id, i.dataset, i.final_score, 
       rc.description, rc.confidence, entity_matches
ORDER BY entity_matches DESC, i.final_score DESC
LIMIT $top_k
```

**find_causal_paths(source, target)**:
```cypher
MATCH path = (e1:Entity {name: $source})<-[:INVOLVES]-(i:Incident)-[:INVOLVES]->(e2:Entity {name: $target})
WHERE e1 <> e2
WITH i, e1, e2
MATCH (i)-[:HAS_ROOT_CAUSE]->(rc:RootCause)
RETURN i.incident_id, i.dataset, rc.description, rc.confidence
LIMIT 10
```

## 3.4 Debate Protocol

### 3.4.1 Protocol Overview

The debate protocol orchestrates multi-round hypothesis refinement:

```
Round 1: Initial Hypotheses
├── Log Reasoner → 3-5 hypotheses
├── KG Reasoner → 3-5 hypotheses
├── Hybrid Reasoner → 3-5 hypotheses
└── Judge → Scores, ranks, provides feedback

Round 2: Refinement
├── Log Reasoner → Refines based on feedback + other hypotheses
├── KG Reasoner → Refines based on feedback + other hypotheses
├── Hybrid Reasoner → Refines based on feedback + other hypotheses
└── Judge → Re-scores, checks convergence

Round 3 (if needed): Final Refinement
├── Continue if improvement > threshold
└── Stop if converged

Final: Select Best Hypothesis
└── Judge → Returns top hypothesis with confidence
```

### 3.4.2 Multi-Round Refinement

Each refinement round provides agents with:

1. **Previous Hypotheses**: Their own hypotheses from the previous round with scores
2. **Judge Feedback**: Specific strengths and weaknesses identified
3. **Other Hypotheses**: Top hypotheses from other reasoners
4. **Instruction**: Address weaknesses while preserving strengths

**Refinement Prompt Structure**:
```
You are refining your previous hypotheses based on feedback.

Your previous hypotheses:
- Hypothesis 1 (Score: 85): "..."
- Hypothesis 2 (Score: 78): "..."

Judge feedback:
- Strengths: Clear temporal analysis
- Weaknesses: Missing historical context

Other reasoners' top hypotheses:
- KG Reasoner: "Historical pattern suggests..."
- Hybrid Reasoner: "Combined analysis indicates..."

Instructions:
1. Address the identified weaknesses
2. Incorporate insights from other reasoners
3. Maintain your analytical strengths
4. Provide stronger evidence
```

### 3.4.3 Convergence Detection

The debate stops when one of the following conditions is met:

1. **Score Plateau**: Improvement between rounds is less than threshold (default: 5 points)
2. **Maximum Rounds**: Reached maximum number of rounds (default: 3)
3. **High Confidence**: Top hypothesis exceeds confidence threshold (default: 0.95)

**Convergence Check**:
```python
def check_convergence(self, current_score, previous_score, round_num):
    improvement = current_score - previous_score
    if improvement < self.convergence_threshold:
        return True  # Score plateau
    if round_num >= self.max_rounds:
        return True  # Maximum rounds reached
    return False
```

### 3.4.4 Cross-Pollination

A key feature of the debate protocol is cross-pollination of ideas:

- Each reasoner sees the top hypotheses from other reasoners
- This enables agents to incorporate insights they may have missed
- The hybrid reasoner often benefits most, combining log and KG perspectives
- Empirically, the hybrid reasoner wins 67-100% of debates

## 3.5 Data Flow

### 3.5.1 Complete Pipeline Flow

```
1. Input: Raw log files for an application
   └── e.g., loghub/Hadoop1/application_xxx/*.log

2. Log Parsing:
   ├── Load and sample log files (max 6 files, 2500 lines)
   ├── Extract error-focused lines (ERROR, WARN, Exception, etc.)
   └── Output: events[], entities[], error_messages[]

3. KG Retrieval:
   ├── Extract entity names from parsed data
   ├── Query Neo4j for similar incidents
   └── Output: similar_incidents[], entity_contexts{}

4. Hypothesis Generation (Round 1):
   ├── Log Reasoner: Analyze log patterns → hypotheses[]
   ├── KG Reasoner: Leverage historical data → hypotheses[]
   └── Hybrid Reasoner: Combine perspectives → hypotheses[]

5. Judge Evaluation (Round 1):
   ├── Collect all hypotheses (7-15 total)
   ├── Score each on 5 criteria
   ├── Rank by score
   └── Generate feedback for each reasoner

6. Refinement (Round 2+):
   ├── Each reasoner refines based on feedback
   ├── Judge re-evaluates
   └── Check convergence

7. Final Output:
   ├── Top hypothesis with score and confidence
   ├── Category (network, disk, config, etc.)
   ├── Evidence supporting the diagnosis
   └── Suggested resolution
```

### 3.5.2 Data Structures

**Parsed Data**:
```python
{
    "events": List[Dict],      # Structured log events
    "entities": List[Dict],    # Identified entities
    "error_messages": List[str], # Extracted error messages
    "raw_logs": str,           # Original log text (sampled)
    "timeline": List[Dict]     # Temporally ordered events
}
```

**KG Context**:
```python
{
    "similar_incidents": List[Dict],  # Past incidents
    "entity_contexts": Dict[str, Dict], # Entity statistics
    "causal_paths": List[List[Dict]]  # Causal relationships
}
```

**Hypothesis**:
```python
{
    "hypothesis": str,         # Root cause description
    "confidence": float,       # 0-1 confidence score
    "category": str,           # Failure category
    "evidence": List[str],     # Supporting evidence
    "reasoning_chain": List[str], # Step-by-step reasoning
    "suggested_resolution": str, # Recommended fix
    "source": str              # Which reasoner generated this
}
```

**Final Result**:
```python
{
    "top_hypothesis": Dict,    # Best hypothesis with judge score
    "evaluated_hypotheses": List[Dict], # All ranked hypotheses
    "rounds_completed": int,   # Number of debate rounds
    "convergence_reason": str, # Why debate stopped
    "total_time": float        # Execution time in seconds
}
```
