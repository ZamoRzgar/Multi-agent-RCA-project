# Master's Thesis: Multi-Agent Knowledge-Graph-Guided Root Cause Analysis for Distributed System Logs

## Thesis Structure

### Front Matter
- Title Page
- Abstract
- Acknowledgments
- Table of Contents
- List of Figures
- List of Tables

### Chapter 1: Introduction
- 1.1 Problem Statement
- 1.2 Motivation
- 1.3 Research Questions
- 1.4 Contributions
- 1.5 Thesis Organization

### Chapter 2: Background and Related Work
- 2.1 Log Analysis in Distributed Systems
- 2.2 Root Cause Analysis (RCA)
- 2.3 Large Language Models for Log Analysis
- 2.4 Multi-Agent Systems
- 2.5 Knowledge Graphs for RCA
- 2.6 Summary and Research Gap

### Chapter 3: System Design and Architecture
- 3.1 System Overview
- 3.2 Agent Architecture
  - 3.2.1 Log Parser Agent
  - 3.2.2 KG Retrieval Agent
  - 3.2.3 RCA Reasoner Agents (Log, KG, Hybrid)
  - 3.2.4 Judge Agent
- 3.3 Knowledge Graph Design
  - 3.3.1 Schema Design
  - 3.3.2 Node and Relationship Types
- 3.4 Debate Protocol
  - 3.4.1 Multi-Round Refinement
  - 3.4.2 Convergence Detection
- 3.5 Data Flow

### Chapter 4: Implementation
- 4.1 Technology Stack
- 4.2 Agent Implementation Details
- 4.3 Knowledge Graph Population
- 4.4 Validation Framework
- 4.5 Single-Agent Baseline

### Chapter 5: Evaluation and Results
- 5.1 Experimental Setup
  - 5.1.1 Dataset: Hadoop1
  - 5.1.2 Evaluation Metrics
  - 5.1.3 Baseline Comparison
- 5.2 Multi-Agent Pipeline Results
  - 5.2.1 Strict (4-class) Evaluation
  - 5.2.2 Coarse (3-class) Evaluation
  - 5.2.3 Per-Class Analysis
- 5.3 Single-Agent Baseline Results
- 5.4 Comparative Analysis
- 5.5 Misclassification Audit
- 5.6 Cross-Dataset Generalization

### Chapter 6: Discussion
- 6.1 Key Findings
- 6.2 Multi-Agent vs Single-Agent
- 6.3 Role of Knowledge Graph
- 6.4 Debate Protocol Effectiveness
- 6.5 Limitations
- 6.6 Threats to Validity

### Chapter 7: Conclusion and Future Work
- 7.1 Summary of Contributions
- 7.2 Answers to Research Questions
- 7.3 Future Work
- 7.4 Concluding Remarks

### References

### Appendices
- A. Configuration Files
- B. Sample Log Data
- C. Full Experimental Results
- D. Code Repository

---

## Key Data Points for Thesis

### System Components
- 6 Agents: LogParser, KGRetrieval, LogReasoner, KGReasoner, HybridReasoner, Judge
- 3 LLMs: qwen2:7b, mistral:7b, llama2:7b (via Ollama)
- Neo4j Knowledge Graph: 38 nodes, 70 relationships, 14 incidents

### Evaluation Dataset
- Hadoop1: 55 labeled applications
- 4 failure types: normal (11), machine_down (28), network_disconnection (7), disk_full (9)
- Coarse labels: normal, connectivity (35), disk_full

### Multi-Agent Results (Week 6)
- Strict Accuracy: 21.8%
- Strict Macro F1: 21.6%
- Coarse Accuracy: 61.8%
- Coarse Macro F1: 39.1%
- Connectivity F1: 81.0%
- Disk_full F1: 36.4%

### Single-Agent Baseline Results (Week 8)
- Strict Accuracy: 50.9%
- Strict Macro F1: 17.3%
- Coarse Accuracy: 61.8%
- Coarse Macro F1: 25.8%
- Connectivity F1: 77.3%
- Disk_full F1: 0.0%

### Key Comparisons
- Multi-agent improves coarse macro-F1 by +13.3 percentage points
- Multi-agent detects disk_full (36.4% F1) while baseline fails (0%)
- Multi-agent has better class balance (detects minority classes)

---

## File Locations
- Chapter files: `docs/thesis/chapters/`
- Figures: `docs/thesis/figures/`
- Tables: `docs/thesis/tables/`
