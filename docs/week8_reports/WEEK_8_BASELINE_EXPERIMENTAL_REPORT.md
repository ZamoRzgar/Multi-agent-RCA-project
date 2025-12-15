# Week 8 Experimental Report: Single-Agent LLM Baseline vs Multi-Agent Pipeline (Hadoop1)

## 1. Objective
This report documents a **single-agent LLM baseline** for the Hadoop1 ground-truth validation task and compares it against the existing **multi-agent** RCA pipeline.

The goal of the baseline is to provide a simple reference point:
- One LLM call per application
- No debate
- No knowledge graph reasoning
- Same evaluation outputs and metrics format as the multi-agent pipeline

## 2. Dataset and Labels
- **Dataset**: LogHub Hadoop1 (`loghub/Hadoop1/`)
- **Ground truth labels**: `loghub/Hadoop1/abnormal_label.txt`
- **Strict labels (4-class)**:
  - `normal`
  - `machine_down`
  - `network_disconnection`
  - `disk_full`
- **Coarse labels (3-class)**:
  - `normal`
  - `connectivity` (merge of `machine_down` and `network_disconnection`)
  - `disk_full`

## 3. Implementation Summary
### 3.1 Single-agent baseline
Implemented in `scripts/validate_ground_truth.py` as:
- `SingleAgentBaselineAgent` (inherits `BaseAgent`)
- Activated with `--pipeline single_agent`

The baseline:
- Builds a prompt from `raw_logs`, extracted error messages, and entities
- Calls the local LLM once per application
- Uses lightweight post-processing to map the response into the evaluation label space

Important robustness behavior:
- If the LLM does not return strict JSON, the system uses the **raw response text as the hypothesis** so `_normalize_predicted_category(...)` can still classify.

### 3.2 Multi-agent pipeline
The existing pipeline is activated with `--pipeline multi_agent` and includes:
- KG retrieval (when available)
- Multiple reasoners + judge with debate coordination

## 4. Reproducibility / How to Run
All commands are executed from the repo root.

### 4.1 Requirements
- Python environment configured for this repo
- Hadoop1 data present at `loghub/Hadoop1/`
- Local LLM server running via Ollama

To use the same baseline model as this report:
- Ensure Ollama has `qwen2:7b` available

### 4.2 Run single-agent baseline (full 55 apps)
```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline single_agent \
  --all \
  --single-agent-model qwen2:7b
```
Outputs:
- `docs/HADOOP1_SINGLE_AGENT_RESULTS.json`
- `docs/HADOOP1_SINGLE_AGENT_METRICS.json`

### 4.3 Run multi-agent pipeline (full 55 apps)
```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline multi_agent \
  --all
```
Outputs:
- `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`
- `docs/HADOOP1_GROUND_TRUTH_METRICS.json`

Note:
- The multi-agent path may attempt KG retrieval. If Neo4j is not configured/running, KG retrieval may be empty or error-handled (implementation-dependent).
- The single-agent baseline does **not** require Neo4j.

### 4.4 Quick smoke test (2 apps)
```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline single_agent \
  --max-apps 2 \
  --max-lines 2500 \
  --max-files 6 \
  --single-agent-model qwen2:7b
```

## 5. Evaluation Protocol
For each application, the validator produces:
- `predicted_failure_type_from_hypothesis`: derived from category + hypothesis text via `_normalize_predicted_category(...)`
- `predicted_failure_type_from_indicators`: regex indicator score winner
- `predicted_failure_type`: uses hypothesis-derived type, with a fallback to indicators if hypothesis-derived is `unknown`

Metrics are computed for:
- **Strict** prediction vs `ground_truth`
- **Coarse** prediction vs `ground_truth_coarse`

In addition to accuracy, we report macro-averaged precision/recall/F1 and per-class results to reduce the impact of class imbalance.

## 6. Results
### 6.1 Single-agent baseline (qwen2:7b) on all 55 apps
Source: `docs/HADOOP1_SINGLE_AGENT_METRICS.json`

#### Strict (4-class)
- Accuracy: **50.9%**
- Macro Precision/Recall/F1: **13.2% / 25.0% / 17.3%**

Per-class F1:
- `normal`: 0.0%
- `machine_down`: 69.1%
- `network_disconnection`: 0.0%
- `disk_full`: 0.0%

Confusion highlights:
- The baseline predicted **`machine_down` for 53/55** applications.
- It predicted **`disk_full` for 2/55** applications.

#### Coarse (3-class)
- Accuracy: **61.8%**
- Macro Precision/Recall/F1: **21.4% / 32.4% / 25.8%**

Per-class F1:
- `normal`: 0.0%
- `connectivity`: 77.3%
- `disk_full`: 0.0%

### 6.2 Multi-agent pipeline on all 55 apps (Week 6 reference)
Source: `docs/week6_validation_results/MAIN_HADOOP1_GROUND_TRUTH_METRICS.json`

#### Strict (4-class)
- Accuracy: **21.8%**
- Macro Precision/Recall/F1: **41.7% / 30.6% / 21.6%**

Per-class F1:
- `normal`: 0.0%
- `machine_down`: 22.2%
- `network_disconnection`: 27.9%
- `disk_full`: 36.4%

#### Coarse (3-class)
- Accuracy: **61.8%**
- Macro Precision/Recall/F1: **57.6% / 37.9% / 39.1%**

Per-class F1:
- `normal`: 0.0%
- `connectivity`: 81.0%
- `disk_full`: 36.4%

## 7. Comparison and Interpretation
### 7.1 Accuracy is misleading on this dataset
The Hadoop1 dataset is imbalanced:
- Strict supports in the baseline run: `machine_down` (28/55) dominates.
- Coarse supports: `connectivity` (35/55) dominates.

Because the baseline collapses to predicting the majority-like label (mostly `machine_down` / `connectivity`), it achieves:
- **High strict accuracy (50.9%)** mostly because `machine_down` is ~half the dataset.
- **Same coarse accuracy as multi-agent (61.8%)** largely because `connectivity` is ~64% of the dataset.

### 7.2 Macro-F1 and per-class F1 show the real baseline quality
- The baseline **fails completely** on `normal` and `disk_full` (0% F1).
- The baseline also fails on `network_disconnection` in strict space (0% F1).

Macro-F1 (better reflects robustness across classes):
- Strict macro-F1:
  - Single-agent: **17.3%**
  - Multi-agent: **21.6%**
- Coarse macro-F1:
  - Single-agent: **25.8%**
  - Multi-agent: **39.1%**

Conclusion:
- The **multi-agent pipeline is meaningfully stronger** on balanced, per-class performance (macro-F1), especially on `disk_full`.
- The single-agent baseline provides a valid low-complexity reference but is not competitive in robust classification.

## 8. Artifacts
- Baseline results:
  - `docs/HADOOP1_SINGLE_AGENT_RESULTS.json`
  - `docs/HADOOP1_SINGLE_AGENT_METRICS.json`
- Multi-agent reference metrics:
  - `docs/week6_validation_results/MAIN_HADOOP1_GROUND_TRUTH_METRICS.json`

## 9. Limitations
- The baseline mapping relies on keyword-style normalization (`_normalize_predicted_category`) and may collapse to majority classes.
- Both systems currently achieve 0% F1 on the `normal` class under this evaluation definition (indicating the task is hard and the label space may not align cleanly with log artifacts).
