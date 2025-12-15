# Week 8 Report: Single-Agent Baseline (Implementation Progress and Achievements)

## 1. Week 8 Goal
Deliver a **single-agent LLM baseline** for the Hadoop1 ground-truth validation workflow that:
- Uses **one LLM call** per application
- Avoids multi-agent debate and KG reasoning
- Produces **comparable outputs and metrics** to the existing validation pipeline
- Is runnable via CLI for reproducible experimentation

## 2. What Was Implemented
### 2.1 Single-agent baseline execution path
File: `scripts/validate_ground_truth.py`

Added:
- `SingleAgentBaselineAgent` (subclass of `BaseAgent`)
- New validation path inside `GroundTruthValidator.validate_hadoop1_applications(...)` controlled by a `pipeline` argument

Behavior:
- For `pipeline=single_agent`, the validator calls `SingleAgentBaselineAgent.process(parsed_data)`.
- For `pipeline=multi_agent`, the validator runs the existing debate-based RCA pipeline.

### 2.2 CLI support
File: `scripts/validate_ground_truth.py`

Added CLI flags:
- `--pipeline {multi_agent,single_agent}`
- `--single-agent-model <model_name>`
- `--output-results <path>`
- `--output-metrics <path>`

Default output behavior:
- Multi-agent uses:
  - `docs/HADOOP1_GROUND_TRUTH_RESULTS.json`
  - `docs/HADOOP1_GROUND_TRUTH_METRICS.json`
- Single-agent uses:
  - `docs/HADOOP1_SINGLE_AGENT_RESULTS.json`
  - `docs/HADOOP1_SINGLE_AGENT_METRICS.json`

### 2.3 Robustness fixes during smoke testing
During initial smoke tests, the following issues were fixed:
- Restored missing `GroundTruthValidator.compute_metrics(...)` method (was causing `AttributeError`).
- Ensured the single-agent run honors `--single-agent-model` correctly.
- Ensured that if the LLM response is not valid JSON, the system still uses the raw response text as the hypothesis so downstream label normalization works.

## 3. How to Run (Week 8 Baseline)
### 3.1 Full baseline run (all Hadoop1 apps)
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

### 3.2 Balanced sampling
```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline single_agent \
  --balanced-per-class 5 \
  --seed 42 \
  --single-agent-model qwen2:7b
```

### 3.3 Multi-agent run (reference)
```bash
python scripts/validate_ground_truth.py \
  --mode hadoop1 \
  --pipeline multi_agent \
  --all
```

## 4. Verification Completed
- Smoke test (`--max-apps 2`) successfully produced results + metrics.
- Balanced run (`--balanced-per-class 5`) successfully produced results + metrics.
- Full run (`--all`) successfully produced results + metrics.

The baseline artifacts are now generated deterministically by CLI arguments and can be reproduced.

## 5. Key Outcomes
- A working single-agent baseline exists and can be used as a Week 8 reference point.
- The baseline outputs follow the same schema pattern as the multi-agent validation, enabling direct comparison.
- The baseline highlights the value of multi-agent reasoning when comparing macro/per-class metrics.

## 6. Deliverables Created
- Experimental results (single-agent):
  - `docs/HADOOP1_SINGLE_AGENT_RESULTS.json`
  - `docs/HADOOP1_SINGLE_AGENT_METRICS.json`
- Week 8 experimental report:
  - `docs/week8_reports/WEEK_8_BASELINE_EXPERIMENTAL_REPORT.md`
- Week 8 progress report:
  - `docs/week8_reports/WEEK_8_PROGRESS_AND_ACHIEVEMENTS.md`
