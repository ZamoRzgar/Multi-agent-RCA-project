# AetherLog 2.0 - Complete System Architecture

**Project**: Multi-Agent Knowledge-Graph-Guided RCA System  
**Version**: 2.0  
**Status**: Phase 1 - Week 1 Complete ✅  
**Last Updated**: December 5, 2025

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Layers](#architecture-layers)
3. [Agent Architecture](#agent-architecture)
4. [Data Flow](#data-flow)
5. [Knowledge Graph Architecture](#knowledge-graph-architecture)
6. [Debate Protocol](#debate-protocol)
7. [Technology Stack](#technology-stack)

---

## 🎯 System Overview

### Purpose
AetherLog 2.0 is a **multi-agent system** that performs **Root Cause Analysis (RCA)** on system logs using:
- **Large Language Models (LLMs)** for reasoning
- **Knowledge Graphs (KG)** for historical context
- **Multi-agent debate** for reliability and accuracy

### Core Problem Solved
Traditional single-LLM RCA systems suffer from:
- ❌ **Hallucinations**: Making unsupported claims
- ❌ **Tunnel vision**: Missing alternative explanations
- ❌ **Limited reasoning**: No cross-checking of hypotheses

### Solution Approach
✅ **Multi-agent collaboration** with specialized perspectives  
✅ **Knowledge graph grounding** for factual accuracy  
✅ **Structured debate protocol** for hypothesis refinement  
✅ **Judge mechanism** for evidence-based selection

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  - CLI Interface                                                 │
│  - Web Dashboard (Future)                                        │
│  - API Endpoints                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
│  - MultiAgentRCASystem (Main Orchestrator)                      │
│  - DebateProtocol (Debate Management)                           │
│  - WorkflowEngine (Pipeline Control)                            │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Log Parser  │  │KG Retrieval │  │Log Reasoner │            │
│  │   Agent     │  │   Agent     │  │   Agent     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │KG Reasoner  │  │   Hybrid    │  │    Judge    │            │
│  │   Agent     │  │  Reasoner   │  │    Agent    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE LAYER                               │
│  - Knowledge Graph (Neo4j)                                       │
│  - Historical Incidents Database                                 │
│  - Causal Relationship Store                                     │
│  - Entity & Event Catalog                                        │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                   │
│  - Raw Logs (HDFS, BGL, Hadoop)                                 │
│  - Processed Logs                                                │
│  - Embeddings & Vectors                                          │
│  - Evaluation Datasets                                           │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                             │
│  - LLM Backend (Ollama)                                          │
│  - GPU Acceleration (CUDA)                                       │
│  - Graph Database (Neo4j)                                        │
│  - File Storage                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Architecture

### 1. **Log Parser Agent** ✅ IMPLEMENTED
**Role**: Extract structured information from raw logs

**Responsibilities**:
- Parse raw log text
- Extract events with timestamps
- Identify entities (services, hosts, components)
- Extract error messages
- Build temporal timeline

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
  "timeline": [...],
  "error_messages": [...]
}
```

**LLM**: Qwen2-7B (low temperature=0.2 for structured extraction)

**Status**: ✅ Complete (292 lines, 100% test pass)

---

### 2. **KG Retrieval Agent** ⏳ NEXT WEEK
**Role**: Query knowledge graph for relevant context

**Responsibilities**:
- Query similar historical incidents
- Find causal paths in KG
- Retrieve entity context
- Fetch related error patterns
- Return top-K relevant facts

**Input**: Parsed events + entities

**Output**:
```json
{
  "similar_incidents": [
    {
      "incident_id": "INC-2024-001",
      "similarity_score": 0.87,
      "root_cause": "Disk failure",
      "resolution": "Replace disk"
    }
  ],
  "causal_paths": [
    "DiskError → ReplicationFailure → DataLoss"
  ],
  "entity_context": {...}
}
```

**Technology**: Neo4j Cypher queries + embedding similarity

**Status**: ⏳ Week 2 (Dec 8-9)

---

### 3. **RCA Reasoner Agents** (3 Agents) ⏳ WEEK 2
**Role**: Generate root cause hypotheses from different perspectives

#### 3a. **Log-Focused Reasoner**
- **LLM**: Mistral-7B
- **Focus**: Analyze log patterns, sequences, anomalies
- **Strength**: Temporal reasoning, error propagation
- **Weakness**: May miss historical context

#### 3b. **KG-Focused Reasoner**
- **LLM**: LLaMA2-7B
- **Focus**: Leverage KG facts, causal chains, historical incidents
- **Strength**: Historical knowledge, proven patterns
- **Weakness**: May miss novel failures

#### 3c. **Hybrid Reasoner**
- **LLM**: Qwen2-7B
- **Focus**: Combine logs + KG for comprehensive analysis
- **Strength**: Balanced perspective
- **Weakness**: More complex reasoning

**Common Output Format**:
```json
{
  "hypothesis": "Root cause is disk failure on DataNode-03",
  "confidence": 0.85,
  "evidence": [
    "Log shows I/O errors on DataNode-03",
    "KG shows similar pattern in INC-2024-001"
  ],
  "reasoning_chain": [...]
}
```

**Status**: ⏳ Week 2 (Dec 10-12)

---

### 4. **Judge Agent** ⏳ WEEK 2
**Role**: Evaluate and score competing hypotheses

**Responsibilities**:
- Score each hypothesis (0-1)
- Compare evidence quality
- Rank hypotheses
- Provide feedback for refinement
- Select best explanation

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

**Status**: ⏳ Week 2 (Dec 13)

---

## 🔄 Data Flow

### End-to-End Pipeline

```
Raw Log File → Log Parser → KG Retrieval → 3 Reasoners → Debate → Judge → Final RCA
```

**Detailed Flow**:

1. **Log Parsing**: Extract 18 events, 11 entities, build timeline
2. **KG Retrieval**: Find 5 similar incidents, 3 causal paths
3. **Hypothesis Generation**: 3 agents produce hypotheses A, B, C
4. **Debate Round 1**: Judge scores (0.75, 0.82, 0.87) + feedback
5. **Refinement**: Agents improve to (0.80, 0.85, 0.91)
6. **Final Selection**: Winner = Hypothesis C' (score 0.91)

---

## 🗄️ Knowledge Graph Architecture

### Schema Design

**Node Types**:
1. **Incident**: Historical failure cases
2. **Event**: Log events with timestamps
3. **Entity**: System components (services, hosts, etc.)
4. **Error**: Error messages and types
5. **Template**: Log templates
6. **RootCause**: Known root causes

**Relationship Types**:
1. **CONTAINS**: Incident → Event
2. **INVOLVES**: Event → Entity
3. **REPORTS**: Event → Error
4. **CAUSES**: Event → Event (causal)
5. **PRECEDES**: Event → Event (temporal)
6. **SIMILAR_TO**: Incident → Incident
7. **HAS_ROOT_CAUSE**: Incident → RootCause
8. **MATCHES**: Event → Template

### Example KG Structure

```
(Incident:INC-001)
    ├─[CONTAINS]→ (Event:E1 {component: "DataNode"})
    │                 ├─[INVOLVES]→ (Entity:DataNode-03)
    │                 ├─[REPORTS]→ (Error:DiskIOError)
    │                 └─[CAUSES]→ (Event:E2)
    │
    ├─[HAS_ROOT_CAUSE]→ (RootCause:DiskFailure)
    └─[SIMILAR_TO]→ (Incident:INC-002)
```

---

## 🎭 Debate Protocol

### Protocol Flow

```
1. Initialize: Setup 3 reasoners + judge
2. Round 1: Generate initial hypotheses
3. Judge: Score and provide feedback
4. Round 2: Refine based on feedback
5. Judge: Re-score
6. Convergence Check: If converged or max rounds → select winner
7. Output: Final RCA result
```

### Debate Rules

1. **Max Rounds**: 3 (configurable)
2. **Convergence**: Score difference < 0.05
3. **Timeout**: 5 minutes per round
4. **Evidence Required**: All claims must cite log lines or KG facts

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM Backend** | Ollama | Local LLM inference |
| **LLM Models** | Qwen2-7B, Mistral-7B, LLaMA2-7B | Reasoning |
| **Knowledge Graph** | Neo4j 5.x | Graph database |
| **Programming** | Python 3.10 | Main language |
| **Environment** | Conda | Dependency management |
| **GPU** | CUDA 12.1 | GPU acceleration |
| **Testing** | pytest | Unit tests |
| **Logging** | loguru | Structured logging |

### Key Dependencies

```txt
ollama==0.1.0
neo4j==5.14.0
torch==2.1.0
spacy==3.7.0
pandas==2.1.3
loguru==0.7.2
pytest==7.4.3
```

---

## 📦 Project Structure

```
log/
├── src/
│   ├── agents/
│   │   ├── log_parser.py        # ✅ Complete
│   │   ├── kg_retrieval.py      # ⏳ Week 2
│   │   ├── rca_reasoner.py      # ⏳ Week 2
│   │   └── judge.py             # ⏳ Week 2
│   ├── debate/
│   │   └── protocol.py          # ⏳ Week 2
│   ├── kg/
│   │   ├── builder.py           # ⏳ Week 4-6
│   │   └── query.py             # ⏳ Week 2
│   └── utils/
│       ├── llm_client.py        # ✅ Complete
│       └── metrics.py           # ⏳ Week 10-12
├── tests/
│   └── unit/
│       └── test_log_parser.py   # ✅ Complete
├── data/
│   ├── raw/                      # HDFS, BGL, Hadoop logs
│   └── kg/                       # KG storage
├── docs/
│   ├── ARCHITECTURE.md           # This file
│   └── PROJECT_ROADMAP.md        # Detailed roadmap
└── config/
    └── config.yaml               # Configuration
```

---

## 🎯 Current Status

**Week 1 Complete** ✅
- Environment setup
- Log Parser Agent implemented
- 100% test pass rate
- Documentation complete

**Next Week (Week 2)** ⏳
- KG Retrieval Agent (Dec 8-9)
- 3 RCA Reasoner Agents (Dec 10-12)
- Judge Agent (Dec 13)
- Debate Protocol (Dec 14)

**Timeline**: 15 weeks total, 7% complete

---

## 📚 Research Questions

**RQ1**: Does multi-agent achieve higher accuracy than single-LLM?  
**RQ2**: Does debate reduce hallucinations?  
**RQ3**: Are multi-agent explanations better quality?  
**RQ4**: How does agent agreement relate to correctness?  
**RQ5**: Is computational overhead acceptable?

---

**For detailed roadmap, see**: [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md)  
**For Week 1 summary, see**: [WEEK1_SUMMARY.md](WEEK1_SUMMARY.md)
