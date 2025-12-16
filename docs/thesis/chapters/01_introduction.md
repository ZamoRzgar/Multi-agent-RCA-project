# Chapter 1: Introduction

## 1.1 Problem Statement

Modern distributed systems generate massive volumes of log data that are critical for understanding system behavior, diagnosing failures, and performing root cause analysis (RCA). As cloud-native architectures become increasingly complex—spanning microservices, container orchestration platforms, and distributed storage systems—the challenge of analyzing logs to identify the root cause of failures has grown exponentially.

Traditional approaches to log analysis rely heavily on manual inspection by system administrators or rule-based pattern matching systems. These methods suffer from several fundamental limitations:

1. **Scale**: A single Hadoop cluster can generate millions of log entries per hour, making manual analysis infeasible.
2. **Complexity**: Failures in distributed systems often manifest as cascading events across multiple components, requiring correlation of logs from different sources.
3. **Domain Knowledge**: Effective RCA requires deep understanding of system architecture, failure modes, and historical patterns—knowledge that is often siloed within individual experts.
4. **Timeliness**: Production incidents require rapid diagnosis, but manual analysis is inherently slow.

Recent advances in Large Language Models (LLMs) have shown promise for automated log analysis. However, single-LLM approaches face their own challenges:

- **Hallucinations**: LLMs may generate plausible-sounding but incorrect diagnoses without supporting evidence.
- **Tunnel Vision**: A single model may fixate on one interpretation, missing alternative explanations.
- **Limited Context**: LLMs lack access to historical incident data and organizational knowledge.
- **No Cross-Validation**: Without multiple perspectives, there is no mechanism to verify or refine hypotheses.

This thesis addresses these challenges by proposing a **multi-agent system** that combines multiple specialized LLM agents with a **knowledge graph** of historical incidents, orchestrated through a **structured debate protocol** to produce reliable, evidence-based root cause analyses.

## 1.2 Motivation

The motivation for this research stems from three key observations:

### 1.2.1 The Reliability Problem

Single-LLM systems for RCA lack mechanisms for self-correction. When an LLM generates an incorrect hypothesis, there is no built-in process to challenge or refine it. In contrast, human expert teams naturally engage in debate and cross-validation when diagnosing complex failures. This suggests that a multi-agent approach, where different agents can challenge and refine each other's hypotheses, may produce more reliable results.

### 1.2.2 The Knowledge Gap

LLMs are trained on general corpora and lack access to organization-specific historical data. When a similar failure has occurred before, human experts can recall past incidents and apply lessons learned. A knowledge graph that captures historical incidents, their root causes, and the entities involved can provide this contextual grounding, reducing hallucinations and improving accuracy.

### 1.2.3 The Specialization Opportunity

Different aspects of RCA benefit from different analytical approaches:
- **Log-focused analysis** excels at identifying temporal patterns and error propagation.
- **Knowledge-graph-focused analysis** leverages historical patterns and known failure modes.
- **Hybrid analysis** combines both perspectives for comprehensive diagnosis.

A multi-agent architecture allows each agent to specialize in one approach, with a judge agent synthesizing the best elements from each.

## 1.3 Research Questions

This thesis investigates the following research questions:

**RQ1: Does a multi-agent approach achieve higher accuracy than a single-agent LLM baseline for root cause analysis?**

We hypothesize that the combination of multiple specialized agents, each contributing different perspectives, will produce more accurate diagnoses than a single LLM call.

**RQ2: Does a structured debate protocol reduce hallucinations and improve reliability?**

We hypothesize that multi-round refinement, where agents receive feedback and can revise their hypotheses, will lead to more evidence-grounded and reliable conclusions.

**RQ3: Does knowledge graph integration improve RCA quality?**

We hypothesize that access to historical incident data through a knowledge graph will provide valuable context that improves diagnosis accuracy, particularly for recurring failure patterns.

**RQ4: Are the generated explanations high-quality and actionable?**

Beyond accuracy metrics, we evaluate whether the system produces explanations that are specific, evidence-based, and actionable for system administrators.

## 1.4 Contributions

This thesis makes the following contributions:

### 1.4.1 System Architecture
We design and implement **AetherLog 2.0**, a multi-agent RCA system comprising six specialized agents:
- **Log Parser Agent**: Extracts structured information from raw logs
- **KG Retrieval Agent**: Queries historical incidents from a knowledge graph
- **Log-Focused Reasoner**: Generates hypotheses based on log pattern analysis
- **KG-Focused Reasoner**: Generates hypotheses leveraging historical knowledge
- **Hybrid Reasoner**: Combines log and KG perspectives
- **Judge Agent**: Evaluates, scores, and selects the best hypothesis

### 1.4.2 Debate Protocol
We implement a **multi-round debate protocol** that enables:
- Iterative hypothesis refinement based on judge feedback
- Cross-pollination of ideas between agents
- Convergence detection to avoid unnecessary iterations
- Evidence-based scoring on multiple criteria

### 1.4.3 Knowledge Graph Integration
We design and populate a **Neo4j knowledge graph** with:
- Historical incident nodes with root causes and confidence scores
- Entity nodes representing system components
- Relationships capturing involvement and similarity patterns
- Query methods for retrieving relevant historical context

### 1.4.4 Empirical Evaluation
We conduct a comprehensive evaluation on the **Hadoop1 dataset** (55 labeled applications) comparing:
- Multi-agent pipeline vs. single-agent baseline
- Strict (4-class) vs. coarse (3-class) classification
- Per-class precision, recall, and F1 scores
- Qualitative misclassification analysis

### 1.4.5 Open-Source Implementation
We provide a complete, reproducible implementation using:
- Local LLMs via Ollama (qwen2:7b, mistral:7b, llama2:7b)
- Neo4j for knowledge graph storage
- Python-based agent framework
- Comprehensive test suite and documentation

## 1.5 Thesis Organization

The remainder of this thesis is organized as follows:

**Chapter 2: Background and Related Work** provides the theoretical foundation, covering log analysis techniques, root cause analysis methods, LLM applications, multi-agent systems, and knowledge graphs for RCA.

**Chapter 3: System Design and Architecture** presents the overall system architecture, detailing each agent's role, the knowledge graph schema, and the debate protocol.

**Chapter 4: Implementation** describes the technical implementation, including the technology stack, agent implementations, and validation framework.

**Chapter 5: Evaluation and Results** presents the experimental setup, evaluation metrics, and detailed results comparing the multi-agent system against the single-agent baseline.

**Chapter 6: Discussion** interprets the results, discusses key findings, and addresses limitations and threats to validity.

**Chapter 7: Conclusion and Future Work** summarizes the contributions, answers the research questions, and outlines directions for future research.
