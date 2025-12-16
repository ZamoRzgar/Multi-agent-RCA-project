# Abstract

Modern distributed systems generate massive volumes of log data that are critical for diagnosing failures and performing root cause analysis (RCA). Traditional approaches relying on manual inspection or rule-based pattern matching cannot scale to the complexity of cloud-native architectures. While Large Language Models (LLMs) offer promising capabilities for automated log analysis, single-LLM approaches suffer from hallucinations, limited context, and lack of verification mechanisms.

This thesis presents **AetherLog 2.0**, a multi-agent knowledge-graph-guided root cause analysis system that addresses these limitations. The system comprises six specialized agents: a Log Parser for structured extraction, a KG Retrieval Agent for historical context, three RCA Reasoners (Log-focused, KG-focused, and Hybrid), and a Judge Agent for hypothesis evaluation. These agents collaborate through a structured debate protocol that enables iterative hypothesis refinement and cross-validation.

We evaluate the system on the Hadoop1 dataset (55 labeled applications with 4 failure types) and compare against a single-agent LLM baseline. Results demonstrate that the multi-agent approach achieves:

- **+13.3 percentage points** improvement in coarse macro-F1 (39.1% vs 25.8%)
- **+36.4 percentage points** improvement in disk_full detection (36.4% F1 vs 0%)
- **81.0% F1** on connectivity-related failures
- **100% convergence rate** in the debate protocol

The multi-agent system prevents majority-class collapse, detects minority failure classes that the baseline misses entirely, and produces evidence-based, actionable explanations. We discuss limitations including normal class detection (0% for both systems) and identify future work directions including additional baselines, ablation studies, and knowledge graph expansion.

The complete implementation is provided as open-source software using local LLMs (Ollama), Neo4j for knowledge graph storage, and a Python-based agent framework.

**Keywords**: Root Cause Analysis, Multi-Agent Systems, Large Language Models, Knowledge Graphs, Log Analysis, Distributed Systems, Debate Protocol
