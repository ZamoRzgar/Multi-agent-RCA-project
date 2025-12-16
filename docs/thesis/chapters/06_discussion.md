# Chapter 6: Discussion

This chapter interprets the experimental results, discusses key findings, and addresses limitations and threats to validity.

## 6.1 Key Findings

### 6.1.1 Multi-Agent Debate Improves Classification Balance

The most significant finding is that the multi-agent system produces more balanced predictions across classes, as evidenced by the 13.3 percentage point improvement in coarse macro-F1 (39.1% vs 25.8%).

This improvement stems from the debate protocol's ability to:
- **Prevent majority-class collapse**: Multiple reasoners with different perspectives generate diverse hypotheses
- **Cross-validate predictions**: The judge evaluates evidence quality, not just pattern matching
- **Refine through feedback**: Iterative refinement allows agents to address weaknesses

### 6.1.2 Minority Class Detection is the Key Differentiator

The multi-agent system's ability to detect `disk_full` failures (36.4% F1 vs 0%) represents the clearest advantage over the baseline. This capability emerges from:

- **KG-focused reasoning**: Historical patterns of disk failures inform hypothesis generation
- **Hybrid integration**: Combining log evidence with historical context
- **Evidence-based scoring**: The judge rewards hypotheses with specific, relevant evidence

### 6.1.3 Accuracy Alone is Insufficient for Evaluation

Our results demonstrate why accuracy is a poor metric for imbalanced classification:
- The single-agent baseline achieves 50.9% strict accuracy by predicting the majority class
- The multi-agent system achieves only 21.8% strict accuracy but better macro-F1
- Macro-averaged metrics provide a more honest assessment of classification quality

### 6.1.4 Symptom-Level vs Fault-Level Classification

The large gap between strict (21.8%) and coarse (61.8%) accuracy reveals a fundamental challenge: log-based RCA identifies *symptoms*, not *injected faults*.

When a machine goes down, the logs show connection failures—the same symptoms as a network disconnection. The system correctly identifies the symptom class (connectivity) even when it cannot distinguish the underlying fault type.

This suggests that:
- Coarse operational diagnosis is a more realistic evaluation target
- Strict fault classification may require additional signals beyond logs
- The system provides actionable information even when strict classification fails

## 6.2 Multi-Agent vs Single-Agent

### 6.2.1 Advantages of Multi-Agent Approach

**Diverse Perspectives**: Three specialized reasoners bring different analytical lenses:
- Log-focused: Temporal patterns, error propagation
- KG-focused: Historical patterns, known failure modes
- Hybrid: Integrated analysis combining both

**Cross-Validation**: The judge agent provides an independent evaluation layer that:
- Scores hypotheses on multiple criteria
- Identifies weaknesses for refinement
- Prevents overconfident incorrect predictions

**Iterative Refinement**: The debate protocol enables:
- Hypothesis improvement based on feedback
- Incorporation of insights from other reasoners
- Convergence toward well-supported conclusions

### 6.2.2 Costs of Multi-Agent Approach

**Computational Overhead**: The multi-agent system requires 8-15 LLM calls per application vs 1 for the baseline, resulting in:
- ~10x longer runtime (3-5 minutes vs 30 seconds)
- Higher resource utilization
- Increased complexity

**Implementation Complexity**: The multi-agent architecture requires:
- Careful orchestration of agent interactions
- Consistent data formats across agents
- Robust error handling for multi-step pipelines

### 6.2.3 When to Use Each Approach

**Use Multi-Agent When**:
- Accuracy on minority classes matters
- Time is not critical (batch processing)
- Historical context is available
- Explanation quality is important

**Use Single-Agent When**:
- Speed is critical (real-time alerting)
- Resources are constrained
- The failure distribution is known and stable
- A quick initial triage is sufficient

## 6.3 Role of Knowledge Graph

### 6.3.1 Current KG Contribution

The knowledge graph provides:
- **Historical Context**: 14 past incidents with root causes
- **Entity Statistics**: Frequency of entities across incidents
- **Similarity Matching**: Finding relevant past cases

In our evaluation, the KG-focused reasoner won 1/3 scenarios in Week 3 testing, demonstrating that historical knowledge adds value.

### 6.3.2 Limitations of Current KG

The current KG has limitations:
- **Small Size**: Only 14 incidents may not capture all patterns
- **Entity Mismatch**: HDFS entities differ from Hadoop/Spark entities in KG
- **No Temporal Patterns**: Event-level temporal relationships not implemented

### 6.3.3 Potential for Improvement

