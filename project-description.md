Title of project : Multi-Agent Knowledge-Graph-Guided Reasoning for Reliable Log-Based Root Cause Analysis

I am building a multi-agent, knowledge-graph-guided system for reliable log-based root cause analysis. that the agents are specialized and collaborate through a knowledge graph to improve accuracy and reliability. by making a counsul and debating each other

Formalize the architecture of a multi-agent RCA system with:

Log Parser Agent

KG Retrieval Agent

Multiple RCA Reasoner Agents (log-focused, KG-focused, hybrid)

Judge Agent (and optional referee)


Design and evaluate a multi-agent, knowledge-graph-guided RCA system that improves accuracy, robustness, and explanation reliability compared to single-LLM baselines.

Integrate a domain knowledge graph as shared memory:

Construct or reuse a KG from historical logs / incident data.

Define how agents query and use KG facts during reasoning.

Design a debate and judging protocol:

How agents generate hypotheses.

How they critique, refine, and disagree.

How the judge scores and selects explanations.

Define evaluation metrics beyond accuracy:

Hallucination rate (KG/log-groundedness).

Explanation quality (correctness, clarity, evidence).

Agent agreement/consensus.

Experimentally validate:

Compare multi-agent AetherLog 2.0 to:

Single-LLM (no KG)

Single-LLM + KG (AetherLog 1.0)

Self-consistency / multi-sample LLM

Research Questions

You can write them like this:

RQ1 – Accuracy:
Does a multi-agent, KG-guided RCA framework achieve higher root cause identification accuracy than a single-LLM + KG baseline?

RQ2 – Reliability & Hallucination:
Does agent debate + KG grounding reduce hallucinations (unsupported claims) in explanations compared to:

single-LLM + KG

self-consistency sampling?

RQ3 – Explanation Quality:
Do explanations produced by the multi-agent system score higher in perceived correctness, clarity, and evidence-use according to human evaluators (e.g., SREs)?

RQ4 – Agent Dynamics:
How does agent agreement/disagreement relate to correctness?
When agents disagree, does the judge mechanism reliably choose the correct explanation?

RQ5 – Cost vs Benefit:
What is the computational and latency overhead of multi-agent RCA compared to single-agent methods, and is it acceptable for practical RCA workflows?






Phase 2 – System Design (Weeks 4–6)

Specify AetherLog 2.0 architecture:

Agent roles, inputs/outputs, and protocols (parsing → KG lookup → hypothesis generation → debate → judge).

Prompt design principles for each agent.

Define:

What information flows between agents.

How KG context is injected (what triples, how many).

Debate rules: number of rounds, how agents critique and refine.

Deliverables:

Architectural diagrams (block diagram, sequence diagram).

Written design section (for thesis + paper).

Phase 3 – Knowledge Graph Construction (Weeks 5–8)

Choose dataset(s):

AetherLog datasets (Alibaba/Telecom) or similar system logs.

Implement or reuse pipeline to:

Parse historical logs.

Extract entities, templates, and relations.

Normalize entities (clustering similar phrases).

Build KG and store in Neo4j or another graph DB.

Evaluate KG quality:

Number of nodes/edges; coverage of frequent causes.

Spot-check a few causal chains.

Deliverables:

Working KG instance.

Short KG design section (schema, example triples).

Phase 4 – Multi-Agent Implementation (Weeks 8–12)

Implement agents using Python + LLM API (or local LLM):

Agent 1: Log Parser – extract events/entities; produce structured representation.

Agent 2: KG Retrieval – given entities, retrieve top-K related KG facts and candidate causes.

Agents 3 & 4: RCA Reasoners – log-focused vs KG-focused prompts.

Agent 5 (optional): Referee reasoner.

Judge Agent: scoring and selection.

Implement debate loop:

Initial hypothesis generation.

Critique / rebuttal round.

Optional refinement.

Wrap everything in a reproducible pipeline:

Given a log case → final RCA prediction + explanation.

Phase 5 – Baselines & Evaluation Setup (Weeks 12–15)

Implement baselines:

Single-LLM with logs only.

Single-LLM with logs + KG (AetherLog-like).

Self-consistency with N samples (e.g., 5) + majority vote.

Multi-agent w/o debate and/or w/o judge (ablations).

Define metrics:

Accuracy / F1 for RCA prediction.

Hallucination detection procedure (compare explanation tokens to logs + KG).

Human evaluation protocol for explanation quality.

Agent agreement statistics.

Phase 6 – Experiments & Analysis (Weeks 15–19)

Run experiments:

On all test cases in selected datasets.

Record metrics for all methods.

Perform detailed analysis:

Where multi-agent wins / loses.

Examples of debate that corrects initial errors.

Effect of turning off debate, judge, or KG.

Visualize results:

Tables of metrics.

Charts (e.g. F1 vs method, hallucination rate vs method).

Example debate transcripts (short).