With a larger, more comprehensive KG, we expect:
- Better similarity matching with more historical cases
- Improved entity coverage across datasets
- Stronger KG-focused reasoning contributions

## 6.4 Debate Protocol Effectiveness

### 6.4.1 Convergence Behavior

The debate protocol demonstrates efficient convergence:
- 100% convergence rate across all tested scenarios
- Average of 2 rounds to reach consensus
- Score improvements of 2-5 points per round

### 6.4.2 Refinement Quality

Hypothesis refinement produces measurable improvements:
- Round 1 winner: Simple, log-focused hypothesis
- Round 2 winner: Comprehensive, multi-source hypothesis
- Evidence strengthens with each round
- Resolutions become more specific

### 6.4.3 Hybrid Reasoner Dominance

The hybrid reasoner wins 67-100% of debates, suggesting that:
- Combined perspectives are more valuable than single perspectives
- The debate protocol successfully synthesizes diverse inputs
- Multi-source reasoning is the key to quality

## 6.5 Limitations

### 6.5.1 Dataset Limitations

**Single Dataset**: We evaluate primarily on Hadoop1. While cross-dataset testing (HDFS, Spark) shows generalization, formal evaluation on other labeled datasets would strengthen claims.

**Label Semantics**: The "normal" label means "no injected fault," not "no errors." This affects interpretation of normal class performance.

**Class Imbalance**: With 50.9% `machine_down`, the dataset is heavily imbalanced, complicating evaluation.

### 6.5.2 System Limitations

**Normal Detection**: The system achieves 0% F1 on the normal class. This is partly a dataset issue (normal runs contain errors) but also reflects the system's design focus on finding problems.

**Disk Full Recall**: Only 22.2% recall on disk_full suggests the system needs stronger disk-related pattern recognition.

**Unknown Predictions**: 9/55 predictions (16.4%) are "unknown," indicating cases where the system cannot confidently classify.

### 6.5.3 Evaluation Limitations

**No Statistical Significance Tests**: We do not perform bootstrap confidence intervals or McNemar tests. The consistent pattern across metrics suggests meaningful differences, but formal tests would strengthen claims.

**Single Baseline**: We compare only against a single-agent LLM baseline. Additional baselines (CoT prompting, RAG-only, traditional ML) would provide broader context.

**No Ablation Studies**: We do not formally measure the contribution of individual components (KG, debate, specific reasoners).

## 6.6 Threats to Validity

### 6.6.1 Internal Validity

**Heuristic Label Mapping**: Predictions are mapped to ground truth labels using keyword matching. This may introduce errors if the hypothesis text does not contain expected keywords.

**LLM Variability**: LLM outputs are non-deterministic. Different runs may produce slightly different results, though we use low temperatures for consistency.

**Configuration Sensitivity**: Results may depend on specific model choices, temperatures, and prompt designs.

### 6.6.2 External Validity

**Dataset Representativeness**: Hadoop1 may not represent all distributed system failure modes. Results may not generalize to other systems (Kubernetes, microservices, etc.).

**Log Format Dependency**: The system is designed for semi-structured logs. Highly structured or unstructured logs may require adaptation.

**Scale**: We evaluate on 55 applications. Larger-scale evaluation would increase confidence.

### 6.6.3 Construct Validity

**Metric Choice**: We use accuracy and macro-F1, but other metrics (AUC, weighted F1) might tell different stories.

**Coarse vs Strict**: The choice to report coarse metrics as primary could be seen as cherry-picking. We report both transparently.

**Ground Truth Quality**: We assume the Hadoop1 labels are correct. Labeling errors would affect all evaluations.

## 6.7 Implications for Practice

### 6.7.1 For System Operators

The multi-agent RCA system can:
- Provide initial diagnosis for incident triage
- Suggest likely root causes with supporting evidence
- Reduce time-to-diagnosis for common failure patterns

However, operators should:
- Verify system suggestions against actual system state
- Not rely solely on automated diagnosis for critical decisions
- Use the system as a starting point, not a final answer

### 6.7.2 For Researchers

This work demonstrates that:
- Multi-agent debate improves LLM-based RCA quality
- Knowledge graphs provide valuable historical context
- Macro-averaged metrics are essential for imbalanced evaluation

Future research directions include:
- Larger knowledge graphs with more historical data
- Ablation studies to quantify component contributions
- Evaluation on diverse datasets and systems

### 6.7.3 For Tool Developers

Key design lessons:
- Multiple perspectives prevent single-model biases
- Iterative refinement improves hypothesis quality
- Evidence-based scoring reduces hallucinations
- Graceful degradation when KG is unavailable
